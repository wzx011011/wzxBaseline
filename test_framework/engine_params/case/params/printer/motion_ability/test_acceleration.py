"""Test acceleration limitation group parameters for motion_ability page"""

import pytest
from pathlib import Path
from engine_params.src.gcode.printer.motion_ability.acceleration_check import (
    parse_machine_max_acceleration_x,
    parse_machine_max_acceleration_y,
    parse_machine_max_acceleration_z,
    parse_machine_max_acceleration_e,
    parse_machine_max_acceleration_extruding,
    parse_machine_max_acceleration_retracting,
    parse_machine_max_acceleration_travel,
)


@pytest.mark.engine_params
def test_machine_max_acceleration_x(
    slice_and_export: Path,
    expected_value: int,
):
    """Test machine_max_acceleration_x (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_machine_max_acceleration_x(gcode_path, expected_value)
    
    assert ok, (
        f"machine_max_acceleration_x validation failed. "
        f"Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )


@pytest.mark.engine_params
def test_machine_max_acceleration_y(
    slice_and_export: Path,
    expected_value: int,
):
    """Test machine_max_acceleration_y (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_machine_max_acceleration_y(gcode_path, expected_value)
    
    assert ok, (
        f"machine_max_acceleration_y validation failed. "
        f"Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )


@pytest.mark.engine_params
def test_machine_max_acceleration_z(
    slice_and_export: Path,
    expected_value: int,
):
    """Test machine_max_acceleration_z (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_machine_max_acceleration_z(gcode_path, expected_value)
    
    assert ok, (
        f"machine_max_acceleration_z validation failed. "
        f"Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )


@pytest.mark.engine_params
def test_machine_max_acceleration_e(
    slice_and_export: Path,
    expected_value: int,
):
    """Test machine_max_acceleration_e (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_machine_max_acceleration_e(gcode_path, expected_value)
    
    assert ok, (
        f"machine_max_acceleration_e validation failed. "
        f"Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )


@pytest.mark.engine_params
def test_machine_max_acceleration_extruding(
    slice_and_export: Path,
    expected_value: int,
):
    """Test machine_max_acceleration_extruding (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_machine_max_acceleration_extruding(gcode_path, expected_value)
    
    assert ok, (
        f"machine_max_acceleration_extruding validation failed. "
        f"Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )


@pytest.mark.engine_params
def test_machine_max_acceleration_retracting(
    slice_and_export: Path,
    expected_value: int,
):
    """Test machine_max_acceleration_retracting (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_machine_max_acceleration_retracting(gcode_path, expected_value)
    
    assert ok, (
        f"machine_max_acceleration_retracting validation failed. "
        f"Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )


@pytest.mark.engine_params
def test_machine_max_acceleration_travel(
    slice_and_export: Path,
    expected_value: int,
):
    """Test machine_max_acceleration_travel (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_machine_max_acceleration_travel(gcode_path, expected_value)
    
    assert ok, (
        f"machine_max_acceleration_travel validation failed. "
        f"Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )
