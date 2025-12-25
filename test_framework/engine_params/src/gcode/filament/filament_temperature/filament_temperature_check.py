"""
Filament Temperature parameter validation functions.

This module contains parsing and validation functions for filament temperature parameters.
Total: 20 parameters
"""

from pathlib import Path
from typing import Tuple, Dict, Any
from engine_params.src.gcode.GCodeParser import GCodeParser


def _str_norm(v: Any) -> str | None:
    if v is None:
        return None
    return str(v).strip()


def parse_chamber_temperature(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test chamber_temperature parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("chamber_temperature")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Chamber temperature: {actual}"},
    )


def parse_activate_chamber_temp_control(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test activate_chamber_temp_control parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("activate_chamber_temp_control")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Activate chamber temp control: {actual}"},
    )


def parse_activate_chamber_layer(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test activate_chamber_layer parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("activate_chamber_layer")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Activate chamber layer: {actual}"},
    )


def parse_nozzle_temperature_initial_layer(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test nozzle_temperature_initial_layer parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("nozzle_temperature_initial_layer")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Nozzle temperature initial layer: {actual}"},
    )


def parse_nozzle_temperature(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test nozzle_temperature parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("nozzle_temperature")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Nozzle temperature: {actual}"},
    )


def parse_material_flow_dependent_temperature(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test material_flow_dependent_temperature parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("material_flow_dependent_temperature")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Material flow dependent temperature: {actual}"},
    )


def parse_material_flow_temp_graph(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test material_flow_temp_graph parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("material_flow_temp_graph")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Material flow temp graph: {actual}"},
    )


def parse_cool_plate_temp_initial_layer(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test cool_plate_temp_initial_layer parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("cool_plate_temp_initial_layer")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Cool plate temp initial layer: {actual}"},
    )


def parse_cool_plate_temp(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test cool_plate_temp parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("cool_plate_temp")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Cool plate temp: {actual}"},
    )


def parse_eng_plate_temp_initial_layer(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test eng_plate_temp_initial_layer parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("eng_plate_temp_initial_layer")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Eng plate temp initial layer: {actual}"},
    )


def parse_eng_plate_temp(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test eng_plate_temp parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("eng_plate_temp")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Eng plate temp: {actual}"},
    )


def parse_hot_plate_temp_initial_layer(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test hot_plate_temp_initial_layer parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("hot_plate_temp_initial_layer")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Hot plate temp initial layer: {actual}"},
    )


def parse_hot_plate_temp(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test hot_plate_temp parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("hot_plate_temp")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Hot plate temp: {actual}"},
    )


def parse_textured_plate_temp_initial_layer(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test textured_plate_temp_initial_layer parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("textured_plate_temp_initial_layer")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Textured plate temp initial layer: {actual}"},
    )


def parse_textured_plate_temp(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test textured_plate_temp parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("textured_plate_temp")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Textured plate temp: {actual}"},
    )


def parse_customized_plate_temp_initial_layer(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test customized_plate_temp_initial_layer parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("customized_plate_temp_initial_layer")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Customized plate temp initial layer: {actual}"},
    )


def parse_customized_plate_temp(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test customized_plate_temp parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("customized_plate_temp")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Customized plate temp: {actual}"},
    )


def parse_epoxy_resin_plate_temp_initial_layer(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test epoxy_resin_plate_temp_initial_layer parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("epoxy_resin_plate_temp_initial_layer")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Epoxy resin plate temp initial layer: {actual}"},
    )


def parse_epoxy_resin_plate_temp(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test epoxy_resin_plate_temp parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("epoxy_resin_plate_temp")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Epoxy resin plate temp: {actual}"},
    )


def parse_filament_max_volumetric_speed(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_max_volumetric_speed parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_max_volumetric_speed")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament max volumetric speed: {actual}"},
    )
