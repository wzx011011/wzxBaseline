"""
Bridging（桥接）参数的 G-code 校验逻辑
新增参数: bridge_angle, bridge_flow, bridge_density, bridge_speed, thick_bridges,
         dont_filter_internal_bridges, thick_internal_bridges, internal_bridge_speed,
         counterbore_hole_bridging
"""
from __future__ import annotations

from pathlib import Path
from typing import Tuple, Dict, Any

from engine_params.src.gcode.GCodeParser import GCodeParser


def parse_bridge_angle(
    gcode_path: Path | str,
    expected_angle: float,
    tolerance: float = 0.1
) -> Tuple[bool, float | None, Dict[str, Any]]:
    """
    检测桥接角度参数 (bridge_angle)
    
    Level 1: 从 CONFIG_BLOCK 读取配置值
    
    参数:
        gcode_path: G-code 文件路径
        expected_angle: 期望的桥接角度
        tolerance: 允许的误差范围
    
    返回:
        (是否通过, 实际值, 详细信息)
    """
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("bridge_angle")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 bridge_angle 参数"})
    
    try:
        actual_angle = float(raw_value)
        ok = abs(actual_angle - expected_angle) <= tolerance
        details = {
            "config_value": actual_angle,
            "expected": expected_angle,
            "tolerance": tolerance,
            "method": "L1 - CONFIG_BLOCK"
        }
        return (ok, actual_angle, details)
    except (ValueError, TypeError) as e:
        return (False, None, {"error": f"无法解析 bridge_angle 值: {raw_value}", "exception": str(e)})


def parse_bridge_flow(
    gcode_path: Path | str,
    expected_flow: float,
    tolerance: float = 0.01
) -> Tuple[bool, float | None, Dict[str, Any]]:
    """
    检测桥接流量参数 (bridge_flow)
    
    Level 1: 从 CONFIG_BLOCK 读取配置值
    
    参数:
        gcode_path: G-code 文件路径
        expected_flow: 期望的桥接流量
        tolerance: 允许的误差范围
    
    返回:
        (是否通过, 实际值, 详细信息)
    """
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("bridge_flow")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 bridge_flow 参数"})
    
    try:
        actual_flow = float(raw_value)
        ok = abs(actual_flow - expected_flow) <= tolerance
        details = {
            "config_value": actual_flow,
            "expected": expected_flow,
            "tolerance": tolerance,
            "method": "L1 - CONFIG_BLOCK"
        }
        return (ok, actual_flow, details)
    except (ValueError, TypeError) as e:
        return (False, None, {"error": f"无法解析 bridge_flow 值: {raw_value}", "exception": str(e)})


def parse_bridge_density(
    gcode_path: Path | str,
    expected_density: str,
) -> Tuple[bool, str | None, Dict[str, Any]]:
    """
    检测桥接密度参数 (bridge_density)
    
    Level 1: 从 CONFIG_BLOCK 读取配置值
    
    参数:
        gcode_path: G-code 文件路径
        expected_density: 期望的桥接密度 (如 "80%", "100%")
    
    返回:
        (是否通过, 实际值, 详细信息)
    """
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("bridge_density")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 bridge_density 参数"})
    
    actual_density = str(raw_value).strip()
    ok = actual_density == expected_density
    details = {
        "config_value": actual_density,
        "expected": expected_density,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_density, details)


def parse_bridge_speed(
    gcode_path: Path | str,
    expected_speed: float,
    tolerance: float = 0.1
) -> Tuple[bool, float | None, Dict[str, Any]]:
    """
    检测桥接速度参数 (bridge_speed)
    
    Level 1: 从 CONFIG_BLOCK 读取配置值
    
    参数:
        gcode_path: G-code 文件路径
        expected_speed: 期望的桥接速度
        tolerance: 允许的误差范围
    
    返回:
        (是否通过, 实际值, 详细信息)
    """
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("bridge_speed")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 bridge_speed 参数"})
    
    try:
        actual_speed = float(raw_value)
        ok = abs(actual_speed - expected_speed) <= tolerance
        details = {
            "config_value": actual_speed,
            "expected": expected_speed,
            "tolerance": tolerance,
            "method": "L1 - CONFIG_BLOCK"
        }
        return (ok, actual_speed, details)
    except (ValueError, TypeError) as e:
        return (False, None, {"error": f"无法解析 bridge_speed 值: {raw_value}", "exception": str(e)})


def parse_thick_bridges(
    gcode_path: Path | str,
    expected_value: bool,
) -> Tuple[bool, bool | None, Dict[str, Any]]:
    """
    检测厚桥接参数 (thick_bridges)
    
    Level 1: 从 CONFIG_BLOCK 读取配置值
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的布尔值
    
    返回:
        (是否通过, 实际值, 详细信息)
    """
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("thick_bridges")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 thick_bridges 参数"})
    
    # 处理布尔值: "1"/"0", "true"/"false", 1/0
    actual_value = None
    if isinstance(raw_value, bool):
        actual_value = raw_value
    elif isinstance(raw_value, (int, float)):
        actual_value = bool(int(raw_value))
    elif isinstance(raw_value, str):
        raw_str = raw_value.lower().strip()
        if raw_str in ("1", "true", "yes"):
            actual_value = True
        elif raw_str in ("0", "false", "no"):
            actual_value = False
    
    if actual_value is None:
        return (False, None, {"error": f"无法解析 thick_bridges 布尔值: {raw_value}"})
    
    ok = actual_value == expected_value
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


def parse_dont_filter_internal_bridges(
    gcode_path: Path | str,
    expected_value: bool,
) -> Tuple[bool, bool | None, Dict[str, Any]]:
    """
    检测不过滤内部桥接参数 (dont_filter_internal_bridges)
    
    Level 1: 从 CONFIG_BLOCK 读取配置值
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的布尔值
    
    返回:
        (是否通过, 实际值, 详细信息)
    """
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("dont_filter_internal_bridges")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 dont_filter_internal_bridges 参数"})
    
    # 特殊处理: 可能的值 "disabled", "enabled", "1", "0"
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
        return (False, None, {"error": f"无法解析 dont_filter_internal_bridges 值: {raw_value}"})
    
    ok = actual_value == expected_value
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


def parse_thick_internal_bridges(
    gcode_path: Path | str,
    expected_value: bool,
) -> Tuple[bool, bool | None, Dict[str, Any]]:
    """
    检测厚内部桥接参数 (thick_internal_bridges)
    
    Level 1: 从 CONFIG_BLOCK 读取配置值
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的布尔值
    
    返回:
        (是否通过, 实际值, 详细信息)
    """
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("thick_internal_bridges")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 thick_internal_bridges 参数"})
    
    actual_value = None
    if isinstance(raw_value, bool):
        actual_value = raw_value
    elif isinstance(raw_value, (int, float)):
        actual_value = bool(int(raw_value))
    elif isinstance(raw_value, str):
        raw_str = raw_value.lower().strip()
        if raw_str in ("1", "true", "yes"):
            actual_value = True
        elif raw_str in ("0", "false", "no"):
            actual_value = False
    
    if actual_value is None:
        return (False, None, {"error": f"无法解析 thick_internal_bridges 布尔值: {raw_value}"})
    
    ok = actual_value == expected_value
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


def parse_internal_bridge_speed(
    gcode_path: Path | str,
    expected_speed: str,
) -> Tuple[bool, str | None, Dict[str, Any]]:
    """
    检测内部桥接速度参数 (internal_bridge_speed)
    
    Level 1: 从 CONFIG_BLOCK 读取配置值
    
    参数:
        gcode_path: G-code 文件路径
        expected_speed: 期望的速度值 (可能是百分比如 "150%")
    
    返回:
        (是否通过, 实际值, 详细信息)
    """
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("internal_bridge_speed")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 internal_bridge_speed 参数"})
    
    actual_speed = str(raw_value).strip()
    ok = actual_speed == expected_speed
    details = {
        "config_value": actual_speed,
        "expected": expected_speed,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_speed, details)


def parse_counterbore_hole_bridging(
    gcode_path: Path | str,
    expected_value: str,
) -> Tuple[bool, str | None, Dict[str, Any]]:
    """
    检测沉孔桥接参数 (counterbore_hole_bridging)
    
    Level 1: 从 CONFIG_BLOCK 读取配置值
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的枚举值 (none/sparse_infill/etc)
    
    返回:
        (是否通过, 实际值, 详细信息)
    """
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("counterbore_hole_bridging")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 counterbore_hole_bridging 参数"})
    
    actual_value = str(raw_value).strip()
    ok = actual_value == expected_value
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)
