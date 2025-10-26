from __future__ import annotations

import os
import re
import shutil
import itertools
from typing import Optional
from pathlib import Path
import time

import pytest
from .src.slicerctl.session import EngineSession
from .src.slicerctl.constants import SLICE_BTN_ID


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
    # 1) 读 CLI（选项不存在时 getoption 可能抛 ValueError；不同 pytest 版本略有差异）
    try:
        cli_val = config.getoption("--slicer-exe")  # 有的版本可加 default=None
    except ValueError:
        cli_val = None  # 选项未注册就当作没给

    exe = (cli_val or os.getenv("CREALITY_PRINTER_PATH") or "").strip()
    if not exe:
        return None  # 都没提供就按你的约定返回 None

    p = Path(exe).expanduser()
    if not (p.exists() and p.is_file()):
        # 显式提供了，但不存在 -> 清晰报错给用户
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

    # TODO，先写死，不知道为什么命令行参数注册不了
    # exe_path = r"D:\C3D_Automation\C3DSlicer\build_Release\src\Release\CrealityPrint.exe"
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

    # 进入上下文，拿到 (client, injector)
    client, injector = session.__enter__()
    try:
        # 连通性自检：等待后台工作线程往返
        fut = injector.submit("ping", {})
        resp = fut.result(timeout=10)
        assert resp.get("code") == 0, f"ping 失败：{resp}"
        yield client, injector
    finally:
        session.__exit__(None, None, None)


# 便捷别名（可选）：需要谁就注入谁
@pytest.fixture(scope="session")
def engine_client(engine_session):
    client, _ = engine_session
    return client


@pytest.fixture(scope="session")
def engine_injector(engine_session):
    _, injector = engine_session
    return injector


# 可选：按标记自动启用（只在带标记的用例中自动“触发”会话资源）
@pytest.fixture(autouse=True)
def _maybe_start_engine(request, engine_session):
    if request.node.get_closest_marker("functional") or \
            request.node.get_closest_marker("engine_params"):
        # 引用即可确保 session 已启动
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
        # 会话级通常不自动清理；如需清理，可在 session 收尾手动处理
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

    # function（默认）
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


# =================                 =================
#                    引擎切片固定步骤fixture
# =================                 =================

# slice_and_export: 强制通过 request.param 提供运行参数
# request.param 必须为 dict，必要键：
#   - "input_3mf": str (必须存在)
# 可选键：
#     - "output_gcode": str(目标路径)
#   - "slice_btn_id": int  (如果不提供，使用 9000)
#   - "timeouts": dict with {"load": int, "export": int, "slice": int}
#
# 用法（示例见 test 文件）:
# @pytest.mark.parametrize("slice_and_export", [ { ... } ], indirect=True)
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
    output_gcode_param = params.get("output_gcode")
    if output_gcode_param:
        output_gcode = Path(output_gcode_param)
    else:
        output_gcode = Path(gcode_path_factory())
    if not output_gcode:
        raise pytest.UsageError(f"slice_and_export: 'output_gcode' must be provided. Got: {output_gcode}")

    # 可选
    slice_btn_id = int(params.get("slice_btn_id", SLICE_BTN_ID))
    timeouts = params.get("timeouts", {})
    load_timeout = timeouts.get("load", 90)
    slice_timeout = timeouts.get("slice", 120)
    export_timeout = timeouts.get("export", 360)

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

    # 等待文件落盘（短轮询）
    if not output_gcode.exists():
        end = time.time() + 5.0
        while time.time() < end:
            if output_gcode.exists():
                break
            time.sleep(0.25)
    assert output_gcode.exists(), f"G-code 未生成：{output_gcode}"
    return output_gcode

    # # 返回给测试用例，在测试结束后清理？
    # try:
    #     yield output_gcode
    # finally:
    #     pass
    #     # try:
    #     #     if output_gcode.exists():
    #     #         output_gcode.unlink()
    #     # except Exception:
    #     #     pass


# =================                 =================
#                 批量3mf生成gcode夹具
# =================                 =================

@pytest.fixture
def batch_slice_3mf_to_gcode(engine_injector, gcode_path_factory, pytestconfig):
    """
    批量将3mf文件转换为gcode文件的夹具。
    生成的gcode文件名附带3mf文件的修改日期，如果gcode已经存在则跳过不生成。
    自动遍历data/models目录获取所有3mf文件。
    执行完后生成一个json文件保存3mf文件名和gcode文件名的映射关系。
    
    参数:
        engine_injector: 引擎注入器
        gcode_path_factory: gcode路径工厂
        pytestconfig: pytest配置
        
    返回:
        函数，执行批量切片并返回生成的gcode文件映射
    """
    def _slice_all(output_dir=None):
        """
        批量切片data/models目录下的所有3mf文件到gcode
        
        参数:
            output_dir: 输出目录，如果为None则使用默认gcode目录
            
        返回:
            3mf文件到gcode文件的映射字典
        """
        # 获取data/models目录路径
        data_root = Path(pytestconfig.rootpath) / "test_framework" / "engine_params" / "data" / "models"
        if not data_root.exists():
            raise FileNotFoundError(f"数据目录不存在: {data_root}")
        
        # 查找所有3mf文件
        three_mf_files = list(data_root.rglob("*.3mf"))
        if not three_mf_files:
            raise FileNotFoundError(f"在 {data_root} 目录下未找到任何.3mf文件")
        
        print(f"找到 {len(three_mf_files)} 个3mf文件")
        
        generated_gcode_files = {}
        
        for three_mf_path in three_mf_files:
            three_mf_path = Path(three_mf_path)
            if not three_mf_path.exists():
                print(f"警告: 3mf文件不存在: {three_mf_path}")
                continue
                
            # 获取3mf文件的修改时间
            mtime = three_mf_path.stat().st_mtime
            mtime_str = time.strftime("%Y%m%d_%H%M%S", time.localtime(mtime))
            
            # 构造gcode文件名
            if output_dir is None:
                gcode_path = Path(gcode_path_factory(
                    filename=f"{three_mf_path.stem}_{mtime_str}.gcode"
                ))
            else:
                output_dir = Path(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                gcode_path = output_dir / f"{three_mf_path.stem}_{mtime_str}.gcode"
            
            # 保存映射关系
            relative_3mf_path = three_mf_path.relative_to(data_root.parent.parent)
            generated_gcode_files[str(relative_3mf_path)] = str(gcode_path)
            
            # 如果gcode文件已存在，跳过生成
            if gcode_path.exists():
                print(f"Gcode文件已存在，跳过生成: {gcode_path}")
                continue
                
            # 重置项目
            reset_fut = engine_injector.submit("reset_project", {
                "skip_confirm": True,
                "silent": True,
                "project_name": f"batch_slice_project_{three_mf_path.stem}",
            })
            reset_result = reset_fut.result(timeout=30)
            assert reset_result.get("code") == 0, f"reset_project 失败：{reset_result}"
            
            # 加载3mf文件
            load_fut = engine_injector.submit("trigger_load_project2",
                                              {"file": str(three_mf_path),
                                               "discard_preset_changes": True},
                                              timeout=60)
            load_res = load_fut.result(timeout=90)
            assert load_res.get("code") == 0, f"加载模型失败：{load_res}"
            
            # 点击切片按钮
            slice_fut = engine_injector.submit("click_button", {"id": SLICE_BTN_ID})
            slice_res = slice_fut.result(timeout=120)
            assert slice_res.get("code") == 0, f"切片失败：{slice_res}"
            
            # 导出gcode
            export_fut = engine_injector.submit("export_gcode", {
                "export_all": False,
                "output": str(gcode_path)
            }, timeout=300)
            export_res = export_fut.result(timeout=360)
            assert export_res.get("code") == 0, f"导出 G-code 失败：{export_res}"
            
            # 等待文件落盘
            if not gcode_path.exists():
                end = time.time() + 5.0
                while time.time() < end:
                    if gcode_path.exists():
                        break
                    time.sleep(0.25)
            assert gcode_path.exists(), f"G-code 未生成：{gcode_path}"
            print(f"成功生成: {gcode_path}")
        
        # 生成映射关系的JSON文件
        mapping_file = (output_dir or gcode_path_factory("") / ".." / "3mf_gcode_mapping.json")
        if isinstance(mapping_file, str):
            mapping_file = Path(mapping_file)
        mapping_file = mapping_file.resolve() / "3mf_gcode_mapping.json"
        
        # 确保目录存在
        mapping_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入JSON文件
        import json
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(generated_gcode_files, f, indent=2, ensure_ascii=False)
        
        print(f"映射关系已保存到: {mapping_file}")
        return generated_gcode_files
        
    return _slice_all
