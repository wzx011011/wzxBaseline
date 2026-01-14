import pytest
from pathlib import Path
from engine_params.src.gcode.filament.multimaterial.single_extruder_toolchange_check import (
    parse_filament_loading_speed_start,
    parse_filament_loading_speed,
    parse_filament_unloading_speed_start,
    parse_filament_unloading_speed,
    parse_filament_toolchange_delay,
    parse_filament_cooling_moves,
    parse_filament_cooling_initial_speed,
    parse_filament_cooling_final_speed,
    parse_filament_stamping_loading_speed,
    parse_filament_stamping_distance,
)

def test_filament_loading_speed_start(slice_and_export: Path, expected_value: str):
    """Test filament_loading_speed_start parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_loading_speed_start(gcode_path, expected_value)
    assert ok, f"filament_loading_speed_start expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params

def test_filament_loading_speed(slice_and_export: Path, expected_value: str):
    """Test filament_loading_speed parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_loading_speed(gcode_path, expected_value)
    assert ok, f"filament_loading_speed expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params

def test_filament_unloading_speed_start(slice_and_export: Path, expected_value: str):
    """Test filament_unloading_speed_start parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_unloading_speed_start(gcode_path, expected_value)
    assert ok, f"filament_unloading_speed_start expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params

def test_filament_unloading_speed(slice_and_export: Path, expected_value: str):
    """Test filament_unloading_speed parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_unloading_speed(gcode_path, expected_value)
    assert ok, f"filament_unloading_speed expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params

def test_filament_toolchange_delay(slice_and_export: Path, expected_value: str):
    """Test filament_toolchange_delay parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_toolchange_delay(gcode_path, expected_value)
    assert ok, f"filament_toolchange_delay expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params

def test_filament_cooling_moves(slice_and_export: Path, expected_value: str):
    """Test filament_cooling_moves parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_cooling_moves(gcode_path, expected_value)
    assert ok, f"filament_cooling_moves expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params

def test_filament_cooling_initial_speed(slice_and_export: Path, expected_value: str):
    """Test filament_cooling_initial_speed parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_cooling_initial_speed(gcode_path, expected_value)
    assert ok, f"filament_cooling_initial_speed expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params

def test_filament_cooling_final_speed(slice_and_export: Path, expected_value: str):
    """Test filament_cooling_final_speed parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_cooling_final_speed(gcode_path, expected_value)
    assert ok, f"filament_cooling_final_speed expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params

def test_filament_stamping_loading_speed(slice_and_export: Path, expected_value: str):
    """Test filament_stamping_loading_speed parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_stamping_loading_speed(gcode_path, expected_value)
    assert ok, f"filament_stamping_loading_speed expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params

def test_filament_stamping_distance(slice_and_export: Path, expected_value: str):
    """Test filament_stamping_distance parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_stamping_distance(gcode_path, expected_value)
    assert ok, f"filament_stamping_distance expected {expected_value}, got {actual}: {details}"



