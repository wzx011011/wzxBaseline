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
    验证最大体积挤出率斜率开关：检查最后一层外墙路径点数是否被细分。
    - expected=0 -> 关闭：最后一层外墙路径点数不超过 5。
    - expected>0 -> 开启：最后一层至少有一条外墙路径点数大于 5。
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
    分段长度限制：统计外墙段长，超阈段若偏离均值不超过20%则判违规，否则舍弃。
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
    speed_limit_to_height_enable：利用 SmoothSpeedAcc 校验裁剪后的速度/加速度是否匹配。
    - 目标类型：外墙/内墙/稀疏填充/内部实心填充；跳过首层。
    - 速度取 point.f，与 detect_speed(raw_speed, z) 结果对比；
    - 加速度取 velocity_limits.ACCEL，与 detect_acc(raw_acc, z) 结果对比。
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
    acceleration_limit_mess_enable：按耗材重量做线性裁剪，校验打印块的速度/加速度是否匹配裁剪后的期望值。
    - 首层仅用于累计耗材重量，实际校验从第 1 层开始。
    - 目标挤出类型：外墙/内墙/稀疏填充/内部实心填充。
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
