"""
Test cases for Cooling parameters.

Total: 22 test functions
"""

import pytest
from pathlib import Path
from engine_params.src.gcode.filament.cooling import (
    parse_close_fan_the_first_x_layers,
    parse_full_fan_speed_layer,
    parse_fan_min_speed,
    parse_fan_cooling_layer_time,
    parse_fan_max_speed,
    parse_slow_down_layer_time,
    parse_reduce_fan_stop_start_freq,
    parse_slow_down_for_layer_cooling,
    parse_cooling_slowdown_logic,
    parse_cooling_perimeter_transition_distance,
    parse_slow_down_min_speed,
    parse_enable_overhang_bridge_fan,
    parse_overhang_fan_threshold,
    parse_overhang_fan_speed,
    parse_support_material_interface_fan_speed,
    parse_additional_cooling_fan_speed,
    parse_enable_special_area_additional_cooling_fan,
    parse_cool_special_cds_fan_speed,
    parse_cool_cds_fan_start_at_height,
    parse_activate_air_filtration,
    parse_during_print_exhaust_fan_speed,
    parse_complete_print_exhaust_fan_speed,
)


@pytest.mark.engine_params
def test_close_fan_the_first_x_layers(slice_and_export: Path, expected_value: str):
    """Test close_fan_the_first_x_layers parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_close_fan_the_first_x_layers(gcode_path, expected_value)
    assert ok, f"close_fan_the_first_x_layers expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_full_fan_speed_layer(slice_and_export: Path, expected_value: str):
    """Test full_fan_speed_layer parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_full_fan_speed_layer(gcode_path, expected_value)
    assert ok, f"full_fan_speed_layer expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_fan_min_speed(slice_and_export: Path, expected_value: str):
    """Test fan_min_speed parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_fan_min_speed(gcode_path, expected_value)
    assert ok, f"fan_min_speed expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_fan_cooling_layer_time(slice_and_export: Path, expected_value: str):
    """Test fan_cooling_layer_time parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_fan_cooling_layer_time(gcode_path, expected_value)
    assert ok, f"fan_cooling_layer_time expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_fan_max_speed(slice_and_export: Path, expected_value: str):
    """Test fan_max_speed parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_fan_max_speed(gcode_path, expected_value)
    assert ok, f"fan_max_speed expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_slow_down_layer_time(slice_and_export: Path, expected_value: str):
    """Test slow_down_layer_time parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_slow_down_layer_time(gcode_path, expected_value)
    assert ok, f"slow_down_layer_time expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_reduce_fan_stop_start_freq(slice_and_export: Path, expected_value: str):
    """Test reduce_fan_stop_start_freq parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_reduce_fan_stop_start_freq(gcode_path, expected_value)
    assert ok, f"reduce_fan_stop_start_freq expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_slow_down_for_layer_cooling(slice_and_export: Path, expected_value: str):
    """Test slow_down_for_layer_cooling parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_slow_down_for_layer_cooling(gcode_path, expected_value)
    assert ok, f"slow_down_for_layer_cooling expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_cooling_slowdown_logic(slice_and_export: Path, expected_value: str):
    """Test cooling_slowdown_logic parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_cooling_slowdown_logic(gcode_path, expected_value)
    assert ok, f"cooling_slowdown_logic expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_cooling_perimeter_transition_distance(slice_and_export: Path, expected_value: str):
    """Test cooling_perimeter_transition_distance parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_cooling_perimeter_transition_distance(gcode_path, expected_value)
    assert ok, f"cooling_perimeter_transition_distance expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_slow_down_min_speed(slice_and_export: Path, expected_value: str):
    """Test slow_down_min_speed parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_slow_down_min_speed(gcode_path, expected_value)
    assert ok, f"slow_down_min_speed expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_enable_overhang_bridge_fan(slice_and_export: Path, expected_value: str):
    """Test enable_overhang_bridge_fan parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_enable_overhang_bridge_fan(gcode_path, expected_value)
    assert ok, f"enable_overhang_bridge_fan expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_overhang_fan_threshold(slice_and_export: Path, expected_value: str):
    """Test overhang_fan_threshold parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_overhang_fan_threshold(gcode_path, expected_value)
    assert ok, f"overhang_fan_threshold expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_overhang_fan_speed(slice_and_export: Path, expected_value: str):
    """Test overhang_fan_speed parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_overhang_fan_speed(gcode_path, expected_value)
    assert ok, f"overhang_fan_speed expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_material_interface_fan_speed(slice_and_export: Path, expected_value: str):
    """Test support_material_interface_fan_speed parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_support_material_interface_fan_speed(gcode_path, expected_value)
    assert ok, f"support_material_interface_fan_speed expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_additional_cooling_fan_speed(slice_and_export: Path, expected_value: str):
    """Test additional_cooling_fan_speed parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_additional_cooling_fan_speed(gcode_path, expected_value)
    assert ok, f"additional_cooling_fan_speed expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_enable_special_area_additional_cooling_fan(slice_and_export: Path, expected_value: str):
    """Test enable_special_area_additional_cooling_fan parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_enable_special_area_additional_cooling_fan(gcode_path, expected_value)
    assert ok, f"enable_special_area_additional_cooling_fan expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_cool_special_cds_fan_speed(slice_and_export: Path, expected_value: str):
    """Test cool_special_cds_fan_speed parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_cool_special_cds_fan_speed(gcode_path, expected_value)
    assert ok, f"cool_special_cds_fan_speed expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_cool_cds_fan_start_at_height(slice_and_export: Path, expected_value: str):
    """Test cool_cds_fan_start_at_height parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_cool_cds_fan_start_at_height(gcode_path, expected_value)
    assert ok, f"cool_cds_fan_start_at_height expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_activate_air_filtration(slice_and_export: Path, expected_value: str):
    """Test activate_air_filtration parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_activate_air_filtration(gcode_path, expected_value)
    assert ok, f"activate_air_filtration expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_during_print_exhaust_fan_speed(slice_and_export: Path, expected_value: str):
    """Test during_print_exhaust_fan_speed parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_during_print_exhaust_fan_speed(gcode_path, expected_value)
    assert ok, f"during_print_exhaust_fan_speed expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_complete_print_exhaust_fan_speed(slice_and_export: Path, expected_value: str):
    """Test complete_print_exhaust_fan_speed parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_complete_print_exhaust_fan_speed(gcode_path, expected_value)
    assert ok, f"complete_print_exhaust_fan_speed expected {expected_value}, got {actual}: {details}"
