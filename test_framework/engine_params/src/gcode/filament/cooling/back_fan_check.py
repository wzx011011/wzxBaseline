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


def parse_activate_air_filtration(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test activate_air_filtration parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("activate_air_filtration")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Activate air filtration: {actual}"},
    )


def parse_during_print_exhaust_fan_speed(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test during_print_exhaust_fan_speed parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("during_print_exhaust_fan_speed")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"During print exhaust fan speed: {actual}"},
    )


def parse_complete_print_exhaust_fan_speed(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test complete_print_exhaust_fan_speed parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("complete_print_exhaust_fan_speed")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Complete print exhaust fan speed: {actual}"},
    )

