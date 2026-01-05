from __future__ import annotations

from pathlib import Path

import pytest

from engine_params.src.gcode.wipe_speed_check import check_wipe_speed_by_layer
from engine_params.src.gcode.process.quality.seam_check import (
    parse_seam_position,
    parse_seam_gap,
    parse_staggered_inner_seams,
    parse_seam_slope_type,
    parse_scarf_joint_flow_ratio,
)


# ================== seam_position ==================
@pytest.mark.engine_params
def test_seam_position(slice_and_export: Path, expected_seam_position: str):
    """测试接缝位置参数 (aligned/nearest/random)"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_seam_position(gcode_path, expected_seam_position)
    assert ok, f"seam_position expected {expected_seam_position}, actual {actual}, details: {details}"


# ================== seam_gap ==================
@pytest.mark.engine_params
def test_seam_gap(slice_and_export: Path, expected_seam_gap: float):
    """测试接缝间隙参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_seam_gap(gcode_path, expected_seam_gap, tolerance=0.001)
    assert ok, f"seam_gap expected {expected_seam_gap}, actual {actual}, details: {details}"


# ================== staggered_inner_seams ==================
@pytest.mark.engine_params
def test_staggered_inner_seams(slice_and_export: Path, expected_staggered: bool):
    """测试交错内墙接缝参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_staggered_inner_seams(gcode_path, expected_staggered)
    assert ok, f"staggered_inner_seams expected {expected_staggered}, actual {actual}, details: {details}"


# ================== seam_slope_type ==================
@pytest.mark.engine_params
@pytest.mark.xfail(reason="seam_slope_type parameter may not be supported by current slicer version")
def test_seam_slope_type(slice_and_export: Path, expected_slope_type: str):
    """测试接缝斜坡类型参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_seam_slope_type(gcode_path, expected_slope_type)
    assert ok, f"seam_slope_type expected {expected_slope_type}, actual {actual}, details: {details}"


# ================== scarf_joint_flow_ratio ==================
@pytest.mark.engine_params
def test_scarf_joint_flow_ratio(slice_and_export: Path, expected_flow_ratio: float):
    """测试斜接流量比参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_scarf_joint_flow_ratio(
        gcode_path, expected_flow_ratio, tolerance=0.01
    )
    assert ok, f"scarf_joint_flow_ratio expected {expected_flow_ratio}, actual {actual}, details: {details}"


# ================== wipe_speed ==================
@pytest.mark.engine_params
def test_wipe_speed(slice_and_export: Path, expected_has_wipe: bool) -> None:
    """
    slice_and_export fixture 已完成导出，并返回导出的 gcode Path。
    这里只做解析与断言（占位解析器逻辑）。
    """
    gcode_path: Path = slice_and_export  # fixture 返回的文件路径
    assert gcode_path.exists(), "导出的 gcode 文件不存在（fixture 逻辑异常）"

    wipe_cfg: dict[str, object] = check_wipe_speed_by_layer(gcode_path, 500)
    # 通过配置结果判断是否检测到了 wipe 指令，必须与预期保持一致
    assert bool(wipe_cfg) is expected_has_wipe, (
        f"wipe 检测结果应为 {expected_has_wipe}，实际为 {bool(wipe_cfg)}，详情: {wipe_cfg}"
    )
    assert wipe_cfg is not None, "未在 G-code 中检测到 wipe"
    # TODO: 完成 wipe 相关的具体断言逻辑
