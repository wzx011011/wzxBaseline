# tests/engine_params/speed/test_other_layers_speed.py
from pathlib import Path
import pytest

from engine_params.src.gcode.process.speed.other_layers_speed_check import (
    parse_outer_wall_speed,
    parse_inner_wall_speed,
    parse_sparse_infill_speed,
    parse_solid_infill_speed,
    parse_top_surface_speed,
    parse_gap_infill_speed,
    parse_small_perimeter_threshold,
    parse_small_perimeter_speed,
)


@pytest.mark.engine_params
def test_outer_wall_speed(slice_and_export: Path, expected_outer_wall_speed: float, tolerance: float):
    """
    验证方法：
    1. 跳过首层，仅解析 OUTER_WALL（外墙）Region。
    2. 读取 Region.feedrate（mm/s），与 outer_wall_speed 期望值逐一比较。
    通过标准：至少检查到一个外墙 Region，feedrate 不缺失，且全部在容差范围内。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, expected, details = parse_outer_wall_speed(
        gcode_path,
        expected_outer_wall_speed,
        tolerance,
    )
    assert ok, f"details={details}"


@pytest.mark.engine_params
def test_inner_wall_speed(slice_and_export: Path, expected_inner_wall_speed: float, tolerance: float):
    """
    验证方法：
    1. 跳过首层，仅解析 INNER_WALL（内墙）Region。
    2. 读取 Region.feedrate（mm/s），与 inner_wall_speed 期望值逐一比较。
    通过标准：解析到的内墙 Region 均有 feedrate，且全部在容差范围内。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, expected, details = parse_inner_wall_speed(
        gcode_path,
        expected_inner_wall_speed,
        tolerance,
    )
    assert ok, f"details={details}"


@pytest.mark.engine_params
def test_sparse_infill_speed(slice_and_export: Path, expected_sparse_infill_speed: float, tolerance: float):
    """
    验证方法：
    1. 跳过首层，仅解析 SPARSE_INFILL（稀疏填充）Region。
    2. 读取 Region.feedrate（mm/s），与 sparse_infill_speed 期望值逐一比较。
    通过标准：解析到的稀疏填充 Region 均有 feedrate，且全部在容差范围内。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, expected, details = parse_sparse_infill_speed(
        gcode_path,
        expected_sparse_infill_speed,
        tolerance,
    )
    assert ok, f"details={details}"


@pytest.mark.engine_params
def test_solid_infill_speed(slice_and_export: Path, expected_solid_infill_speed: float, tolerance: float):
    """
    验证方法：
    1. 跳过首层，仅解析 INTERNAL_SOLID_INFILL（内部实心填充）Region。
    2. 读取 Region.feedrate（mm/s），与 solid_infill_speed 期望值逐一比较。
    通过标准：解析到的内部实心填充 Region 均有 feedrate，且全部在容差范围内。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, expected, details = parse_solid_infill_speed(
        gcode_path,
        expected_solid_infill_speed,
        tolerance,
    )
    assert ok, f"details={details}"


@pytest.mark.engine_params
def test_top_surface_speed(slice_and_export: Path, expected_top_surface_speed: float, tolerance: float):
    """
    验证方法：
    1. 跳过首层，仅解析 TOP_SURFACE（顶面）Region。
    2. 读取 Region.feedrate（mm/s），与 top_surface_speed 期望值逐一比较。
    通过标准：解析到的顶面 Region 均有 feedrate，且全部在容差范围内。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, expected, details = parse_top_surface_speed(
        gcode_path,
        expected_top_surface_speed,
        tolerance,
    )
    assert ok, f"details={details}"


@pytest.mark.engine_params
def test_gap_infill_speed(slice_and_export: Path, expected_gap_infill_speed: float, tolerance: float):
    """
    验证方法：
    1. 跳过首层，仅解析 GAP_INFILL（间隙填充）Region。
    2. 读取 Region.feedrate（mm/s），与 gap_infill_speed 期望值逐一比较。
    通过标准：解析到的间隙填充 Region 均有 feedrate，且全部在容差范围内。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, expected, details = parse_gap_infill_speed(
        gcode_path,
        expected_gap_infill_speed,
        tolerance,
    )
    assert ok, f"details={details}"


@pytest.mark.engine_params
def test_small_perimeter_threshold(slice_and_export: Path, expected_small_perimeter_threshold: float, tolerance: float):
    """
    验证方法：
    1. 跳过首层，提取内墙/外墙路径并补上首尾闭合段，计算每条墙路径的实际周长。
    2. 将阈值按圆半径解释并换算为 2πr；小于阈值的路径应使用 small_perimeter_speed。
    3. 大于等于阈值的路径应保持对应的 outer_wall_speed 或 inner_wall_speed。
    通过标准：至少检查到一条墙路径，速度不缺失，且阈值两侧的速度选择全部正确。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, expected, details = parse_small_perimeter_threshold(
        gcode_path,
        expected_small_perimeter_threshold,
        tolerance,
    )
    assert ok, f"details={details}"


@pytest.mark.engine_params
def test_small_perimeter_speed(slice_and_export: Path, expected_small_perimeter_speed: float, tolerance: float):
    """
    验证方法：
    1. 从 CONFIG_BLOCK 读取 small_perimeter_threshold，并换算成周长阈值 2πr。
    2. 跳过首层，计算每条内墙/外墙路径周长；小轮廓使用期望速度，其他轮廓保持墙速度。
    通过标准：至少检查到一条墙路径，速度不缺失，且所有路径的实际速度符合上述规则。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, expected, details = parse_small_perimeter_speed(
        gcode_path,
        expected_small_perimeter_speed,
        tolerance,
    )
    assert ok, f"details={details}"
