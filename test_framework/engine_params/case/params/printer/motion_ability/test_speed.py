"""Test speed limitation group parameters for motion_ability page"""

import pytest
from pathlib import Path
from engine_params.src.gcode.printer.motion_ability.speed_check import (
    parse_machine_max_speed_x,
    parse_machine_max_speed_y,
    parse_machine_max_speed_z,
    parse_machine_max_speed_e,
)


@pytest.mark.engine_params
def test_machine_max_speed_x(
    slice_and_export: Path,
    expected_value: int,
):
    """Test machine_max_speed_x (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_machine_max_speed_x(gcode_path, expected_value)
    
    assert ok, (
        f"machine_max_speed_x validation failed. "
        f"Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )


@pytest.mark.engine_params
def test_machine_max_speed_y(
    slice_and_export: Path,
    expected_value: int,
):
    """Test machine_max_speed_y (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_machine_max_speed_y(gcode_path, expected_value)
    
    assert ok, (
        f"machine_max_speed_y validation failed. "
        f"Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )


@pytest.mark.engine_params
def test_machine_max_speed_z(
    slice_and_export: Path,
    expected_value: int,
):
    """Test machine_max_speed_z (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_machine_max_speed_z(gcode_path, expected_value)
    
    assert ok, (
        f"machine_max_speed_z validation failed. "
        f"Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )


@pytest.mark.engine_params
def test_machine_max_speed_e(
    slice_and_export: Path,
    expected_value: int,
):
    """Test machine_max_speed_e (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_machine_max_speed_e(gcode_path, expected_value)
    
    assert ok, (
        f"machine_max_speed_e validation failed. "
        f"Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )
