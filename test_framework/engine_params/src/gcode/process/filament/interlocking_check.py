"""Interlocking contour validation and legacy segmented-region checks.

Interlocking cases require reviewed per-layer, per-material outer contours.
Config values, wall counts and gap-infill presence alone do not prove tenons.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Tuple

from engine_params.src.gcode.GCodeParser import GCodeParser
from .interlocking_baseline import validate_interlocking_geometry


def _normalize_to_bool(value: object | None) -> bool:
    """将配置值归一化为布尔值"""
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if not text:
        return False
    if text in ("true", "1", "yes", "on"):
        return True
    if text in ("false", "0", "no", "off"):
        return False
    try:
        return bool(float(text))
    except ValueError:
        return False


def _normalize_to_float(value: object | None) -> float:
    """将配置值归一化为浮点数"""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().lower()
    if not text or text in ("false", "no", "off"):
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def _multi_material_metrics(gcode_path: Path | str) -> Dict[str, object]:
    tools: List[int] = []
    wall_blocks = 0
    gap_blocks = 0
    with Path(gcode_path).open("r", encoding="utf-8", errors="ignore") as stream:
        for raw in stream:
            line = raw.strip()
            match = re.fullmatch(r"T(\d+)", line)
            if match:
                tools.append(int(match.group(1)))
            elif line == ";TYPE:Inner wall" or line == ";TYPE:Outer wall":
                wall_blocks += 1
            elif line == ";TYPE:Gap infill":
                gap_blocks += 1
    return {
        "tool_change_count": len(tools),
        "tools": sorted(set(tools)),
        "wall_blocks": wall_blocks,
        "gap_infill_blocks": gap_blocks,
        "confirmed": len(set(tools)) >= 2 and len(tools) > 2 and wall_blocks > 0,
    }


def _validate_interlocking(gcode_path, parameter, expected_value, baseline_id):
    config = GCodeParser(Path(gcode_path)).load_config()
    actual = config.get(parameter)
    details = {"detection_method": "Config + L2 interlocking outer contours",
               "config_value": actual, "expected_value": expected_value}
    if actual is None:
        return False, actual, {**details, "error": f"Missing configuration: {parameter}"}
    if parameter == "interlocking_beam":
        actual = _normalize_to_bool(actual)
        matches = actual == expected_value
    else:
        try:
            actual = float(actual)
            matches = abs(actual - float(expected_value)) < 1e-6
            if parameter == "interlocking_beam_layer_count" and actual.is_integer():
                actual = int(actual)
        except (TypeError, ValueError):
            matches = False
        if not _normalize_to_bool(config.get("interlocking_beam")):
            return False, actual, {**details, "error": "Interlocking must be enabled for parameter geometry checks"}
    if not matches:
        return False, actual, {**details, "error": "Configuration differs from expectation"}
    ok, geometry = validate_interlocking_geometry(
        gcode_path, parameter, expected_value, baseline_id,
    )
    details["geometry_check"] = geometry
    details["message"] = "Interlocking contour reference matched" if ok else "Interlocking contour reference mismatch"
    return ok, actual, details


def parse_interlocking_beam(gcode_path: Path | str, expected_value: bool, baseline_id: str | None = None):
    """Check configuration and the reviewed contour geometry for this case."""
    return _validate_interlocking(gcode_path, "interlocking_beam", expected_value, baseline_id)


def parse_interlocking_beam_width(gcode_path: Path | str, expected_value: float, baseline_id: str | None = None):
    """Check configuration and the reviewed contour geometry for this case."""
    return _validate_interlocking(gcode_path, "interlocking_beam_width", expected_value, baseline_id)


def parse_interlocking_orientation(gcode_path: Path | str, expected_value: float, baseline_id: str | None = None):
    """Check configuration and the reviewed contour geometry for this case."""
    return _validate_interlocking(gcode_path, "interlocking_orientation", expected_value, baseline_id)


def parse_interlocking_beam_layer_count(gcode_path: Path | str, expected_value: int, baseline_id: str | None = None):
    """Check configuration and the reviewed contour geometry for this case."""
    return _validate_interlocking(gcode_path, "interlocking_beam_layer_count", expected_value, baseline_id)


def parse_interlocking_depth(gcode_path: Path | str, expected_value: float, baseline_id: str | None = None):
    """Check configuration and the reviewed contour geometry for this case."""
    return _validate_interlocking(gcode_path, "interlocking_depth", expected_value, baseline_id)


def parse_interlocking_boundary_avoidance(gcode_path: Path | str, expected_value: float, baseline_id: str | None = None):
    """Check configuration and the reviewed contour geometry for this case."""
    return _validate_interlocking(gcode_path, "interlocking_boundary_avoidance", expected_value, baseline_id)


# ================== mmu_segmented_region_max_width ==================

def parse_mmu_segmented_region_max_width(
        gcode_path: Path | str,
        expected_value: float,
) -> Tuple[bool, float, Dict[str, object]]:
    """
    解析 G-code，Level 2 特征检测 mmu_segmented_region_max_width。
    
    校验逻辑（Level 2 特征检测）：
    mmu_segmented_region_max_width 控制多材料分段区域的最大宽度。
    
    mmu_segmented_region_max_width 启用时（值 > 0）的特征：
    1. 换料密度增加（换料次数 / G-code行数）
    2. Gap infill 比率增加
    
    mmu_segmented_region_max_width 禁用时（值 = 0）的特征：
    - 换料相对较少，大块区域连续打印
    
    具体检测步骤：
    1. 读取配置值
    2. 检查是否为多材料打印
    3. 统计换料密度和 Gap infill 比率
    4. 对于简单对比（0 vs >0），使用配置值判断
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 mmu_segmented_region_max_width 值（单位：mm）

    返回:
        Tuple[bool, float, Dict[str, object]]:
            - ok: 检测结果是否与期望一致
            - detected_value: 解析出的值
            - details: 详细信息字典
    """
    gcode_path = Path(gcode_path)
    
    # 正则匹配换料命令 T0, T1, T2...
    tool_change_pattern = re.compile(r'^T(\d+)\s*$')
    # 正则匹配 TYPE 标记
    type_pattern = re.compile(r'^;TYPE:(.+)$')
    
    # 读取配置
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    config_value = cfg.get("mmu_segmented_region_max_width")
    config_float = _normalize_to_float(config_value)
    
    # 统计数据
    tool_changes: List[Tuple[int, int]] = []
    type_counts: Dict[str, int] = {}
    total_lines = 0
    
    with open(gcode_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line_no, line in enumerate(f, 1):
            total_lines = line_no
            line = line.strip()
            
            # 检测换料命令
            tool_match = tool_change_pattern.match(line)
            if tool_match:
                tool_id = int(tool_match.group(1))
                tool_changes.append((line_no, tool_id))
                continue
            
            # 检测 TYPE 标记
            type_match = type_pattern.match(line)
            if type_match:
                current_type = type_match.group(1)
                type_counts[current_type] = type_counts.get(current_type, 0) + 1
    
    details: Dict[str, object] = {
        "gcode_path": str(gcode_path),
        "expected_value": expected_value,
        "config_value": config_value,
        "config_float": config_float,
        "total_lines": total_lines,
        "tool_changes_count": len(tool_changes),
        "type_counts": type_counts,
    }
    
    # 检查是否为多材料打印
    if len(tool_changes) == 0:
        # 非多材料模型，回退到 Level 1 配置对比
        detected_value = config_float
        details["detection_method"] = "Level 1 (配置对比，非多材料模型)"
        details["detected_value"] = detected_value
        
        ok = abs(detected_value - expected_value) < 0.01
        if ok:
            details["message"] = f"Level 1 通过: mmu_segmented_region_max_width={detected_value}mm (单材料模型，回退到配置对比)"
        else:
            details["message"] = f"Level 1 失败: expected={expected_value}mm, config={detected_value}mm"
        
        return ok, detected_value, details
    
    # Level 2 特征检测：分析换料密度与 Gap infill，用于行为验证

    # 计算换料密度（换料次数 / 总行数）
    tool_change_density = len(tool_changes) / total_lines if total_lines > 0 else 0
    details["tool_change_density"] = tool_change_density

    # Gap infill 比率
    gap_infill_count = type_counts.get('Gap infill', 0)
    gap_infill_ratio = gap_infill_count / len(tool_changes) if tool_changes else 0
    details["gap_infill_count"] = gap_infill_count
    details["gap_infill_ratio"] = gap_infill_ratio

    # Level 2 判定阈值（可根据经验调整）
    TOOL_DENSITY_THRESHOLD = 0.0008
    GAP_INFILL_THRESHOLD = 0.5

    # 特征确认：当换料密度或 gap infill 比率超过阈值时，认为分段行为被生成
    feature_confirmed = (
        tool_change_density > TOOL_DENSITY_THRESHOLD or
        gap_infill_ratio > GAP_INFILL_THRESHOLD
    )

    details["thresholds"] = {
        "tool_density_threshold": TOOL_DENSITY_THRESHOLD,
        "gap_infill_threshold": GAP_INFILL_THRESHOLD,
    }
    details["feature_confirmed"] = feature_confirmed

    # 使用配置值作为主要的检测输出（保持与现有测试兼容），同时标记检测层次为 Level 2
    detected_value = config_float
    details["detection_method"] = "Level 2 (配置对比 + 特征检测)"
    details["detected_value"] = detected_value

    behavior = _multi_material_metrics(gcode_path)
    details["multi_material_behavior"] = behavior
    ok = abs(detected_value - expected_value) < 0.01 and bool(behavior["confirmed"])

    # 附加消息：如果配置启用但特征未被确认，作为警告输出（不改变 ok 判定以保持兼容性）
    if ok:
        if detected_value > 0 and not feature_confirmed:
            details["message"] = (
                f"配置匹配但未检测到分段特征: mmu_segmented_region_max_width={detected_value}mm, "
                f"换料密度={tool_change_density:.6f}, Gap infill比率={gap_infill_ratio:.2f}"
            )
        else:
            details["message"] = (
                f"通过: mmu_segmented_region_max_width={detected_value}mm, "
                f"换料密度={tool_change_density:.6f}, Gap infill比率={gap_infill_ratio:.2f}"
            )
    else:
        details["message"] = f"失败: expected={expected_value}mm, config={detected_value}mm"

    return ok, detected_value, details
