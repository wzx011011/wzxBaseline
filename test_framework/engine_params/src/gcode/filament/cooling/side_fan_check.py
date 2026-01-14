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


def parse_additional_cooling_fan_speed(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test additional_cooling_fan_speed parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("additional_cooling_fan_speed")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Additional cooling fan speed: {actual}"},
    )


def parse_enable_special_area_additional_cooling_fan(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test enable_special_area_additional_cooling_fan parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("enable_special_area_additional_cooling_fan")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Enable special area additional cooling fan: {actual}"},
    )


def parse_cool_special_cds_fan_speed(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test cool_special_cds_fan_speed parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("cool_special_cds_fan_speed")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Cool special cds fan speed: {actual}"},
    )


def parse_cool_cds_fan_start_at_height(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test cool_cds_fan_start_at_height parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("cool_cds_fan_start_at_height")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Cool cds fan start at height: {actual}"},
    )

