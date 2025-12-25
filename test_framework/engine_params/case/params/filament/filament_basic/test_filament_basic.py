"""
Test cases for Filament Basic parameters.

Total: 19 test functions
"""

import pytest
from pathlib import Path
from engine_params.src.gcode.filament.filament_basic import (
    parse_filament_type,
    parse_filament_vendor,
    parse_filament_soluble,
    parse_filament_is_support,
    parse_required_nozzle_HRC,
    parse_default_filament_colour,
    parse_filament_diameter,
    parse_filament_adhesiveness_category,
    parse_filament_flow_ratio,
    parse_enable_pressure_advance,
    parse_pressure_advance,
    parse_filament_density,
    parse_filament_shrink,
    parse_filament_shrinkage_compensation_z,
    parse_filament_cost,
    parse_temperature_vitrification,
    parse_idle_temperature,
    parse_nozzle_temperature_range_low,
    parse_nozzle_temperature_range_high,
)


@pytest.mark.engine_params
def test_filament_type(slice_and_export: Path, expected_value: str):
    """Test filament_type parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_type(gcode_path, expected_value)
    assert ok, f"filament_type expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_filament_vendor(slice_and_export: Path, expected_value: str):
    """Test filament_vendor parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_vendor(gcode_path, expected_value)
    assert ok, f"filament_vendor expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_filament_soluble(slice_and_export: Path, expected_value: str):
    """Test filament_soluble parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_soluble(gcode_path, expected_value)
    assert ok, f"filament_soluble expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_filament_is_support(slice_and_export: Path, expected_value: str):
    """Test filament_is_support parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_is_support(gcode_path, expected_value)
    assert ok, f"filament_is_support expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_required_nozzle_HRC(slice_and_export: Path, expected_value: str):
    """Test required_nozzle_HRC parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_required_nozzle_HRC(gcode_path, expected_value)
    assert ok, f"required_nozzle_HRC expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_default_filament_colour(slice_and_export: Path, expected_value: str):
    """Test default_filament_colour parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_default_filament_colour(gcode_path, expected_value)
    assert ok, f"default_filament_colour expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_filament_diameter(slice_and_export: Path, expected_value: str):
    """Test filament_diameter parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_diameter(gcode_path, expected_value)
    assert ok, f"filament_diameter expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_filament_adhesiveness_category(slice_and_export: Path, expected_value: str):
    """Test filament_adhesiveness_category parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_adhesiveness_category(gcode_path, expected_value)
    assert ok, f"filament_adhesiveness_category expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_filament_flow_ratio(slice_and_export: Path, expected_value: str):
    """Test filament_flow_ratio parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_flow_ratio(gcode_path, expected_value)
    assert ok, f"filament_flow_ratio expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_enable_pressure_advance(slice_and_export: Path, expected_value: str):
    """Test enable_pressure_advance parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_enable_pressure_advance(gcode_path, expected_value)
    assert ok, f"enable_pressure_advance expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_pressure_advance(slice_and_export: Path, expected_value: str):
    """Test pressure_advance parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_pressure_advance(gcode_path, expected_value)
    assert ok, f"pressure_advance expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_filament_density(slice_and_export: Path, expected_value: str):
    """Test filament_density parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_density(gcode_path, expected_value)
    assert ok, f"filament_density expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_filament_shrink(slice_and_export: Path, expected_value: str):
    """Test filament_shrink parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_shrink(gcode_path, expected_value)
    assert ok, f"filament_shrink expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_filament_shrinkage_compensation_z(slice_and_export: Path, expected_value: str):
    """Test filament_shrinkage_compensation_z parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_shrinkage_compensation_z(gcode_path, expected_value)
    assert ok, f"filament_shrinkage_compensation_z expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_filament_cost(slice_and_export: Path, expected_value: str):
    """Test filament_cost parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_cost(gcode_path, expected_value)
    assert ok, f"filament_cost expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_temperature_vitrification(slice_and_export: Path, expected_value: str):
    """Test temperature_vitrification parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_temperature_vitrification(gcode_path, expected_value)
    assert ok, f"temperature_vitrification expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_idle_temperature(slice_and_export: Path, expected_value: str):
    """Test idle_temperature parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_idle_temperature(gcode_path, expected_value)
    assert ok, f"idle_temperature expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_nozzle_temperature_range_low(slice_and_export: Path, expected_value: str):
    """Test nozzle_temperature_range_low parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_nozzle_temperature_range_low(gcode_path, expected_value)
    assert ok, f"nozzle_temperature_range_low expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_nozzle_temperature_range_high(slice_and_export: Path, expected_value: str):
    """Test nozzle_temperature_range_high parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_nozzle_temperature_range_high(gcode_path, expected_value)
    assert ok, f"nozzle_temperature_range_high expected {expected_value}, got {actual}: {details}"
