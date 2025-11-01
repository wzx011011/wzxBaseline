from __future__ import annotations

import os
import re
import shutil
import itertools
from typing import Optional
from pathlib import Path
import time
import threading

import pytest
from .src.slicerctl.session import EngineSession
from .src.slicerctl.constants import SLICE_BTN_ID

# ========== watchdog 依赖 ==========
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
except Exception as _e_watchdog:
    Observer = None
    FileSystemEventHandler = object  # 兜底占位
    _WATCHDOG_IMPORT_ERROR = _e_watchdog
else:
    _WATCHDOG_IMPORT_ERROR = None


# 为engine_param_item提供默认参数
@pytest.fixture
def engine_param_item():
    return {"input": "default_param", "expectation": True}


# 为baseline_cur_path提供默认路径
@pytest.fixture
def baseline_cur_path():
    return os.path.dirname(os.path.abspath(__file__))


# ==============================
# 通用：获取 EXE 路径（命令行 > 环境变量）
# ==============================
ENV_KEY = "CREALITY_PRINTER_PATH"


def _get_exe_path_from_cli_or_env(config: "pytest.Config") -> Optional[str]:
    """
    优先命令行 --slicer-exe；否则读取环境变量 CREALITY_PRINTER_PATH。
    两者都没有则返回 None。若显式提供了路径但文件不存在，抛 UsageError。
    """
    try:
        cli_val = config.getoption("--slicer-exe")
    except ValueError:
        cli_val = None

    exe = (cli_val or os.getenv(ENV_KEY) or "").strip()
    if not exe:
        return None

    p = Path(exe).expanduser()
    if not (p.exists() and p.is_file()):
        raise pytest.UsageError(
            f"指定的切片器路径不存在或不是文件: {p}。"
            " 请用 --slicer-exe <path> 或设置环境变量 CREALITY_PRINTER_PATH。"
        )
    return str(p)


# ==============================
# 会话级引擎 Session
# ==============================
@pytest.fixture(scope="session")
def engine_session(pytestconfig):
    """
    启动一次 EngineSession，返回 (client, injector)。
    若未提供 --slicer-exe 且未设置 CREALITY_PRINTER_PATH，则跳过相关用例。
    """
    exe_path = _get_exe_path_from_cli_or_env(pytestconfig)
    if not exe_path:
        pytest.skip(
            "未提供 --slicer-exe 且未设置环境变量 "
            f"{ENV_KEY}；跳过依赖引擎的测试会话"
        )

    session = EngineSession(
        exe_path=exe_path,
        log_path=pytestconfig.getoption("--slicer-log"),
        cli_args=[exe_path, "test#157369"],
        host=pytestconfig.getoption("--slicer-host"),
        port=pytestconfig.getoption("--slicer-port"),
        timeout=pytestconfig.getoption("--slicer-timeout"),
        inter_command_delay=pytestconfig.getoption("--slicer-inter-delay"),
        retries=pytestconfig.getoption("--slicer-retries"),
        backoff=pytestconfig.getoption("--slicer-backoff"),
    )

    client, injector = session.__enter__()
    try:
        fut = injector.submit("ping", {})
        resp = fut.result(timeout=10)
        assert resp.get("code") == 0, f"ping 失败：{resp}"
        yield client, injector
    finally:
        session.__exit__(None, None, None)


# 便捷别名
@pytest.fixture(scope="session")
def engine_client(engine_session):
    client, _ = engine_session
    return client


@pytest.fixture(scope="session")
def engine_injector(engine_session):
    _, injector = engine_session
    return injector


# 可选：按标记自动启用
@pytest.fixture(autouse=True)
def _maybe_start_engine(request, engine_session):
    if request.node.get_closest_marker("functional") or \
            request.node.get_closest_marker("engine_params"):
        _ = engine_session


# =================                 =================
#                    管理gcode生成路径fixture
# =================                 =================

def _sanitize(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", s)


@pytest.fixture(scope="session")
def gcode_root(pytestconfig, tmp_path_factory):
    user_root = pytestconfig.getoption("--gcode-root")
    if user_root:
        root = Path(user_root).resolve()
        root.mkdir(parents=True, exist_ok=True)
        return root
    return tmp_path_factory.mktemp("gcode-outputs", numbered=True)


@pytest.fixture
def gcode_dir(request, pytestconfig, gcode_root):
    scope = pytestconfig.getoption("--gcode-scope")
    clean = pytestconfig.getoption("--clean-gcode")

    if scope == "session":
        d = gcode_root / "session"
        d.mkdir(exist_ok=True)
        if clean:
            request.addfinalizer(lambda: shutil.rmtree(d, ignore_errors=True))
        return d

    elif scope == "module":
        modname = _sanitize(request.module.__name__ if request.module else "mod")
        d = gcode_root / f"mod_{modname}"
        d.mkdir(exist_ok=True)
        if clean:
            request.addfinalizer(lambda: shutil.rmtree(d, ignore_errors=True))
        return d

    nodeid = _sanitize(request.node.nodeid)
    d = gcode_root / f"case_{nodeid}"
    d.mkdir(exist_ok=True)
    if clean:
        request.addfinalizer(lambda: shutil.rmtree(d, ignore_errors=True))
    return d


@pytest.fixture
def gcode_path_factory(request, gcode_dir):
    counter = itertools.count(1)
    base = _sanitize(request.node.name)

    def make(filename: str | None = None, *, ext: str = ".gcode", prefix: str = "") -> Path:
        if filename:
            p = gcode_dir / filename
            return p.with_suffix(ext) if ext and not str(p).lower().endswith(ext) else p
        idx = next(counter)
        name = f"{prefix}{base}_{idx}{ext}"
        return gcode_dir / name

    return make


# =========================
# watchdog: 等待目标文件写入完成
# =========================

class _WaitForFileHandler(FileSystemEventHandler):
    """
    监听目标目录中与目标文件同名（或被移动成该名）的事件。
    检测到后做“稳定期”判断：大小/mtime 在一段时间内不变，且可读打开，即视为写入完成。
    """
    def __init__(self, target: Path, ready_evt: threading.Event, settle_time: float = 1.0):
        self.target = target.resolve()
        self.ready_evt = ready_evt
        self.settle_time = max(0.1, settle_time)
        self._lock = threading.Lock()
        self._last_size = None
        self._last_mtime = None
        self._last_check_ts = 0.0

    # 只要有可能影响目标文件状态的事件，都尝试检查
    def on_created(self, event: FileSystemEvent):
        self._maybe_check(event)

    def on_modified(self, event: FileSystemEvent):
        self._maybe_check(event)

    def on_moved(self, event: FileSystemEvent):
        # moved 到目标名时也可能完成
        self._maybe_check(event)

    def _maybe_check(self, event: FileSystemEvent):
        if self.ready_evt.is_set():
            return
        # 只关心目录内的目标文件（同路径或 basename 匹配）
        try:
            p = Path(getattr(event, "dest_path", getattr(event, "src_path", "")) or "")
        except Exception:
            return

        if not p:
            return

        # 事件可能来自同目录内的临时名 -> 正式名（rename），也可能直接是目标名修改
        if p.name != self.target.name and getattr(event, "src_path", None):
            # 还可以检查 src_path 是否就是 target（反向移动）
            try:
                src = Path(event.src_path)
                if src.name != self.target.name:
                    return
            except Exception:
                return
        elif p.name != self.target.name:
            return

        # 尝试进行“稳定期”判断
        self._check_stable()

    def _check_stable(self):
        with self._lock:
            now = time.time()
            # 为了避免极端高频事件，限制检查频率
            if now - self._last_check_ts < 0.05:
                return
            self._last_check_ts = now

            if not self.target.exists() or not self.target.is_file():
                return

            try:
                stat = self.target.stat()
                size = stat.st_size
                mtime = stat.st_mtime
            except FileNotFoundError:
                return

            # 第一次记录
            if self._last_size is None:
                self._last_size = size
                self._last_mtime = mtime
                return

            # 若 size/mtime 有变化，更新观察起点
            if size != self._last_size or mtime != self._last_mtime:
                self._last_size = size
                self._last_mtime = mtime
                self._first_stable_ts = time.time()
                return

            # size/mtime 未变化，判断是否达到稳定期
            first_stable_ts = getattr(self, "_first_stable_ts", None)
            if first_stable_ts is None:
                self._first_stable_ts = time.time()
                return

            if time.time() - self._first_stable_ts < self.settle_time:
                return

            # 尝试可读打开（Windows 下可检测写锁释放）
            try:
                with open(self.target, "rb"):
                    pass
            except Exception:
                return

            # 稳定且可读
            self.ready_evt.set()


def wait_for_file_written(target: Path, timeout: float = 60.0, settle_time: float = 1.0) -> None:
    """
    使用 watchdog 事件监听等待 target 写入完成：
    - 文件存在
    - 大小/mtime 在 settle_time 内保持不变
    - 能以二进制只读方式打开（Windows 下避免写锁）

    :raises pytest.UsageError: 未安装 watchdog
    :raises TimeoutError: 超时仍未满足条件
    """
    if Observer is None:
        raise pytest.UsageError(
            "需要安装 'watchdog' 才能使用事件驱动等待文件落盘：\n"
            "    pip install watchdog\n"
            f"具体错误：{_WATCHDOG_IMPORT_ERROR}"
        )

    target = Path(target).resolve()
    parent = target.parent
    parent.mkdir(parents=True, exist_ok=True)

    # 先做一次“已存在且稳定”的快速路径
    quick_start = time.time()
    while time.time() - quick_start < min(0.5, settle_time):
        if target.exists() and target.is_file():
            try:
                # 读两次 stat 判断是否已稳定
                st1 = target.stat()
                time.sleep(min(0.2, settle_time))
                st2 = target.stat()
                if st1.st_size == st2.st_size and st1.st_mtime == st2.st_mtime:
                    with open(target, "rb"):
                        return
            except Exception:
                pass
        time.sleep(0.05)

    ready_evt = threading.Event()
    handler = _WaitForFileHandler(target, ready_evt, settle_time=settle_time)
    observer = Observer()
    observer.schedule(handler, str(parent), recursive=False)
    observer.daemon = True
    observer.start()
    try:
        # 目标也可能“先存在后稳定”，因此轮询一次
        start = time.time()
        while True:
            if ready_evt.is_set():
                return
            # 主动检查一次（防止错过边缘事件）
            handler._check_stable()
            if ready_evt.is_set():
                return
            if time.time() - start > timeout:
                raise TimeoutError(f"等待文件写入完成超时（{timeout}s）：{target}")
            time.sleep(0.05)
    finally:
        observer.stop()
        observer.join(timeout=5)


# =================                 =================
#                    引擎切片固定步骤fixture
# =================                 =================

# slice_and_export: 强制通过 request.param 提供运行参数
# request.param 必须为 dict，必要键：
#   - "input_3mf": str (必须存在)
# 可选键：
#   - "output_gcode": str(目标路径)
#   - "slice_btn_id": int
#   - "timeouts": dict with {"load": int, "export": int, "slice": int, "settle": float, "wait": float}
#
# 示例：
# @pytest.mark.parametrize("slice_and_export", [
#     {"input_3mf": r"C:\a.3mf"}
# ], indirect=True)
@pytest.fixture
def slice_and_export(request, engine_injector, gcode_path_factory):
    # ---- 验参（严格：必须提供 request.param） ----
    if not hasattr(request, "param") or not isinstance(request.param, dict):
        raise pytest.UsageError(
            "slice_and_export fixture requires request.param to be a dict. "
            "Example: @pytest.mark.parametrize('slice_and_export', [{'input_3mf':'C:/a.3mf','output_gcode':'C:/out.gcode'}], indirect=True)"
        )

    params = request.param.copy()
    # 必需字段
    input_3mf = Path(params.get("input_3mf", ""))

    if not input_3mf or not input_3mf.exists():
        raise pytest.UsageError(f"slice_and_export: 'input_3mf' must be provided and exist. Got: {input_3mf}")

    # 如果不给该fixture提供output_gcode，那么就由pytest自动根据fixture管理输出目录
    output_gcode = Path(params.get("output_gcode")) if params.get("output_gcode") else gcode_path_factory()
    if not output_gcode:
        raise pytest.UsageError(f"slice_and_export: 'output_gcode' must be provided. Got: {output_gcode}")

    # 可选
    slice_btn_id = int(params.get("slice_btn_id", SLICE_BTN_ID))
    timeouts = params.get("timeouts", {})
    load_timeout = int(timeouts.get("load", 90))
    slice_timeout = int(timeouts.get("slice", 120))
    export_timeout = int(timeouts.get("export", 360))
    # 事件落盘稳定期与整体等待上限（新的两个可选超时）
    settle_seconds = float(timeouts.get("settle", 1.0))   # 文件大小/mtime 保持不变的时间
    wait_written   = float(timeouts.get("wait", 60.0))    # 监听等待总时长

    # 确保父目录存在
    output_gcode.parent.mkdir(parents=True, exist_ok=True)

    # ---- 1) reset_project ----
    reset_fut = engine_injector.submit("reset_project", {
        "skip_confirm": True,
        "silent": True,
        "project_name": params.get("project_name", "pytest_case_project"),
    })
    reset_result = reset_fut.result(timeout=30)
    assert reset_result.get("code") == 0, f"reset_project 失败：{reset_result}"

    # ---- 2) trigger_load_project ----
    load_fut = engine_injector.submit("trigger_load_project2",
                                      {"file": str(input_3mf),
                                       "discard_preset_changes": True},
                                      timeout=60)
    load_res = load_fut.result(timeout=load_timeout)
    assert load_res.get("code") == 0, f"加载模型失败：{load_res}"

    # ---- 3) click slice button ----
    slice_fut = engine_injector.submit("click_button", {"id": slice_btn_id})
    slice_res = slice_fut.result(timeout=slice_timeout)
    assert slice_res.get("code") == 0, f"slice_fut 失败：{slice_res}"

    # ---- 4) export gcode ----
    export_fut = engine_injector.submit("export_gcode", {
        "export_all": False,
        "output": str(output_gcode)
    }, timeout=300)
    export_res = export_fut.result(timeout=export_timeout)
    assert export_res.get("code") == 0, f"导出 G-code 失败：{export_res}"

    # ---- 5) watchdog 等待文件真正落盘且写入完成 ----
    #   - 事件驱动，无需忙等
    #   - 跨平台：Windows 上也通过“可读打开”探测写锁释放
    wait_for_file_written(output_gcode, timeout=wait_written, settle_time=settle_seconds)

    assert output_gcode.exists(), f"G-code 未生成：{output_gcode}"
    return output_gcode
