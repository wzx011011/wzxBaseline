"""
Test cases for Advanced filament parameters.

Total: 3 test functions
"""

import pytest
from pathlib import Path
from engine_params.src.gcode.filament.advanced import (
    parse_filament_start_gcode,
    parse_filament_end_gcode,
    parse_filament_notes,
)


@pytest.mark.engine_params
def test_filament_start_gcode(slice_and_export: Path, expected_value: str):
    """Test filament_start_gcode parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_start_gcode(gcode_path, expected_value)
    assert ok, f"filament_start_gcode expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_filament_end_gcode(slice_and_export: Path, expected_value: str):
    """Test filament_end_gcode parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_end_gcode(gcode_path, expected_value)
    assert ok, f"filament_end_gcode expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_filament_notes(slice_and_export: Path, expected_value: str):
    """Test filament_notes parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_notes(gcode_path, expected_value)
    assert ok, f"filament_notes expected {expected_value}, got {actual}: {details}"
