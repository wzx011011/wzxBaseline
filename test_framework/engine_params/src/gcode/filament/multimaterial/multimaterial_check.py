"""
Multimaterial parameter validation functions.

This module contains parsing and validation functions for multimaterial parameters.
Total: 14 parameters
"""

from pathlib import Path
from typing import Tuple, Dict, Any
from engine_params.src.gcode.GCodeParser import GCodeParser


def _str_norm(v: Any) -> str | None:
    if v is None:
        return None
    return str(v).strip()


def parse_filament_minimal_purge_on_wipe_tower(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_minimal_purge_on_wipe_tower parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_minimal_purge_on_wipe_tower")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament minimal purge on wipe tower: {actual}"},
    )


def parse_filament_loading_speed_start(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_loading_speed_start parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_loading_speed_start")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament loading speed start: {actual}"},
    )


def parse_filament_loading_speed(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_loading_speed parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_loading_speed")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament loading speed: {actual}"},
    )


def parse_filament_unloading_speed_start(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_unloading_speed_start parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_unloading_speed_start")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament unloading speed start: {actual}"},
    )


def parse_filament_unloading_speed(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_unloading_speed parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_unloading_speed")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament unloading speed: {actual}"},
    )


def parse_filament_toolchange_delay(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_toolchange_delay parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_toolchange_delay")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament toolchange delay: {actual}"},
    )


def parse_filament_cooling_moves(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_cooling_moves parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_cooling_moves")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament cooling moves: {actual}"},
    )


def parse_filament_cooling_initial_speed(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_cooling_initial_speed parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_cooling_initial_speed")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament cooling initial speed: {actual}"},
    )


def parse_filament_cooling_final_speed(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_cooling_final_speed parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_cooling_final_speed")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament cooling final speed: {actual}"},
    )


def parse_filament_stamping_loading_speed(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_stamping_loading_speed parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_stamping_loading_speed")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament stamping loading speed: {actual}"},
    )


def parse_filament_stamping_distance(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_stamping_distance parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_stamping_distance")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament stamping distance: {actual}"},
    )


def parse_filament_multitool_ramming(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_multitool_ramming parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_multitool_ramming")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament multitool ramming: {actual}"},
    )


def parse_filament_multitool_ramming_volume(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_multitool_ramming_volume parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_multitool_ramming_volume")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament multitool ramming volume: {actual}"},
    )


def parse_filament_multitool_ramming_flow(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_multitool_ramming_flow parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_multitool_ramming_flow")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament multitool ramming flow: {actual}"},
    )
