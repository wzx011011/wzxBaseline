"""
Precision（精度）参数的 G-code 校验逻辑
参数: slice_closing_radius, resolution, hole_to_polyhole, hole_to_polyhole_threshold,
     hole_to_polyhole_twisted, precise_outer_wall, precise_z_height
"""
from __future__ import annotations

from pathlib import Path
from typing import Tuple, Dict, Any, Optional

from engine_params.src.gcode.GCodeParser import GCodeParser


def _parse_bool_value(raw_value: Any, param_name: str) -> Tuple[bool, Optional[bool], Dict[str, Any]]:
    """通用布尔值解析函数"""
    actual_value = None
    if isinstance(raw_value, bool):
        actual_value = raw_value
    elif isinstance(raw_value, (int, float)):
        actual_value = bool(int(raw_value))
    elif isinstance(raw_value, str):
        raw_str = raw_value.lower().strip()
        if raw_str in ("1", "true", "yes", "enabled"):
            actual_value = True
        elif raw_str in ("0", "false", "no", "disabled"):
            actual_value = False
    
    if actual_value is None:
        return (False, None, {"error": f"无法解析 {param_name} 布尔值: {raw_value}"})
    
    return (True, actual_value, {})


def parse_slice_closing_radius(
    gcode_path: Path | str,
    expected_value: float,
    tolerance: float = 0.001
) -> Tuple[bool, Optional[float], Dict[str, Any]]:
    """检测切片闭合半径参数 (slice_closing_radius) - L1: CONFIG_BLOCK"""
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("slice_closing_radius")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 slice_closing_radius 参数"})
    
    try:
        actual_value = float(raw_value)
        ok = abs(actual_value - expected_value) <= tolerance
    except (ValueError, TypeError) as e:
        return (False, None, {"error": f"无法解析 slice_closing_radius 值: {raw_value}", "exception": str(e)})
    
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "tolerance": tolerance,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


def parse_resolution(
    gcode_path: Path | str,
    expected_value: float,
    tolerance: float = 0.001
) -> Tuple[bool, Optional[float], Dict[str, Any]]:
    """检测分辨率参数 (resolution) - L1: CONFIG_BLOCK"""
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("resolution")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 resolution 参数"})
    
    try:
        actual_value = float(raw_value)
        ok = abs(actual_value - expected_value) <= tolerance
    except (ValueError, TypeError) as e:
        return (False, None, {"error": f"无法解析 resolution 值: {raw_value}", "exception": str(e)})
    
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "tolerance": tolerance,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


def parse_hole_to_polyhole(
    gcode_path: Path | str,
    expected_value: bool
) -> Tuple[bool, Optional[bool], Dict[str, Any]]:
    """检测孔转多边形参数 (hole_to_polyhole) - L1: CONFIG_BLOCK"""
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("hole_to_polyhole")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 hole_to_polyhole 参数"})
    
    parse_ok, actual_value, parse_details = _parse_bool_value(raw_value, "hole_to_polyhole")
    if not parse_ok:
        return (False, None, parse_details)
    
    ok = actual_value == expected_value
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


def parse_hole_to_polyhole_threshold(
    gcode_path: Path | str,
    expected_value: float,
    tolerance: float = 0.001
) -> Tuple[bool, Optional[float], Dict[str, Any]]:
    """检测孔转多边形阈值参数 (hole_to_polyhole_threshold) - L1: CONFIG_BLOCK"""
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("hole_to_polyhole_threshold")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 hole_to_polyhole_threshold 参数"})
    
    try:
        actual_value = float(raw_value)
        ok = abs(actual_value - expected_value) <= tolerance
    except (ValueError, TypeError) as e:
        return (False, None, {"error": f"无法解析 hole_to_polyhole_threshold 值: {raw_value}", "exception": str(e)})
    
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "tolerance": tolerance,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


def parse_hole_to_polyhole_twisted(
    gcode_path: Path | str,
    expected_value: bool
) -> Tuple[bool, Optional[bool], Dict[str, Any]]:
    """检测扭曲多边形孔参数 (hole_to_polyhole_twisted) - L1: CONFIG_BLOCK"""
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("hole_to_polyhole_twisted")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 hole_to_polyhole_twisted 参数"})
    
    parse_ok, actual_value, parse_details = _parse_bool_value(raw_value, "hole_to_polyhole_twisted")
    if not parse_ok:
        return (False, None, parse_details)
    
    ok = actual_value == expected_value
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


def parse_precise_outer_wall(
    gcode_path: Path | str,
    expected_value: bool
) -> Tuple[bool, Optional[bool], Dict[str, Any]]:
    """检测精确外墙参数 (precise_outer_wall) - L1: CONFIG_BLOCK"""
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("precise_outer_wall")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 precise_outer_wall 参数"})
    
    parse_ok, actual_value, parse_details = _parse_bool_value(raw_value, "precise_outer_wall")
    if not parse_ok:
        return (False, None, parse_details)
    
    ok = actual_value == expected_value
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


def parse_precise_z_height(
    gcode_path: Path | str,
    expected_value: float,
    tolerance: float = 0.01
) -> Tuple[bool, Optional[float], Dict[str, Any]]:
    """检测精确 Z 高度参数 (precise_z_height) - L1: CONFIG_BLOCK"""
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("precise_z_height")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 precise_z_height 参数"})
    
    try:
        actual_value = float(raw_value)
        ok = abs(actual_value - expected_value) <= tolerance
    except (ValueError, TypeError) as e:
        return (False, None, {"error": f"无法解析 precise_z_height 值: {raw_value}", "exception": str(e)})
    
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "tolerance": tolerance,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)
