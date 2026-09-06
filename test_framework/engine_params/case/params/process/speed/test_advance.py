# tests/engine_params/speed/test_advance.py
from pathlib import Path
import pytest

from engine_params.src.gcode.process.speed.advance_check import (
    parse_max_volumetric_extrusion_rate_slope,
    parse_max_volumetric_extrusion_rate_slope_segment_length,
    parse_speed_limit_to_height_enable,
    parse_acceleration_limit_mess_enable,
)


@pytest.mark.engine_params
def test_max_volumetric_extrusion_rate_slope(
        slice_and_export: Path,
        expected_max_volumetric_extrusion_rate_slope: float,
):
    """
    验证方法：
    1. 跳过首层，找到包含 OUTER_WALL 的最高层，统计该层每条外墙路径的点数。
    2. expected=0 代表关闭，路径不应被细分；expected>0 代表开启，路径应出现额外细分点。
    通过标准：关闭时所有路径点数不超过 5；开启时至少一条路径点数大于 5。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_max_volumetric_extrusion_rate_slope(
        gcode_path,
        expected_max_volumetric_extrusion_rate_slope,
    )
    assert ok, f"details={details}"


@pytest.mark.engine_params
def test_max_volumetric_extrusion_rate_slope_segment_length(
        slice_and_export: Path,
        expected_max_volumetric_extrusion_rate_slope_segment_length: float,
        tolerance: float,
):
    """
    验证方法：
    1. 核对 CONFIG_BLOCK 中的目标分段长度，再取最高外墙层的相邻线段。
    2. 识别不超过目标值 1.5 倍的重复细分簇，结构拐角和闭合边不计入该簇。
    3. 比较细分簇中位数，并检查其覆盖至少一半外墙线段。
    通过标准：配置匹配、细分簇中位数在容差内且覆盖率达标。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_max_volumetric_extrusion_rate_slope_segment_length(
        gcode_path,
        expected_max_volumetric_extrusion_rate_slope_segment_length,
        tolerance,
    )
    assert ok, f"details={details}"


@pytest.mark.engine_params
def test_speed_limit_to_height_enable(
        slice_and_export: Path,
        expected_speed_limit_to_height_enable: bool,
        speed_limit_to_height: str,
):
    """
    验证方法：
    1. 核对导出 G-code 的 CONFIG_BLOCK 中高度限速开关和限速曲线是否与期望一致。
    2. 在曲线覆盖的高度范围内，从逐点运动路径采集外墙/内墙的实际 F 和 ACCEL。
    3. 对同一种墙类型比较不同高度的采样值，确认速度和加速度都发生变化。
    通过标准：开关及曲线匹配，采样字段不缺失，且至少一种墙类型同时观察到速度、加速度变化。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_speed_limit_to_height_enable(
        gcode_path,
        expected_speed_limit_to_height_enable,
        speed_limit_to_height,
    )
    assert ok, f"details={details}"


@pytest.mark.engine_params
def test_acceleration_limit_mess_enable(
        slice_and_export: Path,
        expected_acceleration_limit_mess_enable: bool,
        acceleration_limit_mess: str,
        material_diameter: float,
        material_density: float,
        speed_tolerance: float,
        acc_tolerance: float,
):
    """
    验证方法：
    1. 核对开关、曲线、丝径和密度，累计完整 G-code 中各类正向挤出的重量。
    2. 对曲线区间内的完整非首层，按层前后重量计算外墙/内墙的限速边界。
    3. 校验真实挤出速度和加速度；允许其它限速降低速度，但拒绝越界和无有效采样。
    通过标准：有可观测的速度/加速度限幅，所有采样均符合边界，且 ACCEL 不缺失。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_acceleration_limit_mess_enable(
        gcode_path,
        expected_acceleration_limit_mess_enable,
        acceleration_limit_mess,
        material_diameter,
        material_density,
        speed_tolerance,
        acc_tolerance,
    )
    assert ok, f"details={details}"
