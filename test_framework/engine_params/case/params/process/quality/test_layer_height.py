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
@pytest.mark.engine_params
def test_initial_layer_print_height(slice_and_export: Path,
                                    expected_first_layer_height: float):
    """验证首层实际打印高度，而不是只回读项目配置。

    解析首个有效 ``LAYER_CHANGE`` 的 ``HEIGHT``，它是首层实际挤出高度；
    ``Z`` 仅保留作诊断，因为部分固件风格不会输出标准 Z 注释。通过标准：
    首层 HEIGHT 与配置中的 ``initial_layer_print_height`` 均匹配期望值。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()
    layer_cfg: dict[str, object] = parse_initial_layer_print_height(gcode_path)
    actual_height = layer_cfg["first_layer_height"]
    assert actual_height is not None, f"未解析到首层 HEIGHT: {layer_cfg}"
    assert math.isclose(actual_height, expected_first_layer_height, abs_tol=1e-4), layer_cfg
    config_height = layer_cfg["config_initial_layer_print_height"]
    assert config_height is not None, layer_cfg
    assert math.isclose(float(config_height), expected_first_layer_height, abs_tol=1e-4), layer_cfg


# ================== layer_height ==================

@pytest.mark.engine_params
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
