from __future__ import annotations

from pathlib import Path

import pytest

from engine_params.src.gcode.process.quality.overhangs_check import (
    parse_extra_perimeters_on_overhangs,
    parse_make_overhang_printable,
    parse_make_overhang_printable_angle,
    parse_make_overhang_printable_hole_size,
    parse_overhang_optimization,
)


# ================== extra_perimeters_on_overhangs ==================
@pytest.mark.engine_params
def test_extra_perimeters_on_overhangs(slice_and_export: Path, expected_extra_perimeters_on_overhangs: bool):
    """验证悬垂区域是否增加额外周长。

    C3DSlicer 在 ``PerimeterGenerator.cpp`` 中仅对非首层、已检测到的悬垂面增加墙；
    规划在悬垂层按岛统计 perimeter 数量，开启组应比关闭组多一圈且普通直壁层不变。
    3MF 使用下窄上宽的阶梯悬挑，并固定 detect_overhang_wall=true。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_extra_perimeters_on_overhangs(gcode_path, expected_extra_perimeters_on_overhangs)
    assert ok, f"extra_perimeters_on_overhangs expected {expected_extra_perimeters_on_overhangs}, actual {actual}, details: {details}"


# ================== make_overhang_printable ==================
@pytest.mark.engine_params
def test_make_overhang_printable(slice_and_export: Path, expected_make_overhang_printable: bool):
    """验证不可打印悬垂轮廓是否被收敛重构。

    C3DSlicer 在 ``PrintObjectSlice.cpp`` 中按允许角度逐层限制上层轮廓扩张；规划
    比较原模型切片轮廓与 G-code 外墙边界，开启时过陡悬垂应被内缩，关闭时保持原轮廓。
    3MF 使用 70° 外倾锥台并包含一段可打印直壁作为对照。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_make_overhang_printable(gcode_path, expected_make_overhang_printable)
    assert ok, f"make_overhang_printable expected {expected_make_overhang_printable}, actual {actual}, details: {details}"


# ================== make_overhang_printable_angle ==================
@pytest.mark.engine_params
def test_make_overhang_printable_angle(slice_and_export: Path, expected_make_overhang_printable_angle: float):
    """验证可打印化采用的最大悬垂角。

    C3DSlicer 将该角度换算为相邻层允许的最大 XY 扩张；规划由各层外墙包围盒变化量
    和层高反算实际坡角，应与设置值一致。3MF 使用连续外倾锥台，且开启
    make_overhang_printable，避免台阶几何掩盖角度效果。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_make_overhang_printable_angle(gcode_path, expected_make_overhang_printable_angle)
    assert ok, f"make_overhang_printable_angle expected {expected_make_overhang_printable_angle}, actual {actual}, details: {details}"


# ================== make_overhang_printable_hole_size ==================
@pytest.mark.engine_params
def test_make_overhang_printable_hole_size(slice_and_export: Path, expected_make_overhang_printable_hole_size: float):
    """验证可打印化忽略小孔的面积阈值。

    C3DSlicer 在 ``PrintObjectSlice.cpp`` 中以孔面积而非直径与该阈值比较；规划在同一层
    检查多组盲孔是否保留；源码会把面积小于阈值且被上层完全覆盖的孔从传播轮廓中
    扣除，从而保护孔形。3MF 使用含 2/3/4 mm 盲孔的实体，使面积跨越测试阈值。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_make_overhang_printable_hole_size(gcode_path, expected_make_overhang_printable_hole_size)
    assert ok, f"make_overhang_printable_hole_size expected {expected_make_overhang_printable_hole_size}, actual {actual}, details: {details}"


# ================== overhang_optimization ==================
@pytest.mark.engine_params
def test_overhang_optimization(slice_and_export: Path, expected_overhang_optimization: bool):
    """验证悬垂优化产生自适应层高和线宽。

    C3DSlicer 在 ``PrintObjectSlice.cpp`` 中为该开关调用 ``layer_height_overhang`` 和
    ``layer_width_profile_adaptive``；规划统计实际 ``;HEIGHT`` 与外墙 ``;WIDTH`` 的变化范围。
    3MF 使用两级阶梯悬垂并关闭支撑；Organic support 与该功能在引擎中是不兼容组合。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_overhang_optimization(gcode_path, expected_overhang_optimization)
    assert ok, f"overhang_optimization expected {expected_overhang_optimization}, actual {actual}, details: {details}"
