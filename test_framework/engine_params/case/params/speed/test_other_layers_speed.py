# tests/engine_params/speed/test_other_layers_speed.py
from pathlib import Path
import pytest

from engine_params.src.gcode.speed.other_layers_speed_check import (
    parse_outer_wall_speed,
    parse_inner_wall_speed,
    parse_sparse_infill_speed,
    parse_solid_infill_speed,
    parse_top_surface_speed,
    parse_gap_infill_speed,
)


@pytest.mark.engine_params
def test_outer_wall_speed(slice_and_export: Path, expected_outer_wall_speed: float, tolerance: float):
    """
    外层壁速度检查：
    - 检查所有层的OUTER_WALL类型的LayerRegion.feedrate
    - 确保所有外层壁的速度与期望值一致
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
    内层壁速度检查：
    - 检查所有层的INNER_WALL类型的LayerRegion.feedrate
    - 确保所有内层壁的速度与期望值一致
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
    稀疏填充速度检查：
    - 检查所有层的SPARSE_INFILL类型的LayerRegion.feedrate
    - 确保所有稀疏填充的速度与期望值一致
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
    实体填充速度检查：
    - 检查所有层的SOLID_INTERNAL_INFILL类型的LayerRegion.feedrate
    - 确保所有实体填充的速度与期望值一致
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
    顶面速度检查：
    - 检查所有层的TOP_SURFACE类型的LayerRegion.feedrate
    - 确保所有顶面的速度与期望值一致
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
    间隙填充速度检查：
    - 检查所有层的GAP_INFILL类型的LayerRegion.feedrate
    - 确保所有间隙填充的速度与期望值一致
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, expected, details = parse_gap_infill_speed(
        gcode_path,
        expected_gap_infill_speed,
        tolerance,
    )
    assert ok, f"details={details}"