import pytest
from pathlib import Path
from engine_params.src.gcode.filament.cooling.cooling_specific_layer_check import (
    parse_close_fan_the_first_x_layers,
    parse_full_fan_speed_layer,
)

def test_close_fan_the_first_x_layers(slice_and_export: Path, expected_value: str):
    """Test close_fan_the_first_x_layers parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_close_fan_the_first_x_layers(gcode_path, expected_value)
    assert ok, f"close_fan_the_first_x_layers expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params

def test_full_fan_speed_layer(slice_and_export: Path, expected_value: str):
    """Test full_fan_speed_layer parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_full_fan_speed_layer(gcode_path, expected_value)
    assert ok, f"full_fan_speed_layer expected {expected_value}, got {actual}: {details}"



