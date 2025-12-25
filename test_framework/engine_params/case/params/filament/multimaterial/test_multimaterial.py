"""
Test cases for Multimaterial parameters.

Total: 14 test functions
"""

import pytest
from pathlib import Path
from engine_params.src.gcode.filament.multimaterial import (
    parse_filament_minimal_purge_on_wipe_tower,
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
    parse_filament_multitool_ramming,
    parse_filament_multitool_ramming_volume,
    parse_filament_multitool_ramming_flow,
)


@pytest.mark.engine_params
def test_filament_minimal_purge_on_wipe_tower(slice_and_export: Path, expected_value: str):
    """Test filament_minimal_purge_on_wipe_tower parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_minimal_purge_on_wipe_tower(gcode_path, expected_value)
    assert ok, f"filament_minimal_purge_on_wipe_tower expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
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


@pytest.mark.engine_params
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
