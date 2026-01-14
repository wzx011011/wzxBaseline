"""
Test cases for Volumetric Speed parameters (Filament Page 1, Group 5).
浣撶Н閫熷害鍒嗙粍娴嬭瘯鐢ㄤ緥

鏍规嵁 filament_parameters_validation.md 2.1.5 Volumetric speed limitation 鍒嗙粍
鍖呭惈1涓弬鏁扮殑娴嬭瘯鐢ㄤ緥
"""

import pytest
from pathlib import Path


@pytest.mark.engine_params
def test_filament_max_volumetric_speed(slice_and_export: Path, expected_value: str):
    """Test filament_max_volumetric_speed parameter (Level 2 - Feature)"""
    from engine_params.src.gcode.filament.filament.volumetric_speed_check import parse_filament_max_volumetric_speed
    
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    result = parse_filament_max_volumetric_speed(gcode_content)
    
    if result["found"]:
        expected_float = float(expected_value)
        assert result["value"] == expected_float, \
            f"filament_max_volumetric_speed expected {expected_float}, got {result['value']}: {result['errors']}"
        assert result["validation"], f"filament_max_volumetric_speed validation failed: {result['errors']}"

