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


def parse_filament_multitool_ramming(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_multitool_ramming parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_multitool_ramming")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament multitool ramming: {actual}"},
    )


def parse_filament_multitool_ramming_volume(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_multitool_ramming_volume parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_multitool_ramming_volume")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament multitool ramming volume: {actual}"},
    )


def parse_filament_multitool_ramming_flow(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_multitool_ramming_flow parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_multitool_ramming_flow")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament multitool ramming flow: {actual}"},
    )

