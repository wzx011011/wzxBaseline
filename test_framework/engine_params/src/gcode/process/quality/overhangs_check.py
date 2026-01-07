"""
Overhangs（悬垂）参数的 G-code 校验逻辑
参数: extra_perimeters_on_overhangs, make_overhang_printable, make_overhang_printable_angle,
     make_overhang_printable_hole_size, overhang_optimization
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


def parse_extra_perimeters_on_overhangs(
    gcode_path: Path | str,
    expected_value: bool
) -> Tuple[bool, Optional[bool], Dict[str, Any]]:
    """检测悬垂额外周长参数 (extra_perimeters_on_overhangs) - L1: CONFIG_BLOCK"""
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("extra_perimeters_on_overhangs")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 extra_perimeters_on_overhangs 参数"})
    
    parse_ok, actual_value, parse_details = _parse_bool_value(raw_value, "extra_perimeters_on_overhangs")
    if not parse_ok:
        return (False, None, parse_details)
    
    ok = actual_value == expected_value
    
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


def parse_make_overhang_printable(
    gcode_path: Path | str,
    expected_value: bool
) -> Tuple[bool, Optional[bool], Dict[str, Any]]:
    """检测使悬垂可打印参数 (make_overhang_printable) - L1: CONFIG_BLOCK"""
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("make_overhang_printable")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 make_overhang_printable 参数"})
    
    parse_ok, actual_value, parse_details = _parse_bool_value(raw_value, "make_overhang_printable")
    if not parse_ok:
        return (False, None, parse_details)
    
    ok = actual_value == expected_value
    
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


def parse_make_overhang_printable_angle(
    gcode_path: Path | str,
    expected_value: float,
    tolerance: float = 0.1
) -> Tuple[bool, Optional[float], Dict[str, Any]]:
    """检测可打印悬垂角度参数 (make_overhang_printable_angle) - L1: CONFIG_BLOCK"""
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("make_overhang_printable_angle")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 make_overhang_printable_angle 参数"})
    
    try:
        actual_value = float(raw_value)
        ok = abs(actual_value - expected_value) <= tolerance
    except (ValueError, TypeError) as e:
        return (False, None, {"error": f"无法解析 make_overhang_printable_angle 值: {raw_value}", "exception": str(e)})
    
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "tolerance": tolerance,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


def parse_make_overhang_printable_hole_size(
    gcode_path: Path | str,
    expected_value: float,
    tolerance: float = 0.01
) -> Tuple[bool, Optional[float], Dict[str, Any]]:
    """检测可打印悬垂孔尺寸参数 (make_overhang_printable_hole_size) - L1: CONFIG_BLOCK"""
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("make_overhang_printable_hole_size")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 make_overhang_printable_hole_size 参数"})
    
    try:
        actual_value = float(raw_value)
        ok = abs(actual_value - expected_value) <= tolerance
    except (ValueError, TypeError) as e:
        return (False, None, {"error": f"无法解析 make_overhang_printable_hole_size 值: {raw_value}", "exception": str(e)})
    
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "tolerance": tolerance,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


def parse_overhang_optimization(
    gcode_path: Path | str,
    expected_value: bool
) -> Tuple[bool, Optional[bool], Dict[str, Any]]:
    """检测悬垂优化参数 (overhang_optimization) - L1: CONFIG_BLOCK"""
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("overhang_optimization")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 overhang_optimization 参数"})
    
    parse_ok, actual_value, parse_details = _parse_bool_value(raw_value, "overhang_optimization")
    if not parse_ok:
        return (False, None, parse_details)
    
    ok = actual_value == expected_value
    
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)
