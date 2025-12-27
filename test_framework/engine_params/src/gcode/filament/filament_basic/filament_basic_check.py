"""
Filament Basic parameter validation functions.

This module contains parsing and validation functions for filament basic parameters.
Total: 19 parameters
"""

from pathlib import Path
from typing import Tuple, Dict, Any
from engine_params.src.gcode.GCodeParser import GCodeParser


def _str_norm(v: Any) -> str | None:
    if v is None:
        return None
    return str(v).strip()


def parse_filament_type(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_type parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_type")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament type: {actual}"},
    )


def parse_filament_vendor(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_vendor parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_vendor")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament vendor: {actual}"},
    )


def parse_filament_soluble(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_soluble parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_soluble")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament soluble: {actual}"},
    )


def parse_filament_is_support(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_is_support parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_is_support")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament is support: {actual}"},
    )


def parse_required_nozzle_HRC(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test required_nozzle_HRC parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    # GCodeParser converts keys to lowercase
    actual = cfg.get("required_nozzle_hrc")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Required nozzle HRC: {actual}"},
    )


def parse_default_filament_colour(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test default_filament_colour parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("default_filament_colour")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Default filament colour: {actual}"},
    )


def parse_filament_diameter(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_diameter parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_diameter")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament diameter: {actual}"},
    )


def parse_filament_adhesiveness_category(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_adhesiveness_category parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_adhesiveness_category")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament adhesiveness category: {actual}"},
    )


def parse_filament_flow_ratio(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_flow_ratio parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_flow_ratio")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament flow ratio: {actual}"},
    )


def parse_enable_pressure_advance(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test enable_pressure_advance parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("enable_pressure_advance")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Enable pressure advance: {actual}"},
    )


def parse_pressure_advance(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test pressure_advance parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("pressure_advance")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Pressure advance: {actual}"},
    )


def parse_filament_density(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_density parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_density")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament density: {actual}"},
    )


def parse_filament_shrink(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_shrink parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_shrink")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament shrink: {actual}"},
    )


def parse_filament_shrinkage_compensation_z(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_shrinkage_compensation_z parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_shrinkage_compensation_z")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament shrinkage compensation Z: {actual}"},
    )


def parse_filament_cost(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_cost parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_cost")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament cost: {actual}"},
    )


def parse_temperature_vitrification(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test temperature_vitrification parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("temperature_vitrification")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Temperature vitrification: {actual}"},
    )


def parse_idle_temperature(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test idle_temperature parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("idle_temperature")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Idle temperature: {actual}"},
    )


def parse_nozzle_temperature_range_low(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test nozzle_temperature_range_low parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("nozzle_temperature_range_low")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Nozzle temperature range low: {actual}"},
    )


def parse_nozzle_temperature_range_high(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test nozzle_temperature_range_high parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("nozzle_temperature_range_high")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Nozzle temperature range high: {actual}"},
    )
