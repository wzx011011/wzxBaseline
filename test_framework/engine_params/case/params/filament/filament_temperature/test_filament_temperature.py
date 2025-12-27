"""
Test cases for Filament Temperature parameters.

Total: 20 test functions
"""

import pytest
from pathlib import Path
from engine_params.src.gcode.filament.filament_temperature import (
    parse_chamber_temperature,
    parse_activate_chamber_temp_control,
    parse_activate_chamber_layer,
    parse_nozzle_temperature_initial_layer,
    parse_nozzle_temperature,
    parse_material_flow_dependent_temperature,
    parse_material_flow_temp_graph,
    parse_cool_plate_temp_initial_layer,
    parse_cool_plate_temp,
    parse_eng_plate_temp_initial_layer,
    parse_eng_plate_temp,
    parse_hot_plate_temp_initial_layer,
    parse_hot_plate_temp,
    parse_textured_plate_temp_initial_layer,
    parse_textured_plate_temp,
    parse_customized_plate_temp_initial_layer,
    parse_customized_plate_temp,
    parse_epoxy_resin_plate_temp_initial_layer,
    parse_epoxy_resin_plate_temp,
    parse_filament_max_volumetric_speed,
)


@pytest.mark.engine_params
def test_chamber_temperature(slice_and_export: Path, expected_value: str):
    """Test chamber_temperature parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_chamber_temperature(gcode_path, expected_value)
    assert ok, f"chamber_temperature expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_activate_chamber_temp_control(slice_and_export: Path, expected_value: str):
    """Test activate_chamber_temp_control parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_activate_chamber_temp_control(gcode_path, expected_value)
    assert ok, f"activate_chamber_temp_control expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_activate_chamber_layer(slice_and_export: Path, expected_value: str):
    """Test activate_chamber_layer parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_activate_chamber_layer(gcode_path, expected_value)
    assert ok, f"activate_chamber_layer expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_nozzle_temperature_initial_layer(slice_and_export: Path, expected_value: str):
    """Test nozzle_temperature_initial_layer parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_nozzle_temperature_initial_layer(gcode_path, expected_value)
    assert ok, f"nozzle_temperature_initial_layer expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_nozzle_temperature(slice_and_export: Path, expected_value: str):
    """Test nozzle_temperature parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_nozzle_temperature(gcode_path, expected_value)
    assert ok, f"nozzle_temperature expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_material_flow_dependent_temperature(slice_and_export: Path, expected_value: str):
    """Test material_flow_dependent_temperature parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_material_flow_dependent_temperature(gcode_path, expected_value)
    assert ok, f"material_flow_dependent_temperature expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
@pytest.mark.xfail(reason="Slicer ignores material_flow_temp_graph from 3MF config - uses preset value instead")
def test_material_flow_temp_graph(slice_and_export: Path, expected_value: str):
    """Test material_flow_temp_graph parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_material_flow_temp_graph(gcode_path, expected_value)
    assert ok, f"material_flow_temp_graph expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_cool_plate_temp_initial_layer(slice_and_export: Path, expected_value: str):
    """Test cool_plate_temp_initial_layer parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_cool_plate_temp_initial_layer(gcode_path, expected_value)
    assert ok, f"cool_plate_temp_initial_layer expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_cool_plate_temp(slice_and_export: Path, expected_value: str):
    """Test cool_plate_temp parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_cool_plate_temp(gcode_path, expected_value)
    assert ok, f"cool_plate_temp expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_eng_plate_temp_initial_layer(slice_and_export: Path, expected_value: str):
    """Test eng_plate_temp_initial_layer parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_eng_plate_temp_initial_layer(gcode_path, expected_value)
    assert ok, f"eng_plate_temp_initial_layer expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_eng_plate_temp(slice_and_export: Path, expected_value: str):
    """Test eng_plate_temp parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_eng_plate_temp(gcode_path, expected_value)
    assert ok, f"eng_plate_temp expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_hot_plate_temp_initial_layer(slice_and_export: Path, expected_value: str):
    """Test hot_plate_temp_initial_layer parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_hot_plate_temp_initial_layer(gcode_path, expected_value)
    assert ok, f"hot_plate_temp_initial_layer expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_hot_plate_temp(slice_and_export: Path, expected_value: str):
    """Test hot_plate_temp parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_hot_plate_temp(gcode_path, expected_value)
    assert ok, f"hot_plate_temp expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_textured_plate_temp_initial_layer(slice_and_export: Path, expected_value: str):
    """Test textured_plate_temp_initial_layer parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_textured_plate_temp_initial_layer(gcode_path, expected_value)
    assert ok, f"textured_plate_temp_initial_layer expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_textured_plate_temp(slice_and_export: Path, expected_value: str):
    """Test textured_plate_temp parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_textured_plate_temp(gcode_path, expected_value)
    assert ok, f"textured_plate_temp expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_customized_plate_temp_initial_layer(slice_and_export: Path, expected_value: str):
    """Test customized_plate_temp_initial_layer parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_customized_plate_temp_initial_layer(gcode_path, expected_value)
    assert ok, f"customized_plate_temp_initial_layer expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_customized_plate_temp(slice_and_export: Path, expected_value: str):
    """Test customized_plate_temp parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_customized_plate_temp(gcode_path, expected_value)
    assert ok, f"customized_plate_temp expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_epoxy_resin_plate_temp_initial_layer(slice_and_export: Path, expected_value: str):
    """Test epoxy_resin_plate_temp_initial_layer parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_epoxy_resin_plate_temp_initial_layer(gcode_path, expected_value)
    assert ok, f"epoxy_resin_plate_temp_initial_layer expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_epoxy_resin_plate_temp(slice_and_export: Path, expected_value: str):
    """Test epoxy_resin_plate_temp parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_epoxy_resin_plate_temp(gcode_path, expected_value)
    assert ok, f"epoxy_resin_plate_temp expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_filament_max_volumetric_speed(slice_and_export: Path, expected_value: str):
    """Test filament_max_volumetric_speed parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_max_volumetric_speed(gcode_path, expected_value)
    assert ok, f"filament_max_volumetric_speed expected {expected_value}, got {actual}: {details}"
