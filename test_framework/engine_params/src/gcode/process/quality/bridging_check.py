from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, Optional, Tuple, Any

from engine_params.src.gcode.GCodeParser import GCodeParser
from engine_params.src.gcode.constants import ExtrusionType


def _extract_last_extrude_e(parser: GCodeParser, type_value: str) -> Optional[float]:
    """Return the last extrude-point E for the given TYPE across all layers."""
    contours = parser.get_type_contours_per_layer(types=[type_value], workers=0)
    if not contours:
        return None

    last_e: Optional[float] = None
    for layer_map in contours:
        if not layer_map:
            continue
        for oid, type_map in (layer_map or {}).items():
            polylines = (type_map or {}).get(type_value) or []
            for poly in polylines or []:
                for pt in poly:
                    if pt.kind == "extrude" and pt.e is not None:
                        last_e = pt.e
    return last_e


def parse_internal_bridge_flow(
        tested_gcode: Path | str,
        baseline_gcode: Path | str,
        expected_ratio: float,
        *,
        tol: float = 1e-3,
) -> Tuple[bool, Optional[float], Dict[str, object]]:
    """
    Compare the last Internal bridge extrude E between tested and baseline G-code.
    """
    tested_path = Path(tested_gcode)
    baseline_path = Path(baseline_gcode)

    tested_parser = GCodeParser(tested_path)
    baseline_parser = GCodeParser(baseline_path)

    tested_e = _extract_last_extrude_e(tested_parser, ExtrusionType.INTERNAL_BRIDGE.value)
    baseline_e = _extract_last_extrude_e(baseline_parser, ExtrusionType.INTERNAL_BRIDGE.value)

    ratio: Optional[float] = None
    ok = False
    if tested_e is not None and baseline_e is not None and abs(baseline_e) > 1e-9:
        ratio = tested_e / baseline_e
        ok = math.isclose(ratio, expected_ratio, rel_tol=tol, abs_tol=tol)

    details: Dict[str, object] = {
        "tested_gcode": str(tested_path),
        "baseline_gcode": str(baseline_path),
        "tested_e": tested_e,
        "baseline_e": baseline_e,
        "ratio": ratio,
        "expected_ratio": expected_ratio,
        "tolerance": tol,
    }

    return ok, ratio, details


# ============= 新增校验函数 (L1 - CONFIG_BLOCK) =============


def parse_bridge_angle(
    gcode_path: Path | str,
    expected_angle: float,
    tolerance: float = 0.1
) -> Tuple[bool, Optional[float], Dict[str, Any]]:
    """检测桥接角度参数 (bridge_angle) - L1: CONFIG_BLOCK"""
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
) -> Tuple[bool, Optional[float], Dict[str, Any]]:
    """检测桥接流量参数 (bridge_flow) - L1: CONFIG_BLOCK"""
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
) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """检测桥接密度参数 (bridge_density) - L1: CONFIG_BLOCK"""
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
) -> Tuple[bool, Optional[float], Dict[str, Any]]:
    """检测桥接速度参数 (bridge_speed) - L1: CONFIG_BLOCK"""
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


def parse_thick_bridges(
    gcode_path: Path | str,
    expected_value: bool,
) -> Tuple[bool, Optional[bool], Dict[str, Any]]:
    """检测厚桥接参数 (thick_bridges) - L1: CONFIG_BLOCK"""
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("thick_bridges")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 thick_bridges 参数"})
    
    parse_ok, actual_value, parse_details = _parse_bool_value(raw_value, "thick_bridges")
    if not parse_ok:
        return (False, None, parse_details)
    
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
) -> Tuple[bool, Optional[bool], Dict[str, Any]]:
    """检测不过滤内部桥接参数 (dont_filter_internal_bridges) - L1: CONFIG_BLOCK"""
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("dont_filter_internal_bridges")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 dont_filter_internal_bridges 参数"})
    
    actual_value = str(raw_value).strip().lower()
    
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
) -> Tuple[bool, Optional[bool], Dict[str, Any]]:
    """检测厚内部桥接参数 (thick_internal_bridges) - L1: CONFIG_BLOCK"""
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("thick_internal_bridges")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 thick_internal_bridges 参数"})
    
    parse_ok, actual_value, parse_details = _parse_bool_value(raw_value, "thick_internal_bridges")
    if not parse_ok:
        return (False, None, parse_details)
    
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
) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """检测内部桥接速度参数 (internal_bridge_speed) - L1: CONFIG_BLOCK"""
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
) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """检测沉孔桥接参数 (counterbore_hole_bridging) - L1: CONFIG_BLOCK"""
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

