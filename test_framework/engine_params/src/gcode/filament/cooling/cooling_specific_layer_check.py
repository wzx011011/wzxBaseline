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


def parse_close_fan_the_first_x_layers(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test close_fan_the_first_x_layers parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("close_fan_the_first_x_layers")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Close fan the first x layers: {actual}"},
    )


def parse_full_fan_speed_layer(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test full_fan_speed_layer parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("full_fan_speed_layer")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Full fan speed layer: {actual}"},
    )

