from pathlib import Path
from typing import Any, Tuple, Dict
import re
from engine_params.src.gcode.GCodeParserEx import GCodeParserEx


def _str_norm(s: Any) -> str:
    """标准化字符串表示"""
    if s is None:
        return ""
    # 如果是ParsedConfig对象，取其value值
    if hasattr(s, 'value'):
        return str(s.value).strip()
    return str(s).strip()


def parse_fan_min_speed(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test fan_min_speed parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("fan_min_speed")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Fan min speed: {actual}"},
    )



def parse_fan_max_speed(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test fan_max_speed parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("fan_max_speed")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Fan max speed: {actual}"},
    )



def parse_reduce_fan_stop_start_freq(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test reduce_fan_stop_start_freq parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("reduce_fan_stop_start_freq")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Reduce fan stop start freq: {actual}"},
    )


def parse_fan_cooling_layer_time(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test fan_cooling_layer_time parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("fan_cooling_layer_time")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Fan cooling layer time: {actual}"},
    )


def parse_slow_down_layer_time(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test slow_down_layer_time parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("slow_down_layer_time")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Slow down layer time: {actual}"},
    )


def parse_slow_down_for_layer_cooling(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test slow_down_for_layer_cooling parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("slow_down_for_layer_cooling")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Slow down for layer cooling: {actual}"},
    )


def parse_cooling_slowdown_logic(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test cooling_slowdown_logic parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("cooling_slowdown_logic")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Cooling slowdown logic: {actual}"},
    )


def parse_cooling_perimeter_transition_distance(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test cooling_perimeter_transition_distance parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("cooling_perimeter_transition_distance")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Cooling perimeter transition distance: {actual}"},
    )


def parse_slow_down_min_speed(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test slow_down_min_speed parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("slow_down_min_speed")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Slow down min speed: {actual}"},
    )


def parse_enable_overhang_bridge_fan(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test enable_overhang_bridge_fan parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("enable_overhang_bridge_fan")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Enable overhang bridge fan: {actual}"},
    )


def parse_overhang_fan_threshold(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test overhang_fan_threshold parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("overhang_fan_threshold")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Overhang fan threshold: {actual}"},
    )


def parse_overhang_fan_speed(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test overhang_fan_speed parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("overhang_fan_speed")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Overhang fan speed: {actual}"},
    )


def parse_support_material_interface_fan_speed(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test support_material_interface_fan_speed parameter (Level 1 - Config)"""
    parser = GCodeParserEx(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("support_material_interface_fan_speed")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Support material interface fan speed: {actual}"},
    )






