"""
Test cases for Chamber Temperature parameters (Filament Page 1, Group 2).
鑵斿娓╁害鍒嗙粍娴嬭瘯鐢ㄤ緥

鏍规嵁 filament_parameters_validation.md 2.1.2 Print chamber temperature 鍒嗙粍
鍖呭惈3涓弬鏁扮殑娴嬭瘯鐢ㄤ緥
"""

import pytest
from pathlib import Path


@pytest.mark.engine_params
def test_chamber_temperature(slice_and_export: Path, expected_value: str):
    """Test chamber_temperature parameter (Level 1 - Config)"""
    from engine_params.src.gcode.filament.filament.chamber_temperature_check import parse_chamber_temperature
    
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    result = parse_chamber_temperature(gcode_content)
    
    if result["found"]:
        expected_float = float(expected_value)
        assert result["value"] == expected_float, \
            f"chamber_temperature expected {expected_float}, got {result['value']}: {result['errors']}"
        assert result["validation"], f"chamber_temperature validation failed: {result['errors']}"


@pytest.mark.engine_params
def test_activate_chamber_temp_control(slice_and_export: Path, expected_value: str):
    """Test activate_chamber_temp_control parameter (Level 1 - Config)"""
    from engine_params.src.gcode.filament.filament.chamber_temperature_check import parse_activate_chamber_temp_control
    
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    result = parse_activate_chamber_temp_control(gcode_content)
    
    if result["found"]:
        expected_bool = expected_value.lower() in ['true', '1']
        assert result["value"] == expected_bool, \
            f"activate_chamber_temp_control expected {expected_bool}, got {result['value']}: {result['errors']}"
        assert result["validation"], f"activate_chamber_temp_control validation failed: {result['errors']}"


@pytest.mark.engine_params
def test_activate_chamber_layer(slice_and_export: Path, expected_value: str):
    """Test activate_chamber_layer parameter (Level 1 - Config)"""
    from engine_params.src.gcode.filament.filament.chamber_temperature_check import parse_activate_chamber_layer
    
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    result = parse_activate_chamber_layer(gcode_content)
    
    if result["found"]:
        expected_int = int(expected_value)
        assert result["value"] == expected_int, \
            f"activate_chamber_layer expected {expected_int}, got {result['value']}: {result['errors']}"
        assert result["validation"], f"activate_chamber_layer validation failed: {result['errors']}"

