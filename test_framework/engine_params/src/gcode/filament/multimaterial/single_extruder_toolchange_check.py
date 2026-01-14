from pathlib import Path
from typing import Any, Tuple, Dict
import re
from engine_params.src.gcode.GCodeParserEx import GCodeParserEx


def _str_norm(s: Any) -> str:
    "标准化字符串表示"
    if s is None:
        return ""
    # 如果是ParsedConfig对象，取其value值
    if hasattr(s, 'value'):
        return str(s.value).strip()
    return str(s).strip()


def parse_filament_loading_speed_start(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_loading_speed_start parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_loading_speed_start")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament loading speed start: {actual}"},
    )


def parse_filament_loading_speed(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_loading_speed parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_loading_speed")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament loading speed: {actual}"},
    )


def parse_filament_unloading_speed_start(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_unloading_speed_start parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_unloading_speed_start")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament unloading speed start: {actual}"},
    )


def parse_filament_unloading_speed(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_unloading_speed parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_unloading_speed")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament unloading speed: {actual}"},
    )


def parse_filament_toolchange_delay(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_toolchange_delay parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_toolchange_delay")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament toolchange delay: {actual}"},
    )


def parse_filament_cooling_moves(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_cooling_moves parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_cooling_moves")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament cooling moves: {actual}"},
    )


def parse_filament_cooling_initial_speed(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_cooling_initial_speed parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_cooling_initial_speed")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament cooling initial speed: {actual}"},
    )


def parse_filament_cooling_final_speed(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_cooling_final_speed parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_cooling_final_speed")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament cooling final speed: {actual}"},
    )


def parse_filament_stamping_loading_speed(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_stamping_loading_speed parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_stamping_loading_speed")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament stamping loading speed: {actual}"},
    )


def parse_filament_stamping_distance(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_stamping_distance parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_stamping_distance")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament stamping distance: {actual}"},
    )

