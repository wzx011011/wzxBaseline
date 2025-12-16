import os, sys, time, json, socket, subprocess, atexit, signal, threading
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

    def start_if_needed(self):
        exe = Path(self.exe_path)
        if not exe.is_file(): raise FileNotFoundError(f"EXE not found: {self.exe_path}")

        if is_process_running_by_name(Path(self.exe_path).name):
            wait_port(self.host, self.port)
            return

        env = os.environ.copy()
        # 重要，拉起子进程的时候会注册一个环境变量来绕开弹窗
        env["SLICER_TEST_RESTORE"] = "discard"
        env["CREALITY_PRINTER_LOG_PATH"] = CREALITY_PRINTER_LOG_PATH

        # 可选：让 C++ 读取端口/复用配置
        # env["SLICER_TEST_PORT"] = str(PORT)
        # env["SLICER_TEST_REUSE"] = "1"

        self.log_file = open(self.log_path, "a", encoding="utf-8", buffering=1)
        flags = subprocess.CREATE_NEW_PROCESS_GROUP
        self.proc = subprocess.Popen(
            args=self.args, cwd=str(exe.parent), env=env,
            stdout=self.log_file, stderr=subprocess.STDOUT,
            creationflags=flags, close_fds=False,
        )
        self.spawned_by_me = True

        atexit.register(self._cleanup)
        for sig in (getattr(signal, "SIGINT", None),
                    getattr(signal, "SIGTERM", None),
                    getattr(signal, "SIGBREAK", None)):
            if sig: signal.signal(sig, self._graceful_exit)

        wait_port(self.host, self.port)

    def _graceful_exit(self, *_):
        sys.exit(0)

    def _cleanup(self):
        if self.log_file:
            try:
                self.log_file.flush()
                self.log_file.close()
            except Exception:
                pass
        if not self.spawned_by_me or not self.proc: return
        pid = self.proc.pid
        try:
            try:
                os.kill(pid, getattr(signal, "CTRL_BREAK_EVENT", signal.SIGTERM))
                self.proc.wait(timeout=5)
            except Exception:
                pass
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception:
            pass

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
