# test_framework/engine_params/case/params/quality/test_layer_height.py
from __future__ import annotations

from pathlib import Path

import math

import pytest

from engine_params.src.gcode.layer_height_check import parse_layer_height,parse_initial_layer_print_height

# ----------- 参数化示例（indirect=True） -----------
# 说明：
#  - 把 dict 作为 request.param 传入 slice_and_export fixture（indirect=True）
#  - 每个 param 会触发一次 fixture 完整流程（reset/load/slice/export）

slice_cases = [
    {"input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\initial_layer_print_height_0.28mm.3mf"},

]
expectations = [0.28]
params = [
    pytest.param(
        sc, exp
    )
    for sc, exp in zip(slice_cases, expectations)
]
@pytest.mark.engine_params
@pytest.mark.parametrize(("slice_and_export", "expected_first_layer_height"), params,
                         indirect=["slice_and_export"])
def test_initial_layer_print_height(slice_and_export: Path,
                                    expected_first_layer_height: float):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()
    layer_cfg: dict[str, object] = parse_initial_layer_print_height(gcode_path)
    assert layer_cfg is not None
    first_layer_z = layer_cfg["first_layer_z"]
    assert first_layer_z == expected_first_layer_height




# ================== layer_height ==================

# 仅供夹具使用的切片参数
slice_cases2 = [
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\layer_height_0.24mm.3mf",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\layer_height_0.32mm.3mf",
    },
]

# 与夹具无关、用于断言的期望
expectation2 = [0.24,0.32]

# 一一对应（而不是笛卡尔积），用 zip 合并：
params = [
    pytest.param(sc, exp)
    for sc, exp in zip(slice_cases2, expectation2)
]
@pytest.mark.engine_params
@pytest.mark.parametrize(("slice_and_export", "expected_layer_height"),
                         params,
                         indirect=["slice_and_export"])
def test_layer_height(slice_and_export, expected_layer_height: float):
    """
    slice_and_export fixture 已完成导出，并返回导出的 gcode Path。
    这里只做解析与断言（占位解析器）。
    """
    gcode_path: Path = slice_and_export  # fixture 返回的值
    assert gcode_path.exists(), "导出的 gcode 文件不存在（fixture 有逻辑问题）"
    layer_cfg = parse_layer_height(gcode_path)
    assert layer_cfg is not None, "未在 G-code 中解析到 layer_height"
    # assert layer_cfg["config_layer_height"] == expected_layer_height
    layers = layer_cfg["layers"]
    for i,layer in enumerate(layers):
        if i == 0:
            continue
        _,h = layer
        assert math.isclose(h, expected_layer_height,rel_tol=1e-3),f"for DEBUG: i = {i}."
