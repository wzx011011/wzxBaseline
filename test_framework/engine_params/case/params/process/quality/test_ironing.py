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
    """测试 ironing_type 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_ironing_type(gcode_path, expected_ironing_type)
    assert ok, f"ironing_type expected {expected_ironing_type}, actual {actual}, details: {details}"


# ================== ironing_pattern ==================
@pytest.mark.engine_params
def test_ironing_pattern(slice_and_export: Path, expected_ironing_pattern: str):
    """测试 ironing_pattern 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_ironing_pattern(gcode_path, expected_ironing_pattern)
    assert ok, f"ironing_pattern expected {expected_ironing_pattern}, actual {actual}, details: {details}"


# ================== ironing_flow ==================
@pytest.mark.engine_params
def test_ironing_flow(slice_and_export: Path, expected_ironing_flow: str):
    """测试 ironing_flow 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_ironing_flow(gcode_path, expected_ironing_flow)
    assert ok, f"ironing_flow expected {expected_ironing_flow}, actual {actual}, details: {details}"


# ================== ironing_spacing ==================
@pytest.mark.engine_params
def test_ironing_spacing(slice_and_export: Path, expected_ironing_spacing: float):
    """测试 ironing_spacing 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_ironing_spacing(gcode_path, expected_ironing_spacing)
    assert ok, f"ironing_spacing expected {expected_ironing_spacing}, actual {actual}, details: {details}"


# ================== ironing_speed ==================
@pytest.mark.engine_params
def test_ironing_speed(slice_and_export: Path, expected_ironing_speed: float):
    """测试 ironing_speed 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_ironing_speed(gcode_path, expected_ironing_speed)
    assert ok, f"ironing_speed expected {expected_ironing_speed}, actual {actual}, details: {details}"


# ================== ironing_angle ==================
@pytest.mark.engine_params
def test_ironing_angle(slice_and_export: Path, expected_ironing_angle: float):
    """测试 ironing_angle 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_ironing_angle(gcode_path, expected_ironing_angle)
    assert ok, f"ironing_angle expected {expected_ironing_angle}, actual {actual}, details: {details}"
