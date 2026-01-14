"""
Test cases for Basic Information parameters (Filament Page 1, Group 1).
鍩虹淇℃伅鍒嗙粍娴嬭瘯鐢ㄤ緥

鏍规嵁 filament_parameters_validation.md 2.1.1 Basic information 鍒嗙粍
鍖呭惈9涓叧閿弬鏁扮殑娴嬭瘯鐢ㄤ緥
"""

import pytest
from pathlib import Path


@pytest.mark.engine_params
def test_filament_type(slice_and_export: Path, expected_value: str):
    """Test filament_type parameter (Level 1 - Config)"""
    from engine_params.src.gcode.filament.filament.basic_information_check import parse_filament_type
    
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    result = parse_filament_type(gcode_content)
    
    if result["found"]:
        assert str(result["value"]) == expected_value, \
            f"filament_type expected {expected_value}, got {result['value']}: {result['errors']}"
        assert result["validation"], f"filament_type validation failed: {result['errors']}"


@pytest.mark.engine_params
def test_filament_diameter(slice_and_export: Path, expected_value: str):
    """Test filament_diameter parameter (Level 1 - Config)"""
    from engine_params.src.gcode.filament.filament.basic_information_check import parse_filament_diameter
    
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    result = parse_filament_diameter(gcode_content)
    
    if result["found"]:
        expected_float = float(expected_value)
        assert result["value"] == expected_float, \
            f"filament_diameter expected {expected_float}, got {result['value']}: {result['errors']}"
        assert result["validation"], f"filament_diameter validation failed: {result['errors']}"


@pytest.mark.engine_params
def test_filament_flow_ratio(slice_and_export: Path, expected_value: str):
    """Test filament_flow_ratio parameter (Level 1 - Config)"""
    from engine_params.src.gcode.filament.filament.basic_information_check import parse_filament_flow_ratio
    
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    result = parse_filament_flow_ratio(gcode_content)
    
    if result["found"]:
        expected_float = float(expected_value)
        assert result["value"] == expected_float, \
            f"filament_flow_ratio expected {expected_float}, got {result['value']}: {result['errors']}"
        assert result["validation"], f"filament_flow_ratio validation failed: {result['errors']}"


@pytest.mark.engine_params
def test_required_nozzle_hrc(slice_and_export: Path, expected_value: str):
    """Test required_nozzle_HRC parameter (Level 1 - Config)"""
    from engine_params.src.gcode.filament.filament.basic_information_check import parse_required_nozzle_hrc
    
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    result = parse_required_nozzle_hrc(gcode_content)
    
    if result["found"]:
        expected_int = int(expected_value)
        assert result["value"] == expected_int, \
            f"required_nozzle_HRC expected {expected_int}, got {result['value']}: {result['errors']}"
        assert result["validation"], f"required_nozzle_HRC validation failed: {result['errors']}"


@pytest.mark.engine_params
def test_filament_density(slice_and_export: Path, expected_value: str):
    """Test filament_density parameter (Level 1 - Config)"""
    from engine_params.src.gcode.filament.filament.basic_information_check import parse_filament_density
    
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    result = parse_filament_density(gcode_content)
    
    if result["found"]:
        expected_float = float(expected_value)
        assert result["value"] == expected_float, \
            f"filament_density expected {expected_float}, got {result['value']}: {result['errors']}"
        assert result["validation"], f"filament_density validation failed: {result['errors']}"


@pytest.mark.engine_params
def test_nozzle_temperature_range_low(slice_and_export: Path, expected_value: str):
    """Test nozzle_temperature_range_low parameter (Level 1 - Config)"""
    from engine_params.src.gcode.filament.filament.basic_information_check import parse_nozzle_temperature_range
    
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    result = parse_nozzle_temperature_range(gcode_content)
    
    if result["found"] and result["value"]["low"] is not None:
        expected_float = float(expected_value)
        assert result["value"]["low"] == expected_float, \
            f"nozzle_temperature_range_low expected {expected_float}, got {result['value']['low']}: {result['errors']}"
        assert result["validation"], f"nozzle_temperature_range_low validation failed: {result['errors']}"


@pytest.mark.engine_params
def test_nozzle_temperature_range_high(slice_and_export: Path, expected_value: str):
    """Test nozzle_temperature_range_high parameter (Level 1 - Config)"""
    from engine_params.src.gcode.filament.filament.basic_information_check import parse_nozzle_temperature_range
    
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    result = parse_nozzle_temperature_range(gcode_content)
    
    if result["found"] and result["value"]["high"] is not None:
        expected_float = float(expected_value)
        assert result["value"]["high"] == expected_float, \
            f"nozzle_temperature_range_high expected {expected_float}, got {result['value']['high']}: {result['errors']}"
        assert result["validation"], f"nozzle_temperature_range_high validation failed: {result['errors']}"


@pytest.mark.engine_params
def test_enable_pressure_advance(slice_and_export: Path, expected_value: str):
    """Test enable_pressure_advance parameter (Level 1 - Config)"""
    from engine_params.src.gcode.filament.filament.basic_information_check import parse_enable_pressure_advance
    
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    result = parse_enable_pressure_advance(gcode_content)
    
    if result["found"]:
        expected_bool = expected_value.lower() in ['true', '1']
        assert result["value"] == expected_bool, \
            f"enable_pressure_advance expected {expected_bool}, got {result['value']}: {result['errors']}"
        assert result["validation"], f"enable_pressure_advance validation failed: {result['errors']}"


@pytest.mark.engine_params
def test_filament_soluble(slice_and_export: Path, expected_value: str):
    """Test filament_soluble parameter (Level 1 - Config)"""
    from engine_params.src.gcode.filament.filament.basic_information_check import parse_filament_soluble
    
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    result = parse_filament_soluble(gcode_content)
    
    if result["found"]:
        expected_bool = expected_value.lower() in ['true', '1']
        assert result["value"] == expected_bool, \
            f"filament_soluble expected {expected_bool}, got {result['value']}: {result['errors']}"
        assert result["validation"], f"filament_soluble validation failed: {result['errors']}"


@pytest.mark.engine_params
def test_filament_vendor(slice_and_export: Path, expected_value: str):
    """Test filament_vendor parameter (Level 1 - Config)"""
    from engine_params.src.gcode.filament.filament.basic_information_check import parse_filament_vendor
    
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    result = parse_filament_vendor(gcode_content)
    
    if result["found"]:
        assert str(result["value"]) == expected_value, \
            f"filament_vendor expected {expected_value}, got {result['value']}: {result['errors']}"
        assert result["validation"], f"filament_vendor validation failed: {result['errors']}"


@pytest.mark.engine_params
def test_default_filament_colour(slice_and_export: Path, expected_value: str):
    """Test default_filament_colour parameter (Level 1 - Config)"""
    from engine_params.src.gcode.filament.filament.basic_information_check import parse_default_filament_colour
    
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    result = parse_default_filament_colour(gcode_content)
    
    if result["found"]:
        assert str(result["value"]) == expected_value, \
            f"default_filament_colour expected {expected_value}, got {result['value']}: {result['errors']}"
        assert result["validation"], f"default_filament_colour validation failed: {result['errors']}"


@pytest.mark.engine_params
def test_pressure_advance(slice_and_export: Path, expected_value: str):
    """Test pressure_advance parameter (Level 2 - Feature)"""
    from engine_params.src.gcode.filament.filament.basic_information_check import parse_pressure_advance
    
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    result = parse_pressure_advance(gcode_content)
    
    if result["found"]:
        expected_float = float(expected_value)
        assert result["value"] == expected_float, \
            f"pressure_advance expected {expected_float}, got {result['value']}: {result['errors']}"
        assert result["validation"], f"pressure_advance validation failed: {result['errors']}"


@pytest.mark.engine_params
def test_filament_cost(slice_and_export: Path, expected_value: str):
    """Test filament_cost parameter (Level 1 - Config)"""
    from engine_params.src.gcode.filament.filament.basic_information_check import parse_filament_cost
    
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    result = parse_filament_cost(gcode_content)
    
    if result["found"]:
        expected_float = float(expected_value)
        assert result["value"] == expected_float, \
            f"filament_cost expected {expected_float}, got {result['value']}: {result['errors']}"
        assert result["validation"], f"filament_cost validation failed: {result['errors']}"


@pytest.mark.engine_params
def test_filament_is_support(slice_and_export: Path, expected_value: str):
    """Test filament_is_support parameter (Level 1 - Config)"""
    from engine_params.src.gcode.filament.filament.basic_information_check import parse_filament_is_support
    
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    result = parse_filament_is_support(gcode_content)
    
    if result["found"]:
        expected_bool = expected_value.lower() in ['true', '1']
        assert result["value"] == expected_bool, \
            f"filament_is_support expected {expected_bool}, got {result['value']}: {result['errors']}"
        assert result["validation"], f"filament_is_support validation failed: {result['errors']}"


@pytest.mark.engine_params
def test_filament_adhesiveness_category(slice_and_export: Path, expected_value: str):
    """Test filament_adhesiveness_category parameter (Level 1 - Config)"""
    # 杩欐槸涓€涓灇涓剧被鍨嬪弬鏁帮紝鏆傛椂鐢ㄥ瓧绗︿覆鍖归厤
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    import re
    pattern = r';.*filament_adhesiveness_category\s*=\s*([^\n;]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        actual_value = matches[0].strip('"\'')
        assert actual_value == expected_value, \
            f"filament_adhesiveness_category expected {expected_value}, got {actual_value}"


@pytest.mark.engine_params
def test_filament_shrink(slice_and_export: Path, expected_value: str):
    """Test filament_shrink parameter (Level 2 - Feature)"""
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    import re
    pattern = r';.*filament_shrink\s*=\s*([0-9.-]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        actual_float = float(matches[0])
        # 澶勭悊鐧惧垎姣旀牸寮忕殑鏈熸湜鍊?
        if expected_value.endswith('%'):
            expected_float = float(expected_value[:-1])
        else:
            expected_float = float(expected_value)
        assert actual_float == expected_float, \
            f"filament_shrink expected {expected_float}, got {actual_float}"
        
        # 鏍￠獙鑼冨洿 0.0 鍒?110.0 (鐧惧垎姣?
        assert 0.0 <= actual_float <= 110.0, \
            f"filament_shrink {actual_float} out of range (0.0 to 110.0)"


@pytest.mark.engine_params
def test_filament_shrinkage_compensation_z(slice_and_export: Path, expected_value: str):
    """Test filament_shrinkage_compensation_z parameter (Level 2 - Feature)"""
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    import re
    pattern = r';.*filament_shrinkage_compensation_z\s*=\s*([0-9.-]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        actual_float = float(matches[0])
        # 澶勭悊鐧惧垎姣旀牸寮忕殑鏈熸湜鍊?
        if expected_value.endswith('%'):
            expected_float = float(expected_value[:-1])
        else:
            expected_float = float(expected_value)
        assert actual_float == expected_float, \
            f"filament_shrinkage_compensation_z expected {expected_float}, got {actual_float}"
        
        # 鏍￠獙鑼冨洿 0.0 鍒?110.0 (鐧惧垎姣?
        assert 0.0 <= actual_float <= 110.0, \
            f"filament_shrinkage_compensation_z {actual_float} out of range (0.0 to 110.0)"


@pytest.mark.engine_params
def test_temperature_vitrification(slice_and_export: Path, expected_value: str):
    """Test temperature_vitrification parameter (Level 2 - Feature)"""
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    import re
    pattern = r';.*temperature_vitrification\s*=\s*([0-9.]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        actual_float = float(matches[0])
        expected_float = float(expected_value)
        assert actual_float == expected_float, \
            f"temperature_vitrification expected {expected_float}, got {actual_float}"
        
        # 鏍￠獙鑼冨洿 0.0-300.0
        assert 0.0 <= actual_float <= 300.0, \
            f"temperature_vitrification {actual_float} out of range (0.0-300.0掳C)"


@pytest.mark.engine_params
def test_idle_temperature(slice_and_export: Path, expected_value: str):
    """Test idle_temperature parameter (Level 2 - Feature)"""
    gcode_path = slice_and_export
    with open(gcode_path, 'r', encoding='utf-8') as f:
        gcode_content = f.read()
    
    import re
    pattern = r';.*idle_temperature\s*=\s*([0-9.]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        actual_float = float(matches[0])
        expected_float = float(expected_value)
        assert actual_float == expected_float, \
            f"idle_temperature expected {expected_float}, got {actual_float}"
        
        # 鏍￠獙鑼冨洿 0.0-300.0
        assert 0.0 <= actual_float <= 300.0, \
            f"idle_temperature {actual_float} out of range (0.0-300.0掳C)"

