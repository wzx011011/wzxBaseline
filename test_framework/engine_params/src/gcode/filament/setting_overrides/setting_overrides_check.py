"""
Setting Overrides parameter validation functions.

This module contains parsing and validation functions for filament setting overrides.
Total: 16 parameters
"""

from pathlib import Path
from typing import Tuple, Dict, Any
from engine_params.src.gcode.GCodeParser import GCodeParser


def _str_norm(v: Any) -> str | None:
    if v is None:
        return None
    return str(v).strip()


def parse_filament_retraction_length(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_retraction_length parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_retraction_length")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament retraction length: {actual}"},
    )


def parse_filament_z_hop(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_z_hop parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_z_hop")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament Z hop: {actual}"},
    )


def parse_filament_z_hop_types(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_z_hop_types parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_z_hop_types")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament Z hop types: {actual}"},
    )


def parse_filament_retract_lift_above(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_retract_lift_above parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_retract_lift_above")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament retract lift above: {actual}"},
    )


def parse_filament_retract_lift_below(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_retract_lift_below parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_retract_lift_below")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament retract lift below: {actual}"},
    )


def parse_filament_retract_lift_enforce(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_retract_lift_enforce parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_retract_lift_enforce")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament retract lift enforce: {actual}"},
    )


def parse_filament_retraction_speed(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_retraction_speed parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_retraction_speed")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament retraction speed: {actual}"},
    )


def parse_filament_deretraction_speed(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_deretraction_speed parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_deretraction_speed")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament deretraction speed: {actual}"},
    )


def parse_filament_retract_restart_extra(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_retract_restart_extra parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_retract_restart_extra")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament retract restart extra: {actual}"},
    )


def parse_filament_retraction_minimum_travel(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_retraction_minimum_travel parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_retraction_minimum_travel")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament retraction minimum travel: {actual}"},
    )


def parse_filament_retract_when_changing_layer(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_retract_when_changing_layer parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_retract_when_changing_layer")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament retract when changing layer: {actual}"},
    )


def parse_filament_wipe(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_wipe parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_wipe")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament wipe: {actual}"},
    )


def parse_filament_wipe_distance(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_wipe_distance parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_wipe_distance")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament wipe distance: {actual}"},
    )


def parse_filament_retract_before_wipe(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_retract_before_wipe parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_retract_before_wipe")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament retract before wipe: {actual}"},
    )


def parse_filament_long_retractions_when_cut(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_long_retractions_when_cut parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_long_retractions_when_cut")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament long retractions when cut: {actual}"},
    )


def parse_filament_retraction_distances_when_cut(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_retraction_distances_when_cut parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_retraction_distances_when_cut")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament retraction distances when cut: {actual}"},
    )
