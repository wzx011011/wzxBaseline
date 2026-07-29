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
    1. 跳过首层，取最高外墙层，计算所有相邻外墙点之间的线段长度。
    2. 用“期望段长 + 容差”分出正常段和超阈段，并计算正常段平均长度。
    3. 超阈段若只比均值长 20% 以内则视为违规；明显更长的结构段不作为细分失败。
    通过标准：存在正常段，且没有应被细分却仍落在违规范围内的超阈段。
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
    1. 解析 acceleration_limit_mess 曲线；首层只累计挤出量，并结合丝径、密度换算耗材重量。
    2. 从第 1 层开始，按外墙、内墙、稀疏填充、内部实心填充切分连续打印块。
    3. 根据累计重量对配置速度/加速度线性裁剪，分别与 point.f 和 velocity_limits.ACCEL 比较。
    通过标准：所有目标打印块的速度和加速度都在各自容差内，且 ACCEL 不缺失。
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
