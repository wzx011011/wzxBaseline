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
