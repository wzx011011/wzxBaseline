import pytest
from pathlib import Path
from engine_params.src.gcode.filament.cooling.model_fan_check import (
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
)

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



