"""Functional coverage of the slicing pipeline stages seen in CrealityPrint's UI.

The GUI walks the user through: 正在准备 → 应用参数 → 网格切片 → 检查支撑必要性
→ 检测悬空 → 裙边/边沿 → 墙 → 填充 → 优化路径 → 生成G-code(层N) → 导出 →
加载显示数据 → G-code 预览(时间/耗材/走线类型表) — plus a gcode-path conflict
warning on crowded plates. This test drives the same pipeline headless with
supports forced on and asserts each observable stage and product.
"""

from __future__ import annotations

import re

import pytest

from utils import gcode, runner, stages
from utils.collect import collect_models, resolve_models_dirs


def pytest_generate_tests(metafunc):
    if "wzx_case" not in metafunc.fixturenames:
        return
    models_dirs = resolve_models_dirs(metafunc.config.getoption("--models-dir"))
    case_regex = metafunc.config.getoption("--case-regex") or ""
    cases = collect_models(models_dirs, case_regex)
    if not cases:
        pytest.skip(
            f"no models under {models_dirs} matching {case_regex!r}",
            allow_module_level=True,
        )
    metafunc.parametrize("wzx_case", cases, ids=[c["rel"] for c in cases])

# Core pipeline stages — every one must appear (names as the CLI prints them).
REQUIRED_STAGES = [
    "Preparing slice",
    "Applying slice parameters",
    "Slicing mesh",
    "Generating walls",
    "Generating infill regions",
    "Optimizing toolpath",
    "Generating G-code",
    "Slice complete",
]
# Unambiguous backbone: pairwise order that holds across models/configs.
BACKBONE_ORDER = [
    "Preparing slice",
    "Slicing mesh",
    "Generating walls",
    "Optimizing toolpath",
    "Generating G-code",
    "Slice complete",
]
# Support flow: either marker proves the support stage ran (the exact wording
# varies with model settings — auto vs forced supports).
SUPPORT_STAGE_MARKERS = ["Generating support", "Checking support necessity"]

SUPPORT_EXTRA_ARGS = ["--enable_support", "1"]


def _backbone_ok(stages_found: list[str]) -> bool:
    cursor = -1
    for needle in BACKBONE_ORDER:
        for i in range(cursor + 1, len(stages_found)):
            if needle.lower() in stages_found[i].lower():
                cursor = i
                break
        else:
            return False
    return True


@pytest.mark.slice
def test_slice_stages_and_support(wzx_case, slicer_exe, harness_config):
    cfg = harness_config
    model: str = wzx_case["rel"]

    out_dir = runner.make_case_out_dir(cfg["artifacts_dir"], f"stages_{model}")
    run = runner.run_slice(
        slicer_exe,
        wzx_case["path"],
        out_dir,
        cfg["case_timeout"],
        extra_args=SUPPORT_EXTRA_ARGS,
    )
    assert run.exit_code == 0, f"{model}: slicer failed: {run.error}"
    assert run.slice_ok, f"{model}: no gcode produced"

    # ── 1. stage coverage: core pipeline present, backbone order intact,
    #       support stages ran (强制开支撑时必须有支撑阶段) ──
    found = stages.parse_stages(run.stdout or "")
    missing = [s for s in REQUIRED_STAGES if stages.stage_index(found, s) == -1]
    assert not missing, f"{model}: missing stages {missing}; trace = {found}"
    assert _backbone_ok(found), f"{model}: backbone order broken; trace = {found}"
    assert any(stages.stage_index(found, m) != -1 for m in SUPPORT_STAGE_MARKERS), (
        f"{model}: no support stage ran; trace = {found}"
    )
    assert stages.stage_index(found, "Detect overhangs") != -1, (
        f"{model}: overhang detection stage missing; trace = {found}"
    )

    # ── 2. per-layer gcode generation progress, monotonic up to the last layer ──
    layers = stages.parse_layers(run.stdout or "")
    assert layers and layers[-1] >= 2, f"{model}: no per-layer gcode progress"
    assert all(b >= a for a, b in zip(layers, layers[1:])), (
        f"{model}: layer progress not monotonic: {layers}"
    )

    # ── 3. service markers: slice start / finished(layers=N) / export finished
    #       (SliceService logs go to stderr) ──
    markers = stages.parse_service_markers(run.stderr or "")
    assert any("slice start" in m for m in markers), f"{model}: no slice start marker"
    assert any("export finished" in m for m in markers), (
        f"{model}: no export finished marker"
    )
    reported_layers = stages.service_layers(run.stderr or "")
    assert reported_layers, f"{model}: 'slice finished layers=' marker missing"
    # The per-layer progress lines are throttled and may trail the true total;
    # the authoritative count is the slice-finished marker, cross-checked
    # against the gcode file below.
    assert layers[-1] <= reported_layers[-1], (
        f"{model}: progress layer {layers[-1]} exceeds reported total "
        f"{reported_layers[-1]}"
    )
    assert layers[-1] >= 0.9 * reported_layers[-1], (
        f"{model}: progress stopped at layer {layers[-1]} of {reported_layers[-1]}"
    )

    # ── 4. gcode products: layers, Z, per-type filament (incl. support) ──
    gci = gcode.parse_gcode(run.gcode_path)
    # File self-consistency: emitted layer changes match the file's own header
    # count. The slice-finished marker plans MORE layers than it exports
    # (empty layers produce no gcode), so only an upper bound holds there.
    if gci.header_total_layers is not None:
        assert gci.layers == gci.header_total_layers, (
            f"{model}: gcode has {gci.layers} layer changes, header claims "
            f"{gci.header_total_layers}"
        )
    assert gci.layers <= reported_layers[-1], (
        f"{model}: gcode layers {gci.layers} exceed planned "
        f"{reported_layers[-1]}"
    )
    assert gci.max_z > 0, f"{model}: no Z movement in gcode"
    assert gci.total_e > 0, f"{model}: no extrusion in gcode"

    wall_mm = gcode.type_length_mm(gci, "WALL")
    support_mm = gcode.type_length_mm(gci, "SUPPORT")
    infill_mm = gcode.type_length_mm(gci, "INFILL")
    assert wall_mm > 0, f"{model}: no WALL extrusion; types seen: {list(gci.type_e)}"
    assert infill_mm > 0, f"{model}: no INFILL extrusion"
    assert support_mm > 0, (
        f"{model}: supports forced on but SUPPORT filament = 0; "
        f"types seen: {list(gci.type_e)}"
    )

    # ── 5. GUI preview stats (打印时间/耗材长度) — soft: presence in preamble ──
    preamble = "\n".join(gci.header_lines)
    has_time = "printing time" in preamble.lower()
    has_length = re.search(r"filament used|filament length", preamble, re.IGNORECASE) is not None
    print(
        f"[stages] {model}: layers={gci.layers} max_z={gci.max_z:.2f} "
        f"wall={wall_mm:.1f}mm support={support_mm:.1f}mm "
        f"types={sorted(gci.type_e)} header_time={has_time} header_len={has_length}"
    )

    # Multi-object crowding produces the GUI conflict warning (gcode-path
    # conflict toast). The CLI pipeline does not run that GUI check, so its
    # absence here is expected — recorded, not asserted.
    conflict_hit = re.search(
        r"conflict|冲突", (run.stdout or "") + (run.stderr or ""), re.IGNORECASE
    )
    print(f"[stages] {model}: conflict warning in CLI output: {bool(conflict_hit)}")

    if run.slice_ok:
        import shutil

        shutil.rmtree(out_dir, ignore_errors=True)
