# tests/engine_params/speed/test_overhang_speed.py
from pathlib import Path
import pytest

from engine_params.src.gcode.speed.overhang_speed_check import (
    parse_bridge_speed,
    parse_internal_bridge_speed,
    parse_enable_overhang_speed,
    parse_slowdown_for_curled_perimeters,
    parse_overhang_speed_classic,
    parse_overhang_totally_speed,
    parse_smooth_speed_discontinuity_area,
)

# ================== bridge_speed ==================
@pytest.mark.engine_params
def test_bridge_speed(slice_and_export: Path, expected_bridge_speed: float, tolerance: float):
    """
    Overhang wall（桥接）速度：校验 LayerRegion.feedrate 是否等于期望值。
    TODO，要加上没有开启翘边降速，额外检测 Bridge 挤出类型（其实就是相当于悬空的 Bridge infill ）的情况
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_bridge_speed(
        gcode_path,
        expected_bridge_speed,
        tolerance,
    )
    assert ok, f"details={details}"


# ================== internal_bridge_speed ==================
@pytest.mark.engine_params
def test_internal_bridge_speed(slice_and_export: Path, expected_internal_bridge_speed: float, tolerance: float):
    """
    Internal bridge 速度：校验 INTERNAL_BRIDGE LayerRegion.feedrate 是否等于期望值。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_internal_bridge_speed(
        gcode_path,
        expected_internal_bridge_speed,
        tolerance,
    )
    assert ok, f"details={details}"


@pytest.mark.engine_params
def test_enable_overhang_speed(slice_and_export: Path, expected_enable_overhang_speed: bool, tolerance: float):
    """
    Overhang 速度开关：检查除首层外外墙路径点的 feedrate 是否与 outer_wall_speed 一致。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_enable_overhang_speed(
        gcode_path,
        expected_enable_overhang_speed,
        tolerance,
    )
    assert ok, f"details={details}"


@pytest.mark.engine_params
def test_slowdown_for_curled_perimeters(slice_and_export: Path, expected_slowdown_for_curled_perimeters: bool, tolerance: float):
    """
    翘边降速：Overhang 层的外墙应出现 overhang_4_4_speed（开启时），否则保持 outer_wall_speed。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_slowdown_for_curled_perimeters(
        gcode_path,
        expected_slowdown_for_curled_perimeters,
        tolerance,
    )
    assert ok, f"details={details}"


@pytest.mark.engine_params
def test_overhang_speed_classic(slice_and_export: Path, expected_overhang_speed_classic: bool, tolerance: float):
    """
    经典悬垂速度：带 Overhang wall 的层，外墙整条路径是否全部为 overhang_4_4_speed。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_overhang_speed_classic(
        gcode_path,
        expected_overhang_speed_classic,
        tolerance,
    )
    assert ok, f"details={details}"


@pytest.mark.engine_params
def test_overhang_totally_speed(slice_and_export: Path, expected_overhang_totally_speed: float, tolerance: float):
    """
    完全悬垂速度：Overhang wall 的路径点 point.f 全部应等于期望值。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_overhang_totally_speed(
        gcode_path,
        expected_overhang_totally_speed,
        tolerance,
    )
    assert ok, f"details={details}"


@pytest.mark.engine_params
def test_smooth_speed_discontinuity_area(slice_and_export: Path, expected_smooth_speed_discontinuity_area: bool, tolerance: float):
    """
    平滑速度过渡：检查含 Overhang wall 的层，外墙路径速度是否单调（增/减）。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_smooth_speed_discontinuity_area(
        gcode_path,
        expected_smooth_speed_discontinuity_area,
        tolerance,
    )
    assert ok, f"details={details}"
