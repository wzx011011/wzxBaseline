import os, time, json, socket, subprocess, atexit, signal, threading
from pathlib import Path
from typing import Optional

from .constants import *


# ----------------- 子进程（Server）托管 -----------------
def is_process_running_by_name(name="CrealityPrint.exe"):
    try:
        out = subprocess.check_output(
            ["tasklist", "/FI", f"IMAGENAME eq {name}"],
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return name.lower() in out.lower()
    except Exception:
        return False


def kill_process_by_name(name="CrealityPrint.exe", timeout=10):
    """
    强制停止指定名称的进程
    
    Args:
        name: 进程名称
        timeout: 等待进程退出的超时时间（秒）
        
    Returns:
        bool: 是否成功停止（或进程本来就不存在）
    """
    if not is_process_running_by_name(name):
        return True
    
    print(f"[SlicerProc] 发现已运行的 {name}，正在强制停止...")
    
    try:
        # 使用 taskkill 强制终止进程及其子进程
        result = subprocess.run(
            ["taskkill", "/IM", name, "/T", "/F"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        
        # 等待进程完全退出
        end_time = time.time() + timeout
        while time.time() < end_time:
            if not is_process_running_by_name(name):
                print(f"[SlicerProc] {name} 已成功停止")
                # 额外等待一小段时间确保端口释放
                time.sleep(1.0)
                return True
            time.sleep(0.5)
        
        print(f"[SlicerProc] 警告: {name} 停止超时")
        return False
        
    except Exception as e:
        print(f"[SlicerProc] 停止进程失败: {e}")
        return False


class SlicerProc:
    def __init__(self, exe_path: str, log_path: str, cli_args: list[str], host, port):
        self.exe_path = str(exe_path)
        self.log_path = str(log_path)
        self.log_file = None
        self.args = cli_args
        self.proc: Optional[subprocess.Popen] = None
        self.host = host
        self.port = port
        self.spawned_by_me = False
        self._orig_handlers = {}

    def start_if_needed(self):
        exe = Path(self.exe_path)
        if not exe.is_file(): raise FileNotFoundError(f"EXE not found: {self.exe_path}")

        proc_name = Path(self.exe_path).name
        
        # 启动前强制停止已有进程，确保干净的启动环境
        if is_process_running_by_name(proc_name):
            kill_process_by_name(proc_name)

        env = os.environ.copy()
        # 重要，拉起子进程的时候会注册一个环境变量来绕开弹窗
        env["SLICER_TEST_RESTORE"] = "discard"
        # 使用外部传入的 CREALITY_PRINTER_LOG_PATH（目录）优先，否则落回默认常量
        env["CREALITY_PRINTER_LOG_PATH"] = os.getenv("CREALITY_PRINTER_LOG_PATH", CREALITY_PRINTER_LOG_PATH)

        # 让 C++ 读取端口/复用配置
        env["SLICER_TEST_PORT"] = str(self.port)
        env["SLICER_TEST_REUSE"] = "1"

        self.log_file = open(self.log_path, "a", encoding="utf-8", buffering=1)
        # 创建新控制台以确保 GUI 前台可见
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
        self.proc = subprocess.Popen(
            args=self.args, cwd=str(exe.parent), env=env,
            stdout=self.log_file, stderr=subprocess.STDOUT,
            creationflags=flags, close_fds=False,
        )
        self.spawned_by_me = True

        atexit.register(self._cleanup)
        self._install_signal_handlers()

        # 首次拉起切片器可能较慢（首次初始化/资源加载/杀毒扫描等），放宽等待时间。
        wait_port(self.host, self.port, timeout=180)

    def _install_signal_handlers(self):
        self._orig_handlers.clear()
        for sig in (getattr(signal, "SIGTERM", None),
                    getattr(signal, "SIGBREAK", None),
                    getattr(signal, "SIGINT", None)):
            if not sig:
                continue
            try:
                self._orig_handlers[sig] = signal.getsignal(sig)
                signal.signal(sig, self._graceful_exit)
            except Exception:
                pass

    def _restore_signal_handlers(self):
        for sig, handler in list(self._orig_handlers.items()):
            try:
                signal.signal(sig, handler)
            except Exception:
                pass
        self._orig_handlers.clear()

    def _graceful_exit(self, signum=None, frame=None):
        self._cleanup()
        if signum == getattr(signal, "SIGINT", None):
            # 保留 Ctrl+C 的 KeyboardInterrupt 语义，让 pytest 能正确终止。
            raise KeyboardInterrupt
        raise SystemExit(0)

    def _cleanup(self):
        try:
            try:
                if self.log_file:
                    try:
                        self.log_file.flush()
                        self.log_file.close()
                    except Exception:
                        pass
                if not self.spawned_by_me or not self.proc:
                    return
                pid = self.proc.pid
                try:
                    os.kill(pid, getattr(signal, "CTRL_BREAK_EVENT", signal.SIGTERM))
                    self.proc.wait(timeout=5)
                except Exception:
                    pass
                subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               creationflags=subprocess.CREATE_NO_WINDOW)
                self.proc = None
            except Exception:
                pass
        except Exception:
            pass
        finally:
            self._restore_signal_handlers()

    def stop(self):
        self._cleanup()


# ----------------- 基础：等待端口 -----------------
def wait_port(host, port, timeout=60):
    end, last = time.time() + timeout, None
    while time.time() < end:
        try:
            with socket.create_connection((host, port), timeout=1):
                return
        except OSError as e:
            last = e
            time.sleep(0.25)
    raise TimeoutError(f"Port {host}:{port} not ready: {last}")


# ----------------- 持久客户端（with 上下文） -----------------
class EngineClient:
    """持久 TCP 客户端，协议：'cmd;{json}' <-> 'cmd_respone;{json}'"""

    def __init__(self, host, port, timeout=30.0, reuse_addr=True):
        self.host, self.port, self.timeout, self.reuse_addr = host, port, timeout, reuse_addr
        self._sock: Optional[socket.socket] = None
        self._buf = ""
        self._lock = threading.Lock()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

    def connect(self):
        if self._sock: return
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.reuse_addr:
            try:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            except OSError:
                pass
        s.settimeout(self.timeout)
        s.connect((self.host, self.port))
        self._sock, self._buf = s, ""

    def close(self):
        if not self._sock: return
        try:
            self._sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            self._sock.close()
        finally:
            self._sock = None
            self._buf = ""

    def _reconnect(self):
        self.close()
        self.connect()

    def send_command(self, cmd: str, obj: Optional[dict] = None, timeout: Optional[float] = None) -> dict:
        obj = obj or {}
        data = f"{cmd};{json.dumps(obj, separators=(',', ':'))}".encode("utf-8")
        with self._lock:
            if not self._sock: self.connect()
            s = self._sock
            s.settimeout(timeout or self.timeout)
            #接受完所有数据再发送
            # 先读取所有剩余数据，防止缓冲区数据干扰
            s.settimeout(0.1)  # 设置短超时，非阻塞检查
            try:
                while True:
                    try:
                        chunk = s.recv(8192)
                        if not chunk:  # 连接关闭
                            break
                        # 处理读取到的数据
                        self._buf += chunk.decode("utf-8", errors="strict")
                        # 检查是否有完整的消息
                        while True:
                            sep = self._buf.find(";")
                            if sep < 0:  # 没有完整消息
                                break
                            frame_cmd, js = self._buf[:sep], self._buf[sep + 1:]
                            try:
                                json.loads(js)  # 尝试解析，验证是否完整
                                self._buf = ""  # 清空缓冲，因为是旧消息
                            except json.JSONDecodeError:
                                break  # JSON 不完整，保留缓冲
                    except socket.timeout:
                        break  # 没有更多数据
            finally:
                s.settimeout(timeout or self.timeout)  # 恢复原超时设置
            try:
                s.sendall(data)
            except (BrokenPipeError, ConnectionResetError, OSError):
                self._reconnect()
                s = self._sock
                s.settimeout(timeout or self.timeout)
                s.sendall(data)

            end = time.time() + (timeout or self.timeout)
            while time.time() < end:
                try:
                    chunk = s.recv(8192)
                    print(chunk)
                except socket.timeout:
                    continue
                if not chunk:
                    raise ConnectionError("server closed connection")

                self._buf += chunk.decode("utf-8", errors="strict")
                sep = self._buf.find(";")
                if sep < 0:  # 半包
                    continue
                frame_cmd, js = self._buf[:sep], self._buf[sep + 1:]
                try:
                    payload = json.loads(js)
                except json.JSONDecodeError:
                    continue  # JSON 还没收全
                self._buf = ""  # 一问一答协议，清空缓冲
                # 期望 'cmd_respone'，若未来扩展可在此分支
                return payload
            raise TimeoutError("no cmd_respone")

    def ping(self) -> dict:
        return self.send_command("ping", {})
