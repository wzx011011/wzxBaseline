"""
Test cases for Bed Temperature parameters (Filament Page 1, Group 4).
搴婇潰娓╁害鍒嗙粍娴嬭瘯鐢ㄤ緥

鏍规嵁 filament_parameters_validation.md 2.1.4 Bed temperature 鍒嗙粍
鍖呭惈12涓弬鏁扮殑娴嬭瘯鐢ㄤ緥锛?绉嶅簥闈㈢被鍨?脳 2绉嶆俯搴︼級
"""

import pytest
from pathlib import Path


@pytest.mark.engine_params
def test_cool_plate_temp_initial_layer(slice_and_export: Path, expected_value: str):
    """Test cool_plate_temp_initial_layer parameter (Level 1 - Config)"""
    from engine_params.src.gcode.filament.filament.bed_temperature_check import parse_cool_plate_temp_initial_layer
    
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    result = parse_cool_plate_temp_initial_layer(gcode_content)
    
    if result["found"]:
        expected_int = int(expected_value)
        assert result["value"] == expected_int, \
            f"cool_plate_temp_initial_layer expected {expected_int}, got {result['value']}: {result['errors']}"
        assert result["validation"], f"cool_plate_temp_initial_layer validation failed: {result['errors']}"


@pytest.mark.engine_params
def test_cool_plate_temp(slice_and_export: Path, expected_value: str):
    """Test cool_plate_temp parameter (Level 1 - Config)"""
    from engine_params.src.gcode.filament.filament.bed_temperature_check import parse_cool_plate_temp
    
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    result = parse_cool_plate_temp(gcode_content)
    
    if result["found"]:
        expected_int = int(expected_value)
        assert result["value"] == expected_int, \
            f"cool_plate_temp expected {expected_int}, got {result['value']}: {result['errors']}"
        assert result["validation"], f"cool_plate_temp validation failed: {result['errors']}"


@pytest.mark.engine_params
def test_eng_plate_temp_initial_layer(slice_and_export: Path, expected_value: str):
    """Test eng_plate_temp_initial_layer parameter (Level 1 - Config)"""
    from engine_params.src.gcode.filament.filament.bed_temperature_check import parse_eng_plate_temp_initial_layer
    
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    result = parse_eng_plate_temp_initial_layer(gcode_content)
    
    if result["found"]:
        expected_int = int(expected_value)
        assert result["value"] == expected_int, \
            f"eng_plate_temp_initial_layer expected {expected_int}, got {result['value']}: {result['errors']}"
        assert result["validation"], f"eng_plate_temp_initial_layer validation failed: {result['errors']}"


@pytest.mark.engine_params
def test_eng_plate_temp(slice_and_export: Path, expected_value: str):
    """Test eng_plate_temp parameter (Level 1 - Config)"""
    from engine_params.src.gcode.filament.filament.bed_temperature_check import parse_eng_plate_temp
    
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    result = parse_eng_plate_temp(gcode_content)
    
    if result["found"]:
        expected_int = int(expected_value)
        assert result["value"] == expected_int, \
            f"eng_plate_temp expected {expected_int}, got {result['value']}: {result['errors']}"
        assert result["validation"], f"eng_plate_temp validation failed: {result['errors']}"


@pytest.mark.engine_params
def test_hot_plate_temp_initial_layer(slice_and_export: Path, expected_value: str):
    """Test hot_plate_temp_initial_layer parameter (Level 1 - Config)"""
    from engine_params.src.gcode.filament.filament.bed_temperature_check import parse_hot_plate_temp_initial_layer
    
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    result = parse_hot_plate_temp_initial_layer(gcode_content)
    
    if result["found"]:
        expected_int = int(expected_value)
        assert result["value"] == expected_int, \
            f"hot_plate_temp_initial_layer expected {expected_int}, got {result['value']}: {result['errors']}"
        assert result["validation"], f"hot_plate_temp_initial_layer validation failed: {result['errors']}"


@pytest.mark.engine_params
def test_hot_plate_temp(slice_and_export: Path, expected_value: str):
    """Test hot_plate_temp parameter (Level 1 - Config)"""
    from engine_params.src.gcode.filament.filament.bed_temperature_check import parse_hot_plate_temp
    
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    result = parse_hot_plate_temp(gcode_content)
    
    if result["found"]:
        expected_int = int(expected_value)
        assert result["value"] == expected_int, \
            f"hot_plate_temp expected {expected_int}, got {result['value']}: {result['errors']}"
        assert result["validation"], f"hot_plate_temp validation failed: {result['errors']}"


@pytest.mark.engine_params
def test_textured_plate_temp_initial_layer(slice_and_export: Path, expected_value: str):
    """Test textured_plate_temp_initial_layer parameter (Level 1 - Config)"""
    from engine_params.src.gcode.filament.filament.bed_temperature_check import parse_textured_plate_temp_initial_layer
    
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    result = parse_textured_plate_temp_initial_layer(gcode_content)
    
    if result["found"]:
        expected_int = int(expected_value)
        assert result["value"] == expected_int, \
            f"textured_plate_temp_initial_layer expected {expected_int}, got {result['value']}: {result['errors']}"
        assert result["validation"], f"textured_plate_temp_initial_layer validation failed: {result['errors']}"


@pytest.mark.engine_params
def test_textured_plate_temp(slice_and_export: Path, expected_value: str):
    """Test textured_plate_temp parameter (Level 1 - Config)"""
    from engine_params.src.gcode.filament.filament.bed_temperature_check import parse_textured_plate_temp
    
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    result = parse_textured_plate_temp(gcode_content)
    
    if result["found"]:
        expected_int = int(expected_value)
        assert result["value"] == expected_int, \
            f"textured_plate_temp expected {expected_int}, got {result['value']}: {result['errors']}"
        assert result["validation"], f"textured_plate_temp validation failed: {result['errors']}"


@pytest.mark.engine_params
def test_customized_plate_temp_initial_layer(slice_and_export: Path, expected_value: str):
    """Test customized_plate_temp_initial_layer parameter (Level 1 - Config)"""
    from engine_params.src.gcode.filament.filament.bed_temperature_check import parse_customized_plate_temp_initial_layer
    
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    result = parse_customized_plate_temp_initial_layer(gcode_content)
    
    if result["found"]:
        expected_int = int(expected_value)
        assert result["value"] == expected_int, \
            f"customized_plate_temp_initial_layer expected {expected_int}, got {result['value']}: {result['errors']}"
        assert result["validation"], f"customized_plate_temp_initial_layer validation failed: {result['errors']}"


@pytest.mark.engine_params
def test_customized_plate_temp(slice_and_export: Path, expected_value: str):
    """Test customized_plate_temp parameter (Level 1 - Config)"""
    from engine_params.src.gcode.filament.filament.bed_temperature_check import parse_customized_plate_temp
    
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    result = parse_customized_plate_temp(gcode_content)
    
    if result["found"]:
        expected_int = int(expected_value)
        assert result["value"] == expected_int, \
            f"customized_plate_temp expected {expected_int}, got {result['value']}: {result['errors']}"
        assert result["validation"], f"customized_plate_temp validation failed: {result['errors']}"


@pytest.mark.engine_params
def test_epoxy_resin_plate_temp_initial_layer(slice_and_export: Path, expected_value: str):
    """Test epoxy_resin_plate_temp_initial_layer parameter (Level 1 - Config)"""
    from engine_params.src.gcode.filament.filament.bed_temperature_check import parse_epoxy_resin_plate_temp_initial_layer
    
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    result = parse_epoxy_resin_plate_temp_initial_layer(gcode_content)
    
    if result["found"]:
        expected_int = int(expected_value)
        assert result["value"] == expected_int, \
            f"epoxy_resin_plate_temp_initial_layer expected {expected_int}, got {result['value']}: {result['errors']}"
        assert result["validation"], f"epoxy_resin_plate_temp_initial_layer validation failed: {result['errors']}"


@pytest.mark.engine_params
def test_epoxy_resin_plate_temp(slice_and_export: Path, expected_value: str):
    """Test epoxy_resin_plate_temp parameter (Level 1 - Config)"""
    from engine_params.src.gcode.filament.filament.bed_temperature_check import parse_epoxy_resin_plate_temp
    
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    result = parse_epoxy_resin_plate_temp(gcode_content)
    
    if result["found"]:
        expected_int = int(expected_value)
        assert result["value"] == expected_int, \
            f"epoxy_resin_plate_temp expected {expected_int}, got {result['value']}: {result['errors']}"
        assert result["validation"], f"epoxy_resin_plate_temp validation failed: {result['errors']}"

