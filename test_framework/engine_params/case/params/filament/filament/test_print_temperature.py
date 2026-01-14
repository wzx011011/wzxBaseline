"""
Test cases for Print Temperature parameters (Filament Page 1, Group 3).
鎵撳嵃娓╁害鍒嗙粍娴嬭瘯鐢ㄤ緥

鏍规嵁 filament_parameters_validation.md 2.1.3 Print temperature 鍒嗙粍
鍖呭惈4涓弬鏁扮殑娴嬭瘯鐢ㄤ緥
"""

import pytest
from pathlib import Path


@pytest.mark.engine_params
def test_nozzle_temperature_initial_layer(slice_and_export: Path, expected_value: str):
    """Test nozzle_temperature_initial_layer parameter (Level 1 - Config)"""
    from engine_params.src.gcode.filament.filament.print_temperature_check import parse_nozzle_temperature_initial_layer
    
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    result = parse_nozzle_temperature_initial_layer(gcode_content)
    
    if result["found"]:
        expected_float = float(expected_value)
        assert result["value"] == expected_float, \
            f"nozzle_temperature_initial_layer expected {expected_float}, got {result['value']}: {result['errors']}"
        assert result["validation"], f"nozzle_temperature_initial_layer validation failed: {result['errors']}"


@pytest.mark.engine_params
def test_nozzle_temperature(slice_and_export: Path, expected_value: str):
    """Test nozzle_temperature parameter (Level 1 - Config)"""
    from engine_params.src.gcode.filament.filament.print_temperature_check import parse_nozzle_temperature
    
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    result = parse_nozzle_temperature(gcode_content)
    
    if result["found"]:
        expected_float = float(expected_value)
        assert result["value"] == expected_float, \
            f"nozzle_temperature expected {expected_float}, got {result['value']}: {result['errors']}"
        assert result["validation"], f"nozzle_temperature validation failed: {result['errors']}"


@pytest.mark.engine_params
def test_material_flow_dependent_temperature(slice_and_export: Path, expected_value: str):
    """Test material_flow_dependent_temperature parameter (Level 2 - Feature)"""
    from engine_params.src.gcode.filament.filament.print_temperature_check import parse_material_flow_dependent_temperature
    
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    result = parse_material_flow_dependent_temperature(gcode_content)
    
    if result["found"]:
        expected_bool = expected_value.lower() in ['true', '1']
        assert result["value"] == expected_bool, \
            f"material_flow_dependent_temperature expected {expected_bool}, got {result['value']}: {result['errors']}"
        assert result["validation"], f"material_flow_dependent_temperature validation failed: {result['errors']}"


@pytest.mark.engine_params
def test_material_flow_temp_graph(slice_and_export: Path, expected_value: str):
    """Test material_flow_temp_graph parameter (Level 3 - Path)"""
    from engine_params.src.gcode.filament.filament.print_temperature_check import parse_material_flow_temp_graph
    
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    result = parse_material_flow_temp_graph(gcode_content)
    
    if result["found"]:
        assert str(result["value"]) == expected_value, \
            f"material_flow_temp_graph expected {expected_value}, got {result['value']}: {result['errors']}"
        assert result["validation"], f"material_flow_temp_graph validation failed: {result['errors']}"

