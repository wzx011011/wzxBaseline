import os, time, json, socket, subprocess, atexit, signal, threading, ctypes
from pathlib import Path
from typing import Optional

from .constants import *


# ----------------- 子进程（Server）托管 -----------------
def is_process_running_by_name(name="CrealityPrint.exe"):
    return any(_pid_is_active(pid) for pid in _get_pids_by_name(name))


def _pid_is_active(pid: int) -> bool:
    """Return False for exited Windows process objects still listed by tasklist."""
    if os.name != "nt":
        return True
    process_query_limited_information = 0x1000
    still_active = 259
    handle = ctypes.windll.kernel32.OpenProcess(
        process_query_limited_information, False, pid
    )
    if not handle:
        return False
    try:
        exit_code = ctypes.c_ulong()
        if not ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
            return False
        return exit_code.value == still_active
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def _get_pids_by_name(name: str) -> list:
    """通过 tasklist 获取指定名称进程的所有 PID"""
    try:
        out = subprocess.check_output(
            ["tasklist", "/FI", f"IMAGENAME eq {name}", "/FO", "CSV", "/NH"],
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        pids = []
        for line in out.strip().splitlines():
            parts = line.split('"')
            # CSV format: "name","PID","Session Name","Session#","Mem Usage"
            if len(parts) >= 4:
                try:
                    pids.append(int(parts[3]))
                except (ValueError, IndexError):
                    pass
        return pids
    except Exception:
        return []


def _is_port_free(host: str, port: int) -> bool:
    """检查端口是否空闲"""
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return False  # 能连上说明被占用
    except (ConnectionRefusedError, OSError):
        return True  # 连不上说明空闲


def kill_process_by_name(name="CrealityPrint.exe", timeout=15):
    """
    强制停止指定名称的进程，多策略兜底。
    对 GUI 卡死（Not Responding）的进程，优先使用 wmic 删除。
    """
    if not is_process_running_by_name(name):
        return True

    print(f"[SlicerProc] 发现已运行的 {name}，正在强制停止...")

    # 策略1: wmic 优先——对 Not Responding 的进程最可靠
    try:
        subprocess.run(
            ["wmic", "process", "where", f"name='{name}'", "delete"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=10,
        )
    except Exception:
        pass
    time.sleep(1.0)

    if not is_process_running_by_name(name):
        print(f"[SlicerProc] {name} 已成功停止 (wmic)")
        time.sleep(1.0)
        return True

    # 策略2: taskkill /IM（按名称批量杀）
    subprocess.run(
        ["taskkill", "/IM", name, "/T", "/F"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    time.sleep(1.0)

    if not is_process_running_by_name(name):
        print(f"[SlicerProc] {name} 已成功停止 (taskkill)")
        time.sleep(1.0)
        return True

    # 策略3: 按 PID 逐个杀
    pids = _get_pids_by_name(name)
    for pid in pids:
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    time.sleep(1.0)

    if not is_process_running_by_name(name):
        print(f"[SlicerProc] {name} 已成功停止 (PID kill)")
        time.sleep(1.0)
        return True

    # 等待进程完全退出
    end_time = time.time() + timeout
    while time.time() < end_time:
        if not is_process_running_by_name(name):
            print(f"[SlicerProc] {name} 已成功停止")
            time.sleep(1.0)
            return True
        time.sleep(0.5)

    print(f"[SlicerProc] 警告: {name} 停止超时")
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

        # 等端口真正释放，避免新进程 bind 10048 错误
        port_deadline = time.time() + 30
        while not _is_port_free(self.host, self.port):
            if time.time() > port_deadline:
                raise RuntimeError(
                    f"Port {self.host}:{self.port} still occupied after killing {proc_name}. "
                    f"Cannot start new engine."
                )
            print(f"[SlicerProc] 等待端口 {self.port} 释放...")
            time.sleep(1.0)

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

    @staticmethod
    def _is_response_for(frame_cmd: str, cmd: str) -> bool:
        """判断收到的帧是否是 cmd 的应答（而不是异步推送）。"""
        fc = frame_cmd.lower()
        c = cmd.lower()
        # 匹配: cmd_respone / cmd / cmd_response / 通用 cmd_respone
        return fc in (c, f"{c}_respone", f"{c}_response", "cmd_respone", "cmd_response")

    def _try_extract_message(self) -> Optional[tuple]:
        """从 _buf 中尝试提取一条完整的 frame_cmd;json 消息。
        返回 (frame_cmd, payload_dict)，或 None 表示数据不完整。"""
        sep = self._buf.find(";")
        if sep < 0:
            return None
        frame_cmd = self._buf[:sep]
        js = self._buf[sep + 1:]
        try:
            payload = json.loads(js)
        except json.JSONDecodeError:
            return None  # JSON 还没收全
        self._buf = ""
        return (frame_cmd, payload)

    def send_command(self, cmd: str, obj: Optional[dict] = None, timeout: Optional[float] = None) -> dict:
        obj = obj or {}
        data = f"{cmd};{json.dumps(obj, separators=(',', ':'))}".encode("utf-8")
        with self._lock:
            if not self._sock: self.connect()
            s = self._sock
            effective_timeout = timeout or self.timeout

            # 排空缓冲区中的旧数据
            s.settimeout(0.1)
            try:
                while True:
                    try:
                        chunk = s.recv(8192)
                        if not chunk:
                            break
                        self._buf += chunk.decode("utf-8", errors="strict")
                        # 丢弃所有能解析的旧消息
                        while self._try_extract_message() is not None:
                            pass
                    except socket.timeout:
                        break
            finally:
                s.settimeout(effective_timeout)

            try:
                s.sendall(data)
            except (BrokenPipeError, ConnectionResetError, OSError):
                self._reconnect()
                s = self._sock
                s.settimeout(effective_timeout)
                s.sendall(data)

            end = time.time() + effective_timeout
            while time.time() < end:
                try:
                    chunk = s.recv(8192)
                except socket.timeout:
                    continue
                if not chunk:
                    raise ConnectionError("server closed connection")

                self._buf += chunk.decode("utf-8", errors="strict")
                msg = self._try_extract_message()
                if msg is None:
                    continue
                frame_cmd, payload = msg
                if self._is_response_for(frame_cmd, cmd):
                    return payload
                # 异步推送（如 app_ready）—— 跳过，继续等真正的应答

            raise TimeoutError(f"no response for '{cmd}' within {effective_timeout}s")

    def ping(self) -> dict:
        return self.send_command("ping", {})
