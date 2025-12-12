import pytest
from pathlib import Path

from engine_params.src.gcode.printer.basic_information.basic_information_check import (
    parse_single_extruder_multi_material,
    parse_extruders_count,
    parse_manual_filament_change,
    parse_purge_in_prime_tower,
    parse_enable_filament_ramming,
    parse_prime_tower_position_type,
    parse_cooling_tube_retraction,
    parse_cooling_tube_length,
    parse_parking_pos_retraction,
    parse_extra_loading_move,
    parse_high_current_on_filament_swap,
)


@pytest.mark.engine_params
def test_single_extruder_multi_material(
    slice_and_export: Path,
    expected_value: str,
):
    """Test single_extruder_multi_material (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_single_extruder_multi_material(gcode_path, expected_value)
    
    assert ok, f"single_extruder_multi_material expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_extruders_count(
    slice_and_export: Path,
    expected_value: str,
):
    """Test extruders_count (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_extruders_count(gcode_path, expected_value)
    
    assert ok, f"extruders_count expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_manual_filament_change(
    slice_and_export: Path,
    expected_value: str,
):
    """Test manual_filament_change (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_manual_filament_change(gcode_path, expected_value)
    
    assert ok, f"manual_filament_change expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_purge_in_prime_tower(
    slice_and_export: Path,
    expected_value: str,
):
    """Test purge_in_prime_tower (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_purge_in_prime_tower(gcode_path, expected_value)
    
    assert ok, f"purge_in_prime_tower expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_enable_filament_ramming(
    slice_and_export: Path,
    expected_value: str,
):
    """Test enable_filament_ramming (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_enable_filament_ramming(gcode_path, expected_value)
    
    assert ok, f"enable_filament_ramming expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_prime_tower_position_type(
    slice_and_export: Path,
    expected_value: str,
):
    """Test prime_tower_position_type (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_prime_tower_position_type(gcode_path, expected_value)
    
    assert ok, f"prime_tower_position_type expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_cooling_tube_retraction(
    slice_and_export: Path,
    expected_value: str,
):
    """Test cooling_tube_retraction (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_cooling_tube_retraction(gcode_path, expected_value)
    
    assert ok, f"cooling_tube_retraction expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_cooling_tube_length(
    slice_and_export: Path,
    expected_value: str,
):
    """Test cooling_tube_length (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_cooling_tube_length(gcode_path, expected_value)
    
    assert ok, f"cooling_tube_length expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_parking_pos_retraction(
    slice_and_export: Path,
    expected_value: str,
):
    """Test parking_pos_retraction (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_parking_pos_retraction(gcode_path, expected_value)
    
    assert ok, f"parking_pos_retraction expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_extra_loading_move(
    slice_and_export: Path,
    expected_value: str,
):
    """Test extra_loading_move (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_extra_loading_move(gcode_path, expected_value)
    
    assert ok, f"extra_loading_move expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_high_current_on_filament_swap(
    slice_and_export: Path,
    expected_value: str,
):
    """Test high_current_on_filament_swap (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_high_current_on_filament_swap(gcode_path, expected_value)
    
    assert ok, f"high_current_on_filament_swap expected {expected_value}, got {actual}: {details}"
