import pytest
from pathlib import Path
from engine_params.src.gcode.filament.cooling.back_fan_check import (
    parse_activate_air_filtration,
    parse_during_print_exhaust_fan_speed,
    parse_complete_print_exhaust_fan_speed,
)

def test_activate_air_filtration(slice_and_export: Path, expected_value: str):
    """Test activate_air_filtration parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_activate_air_filtration(gcode_path, expected_value)
    assert ok, f"activate_air_filtration expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params

def test_during_print_exhaust_fan_speed(slice_and_export: Path, expected_value: str):
    """Test during_print_exhaust_fan_speed parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_during_print_exhaust_fan_speed(gcode_path, expected_value)
    assert ok, f"during_print_exhaust_fan_speed expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params

def test_complete_print_exhaust_fan_speed(slice_and_export: Path, expected_value: str):
    """Test complete_print_exhaust_fan_speed parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_complete_print_exhaust_fan_speed(gcode_path, expected_value)
    assert ok, f"complete_print_exhaust_fan_speed expected {expected_value}, got {actual}: {details}"


