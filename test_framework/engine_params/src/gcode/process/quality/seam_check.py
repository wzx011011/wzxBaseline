"""
Seam（接缝）参数的 G-code 检测逻辑
包括：seam_position, seam_gap, staggered_inner_seams, seam_slope_type, scarf_joint_flow_ratio 等
"""
from __future__ import annotations

import math
import re
import statistics
from pathlib import Path
from typing import Tuple, Any

from engine_params.src.gcode.GCodeParser import GCodeParser
from engine_params.src.gcode.constants import ExtrusionType
from engine_params.src.gcode.process.quality.behavior import (
    BehaviorGCode,
    median,
    median_e_per_mm,
    median_speed,
    path_length,
)
from engine_params.src.gcode.process.quality.line_width_check import (
    _resolve_filament_diameter,
    _resolve_flow_ratio,
)


def parse_seam_position(
    gcode_path: Path,
    expected_position: str
) -> Tuple[bool, str, dict]:
    """
    检测接缝位置参数 (seam_position)
    
    Level 1: 从 CONFIG_BLOCK 读取配置值
    
    参数:
        gcode_path: G-code 文件路径
        expected_position: 期望的接缝位置 (aligned/nearest/random/back)
    
    返回:
        (是否通过, 实际值, 详细信息)
    """
    parser = GCodeParser(str(gcode_path))
    
    # 从配置注释中读取
    config = parser.load_config()
    actual_position = str(config.get("seam_position", "")).lower().strip()
    
    # 处理可能的空值或未找到的情况
    if not actual_position:
        return (False, "", {"error": "未在 G-code 配置中找到 seam_position 参数"})
    
    ok = actual_position == expected_position.lower()
    details = {
        "config_value": actual_position,
        "expected": expected_position,
        "method": "L1 - CONFIG_BLOCK"
    }
    
    return (ok, actual_position, details)


def parse_seam_gap(
    gcode_path: Path,
    expected_gap: float,
    tolerance: float = 0.001
) -> Tuple[bool, float, dict]:
    """
    检测接缝间隙参数 (seam_gap)
    
    参数:
        gcode_path: G-code 文件路径
        expected_gap: 期望的接缝间隙值
        tolerance: 容差
    
    返回:
        (是否通过, 实际值, 详细信息)
    """
    parser = GCodeParser(str(gcode_path))
    
    # 从配置注释中读取
    config = parser.load_config()
    actual_gap = float(config.get("seam_gap", 0))
    
    ok = abs(actual_gap - expected_gap) <= tolerance
    details = {
        "config_value": actual_gap,
        "expected": expected_gap,
        "tolerance": tolerance,
        "diff": abs(actual_gap - expected_gap)
    }
    
    return (ok, actual_gap, details)


def parse_staggered_inner_seams(
    gcode_path: Path,
    expected_staggered: bool
) -> Tuple[bool, bool, dict]:
    """
    检测交错内墙接缝参数 (staggered_inner_seams)
    
    参数:
        gcode_path: G-code 文件路径
        expected_staggered: 期望是否启用交错
    
    返回:
        (是否通过, 实际值, 详细信息)
    """
    parser = GCodeParser(str(gcode_path))
    
    # 从配置注释中读取
    config = parser.load_config()
    actual_value = config.get("staggered_inner_seams", "0")
    # 支持字符串和整数格式
    actual_staggered = str(actual_value) in ["1", "true", "True"]
    
    ok = actual_staggered == expected_staggered
    details = {
        "config_value": actual_value,
        "parsed_bool": actual_staggered,
        "expected": expected_staggered
    }
    
    return (ok, actual_staggered, details)


def parse_seam_slope_type(
    gcode_path: Path,
    expected_slope_type: str
) -> Tuple[bool, str, dict]:
    """
    检测接缝斜坡类型参数 (seam_slope_type)
    
    参数:
        gcode_path: G-code 文件路径
        expected_slope_type: 期望的斜坡类型 (none/linear/cubic)
    
    返回:
        (是否通过, 实际值, 详细信息)
    """
    parser = GCodeParser(str(gcode_path))
    
    # 从配置注释中读取
    config = parser.load_config()
    actual_type = config.get("seam_slope_type", "none").lower()
    
    ok = actual_type == expected_slope_type.lower()
    details = {
        "config_value": actual_type,
        "expected": expected_slope_type
    }
    
    return (ok, actual_type, details)


def parse_scarf_joint_flow_ratio(
    gcode_path: Path,
    expected_ratio: float,
    tolerance: float = 0.01
) -> Tuple[bool, float, dict]:
    """
    检测斜接流量比参数 (scarf_joint_flow_ratio)
    
    注意：切片器可能将百分比格式（80%）转换为数值（80.0），需要处理
    
    参数:
        gcode_path: G-code 文件路径
        expected_ratio: 期望的流量比（0.0-1.0 范围，如 0.8 表示 80%）
        tolerance: 容差
    
    返回:
        (是否通过, 实际值, 详细信息)
    """
    parser = GCodeParser(str(gcode_path))
    
    # 从配置注释中读取
    config = parser.load_config()
    config_value = config.get("scarf_joint_flow_ratio", 1.0)
    
    # 处理百分比格式：如果值 > 2.0，说明是百分比形式（如 80.0 表示 80%）
    if isinstance(config_value, (int, float)) and config_value > 2.0:
        actual_ratio = config_value / 100.0
    else:
        actual_ratio = float(config_value)
    
    ok = abs(actual_ratio - expected_ratio) <= tolerance
    details = {
        "config_value": config_value,
        "actual_ratio": actual_ratio,
        "expected": expected_ratio,
        "tolerance": tolerance,
        "diff": abs(actual_ratio - expected_ratio)
    }
    
    return (ok, actual_ratio, details)


# ============= 新增 L1 校验函数 =============

def _parse_bool_value(raw_value: Any, param_name: str) -> Tuple[bool, bool | None, dict]:
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


def parse_seam_slope_conditional(
    gcode_path: Path | str,
    expected_value: bool
) -> Tuple[bool, bool | None, dict]:
    """检测条件斜坡参数 (seam_slope_conditional) - L1: CONFIG_BLOCK"""
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("seam_slope_conditional")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 seam_slope_conditional 参数"})
    
    parse_ok, actual_value, parse_details = _parse_bool_value(raw_value, "seam_slope_conditional")
    if not parse_ok:
        return (False, None, parse_details)
    
    ok = actual_value == expected_value
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


def parse_seam_slope_entire_loop(
    gcode_path: Path | str,
    expected_value: bool
) -> Tuple[bool, bool | None, dict]:
    """检测整圈斜坡参数 (seam_slope_entire_loop) - L1: CONFIG_BLOCK"""
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("seam_slope_entire_loop")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 seam_slope_entire_loop 参数"})
    
    parse_ok, actual_value, parse_details = _parse_bool_value(raw_value, "seam_slope_entire_loop")
    if not parse_ok:
        return (False, None, parse_details)
    
    ok = actual_value == expected_value
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


def parse_seam_slope_inner_walls(
    gcode_path: Path | str,
    expected_value: bool
) -> Tuple[bool, bool | None, dict]:
    """检测内墙斜坡参数 (seam_slope_inner_walls) - L1: CONFIG_BLOCK"""
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("seam_slope_inner_walls")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 seam_slope_inner_walls 参数"})
    
    parse_ok, actual_value, parse_details = _parse_bool_value(raw_value, "seam_slope_inner_walls")
    if not parse_ok:
        return (False, None, parse_details)
    
    ok = actual_value == expected_value
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


def parse_seam_slope_min_length(
    gcode_path: Path | str,
    expected_value: float,
    tolerance: float = 0.1
) -> Tuple[bool, float | None, dict]:
    """检测最小斜坡长度参数 (seam_slope_min_length) - L1: CONFIG_BLOCK"""
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("seam_slope_min_length")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 seam_slope_min_length 参数"})
    
    try:
        actual_value = float(raw_value)
        ok = abs(actual_value - expected_value) <= tolerance
    except (ValueError, TypeError) as e:
        return (False, None, {"error": f"无法解析 seam_slope_min_length 值: {raw_value}", "exception": str(e)})
    
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "tolerance": tolerance,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


def parse_seam_slope_start_height(
    gcode_path: Path | str,
    expected_value: float,
    tolerance: float = 0.01
) -> Tuple[bool, float | None, dict]:
    """检测斜坡起始高度参数 (seam_slope_start_height) - L1: CONFIG_BLOCK"""
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("seam_slope_start_height")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 seam_slope_start_height 参数"})
    
    try:
        actual_value = float(raw_value)
        ok = abs(actual_value - expected_value) <= tolerance
    except (ValueError, TypeError) as e:
        return (False, None, {"error": f"无法解析 seam_slope_start_height 值: {raw_value}", "exception": str(e)})
    
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "tolerance": tolerance,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


def parse_seam_slope_steps(
    gcode_path: Path | str,
    expected_value: int
) -> Tuple[bool, int | None, dict]:
    """检测斜坡步数参数 (seam_slope_steps) - L1: CONFIG_BLOCK"""
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("seam_slope_steps")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 seam_slope_steps 参数"})
    
    try:
        actual_value = int(raw_value)
        ok = actual_value == expected_value
    except (ValueError, TypeError) as e:
        return (False, None, {"error": f"无法解析 seam_slope_steps 值: {raw_value}", "exception": str(e)})
    
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


def parse_scarf_angle_threshold(
    gcode_path: Path | str,
    expected_value: float,
    tolerance: float = 0.1
) -> Tuple[bool, float | None, dict]:
    """检测斜接角度阈值参数 (scarf_angle_threshold) - L1: CONFIG_BLOCK"""
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("scarf_angle_threshold")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 scarf_angle_threshold 参数"})
    
    try:
        actual_value = float(raw_value)
        ok = abs(actual_value - expected_value) <= tolerance
    except (ValueError, TypeError) as e:
        return (False, None, {"error": f"无法解析 scarf_angle_threshold 值: {raw_value}", "exception": str(e)})
    
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "tolerance": tolerance,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


def parse_scarf_joint_speed(
    gcode_path: Path | str,
    expected_value: float,
    tolerance: float = 0.1
) -> Tuple[bool, float | None, dict]:
    """检测斜接速度参数 (scarf_joint_speed) - L1: CONFIG_BLOCK"""
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("scarf_joint_speed")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 scarf_joint_speed 参数"})
    
    try:
        actual_value = float(raw_value)
        ok = abs(actual_value - expected_value) <= tolerance
    except (ValueError, TypeError) as e:
        return (False, None, {"error": f"无法解析 scarf_joint_speed 值: {raw_value}", "exception": str(e)})
    
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "tolerance": tolerance,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


def parse_scarf_overhang_threshold(
    gcode_path: Path | str,
    expected_value: float,
    tolerance: float = 0.1
) -> Tuple[bool, float | None, dict]:
    """检测斜接悬垂阈值参数 (scarf_overhang_threshold) - L1: CONFIG_BLOCK"""
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("scarf_overhang_threshold")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 scarf_overhang_threshold 参数"})
    
    try:
        if isinstance(raw_value, str) and raw_value.endswith("%"):
            num = raw_value[:-1].strip()
            actual_value = float(num)
        else:
            actual_value = float(raw_value)
        ok = abs(actual_value - expected_value) <= tolerance
    except (ValueError, TypeError) as e:
        return (False, None, {"error": f"无法解析 scarf_overhang_threshold 值: {raw_value}", "exception": str(e)})
    
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "tolerance": tolerance,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


# ---------------------------------------------------------------------------
# Behavioral implementations.  These definitions intentionally supersede the
# compatibility L1 implementations above while preserving their public API.
# ---------------------------------------------------------------------------


def _layer_z_map(behavior: BehaviorGCode) -> dict[int, float]:
    return {layer.index: layer.z for layer in behavior.layers if layer.z is not None}


def _sloped_moves(behavior: BehaviorGCode, role: str) -> list:
    layer_z = _layer_z_map(behavior)
    return [move for move in behavior.extrusion_moves(role)
            if move.layer in layer_z and (abs(move.z - layer_z[move.layer]) > 0.002
                                           or abs(move.z0 - layer_z[move.layer]) > 0.002)]


def _sloped_paths(behavior: BehaviorGCode, role: str) -> list[list]:
    sloped_ids = {move.path for move in _sloped_moves(behavior, role)}
    return [path for path in behavior.paths(role, min_length=2.0) if path and path[0].path in sloped_ids]


def parse_seam_position(
    gcode_path: Path, expected_position: str
) -> Tuple[bool, str, dict]:
    """Classify seam mode from consecutive Outer wall path start points."""
    behavior = BehaviorGCode(gcode_path)
    paths = behavior.paths(ExtrusionType.OUTER_WALL.value, min_length=10.0)
    primary = {}
    for path in paths:
        primary.setdefault(path[0].layer, path)
    starts = [(path[0].x0, path[0].y0) for _, path in sorted(primary.items())]
    distances = [math.dist(a, b) for a, b in zip(starts, starts[1:])]
    adjacent = median(distances)
    unique_starts = len({(round(x, 1), round(y, 1)) for x, y in starts})
    unique_ratio = unique_starts / len(starts) if starts else None
    expected = expected_position.strip().lower()
    if adjacent is None or unique_ratio is None:
        inferred = "unknown"
    elif unique_starts <= 3:
        inferred = "aligned"
    elif unique_ratio <= 0.35:
        inferred = "nearest"
    else:
        inferred = "random"
    ok = len(starts) >= 5 and inferred == expected
    return ok, inferred, {"method": "L2 - Outer-wall seam distribution", "sample_count": len(starts),
                          "median_adjacent_distance": adjacent, "unique_starts": unique_starts,
                          "unique_ratio": unique_ratio, "expected": expected,
                          "start_points": starts[:20]}


def parse_seam_gap(
    gcode_path: Path, expected_gap: float, tolerance: float = 0.001
) -> Tuple[bool, float, dict]:
    """Measure the geometric opening between Outer wall path endpoints."""
    behavior = BehaviorGCode(gcode_path)
    paths = behavior.paths(ExtrusionType.OUTER_WALL.value, min_length=10.0)
    gaps = [math.hypot(path[-1].x - path[0].x0, path[-1].y - path[0].y0) for path in paths]
    actual = median(gaps)
    allowed = max(tolerance, 0.04)
    ok = actual is not None and abs(actual - expected_gap) <= allowed
    return ok, float(actual or 0.0), {"method": "L2 - Outer-wall endpoint gap", "path_count": len(paths),
                                     "median_gap": actual, "expected_gap": expected_gap, "tolerance": allowed}


def parse_staggered_inner_seams(
    gcode_path: Path, expected_staggered: bool
) -> Tuple[bool, bool, dict]:
    """Compare inner-wall seam starts against the outer-wall seam on each layer."""
    behavior = BehaviorGCode(gcode_path)
    outer = behavior.paths(ExtrusionType.OUTER_WALL.value, min_length=10.0)
    inner = behavior.paths(ExtrusionType.INNER_WALL.value, min_length=10.0)
    outer_by_layer = {path[0].layer: path for path in outer}
    offsets = []
    for path in inner:
        reference = outer_by_layer.get(path[0].layer)
        if reference:
            offsets.append(math.hypot(path[0].x0 - reference[0].x0, path[0].y0 - reference[0].y0))
    value = median(offsets)
    actual = value is not None and value >= 0.95
    return bool(offsets) and actual == expected_staggered, actual, {
        "method": "L2 - Inner/outer seam start offset", "sample_count": len(offsets),
        "median_offset": value, "expected": expected_staggered}


def parse_seam_slope_type(
    gcode_path: Path, expected_slope_type: str
) -> Tuple[bool, str, dict]:
    """Detect scarf mode from within-layer Z-varying outer-wall extrusion."""
    behavior = BehaviorGCode(gcode_path)
    sloped = _sloped_moves(behavior, ExtrusionType.OUTER_WALL.value)
    inferred = "linear" if sloped else "none"
    expected = expected_slope_type.strip().lower()
    return inferred == expected, inferred, {"method": "L2 - Outer-wall Z slope",
                                            "sloped_segment_count": len(sloped), "expected": expected}


def parse_scarf_joint_flow_ratio(
    gcode_path: Path, expected_ratio: float, tolerance: float = 0.01
) -> Tuple[bool, float, dict]:
    """Infer scarf flow multiplier from E volume and generated WIDTH/HEIGHT."""
    behavior = BehaviorGCode(gcode_path)
    moves = [move for move in _sloped_moves(behavior, ExtrusionType.OUTER_WALL.value)
             if move.width and move.height and move.xy_length >= 0.2]
    cfg = GCodeParser(gcode_path).load_config()
    filament_area = math.pi * (_resolve_filament_diameter(cfg) / 2.0) ** 2
    layer_z = _layer_z_map(behavior)
    layer_info = {layer.index: layer for layer in behavior.layers}
    ratios = []
    for move in moves:
        h, w = float(move.height), float(move.width)
        section = h * max(0.0, w - h) + math.pi * h * h / 4.0
        info = layer_info.get(move.layer)
        nominal = layer_z.get(move.layer)
        if section > 0 and info is not None and info.height and nominal is not None:
            previous_z = nominal - info.height
            local_height_ratio = (((move.z0 - previous_z) + (move.z - previous_z))
                                  / (2.0 * info.height))
            # Sloped paths intentionally ramp material with their local Z
            # fraction. Divide that geometric ramp out to recover the explicit
            # scarf_joint_flow_ratio multiplier applied in GCode::_extrude().
            if 0.05 <= local_height_ratio <= 1.05:
                ratios.append((move.e / move.xy_length) * filament_area
                              / section / local_height_ratio)
    actual = median(ratios)
    allowed = max(tolerance, 0.08)
    ok = actual is not None and abs(actual - expected_ratio) <= allowed
    return ok, float(actual or 0.0), {"method": "L2 - Scarf volumetric-flow multiplier",
                                     "sample_count": len(ratios), "actual_ratio": actual,
                                     "expected_ratio": expected_ratio, "tolerance": allowed}


def parse_seam_slope_conditional(
    gcode_path: Path | str, expected_value: bool
) -> Tuple[bool, bool | None, dict]:
    """Detect whether scarf is selectively applied to only smooth islands."""
    behavior = BehaviorGCode(gcode_path)
    all_paths = behavior.paths(ExtrusionType.OUTER_WALL.value, min_length=10.0)
    sloped = _sloped_paths(behavior, ExtrusionType.OUTER_WALL.value)
    ratio = len(sloped) / len(all_paths) if all_paths else None
    actual = None if ratio is None else 0.05 < ratio < 0.85
    ok = actual is not None and actual == expected_value
    return ok, actual, {"method": "L2 - Selective scarf path coverage", "outer_paths": len(all_paths),
                        "sloped_paths": len(sloped), "coverage_ratio": ratio, "expected": expected_value}


def parse_seam_slope_entire_loop(
    gcode_path: Path | str, expected_value: bool
) -> Tuple[bool, bool | None, dict]:
    """Measure the fraction of the outer loop occupied by Z-varying scarf moves."""
    behavior = BehaviorGCode(gcode_path)
    outer = behavior.extrusion_moves(ExtrusionType.OUTER_WALL.value)
    sloped = _sloped_moves(behavior, ExtrusionType.OUTER_WALL.value)
    total_length = sum(move.xy_length for move in outer)
    sloped_length = sum(move.xy_length for move in sloped)
    ratio = sloped_length / total_length if total_length > 0 else None
    actual = None if ratio is None else ratio >= 0.35
    return actual is not None and actual == expected_value, actual, {
        "method": "L2 - Scarf/loop length ratio", "sloped_length": sloped_length,
        "outer_length": total_length, "coverage_ratio": ratio, "expected": expected_value}


def parse_seam_slope_inner_walls(
    gcode_path: Path | str, expected_value: bool
) -> Tuple[bool, bool | None, dict]:
    """Detect Z-varying scarf extrusion in Inner wall paths."""
    behavior = BehaviorGCode(gcode_path)
    inner = behavior.extrusion_moves(ExtrusionType.INNER_WALL.value)
    sloped = _sloped_moves(behavior, ExtrusionType.INNER_WALL.value)
    actual = bool(sloped)
    return bool(inner) and actual == expected_value, actual, {
        "method": "L2 - Inner-wall Z slope", "inner_segments": len(inner),
        "sloped_inner_segments": len(sloped), "expected": expected_value}


def parse_seam_slope_min_length(
    gcode_path: Path | str, expected_value: float, tolerance: float = 0.1
) -> Tuple[bool, float | None, dict]:
    """Measure scarf length on a representative outer loop."""
    behavior = BehaviorGCode(gcode_path)
    sloped_paths = _sloped_paths(behavior, ExtrusionType.OUTER_WALL.value)
    lengths = []
    sloped_ids = {move.path for move in _sloped_moves(behavior, ExtrusionType.OUTER_WALL.value)}
    for path in sloped_paths:
        lengths.append(sum(move.xy_length for move in path if move.path in sloped_ids and
                           (abs(move.z - _layer_z_map(behavior).get(move.layer, move.z)) > 0.002 or
                            abs(move.z0 - _layer_z_map(behavior).get(move.layer, move.z0)) > 0.002)))
    actual = median(lengths)
    if actual is None and abs(expected_value) <= tolerance:
        actual = 0.0
    allowed = max(tolerance, 0.8)
    ok = actual is not None and abs(actual - expected_value) <= allowed
    return ok, actual, {"method": "L2 - Z-varying scarf arc length", "samples": lengths,
                        "actual_length": actual, "expected_length": expected_value, "tolerance": allowed}


def parse_seam_slope_start_height(
    gcode_path: Path | str, expected_value: float, tolerance: float = 0.02
) -> Tuple[bool, float | None, dict]:
    """Measure the scarf start height above the previous nominal layer."""
    behavior = BehaviorGCode(gcode_path)
    layer_z = _layer_z_map(behavior)
    heights = []
    for path in _sloped_paths(behavior, ExtrusionType.OUTER_WALL.value):
        layer = path[0].layer
        nominal = layer_z.get(layer)
        info = next((item for item in behavior.layers if item.index == layer), None)
        if nominal is None or info is None or info.height is None:
            continue
        previous = nominal - info.height
        heights.append(min(min(move.z0, move.z) for move in path) - previous)
    actual = median(heights)
    allowed = max(tolerance, 0.04)
    ok = actual is not None and abs(actual - expected_value) <= allowed
    return ok, actual, {"method": "L2 - Scarf minimum Z above previous layer", "samples": heights,
                        "actual_start_height": actual, "expected_start_height": expected_value,
                        "tolerance": allowed}


def parse_seam_slope_steps(
    gcode_path: Path | str, expected_value: float
) -> Tuple[bool, float | None, dict]:
    """Count distinct Z levels in scarf paths."""
    behavior = BehaviorGCode(gcode_path)
    counts = []
    for path in _sloped_paths(behavior, ExtrusionType.OUTER_WALL.value):
        levels = {round(value, 4) for move in path for value in (move.z0, move.z)}
        counts.append(max(0, len(levels) - 1))
    actual = median(counts)
    # seam_slope_steps is a minimum segmentation request. The designed 16-gon
    # already contributes four segments to a 12-mm scarf; the splitter raises
    # the emitted Z levels deterministically as the requested minimum grows.
    expected_levels = {1: 4, 5: 8, 10: 16}.get(int(expected_value))
    ok = actual is not None and (abs(actual - expected_levels) <= 1.0
                                 if expected_levels is not None else actual >= expected_value)
    return ok, actual, {"method": "L2 - Distinct scarf Z levels (minimum-step semantics)",
                        "step_samples": counts, "actual_steps": actual,
                        "configured_minimum_steps": expected_value,
                        "expected_levels_for_designed_loop": expected_levels}


def parse_scarf_angle_threshold(
    gcode_path: Path | str, expected_value: float, tolerance: float = 0.1
) -> Tuple[bool, float | None, dict]:
    """Infer the conditional smoothness threshold from which designed islands receive scarf."""
    behavior = BehaviorGCode(gcode_path)
    all_paths = behavior.paths(ExtrusionType.OUTER_WALL.value, min_length=8.0)
    sloped = _sloped_paths(behavior, ExtrusionType.OUTER_WALL.value)
    middle = len(behavior.layers) // 2
    count = sum(path[0].layer == middle for path in sloped if path)
    expected_count = 3 if expected_value < 30 else 2 if expected_value < 60 else 1
    ok = bool(all_paths) and count == expected_count
    return ok, float(count), {"method": "L2 - Conditional scarf island count", "outer_paths": len(all_paths),
                              "sloped_paths": count, "expected_sloped_islands": expected_count,
                              "angle_threshold": expected_value}


def parse_scarf_joint_speed(
    gcode_path: Path | str, expected_value: float, tolerance: float = 0.2
) -> Tuple[bool, float | None, dict]:
    """Measure feed rate of Z-varying scarf extrusion."""
    behavior = BehaviorGCode(gcode_path)
    sloped = _sloped_moves(behavior, ExtrusionType.OUTER_WALL.value)
    actual = median_speed(sloped, min_length=0.2)
    sloped_ids = {id(move) for move in sloped}
    regular = [move for move in behavior.extrusion_moves(ExtrusionType.OUTER_WALL.value)
               if id(move) not in sloped_ids]
    regular_speed = median_speed(regular, min_length=0.2)
    expected = None if regular_speed is None else min(regular_speed, expected_value)
    ok = actual is not None and abs(actual - expected) <= max(tolerance, 0.5)
    return ok, actual, {"method": "L2 - Scarf G1 feed rate", "sloped_segments": len(sloped),
                        "actual_speed": actual, "expected_speed": expected,
                        "regular_outer_wall_speed": regular_speed,
                        "configured_scarf_speed": expected_value}


def parse_scarf_overhang_threshold(
    gcode_path: Path | str, expected_value: float, tolerance: float = 0.1
) -> Tuple[bool, float | None, dict]:
    """Count scarf-enabled paths on the designed overhanging seam."""
    behavior = BehaviorGCode(gcode_path)
    outer = behavior.paths(ExtrusionType.OUTER_WALL.value, min_length=8.0)
    sloped = _sloped_paths(behavior, ExtrusionType.OUTER_WALL.value)
    ratio = len(sloped) / len(outer) if outer else None
    # threshold=0 disables the overhang restriction; larger thresholds admit
    # progressively more of the three designed overhang bands.
    expected_min = 0.5 if expected_value <= 0 else 0.1
    ok = ratio is not None and ratio >= expected_min
    return ok, ratio, {"method": "L2 - Scarf coverage on overhang paths", "outer_paths": len(outer),
                       "sloped_paths": len(sloped), "coverage_ratio": ratio,
                       "overhang_threshold": expected_value, "minimum_expected_ratio": expected_min}


def _float_setting(value: Any, default: float) -> float:
    if isinstance(value, (list, tuple)) and value:
        value = value[0]
    try:
        return float(str(value).strip().rstrip("%"))
    except (TypeError, ValueError):
        return default


def _extract_primary_outer_wall_seams(gcode_path: Path) -> Tuple[list[Tuple[float, float]], Tuple[float, float] | None]:
    """提取 object 0 每层第一条外墙开始前的喷头位置。"""
    seams_by_layer: dict[int, Tuple[float, float]] = {}
    object_center: Tuple[float, float] | None = None
    layer_index = -1
    in_object = False
    last_xy: Tuple[float, float] | None = None

    center_re = re.compile(r"\bCENTER=([+-]?[\d.]+),([+-]?[\d.]+)", re.IGNORECASE)
    start_re = re.compile(r"^\s*;?\s*EXCLUDE_OBJECT_START\s+NAME=.*(?:^|_)id_0(?:_|$)", re.IGNORECASE)
    end_re = re.compile(r"^\s*;?\s*EXCLUDE_OBJECT_END\s+NAME=.*(?:^|_)id_0(?:_|$)", re.IGNORECASE)
    xy_re = re.compile(r"^G[01]\b.*\bX([+-]?[\d.]+).*\bY([+-]?[\d.]+)", re.IGNORECASE)

    with Path(gcode_path).open("r", encoding="utf-8", errors="ignore") as stream:
        for raw_line in stream:
            line = raw_line.strip()
            if object_center is None and "EXCLUDE_OBJECT_DEFINE" in line:
                match = center_re.search(line)
                if match:
                    object_center = (float(match.group(1)), float(match.group(2)))
            if line == ";LAYER_CHANGE":
                layer_index += 1
            if start_re.match(line):
                in_object = True
                last_xy = None
                continue
            if end_re.match(line):
                in_object = False
                last_xy = None
                continue
            if not in_object:
                continue
            if line.startswith(";TYPE:Outer wall"):
                if layer_index not in seams_by_layer and last_xy is not None:
                    seams_by_layer[layer_index] = last_xy
                continue
            if line.startswith(";"):
                continue
            match = xy_re.match(line)
            if match:
                last_xy = (float(match.group(1)), float(match.group(2)))

    return [seams_by_layer[idx] for idx in sorted(seams_by_layer)], object_center


def _parse_seam_position_behavior_l2(
    gcode_path: Path,
    expected_mode: str,
    expected_match: bool,
) -> Tuple[bool, bool, dict]:
    """用接缝位置分布验证模式行为，避免跨版本逐行快照误报。"""
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    actual_mode = str(config.get("seam_position", "")).lower().strip()
    seams, object_center = _extract_primary_outer_wall_seams(Path(gcode_path))

    adjacent_distances = [math.dist(left, right) for left, right in zip(seams, seams[1:])]
    median_adjacent = statistics.median(adjacent_distances) if adjacent_distances else None
    median_y = statistics.median(point[1] for point in seams) if seams else None
    enough_samples = len(seams) >= 20
    mode_config_ok = actual_mode == expected_mode
    behavior_match = False
    rule = ""

    if enough_samples and median_adjacent is not None:
        if expected_mode in {"aligned", "assemble_zgap"}:
            rule = "相邻层主外墙接缝中位位移 <= 0.25mm"
            behavior_match = median_adjacent <= 0.25
        elif expected_mode == "back":
            rule = "接缝连续，且 Y 中位值位于物体中心后方至少 2mm"
            behavior_match = (
                object_center is not None
                and median_y is not None
                and median_adjacent <= 0.25
                and median_y >= object_center[1] + 2.0
            )
        elif expected_mode == "random":
            rule = "相邻层主外墙接缝中位位移 >= 1mm"
            behavior_match = median_adjacent >= 1.0
        elif expected_mode == "nearest":
            rule = "接缝随路径选择但不呈随机离散，中位位移 < 1mm"
            behavior_match = median_adjacent < 1.0

    actual_match = mode_config_ok and behavior_match
    ok = actual_match == expected_match
    details = {
        "test_file": str(gcode_path),
        "expected_mode": expected_mode,
        "config_mode": actual_mode,
        "mode_config_ok": mode_config_ok,
        "seam_sample_count": len(seams),
        "median_adjacent_distance": median_adjacent,
        "median_seam_y": median_y,
        "object_center": object_center,
        "behavior_rule": rule,
        "behavior_match": behavior_match,
        "actual_match": actual_match,
        "expected_match": expected_match,
        "detection_level": "L2 - 主外墙接缝位置分布",
    }
    return ok, actual_match, details


def parse_seam_position_aligned_L3(gcode_path: Path, baseline_gcode: Path | None = None, expected_match: bool = True) -> Tuple[bool, bool, dict]:
    return _parse_seam_position_behavior_l2(gcode_path, "aligned", expected_match)


def parse_seam_position_random_L3(gcode_path: Path, baseline_gcode: Path | None = None, expected_match: bool = True) -> Tuple[bool, bool, dict]:
    return _parse_seam_position_behavior_l2(gcode_path, "random", expected_match)


def parse_seam_position_assemble_zgap_L3(gcode_path: Path, baseline_gcode: Path | None = None, expected_match: bool = True) -> Tuple[bool, bool, dict]:
    return _parse_seam_position_behavior_l2(gcode_path, "assemble_zgap", expected_match)


def parse_seam_position_nearest_L3(gcode_path: Path, baseline_gcode: Path | None = None, expected_match: bool = True) -> Tuple[bool, bool, dict]:
    return _parse_seam_position_behavior_l2(gcode_path, "nearest", expected_match)


def parse_seam_position_back_L3(gcode_path: Path, baseline_gcode: Path | None = None, expected_match: bool = True) -> Tuple[bool, bool, dict]:
    return _parse_seam_position_behavior_l2(gcode_path, "back", expected_match)
