# tests/engine_params/speed/test_overhang_speed.py
from pathlib import Path
import pytest

from engine_params.src.gcode.process.speed.overhang_speed_check import (
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
    验证方法：
    1. 跳过首层，仅解析 OVERHANG_WALL（悬垂外墙）Region。
    2. 读取 Region.feedrate（mm/s），与 bridge_speed 期望值逐一比较。
    通过标准：至少检查到一个悬垂外墙 Region，feedrate 不缺失，且全部在容差范围内。
    说明：当前实现验证的是 OVERHANG_WALL，不包含普通 BRIDGE 填充类型。
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
    验证方法：
    1. 跳过首层，仅解析 INTERNAL_BRIDGE（内部桥接）Region。
    2. 读取 Region.feedrate（mm/s），与 internal_bridge_speed 期望值逐一比较。
    通过标准：至少检查到一个内部桥接 Region，feedrate 不缺失，且全部在容差范围内。
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
    验证方法：
    1. 从 CONFIG_BLOCK 读取 outer_wall_speed，并跳过首层解析所有外墙路径点。
    2. 只要存在实际速度不同于 outer_wall_speed 的点，就判定悬垂速度功能已生效。
    通过标准：推断出的启用状态与期望一致，所有路径点都有速度值。
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
    验证方法：
    1. 从导出 G-code 的 CONFIG_BLOCK 读取 slowdown_for_curled_perimeters。
    2. 定位非首层 OVERHANG_WALL，并采集实际速度作为诊断信息。
    通过标准：配置开关与期望一致；悬垂路径和速度不参与 L1 通过判定。
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
    验证方法：
    1. 核对 CONFIG_BLOCK 的 overhang_speed_classic 开关，并定位含 OVERHANG_WALL 的非首层。
    2. 检查同层普通外墙路径点，确认至少有点低于 outer_wall_speed，作为分级降速已生效的证据。
    通过标准：配置开关和实际降速共同推断出的状态与期望一致，且速度不缺失。
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
    验证方法：
    1. 跳过首层，仅提取 OVERHANG_WALL 的所有路径点。
    2. 逐点读取实际 F 速度（mm/s），与 overhang_totally_speed 期望值比较。
    通过标准：至少检查到一个点，速度不缺失，且所有点都在容差范围内。
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
    验证方法：
    1. 跳过首层，定位含 OVERHANG_WALL 的层，并提取同层普通外墙每条路径的逐点速度序列。
    2. 开启时要求速度序列单调递增或递减；关闭时要求至少观察到一条非单调路径。
    通过标准：根据路径单调性推断出的开关状态与期望一致，且速度不缺失。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_smooth_speed_discontinuity_area(
        gcode_path,
        expected_smooth_speed_discontinuity_area,
        tolerance,
    )
    assert ok, f"details={details}"
