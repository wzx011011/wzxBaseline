"""
Cooling parameter validation functions.

This module contains parsing and validation functions for cooling parameters.
Total: 22 parameters
"""

from pathlib import Path
from typing import Tuple, Dict, Any
from engine_params.src.gcode.GCodeParser import GCodeParser


def _str_norm(v: Any) -> str | None:
    if v is None:
        return None
    return str(v).strip()


def parse_close_fan_the_first_x_layers(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test close_fan_the_first_x_layers parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("close_fan_the_first_x_layers")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Close fan the first X layers: {actual}"},
    )


def parse_full_fan_speed_layer(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test full_fan_speed_layer parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("full_fan_speed_layer")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Full fan speed layer: {actual}"},
    )


def parse_fan_min_speed(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test fan_min_speed parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("fan_min_speed")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Fan min speed: {actual}"},
    )


def parse_fan_cooling_layer_time(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test fan_cooling_layer_time parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("fan_cooling_layer_time")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Fan cooling layer time: {actual}"},
    )


def parse_fan_max_speed(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test fan_max_speed parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("fan_max_speed")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Fan max speed: {actual}"},
    )


def parse_slow_down_layer_time(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test slow_down_layer_time parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("slow_down_layer_time")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Slow down layer time: {actual}"},
    )


def parse_reduce_fan_stop_start_freq(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test reduce_fan_stop_start_freq parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("reduce_fan_stop_start_freq")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Reduce fan stop start freq: {actual}"},
    )


def parse_slow_down_for_layer_cooling(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test slow_down_for_layer_cooling parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("slow_down_for_layer_cooling")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Slow down for layer cooling: {actual}"},
    )


def parse_cooling_slowdown_logic(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test cooling_slowdown_logic parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("cooling_slowdown_logic")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Cooling slowdown logic: {actual}"},
    )


def parse_cooling_perimeter_transition_distance(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test cooling_perimeter_transition_distance parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("cooling_perimeter_transition_distance")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Cooling perimeter transition distance: {actual}"},
    )


def parse_slow_down_min_speed(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test slow_down_min_speed parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("slow_down_min_speed")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Slow down min speed: {actual}"},
    )


def parse_enable_overhang_bridge_fan(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test enable_overhang_bridge_fan parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("enable_overhang_bridge_fan")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Enable overhang bridge fan: {actual}"},
    )


def parse_overhang_fan_threshold(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test overhang_fan_threshold parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("overhang_fan_threshold")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Overhang fan threshold: {actual}"},
    )


def parse_overhang_fan_speed(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test overhang_fan_speed parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("overhang_fan_speed")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Overhang fan speed: {actual}"},
    )


def parse_support_material_interface_fan_speed(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test support_material_interface_fan_speed parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("support_material_interface_fan_speed")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Support material interface fan speed: {actual}"},
    )


def parse_additional_cooling_fan_speed(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test additional_cooling_fan_speed parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("additional_cooling_fan_speed")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Additional cooling fan speed: {actual}"},
    )


def parse_enable_special_area_additional_cooling_fan(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test enable_special_area_additional_cooling_fan parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("enable_special_area_additional_cooling_fan")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Enable special area additional cooling fan: {actual}"},
    )


def parse_cool_special_cds_fan_speed(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test cool_special_cds_fan_speed parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("cool_special_cds_fan_speed")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Cool special CDS fan speed: {actual}"},
    )


def parse_cool_cds_fan_start_at_height(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test cool_cds_fan_start_at_height parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("cool_cds_fan_start_at_height")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Cool CDS fan start at height: {actual}"},
    )


def parse_activate_air_filtration(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test activate_air_filtration parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("activate_air_filtration")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Activate air filtration: {actual}"},
    )


def parse_during_print_exhaust_fan_speed(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test during_print_exhaust_fan_speed parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("during_print_exhaust_fan_speed")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"During print exhaust fan speed: {actual}"},
    )


def parse_complete_print_exhaust_fan_speed(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test complete_print_exhaust_fan_speed parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("complete_print_exhaust_fan_speed")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Complete print exhaust fan speed: {actual}"},
    )
