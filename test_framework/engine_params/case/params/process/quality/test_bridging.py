from __future__ import annotations

from pathlib import Path

import pytest

from engine_params.src.gcode.process.quality.bridging_check import (
    parse_internal_bridge_flow,
    parse_bridge_angle,
    parse_bridge_flow,
    parse_bridge_density,
    parse_bridge_speed,
    parse_thick_bridges,
    parse_dont_filter_internal_bridges,
    parse_thick_internal_bridges,
    parse_internal_bridge_speed,
    parse_counterbore_hole_bridging,
)


# ================== internal_bridge_flow ==================
@pytest.mark.engine_params
def test_internal_bridge_flow(
    slice_and_export: Path,
    expected_ratio: float,
    baseline_gcode: str | Path,
    tol: float,
):
    gcode_path: Path = slice_and_export
    baseline_path = Path(baseline_gcode)
    assert gcode_path.exists()
    assert baseline_path.exists()

    ok, ratio, details = parse_internal_bridge_flow(
        tested_gcode=gcode_path,
        baseline_gcode=baseline_path,
        expected_ratio=expected_ratio,
        tol=tol,
    )

    assert ok, (
        f"internal_bridge_flow expected {expected_ratio}, actual {ratio}, details: {details}"
    )


# ================== bridge_angle ==================
@pytest.mark.engine_params
def test_bridge_angle(slice_and_export: Path, expected_bridge_angle: float):
    """测试 bridge_angle 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_bridge_angle(gcode_path, expected_bridge_angle)
    assert ok, f"bridge_angle expected {expected_bridge_angle}, actual {actual}, details: {details}"


# ================== bridge_flow ==================
@pytest.mark.engine_params
def test_bridge_flow(slice_and_export: Path, expected_bridge_flow: float):
    """测试 bridge_flow 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_bridge_flow(gcode_path, expected_bridge_flow)
    assert ok, f"bridge_flow expected {expected_bridge_flow}, actual {actual}, details: {details}"


# ================== bridge_density ==================
@pytest.mark.engine_params
def test_bridge_density(slice_and_export: Path, expected_bridge_density: float):
    """测试 bridge_density 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_bridge_density(gcode_path, expected_bridge_density)
    assert ok, f"bridge_density expected {expected_bridge_density}, actual {actual}, details: {details}"


# ================== bridge_speed ==================
@pytest.mark.engine_params
def test_bridge_speed(slice_and_export: Path, expected_bridge_speed: float):
    """测试 bridge_speed 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_bridge_speed(gcode_path, expected_bridge_speed)
    assert ok, f"bridge_speed expected {expected_bridge_speed}, actual {actual}, details: {details}"


# ================== thick_bridges ==================
@pytest.mark.engine_params
def test_thick_bridges(slice_and_export: Path, expected_thick_bridges: bool):
    """测试 thick_bridges 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_thick_bridges(gcode_path, expected_thick_bridges)
    assert ok, f"thick_bridges expected {expected_thick_bridges}, actual {actual}, details: {details}"


# ================== dont_filter_internal_bridges ==================
@pytest.mark.engine_params
def test_dont_filter_internal_bridges(slice_and_export: Path, expected_dont_filter_internal_bridges: str):
    """测试 dont_filter_internal_bridges 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_dont_filter_internal_bridges(gcode_path, expected_dont_filter_internal_bridges)
    assert ok, f"dont_filter_internal_bridges expected {expected_dont_filter_internal_bridges}, actual {actual}, details: {details}"


# ================== thick_internal_bridges ==================
@pytest.mark.engine_params
def test_thick_internal_bridges(slice_and_export: Path, expected_thick_internal_bridges: bool):
    """测试 thick_internal_bridges 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_thick_internal_bridges(gcode_path, expected_thick_internal_bridges)
    assert ok, f"thick_internal_bridges expected {expected_thick_internal_bridges}, actual {actual}, details: {details}"


# ================== internal_bridge_speed ==================
@pytest.mark.engine_params
def test_internal_bridge_speed(slice_and_export: Path, expected_internal_bridge_speed: str):
    """测试 internal_bridge_speed 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_internal_bridge_speed(gcode_path, expected_internal_bridge_speed)
    assert ok, f"internal_bridge_speed expected {expected_internal_bridge_speed}, actual {actual}, details: {details}"


# ================== counterbore_hole_bridging ==================
@pytest.mark.engine_params
def test_counterbore_hole_bridging(slice_and_export: Path, expected_counterbore_hole_bridging: str):
    """测试 counterbore_hole_bridging 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_counterbore_hole_bridging(gcode_path, expected_counterbore_hole_bridging)
    assert ok, f"counterbore_hole_bridging expected {expected_counterbore_hole_bridging}, actual {actual}, details: {details}"
