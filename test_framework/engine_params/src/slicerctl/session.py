import ctypes
import os
import threading
import time
from typing import Optional

from .client import SlicerProc
from .client import EngineClient
from .injector import CommandInjector


def _process_cpu_seconds(pid: int) -> Optional[float]:
    """Return Windows process CPU time without adding a psutil dependency."""
    if os.name != "nt" or not pid:
        return None

    class FILETIME(ctypes.Structure):
        _fields_ = [("low", ctypes.c_uint32), ("high", ctypes.c_uint32)]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
    kernel32.OpenProcess.restype = ctypes.c_void_p
    kernel32.GetProcessTimes.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(FILETIME),
        ctypes.POINTER(FILETIME),
        ctypes.POINTER(FILETIME),
        ctypes.POINTER(FILETIME),
    ]
    kernel32.GetProcessTimes.restype = ctypes.c_int
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_int
    handle = kernel32.OpenProcess(0x1000, False, int(pid))  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return None
    try:
        creation = FILETIME()
        exit_time = FILETIME()
        kernel = FILETIME()
        user = FILETIME()
        if not kernel32.GetProcessTimes(
            handle,
            ctypes.byref(creation),
            ctypes.byref(exit_time),
            ctypes.byref(kernel),
            ctypes.byref(user),
        ):
            return None

        def seconds(value: FILETIME) -> float:
            ticks = (int(value.high) << 32) | int(value.low)
            return ticks / 10_000_000.0

        return seconds(kernel) + seconds(user)
    finally:
        kernel32.CloseHandle(handle)


# ----------------- 起 Server + 建 Client + 起队列 -----------------
class EngineSession:
    """with EngineSession(...) as (client, injector):"""

    def __init__(self, exe_path, log_path, cli_args,
                 host, port,
                 *,
                 new_proc: bool = True,
                 timeout=30.0,
                 inter_command_delay=0.2, retries=1, backoff=0.5):
        self.client: EngineClient = EngineClient(host=host, port=port, timeout=timeout)
        self.injector: CommandInjector = CommandInjector(self.client,
                                                         inter_command_delay=inter_command_delay,
                                                         retries=retries, backoff=backoff)
        if new_proc:
            self.proc = SlicerProc(exe_path,
                                   log_path,
                                   cli_args,
                                   host,
                                   port)

    def __enter__(self) -> tuple[EngineClient, CommandInjector]:
        self.proc.start_if_needed()
        self.client.connect()
        self.injector.start()
        return self.client, self.injector

    def __exit__(self, exc_type, exc, tb):
        try:
            self.injector.stop()
            self.client.close()
        finally:
            self.proc.stop()
        return False


# ----------------- 引擎管理器，负责管理会话期间引擎奔溃的重启。 -----------------
class EngineUnavailable(RuntimeError):
    """TODO,基础设施/引擎不可用，不代表用例断言失败。（但现在不行）"""
    pass


_TRANSIENT_ERRORS = (
    ConnectionRefusedError,
    ConnectionResetError,
    BrokenPipeError,
    TimeoutError,
    OSError,
    RuntimeError,
)


class RestartingEngine:
    """
    会话级引擎管理器：
    - submit 前先 ping；失败则重启
    - submit 期间如遇连接类错误，自动重启并重试一次
    - 线程安全；避免并发重启
    """

    def __init__(self, *, mk_session, ping_timeout: float = 3.0, cool_down: float = 5.0):
        self._mk_session = mk_session  # () -> EngineSession
        self._ping_timeout = ping_timeout
        self._cool_down = cool_down  # 两次重启的间隔
        self._lock = threading.RLock()
        self._session: Optional[EngineSession] = None
        self._client = None
        self._injector = None
        self._last_restart_ts = 0.0
        self._start()

    # ---- 生命周期 ----
    def _start(self):
        sess = self._mk_session()
        client, injector = sess.__enter__()
        self._session, self._client, self._injector = sess, client, injector
        # 初次健康检查（失败不让 assert 失败测试）
        self._ping_or_raise()

    def close(self):
        with self._lock:
            if self._session is not None:
                self._session.__exit__(None, None, None)
            self._session = self._client = self._injector = None

    def _restart_locked(self):
        # 节流，避免疯狂重启
        now = time.time()
        if now - self._last_restart_ts < self._cool_down:
            time.sleep(self._cool_down - (now - self._last_restart_ts))
        self._last_restart_ts = time.time()

        # 关旧开新
        old = self._session
        try:
            if old is not None:
                old.__exit__(None, None, None)
        except Exception:
            pass
        self._session = self._client = self._injector = None
        self._start()

    def restart(self):
        with self._lock:
            self._restart_locked()

    # ---- 健康检查 ----
    def _ping_or_raise(self):
        fut = self._injector.submit("ping", {})
        resp = fut.result(timeout=self._ping_timeout)
        if resp.get("code") != 0:
            raise EngineUnavailable(f"ping 失败：{resp}")

    def ensure_alive(self):
        with self._lock:
            try:
                self._ping_or_raise()
            except Exception:
                # 尝试一次重启 + 再次 ping
                self._restart_locked()
                try:
                    self._ping_or_raise()
                except Exception as e:
                    # 仍不可用，交给上层决定 skip/xfail/报错
                    raise EngineUnavailable(f"重启后仍不可用：{e}") from e

    # ---- 对外能力 ----
    @property
    def client(self):
        return self._client

    def process_state(self):
        """Return the slicer subprocess state without changing its lifecycle."""
        with self._lock:
            session = self._session
            slicer_proc = getattr(session, "proc", None) if session is not None else None
            process = getattr(slicer_proc, "proc", None)
            if process is None:
                return {"running": False, "pid": None, "returncode": None}
            returncode = process.poll()
            return {
                "running": returncode is None,
                "pid": process.pid,
                "returncode": returncode,
                "cpu_seconds": _process_cpu_seconds(process.pid) if returncode is None else None,
            }

    def submit(self, cmd: str, payload: dict, **kwargs):
        self.ensure_alive()
        try:
            return self._injector.submit(cmd, payload, **kwargs)
        except _TRANSIENT_ERRORS as e:
            with self._lock:
                self._restart_locked()
                try:
                    return self._injector.submit(cmd, payload, **kwargs)
                except _TRANSIENT_ERRORS as e2:
                    raise EngineUnavailable(f"提交 `{cmd}` 时连接故障，重启后仍失败：{e2}") from e2
