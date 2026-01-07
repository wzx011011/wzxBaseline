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
    parse_seam_slope_conditional,
    parse_seam_slope_entire_loop,
    parse_seam_slope_inner_walls,
    parse_seam_slope_min_length,
    parse_seam_slope_start_height,
    parse_seam_slope_steps,
    parse_scarf_angle_threshold,
    parse_scarf_joint_speed,
    parse_scarf_overhang_threshold,
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


# ================== seam_slope_conditional ==================
@pytest.mark.engine_params
def test_seam_slope_conditional(slice_and_export: Path, expected_seam_slope_conditional: bool):
    """测试 seam_slope_conditional 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_seam_slope_conditional(gcode_path, expected_seam_slope_conditional)
    assert ok, f"seam_slope_conditional expected {expected_seam_slope_conditional}, actual {actual}, details: {details}"


# ================== seam_slope_entire_loop ==================
@pytest.mark.engine_params
def test_seam_slope_entire_loop(slice_and_export: Path, expected_seam_slope_entire_loop: bool):
    """测试 seam_slope_entire_loop 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_seam_slope_entire_loop(gcode_path, expected_seam_slope_entire_loop)
    assert ok, f"seam_slope_entire_loop expected {expected_seam_slope_entire_loop}, actual {actual}, details: {details}"


# ================== seam_slope_inner_walls ==================
@pytest.mark.engine_params
def test_seam_slope_inner_walls(slice_and_export: Path, expected_seam_slope_inner_walls: bool):
    """测试 seam_slope_inner_walls 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_seam_slope_inner_walls(gcode_path, expected_seam_slope_inner_walls)
    assert ok, f"seam_slope_inner_walls expected {expected_seam_slope_inner_walls}, actual {actual}, details: {details}"


# ================== seam_slope_min_length ==================
@pytest.mark.engine_params
def test_seam_slope_min_length(slice_and_export: Path, expected_seam_slope_min_length: float):
    """测试 seam_slope_min_length 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_seam_slope_min_length(gcode_path, expected_seam_slope_min_length)
    assert ok, f"seam_slope_min_length expected {expected_seam_slope_min_length}, actual {actual}, details: {details}"


# ================== seam_slope_start_height ==================
@pytest.mark.engine_params
def test_seam_slope_start_height(slice_and_export: Path, expected_seam_slope_start_height: float):
    """测试 seam_slope_start_height 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_seam_slope_start_height(gcode_path, expected_seam_slope_start_height)
    assert ok, f"seam_slope_start_height expected {expected_seam_slope_start_height}, actual {actual}, details: {details}"


# ================== seam_slope_steps ==================
@pytest.mark.engine_params
def test_seam_slope_steps(slice_and_export: Path, expected_seam_slope_steps: float):
    """测试 seam_slope_steps 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_seam_slope_steps(gcode_path, expected_seam_slope_steps)
    assert ok, f"seam_slope_steps expected {expected_seam_slope_steps}, actual {actual}, details: {details}"


# ================== scarf_angle_threshold ==================
@pytest.mark.engine_params
def test_scarf_angle_threshold(slice_and_export: Path, expected_scarf_angle_threshold: float):
    """测试 scarf_angle_threshold 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_scarf_angle_threshold(gcode_path, expected_scarf_angle_threshold)
    assert ok, f"scarf_angle_threshold expected {expected_scarf_angle_threshold}, actual {actual}, details: {details}"


# ================== scarf_joint_speed ==================
@pytest.mark.engine_params
def test_scarf_joint_speed(slice_and_export: Path, expected_scarf_joint_speed: float):
    """测试 scarf_joint_speed 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_scarf_joint_speed(gcode_path, expected_scarf_joint_speed)
    assert ok, f"scarf_joint_speed expected {expected_scarf_joint_speed}, actual {actual}, details: {details}"


# ================== scarf_overhang_threshold ==================
@pytest.mark.engine_params
def test_scarf_overhang_threshold(slice_and_export: Path, expected_scarf_overhang_threshold: float):
    """测试 scarf_overhang_threshold 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_scarf_overhang_threshold(gcode_path, expected_scarf_overhang_threshold)
    assert ok, f"scarf_overhang_threshold expected {expected_scarf_overhang_threshold}, actual {actual}, details: {details}"
