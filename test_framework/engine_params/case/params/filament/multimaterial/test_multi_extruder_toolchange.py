import pytest
from pathlib import Path
from engine_params.src.gcode.filament.multimaterial.multi_extruder_toolchange_check import (
    parse_filament_multitool_ramming,
    parse_filament_multitool_ramming_volume,
    parse_filament_multitool_ramming_flow,
)

def test_filament_multitool_ramming(slice_and_export: Path, expected_value: str):
    """Test filament_multitool_ramming parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_multitool_ramming(gcode_path, expected_value)
    assert ok, f"filament_multitool_ramming expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params

def test_filament_multitool_ramming_volume(slice_and_export: Path, expected_value: str):
    """Test filament_multitool_ramming_volume parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_multitool_ramming_volume(gcode_path, expected_value)
    assert ok, f"filament_multitool_ramming_volume expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params

def test_filament_multitool_ramming_flow(slice_and_export: Path, expected_value: str):
    """Test filament_multitool_ramming_flow parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_multitool_ramming_flow(gcode_path, expected_value)
    assert ok, f"filament_multitool_ramming_flow expected {expected_value}, got {actual}: {details}"


