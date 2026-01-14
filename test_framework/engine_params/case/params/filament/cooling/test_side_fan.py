import pytest
from pathlib import Path
from engine_params.src.gcode.filament.cooling.side_fan_check import (
    parse_additional_cooling_fan_speed,
    parse_enable_special_area_additional_cooling_fan,
    parse_cool_special_cds_fan_speed,
    parse_cool_cds_fan_start_at_height,
)

def test_additional_cooling_fan_speed(slice_and_export: Path, expected_value: str):
    """Test additional_cooling_fan_speed parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_additional_cooling_fan_speed(gcode_path, expected_value)
    assert ok, f"additional_cooling_fan_speed expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params

def test_enable_special_area_additional_cooling_fan(slice_and_export: Path, expected_value: str):
    """Test enable_special_area_additional_cooling_fan parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_enable_special_area_additional_cooling_fan(gcode_path, expected_value)
    assert ok, f"enable_special_area_additional_cooling_fan expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params

def test_cool_special_cds_fan_speed(slice_and_export: Path, expected_value: str):
    """Test cool_special_cds_fan_speed parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_cool_special_cds_fan_speed(gcode_path, expected_value)
    assert ok, f"cool_special_cds_fan_speed expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params

def test_cool_cds_fan_start_at_height(slice_and_export: Path, expected_value: str):
    """Test cool_cds_fan_start_at_height parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_cool_cds_fan_start_at_height(gcode_path, expected_value)
    assert ok, f"cool_cds_fan_start_at_height expected {expected_value}, got {actual}: {details}"



