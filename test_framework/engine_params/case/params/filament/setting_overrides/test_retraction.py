import pytest
from pathlib import Path

from engine_params.src.gcode.filament.setting_overrides.retraction_check import (
    parse_filament_retraction_length,
    parse_filament_z_hop,
    parse_filament_z_hop_types,
    parse_filament_retract_lift_above,
    parse_filament_retract_lift_below,
    parse_filament_retract_lift_enforce,
    parse_filament_retraction_speed,
    parse_filament_deretraction_speed,
    parse_filament_retract_restart_extra,
    parse_filament_retraction_minimum_travel,
    parse_filament_retract_when_changing_layer,
    parse_filament_retract_when_changing_layer_behavior,
    parse_filament_wipe,
    parse_filament_wipe_distance,
    parse_filament_retract_before_wipe,
    parse_filament_long_retractions_when_cut,
    parse_filament_retraction_distances_when_cut,
)


@pytest.mark.engine_params
def test_filament_retraction_length(slice_and_export: Path, expected_value: str):
    """Test filament_retraction_length parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_retraction_length(gcode_path, expected_value)
    assert ok, f"filament_retraction_length expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_filament_z_hop(slice_and_export: Path, expected_value: str):
    """Test filament_z_hop parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_z_hop(gcode_path, expected_value)
    assert ok, f"filament_z_hop expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_filament_z_hop_types(slice_and_export: Path, expected_value: str):
    """Test filament_z_hop parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_z_hop_types(gcode_path, expected_value)
    assert ok, f"filament_z_hop_types expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_filament_retract_lift_above(slice_and_export: Path, expected_value: str):
    """Test filament_retract_lift_above parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_retract_lift_above(gcode_path, expected_value)
    assert ok, f"filament_retract_lift_above expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_filament_retract_lift_below(slice_and_export: Path, expected_value: str):
    """Test filament_retract_lift_below parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_retract_lift_below(gcode_path, expected_value)
    assert ok, f"filament_retract_lift_below expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_filament_retract_lift_enforce(slice_and_export: Path, expected_value: str):
    """Test filament_retract_lift_enforce parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_retract_lift_enforce(gcode_path, expected_value)
    assert ok, f"filament_retract_lift_enforce expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_filament_retraction_speed(slice_and_export: Path, expected_value: str):
    """Test filament_retraction_speed parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_retraction_speed(gcode_path, expected_value)
    assert ok, f"filament_retraction_speed expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_filament_deretraction_speed(slice_and_export: Path, expected_value: str):
    """Test filament_deretraction_speed parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_deretraction_speed(gcode_path, expected_value)
    assert ok, f"filament_deretraction_speed expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_filament_retract_restart_extra(slice_and_export: Path, expected_value: str):
    """Test filament_retract_restart_extra parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_retract_restart_extra(gcode_path, expected_value)
    assert ok, f"filament_retract_restart_extra expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_filament_retraction_minimum_travel(slice_and_export: Path, expected_value: str):
    """Test filament_retraction_minimum_travel parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_retraction_minimum_travel(gcode_path, expected_value)
    assert ok, f"filament_retraction_minimum_travel expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_filament_retract_when_changing_layer(slice_and_export: Path, expected_value: str):
    """Test filament_retract_when_changing_layer parameter (Level 1 - Config + Level 2 - Behavior)"""
    gcode_path = slice_and_export
    
    # Level 1: Config validation
    ok1, actual1, details1 = parse_filament_retract_when_changing_layer(gcode_path, expected_value)
    assert ok1, f"Level 1 - filament_retract_when_changing_layer config expected {expected_value}, got {actual1}: {details1}"
    
    # Level 2: G-code behavior validation
    ok2, actual2, details2 = parse_filament_retract_when_changing_layer_behavior(gcode_path, expected_value)
    assert ok2, f"Level 2 - filament_retract_when_changing_layer behavior validation failed. Expected {expected_value}, analysis: {actual2}. Details: {details2}"


@pytest.mark.engine_params
def test_filament_wipe(slice_and_export: Path, expected_value: str):
    """Test filament_wipe parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_wipe(gcode_path, expected_value)
    assert ok, f"filament_wipe expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_filament_wipe_distance(slice_and_export: Path, expected_value: str):
    """Test filament_wipe_distance parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_wipe_distance(gcode_path, expected_value)
    assert ok, f"filament_wipe_distance expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_filament_retract_before_wipe(slice_and_export: Path, expected_value: str):
    """Test filament_retract_before_wipe parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_retract_before_wipe(gcode_path, expected_value)
    assert ok, f"filament_retract_before_wipe expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_filament_long_retractions_when_cut(slice_and_export: Path, expected_value: str):
    """Test filament_long_retractions_when_cut parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_long_retractions_when_cut(gcode_path, expected_value)
    assert ok, f"filament_long_retractions_when_cut expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_filament_retraction_distances_when_cut(slice_and_export: Path, expected_value: str):
    """Test filament_retraction_distances_when_cut parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_retraction_distances_when_cut(gcode_path, expected_value)
    assert ok, f"filament_retraction_distances_when_cut expected {expected_value}, got {actual}: {details}"

