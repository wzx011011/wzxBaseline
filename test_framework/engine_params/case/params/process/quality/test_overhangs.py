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
    """测试 extra_perimeters_on_overhangs 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_extra_perimeters_on_overhangs(gcode_path, expected_extra_perimeters_on_overhangs)
    assert ok, f"extra_perimeters_on_overhangs expected {expected_extra_perimeters_on_overhangs}, actual {actual}, details: {details}"


# ================== make_overhang_printable ==================
@pytest.mark.engine_params
def test_make_overhang_printable(slice_and_export: Path, expected_make_overhang_printable: bool):
    """测试 make_overhang_printable 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_make_overhang_printable(gcode_path, expected_make_overhang_printable)
    assert ok, f"make_overhang_printable expected {expected_make_overhang_printable}, actual {actual}, details: {details}"


# ================== make_overhang_printable_angle ==================
@pytest.mark.engine_params
def test_make_overhang_printable_angle(slice_and_export: Path, expected_make_overhang_printable_angle: float):
    """测试 make_overhang_printable_angle 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_make_overhang_printable_angle(gcode_path, expected_make_overhang_printable_angle)
    assert ok, f"make_overhang_printable_angle expected {expected_make_overhang_printable_angle}, actual {actual}, details: {details}"


# ================== make_overhang_printable_hole_size ==================
@pytest.mark.engine_params
def test_make_overhang_printable_hole_size(slice_and_export: Path, expected_make_overhang_printable_hole_size: float):
    """测试 make_overhang_printable_hole_size 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_make_overhang_printable_hole_size(gcode_path, expected_make_overhang_printable_hole_size)
    assert ok, f"make_overhang_printable_hole_size expected {expected_make_overhang_printable_hole_size}, actual {actual}, details: {details}"


# ================== overhang_optimization ==================
@pytest.mark.engine_params
def test_overhang_optimization(slice_and_export: Path, expected_overhang_optimization: bool):
    """测试 overhang_optimization 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_overhang_optimization(gcode_path, expected_overhang_optimization)
    assert ok, f"overhang_optimization expected {expected_overhang_optimization}, actual {actual}, details: {details}"
