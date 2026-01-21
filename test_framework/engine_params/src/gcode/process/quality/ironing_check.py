"""
Ironing（熨烫）参数的 G-code 校验逻辑 - 新增 L1 校验函数
参数: ironing_type, ironing_pattern, ironing_flow, ironing_spacing, ironing_speed, ironing_angle
"""
from __future__ import annotations

from pathlib import Path
from typing import Tuple, Dict, Any, Optional

from engine_params.src.gcode.GCodeParser import GCodeParser
from engine_params.src.gcode.process.quality.ironing_type_check import (
    parse_ironing_type as _parse_ironing_type_l2_impl,
)


# ============= 新增 L1 校验函数 =============

def parse_ironing_type_l1(
    gcode_path: Path | str,
    expected_value: str
) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """检测熨烫类型参数 (ironing_type) - L1: CONFIG_BLOCK"""
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("ironing_type")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 ironing_type 参数"})
    
    actual_value = str(raw_value).strip()
    ok = actual_value == expected_value
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


def parse_ironing_pattern(
    gcode_path: Path | str,
    expected_value: str
) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """检测熨烫图案参数 (ironing_pattern) - L1: CONFIG_BLOCK"""
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("ironing_pattern")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 ironing_pattern 参数"})
    
    actual_value = str(raw_value).strip()
    ok = actual_value == expected_value
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


def parse_ironing_flow(
    gcode_path: Path | str,
    expected_value: str
) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """检测熨烫流量参数 (ironing_flow) - L1: CONFIG_BLOCK
    注意：值为百分比字符串，如 "10%", "15%"
    """
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("ironing_flow")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 ironing_flow 参数"})
    
    actual_value = str(raw_value).strip()
    ok = actual_value == expected_value
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


def parse_ironing_spacing(
    gcode_path: Path | str,
    expected_value: float,
    tolerance: float = 0.01
) -> Tuple[bool, Optional[float], Dict[str, Any]]:
    """检测熨烫间距参数 (ironing_spacing) - L1: CONFIG_BLOCK"""
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("ironing_spacing")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 ironing_spacing 参数"})
    
    try:
        actual_value = float(raw_value)
        ok = abs(actual_value - expected_value) <= tolerance
    except (ValueError, TypeError) as e:
        return (False, None, {"error": f"无法解析 ironing_spacing 值: {raw_value}", "exception": str(e)})
    
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "tolerance": tolerance,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


def parse_ironing_speed(
    gcode_path: Path | str,
    expected_value: float,
    tolerance: float = 0.1
) -> Tuple[bool, Optional[float], Dict[str, Any]]:
    """检测熨烫速度参数 (ironing_speed) - L1: CONFIG_BLOCK"""
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("ironing_speed")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 ironing_speed 参数"})
    
    try:
        actual_value = float(raw_value)
        ok = abs(actual_value - expected_value) <= tolerance
    except (ValueError, TypeError) as e:
        return (False, None, {"error": f"无法解析 ironing_speed 值: {raw_value}", "exception": str(e)})
    
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "tolerance": tolerance,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


def parse_ironing_angle(
    gcode_path: Path | str,
    expected_value: float,
    tolerance: float = 0.1
) -> Tuple[bool, Optional[float], Dict[str, Any]]:
    """检测熨烫角度参数 (ironing_angle) - L1: CONFIG_BLOCK"""
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("ironing_angle")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 ironing_angle 参数"})
    
    try:
        actual_value = float(raw_value)
        ok = abs(actual_value - expected_value) <= tolerance
    except (ValueError, TypeError) as e:
        return (False, None, {"error": f"无法解析 ironing_angle 值: {raw_value}", "exception": str(e)})
    
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "tolerance": tolerance,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


def parse_ironing_type(
    gcode_path: Path | str,
    expected_value: str
) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    return parse_ironing_type_l1(gcode_path, expected_value)


def parse_ironing_type_l2(
    gcode_path: Path | str,
    *,
    workers: int = 0,
) -> list[dict[int, list[bytes | str]]]:
    return _parse_ironing_type_l2_impl(gcode_path, workers=workers)
