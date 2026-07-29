from __future__ import annotations

from pathlib import Path

import pytest

from engine_params.src.gcode.process.quality.ironing_check import (
    parse_ironing_type,
    parse_ironing_pattern,
    parse_ironing_flow,
    parse_ironing_spacing,
    parse_ironing_speed,
    parse_ironing_angle,
)


# ================== ironing_type ==================
@pytest.mark.engine_params
def test_ironing_type(slice_and_export: Path, expected_ironing_type: str):
    """验证熨平应用的表面范围。

    C3DSlicer 在 ``Fill.cpp`` 中按 no/top/all-solid/topmost 选择熨平层；规划统计各层
    Ironing 挤出块，核对其是否只出现在顶面、全部实心面或完全不出现。
    3MF 使用三层错位台阶，提供顶层、被上层覆盖的实心面和最高顶面三类区域。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_ironing_type(gcode_path, expected_ironing_type)
    assert ok, f"ironing_type expected {expected_ironing_type}, actual {actual}, details: {details}"


# ================== ironing_pattern ==================
@pytest.mark.engine_params
def test_ironing_pattern(slice_and_export: Path, expected_ironing_pattern: str):
    """验证熨平路径图案。

    C3DSlicer 把 ``ironing_pattern`` 交给填充器生成路径；规划从 Ironing 块提取 XY
    折线，zig-zag 应为往复平行线，concentric 应为闭合轮廓族。
    3MF 使用 24 mm 方形平顶，保证两种图案都有足够路径可分类。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_ironing_pattern(gcode_path, expected_ironing_pattern)
    assert ok, f"ironing_pattern expected {expected_ironing_pattern}, actual {actual}, details: {details}"


# ================== ironing_flow ==================
@pytest.mark.engine_params
def test_ironing_flow(slice_and_export: Path, expected_ironing_flow: str):
    """验证熨平流量百分比。

    C3DSlicer 以 ``默认层高 × ironing_flow`` 构造熨平流量；规划统计 Ironing 段
    ``E/XY长度``，与基准用例的比率应等于设置百分比之比。
    3MF 使用固定面积方形平顶，并固定 spacing、speed、line width 与材料参数。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_ironing_flow(gcode_path, expected_ironing_flow)
    assert ok, f"ironing_flow expected {expected_ironing_flow}, actual {actual}, details: {details}"


# ================== ironing_spacing ==================
@pytest.mark.engine_params
def test_ironing_spacing(slice_and_export: Path, expected_ironing_spacing: float):
    """验证相邻熨平线间距。

    C3DSlicer 直接把该值写入 ``ironing_params.line_spacing``；规划拟合 Ironing
    平行路径并计算相邻中心线距离，其中位数应在容差内等于期望值。
    3MF 使用宽大方形平顶，避开边界处被裁剪的短线。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_ironing_spacing(gcode_path, expected_ironing_spacing)
    assert ok, f"ironing_spacing expected {expected_ironing_spacing}, actual {actual}, details: {details}"


# ================== ironing_speed ==================
@pytest.mark.engine_params
def test_ironing_speed(slice_and_export: Path, expected_ironing_speed: float):
    """验证熨平挤出速度。

    C3DSlicer 为 Ironing role 选择 ``ironing_speed``；规划解析 Ironing 块中的
    ``G1 F``，换算 mm/s 后稳定挤出段均应等于期望值。
    3MF 使用边长不少于 24 mm 的平顶，确保存在足够长的恒速熨平线。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_ironing_speed(gcode_path, expected_ironing_speed)
    assert ok, f"ironing_speed expected {expected_ironing_speed}, actual {actual}, details: {details}"


# ================== ironing_angle ==================
@pytest.mark.engine_params
def test_ironing_angle(slice_and_export: Path, expected_ironing_angle: float):
    """验证熨平路径方向。

    C3DSlicer 取显式 ``ironing_angle``，负值时才回退到 infill_direction；规划从
    Ironing 长直段反算无向角并与期望角度比较。3MF 使用方形平顶，避免模型长边
    对 0/45/90 度中的某一方向产生路径不足偏差。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_ironing_angle(gcode_path, expected_ironing_angle)
    assert ok, f"ironing_angle expected {expected_ironing_angle}, actual {actual}, details: {details}"
