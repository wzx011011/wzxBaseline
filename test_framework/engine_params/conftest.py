from __future__ import annotations

import os
import re
import shutil
import itertools
from typing import Optional
from pathlib import Path
import time
import threading
import inspect

import pytest
from .src.slicerctl.session import EngineSession, RestartingEngine, EngineUnavailable
from .src.slicerctl.constants import SLICE_BTN_ID

from .src.testing_utils.caseio import (
    repo_root,
    case_json_path,
    infer_module_and_group_from_file,
    param_name_from_test_func_name,
    load_cases_json,
    normalize_case_for_fixture,
    pick_expected_values,
    resolve_extra_params,
    model_or_baseline_path,
)

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
    # TODO，这里记得删掉
    p = Path(r"E:\Creality Print 7 Alp\Creality Print 7.0 Alpha\CrealityPrint.exe")
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
def engine_manager(pytestconfig):
    exe_path = _get_exe_path_from_cli_or_env(pytestconfig)
    exe_path = Path(r"E:\Creality Print 7 Alp\Creality Print 7.0 Alpha\CrealityPrint.exe")
    if not exe_path:
        pytest.skip(f"未提供 --slicer-exe 或 {ENV_KEY}，跳过依赖引擎的会话")

    def _mk_session():
        return EngineSession(
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

    mgr = RestartingEngine(mk_session=_mk_session, ping_timeout=3.0, cool_down=5.0)
    try:
        yield mgr
    finally:
        mgr.close()


# 便捷别名（保持现有用法尽量不变）
@pytest.fixture(scope="session")
def engine_injector(engine_manager, pytestconfig):
    policy = pytestconfig.getoption("--engine-unavail")

    class InjectorAdapter:
        # 该适配器只能有这个属性
        __slots__ = ("_mgr",)
        def __init__(self, mgr): self._mgr = mgr

        def submit(self, *args, **kwargs):
            """
                - TODO: 在这里决定怎么处理引擎奔溃错误，要区分case断言失败以及引擎奔溃的错误。
            """
            try:
                return self._mgr.submit(*args, **kwargs)
            except EngineUnavailable as e:
                if policy == "skip":
                    pytest.skip(str(e))
                elif policy == "xfail":
                    pytest.xfail(str(e))
                # policy == "error"：保留为 ERROR（基础设施错误），而不是 FAIL
                raise

    return InjectorAdapter(engine_manager)

@pytest.fixture(scope="session")
def engine_client(engine_manager):
    return engine_manager.client


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


# ==================================================
# watchdog: 使用事件通知机制等待目标文件写入完成，不用轮询机制
# ==================================================

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
#                    动态参数化
# =================                 =================


# baseline 文件名解析：放到与 3MF 相同的 param_name 子目录
def _resolve_baseline_gcode(repo: Path, module_: str, group: str, param_name: str, value: object):
    return model_or_baseline_path(repo, module_, group, param_name, str(value))

# 如果 json 文件中有baseline_gcode键值对，那么就会自动调用这个解析器自动将其转化成绝对路径
RESOLVERS = {
    "baseline_gcode": _resolve_baseline_gcode,
    # 可按需添加其它解析器，如 "support_gcode": _resolve_support_gcode
}

@pytest.hookimpl(trylast=True)
def pytest_generate_tests(metafunc: pytest.Metafunc):
    """
    - JSON：test_framework/engine_params/data/case_input/<module>/<group>/<param_name>.json
    - 模型/基线：test_framework/engine_params/data/models/<module>/<group>/<param_name>/<filename>
    - 参数注入顺序：slice_and_export → expected_*（按函数声明顺序）→ extra（按函数声明顺序）
    - 仅当测试函数声明了 slice_and_export 时才注入
    """
    # 仅看“测试函数声明的形参”，避免把隐式/autouse fixture 混进来
    declared_params = tuple(inspect.signature(metafunc.function).parameters.keys())
    if "slice_and_export" not in declared_params:
        return

    # 拆分 expected_* 与 extra（都以“声明顺序”为准）
    expected_params = tuple(n for n in declared_params if n.startswith("expected_"))
    known = {"slice_and_export", *expected_params}
    extra_params = tuple(n for n in declared_params if n not in known)

    # 推断仓库根、module、group、param_name，并定位 JSON
    mod_file = Path(metafunc.module.__file__).resolve()
    repo = repo_root(mod_file)
    module_, group = infer_module_and_group_from_file(mod_file)   # 会去掉 test_ 前缀
    param_name = param_name_from_test_func_name(metafunc.function.__name__)
    json_path = case_json_path(repo, module_, group, param_name)

    # 读取用例
    raw_cases = load_cases_json(json_path)

    # 组装参数行
    arg_names = ("slice_and_export",) + expected_params + extra_params
    arg_rows = []
    for c in raw_cases:
        # 给 fixture 的 case（把 input_3mf 文件名映射为绝对路径）
        case_for_fixture = normalize_case_for_fixture(
            c, repo=repo, module_=module_, group=group, param_name=param_name
        )

        # 期望值：按 expected_* 名依次取
        expected_values = pick_expected_values(c, expected_params)

        # 额外参数：优先用 JSON，同名缺失则尝试 RESOLVERS[name](...)
        extra_values = resolve_extra_params(
            c,
            extra_params,
            repo=repo,
            module_=module_,
            group=group,
            param_name=param_name,
            resolvers=RESOLVERS,
        )

        values = (case_for_fixture,) + tuple(expected_values) + tuple(extra_values)
        arg_rows.append(pytest.param(*values, id=str(c.get("project_name", param_name))))

    # 注入（仅让 slice_and_export 走 indirect）
    metafunc.parametrize(
        argnames=arg_names,
        argvalues=arg_rows,
        indirect=["slice_and_export"],
    )

# =================                 =================
#                    引擎切片固定步骤fixture
# =================                 =================
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
