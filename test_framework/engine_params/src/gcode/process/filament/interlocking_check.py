"""
互锁结构相关参数的G-code解析与校验模块

包含 interlocking_beam、mmu_segmented_region_max_width 等互锁相关参数的解析函数

Level 2 校验逻辑（参考 multimaterial_others_validation_design.md 2.5节）：
1. 定位材料切换边界（通过换料命令 T0/T1/T2...）
2. 分析边界区域的路径交错模式
3. 测量交错深度和宽度
4. 与参数值进行对比

关键特征发现：
- 启用互锁时，墙体交替次数（Inner wall <-> Outer wall）显著增加
- 启用互锁时，Gap infill 数量大幅增加（互锁齿间的填充）
- 启用互锁时，G-code 总行数增加约 100%+
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Tuple

from engine_params.src.gcode.GCodeParser import GCodeParser


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


# ================== interlocking_beam ==================

def parse_interlocking_beam(
        gcode_path: Path | str,
        expected_value: bool,
) -> Tuple[bool, bool, Dict[str, object]]:
    """
    解析 G-code，Level 2 特征检测 interlocking_beam。
    
    校验逻辑（Level 2 特征检测）：
    检测多材料边界处的互锁路径模式。
    
    interlocking_beam 启用时的特征：
    1. 墙体交替次数（Inner wall <-> Outer wall）显著增加（约 +90%）
    2. Gap infill 数量大幅增加（互锁齿间的间隙填充）
    3. G-code 总行数增加（约 +100%）
    
    具体检测步骤：
    1. 检查是否为多材料打印（存在换料命令）
    2. 统计墙体交替次数（Inner wall ↔ Outer wall 的切换）
    3. 统计 Gap infill 出现次数
    4. 计算交替比率（墙体交替次数 / 换料次数）
    5. 根据比率阈值判断是否启用互锁
    
    对于单材料模型或无换料操作，回退到 Level 1 配置对比。
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 interlocking_beam 布尔值

    返回:
        Tuple[bool, bool, Dict[str, object]]:
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
    config_value = cfg.get("interlocking_beam")
    config_bool = _normalize_to_bool(config_value)
    
    # 读取相关参数
    interlocking_depth = cfg.get("interlocking_depth", 2)
    interlocking_beam_width = cfg.get("interlocking_beam_width", 0.8)
    interlocking_beam_layer_count = cfg.get("interlocking_beam_layer_count", 2)
    
    # 统计数据
    tool_changes: List[Tuple[int, int]] = []
    type_sequence: List[str] = []  # TYPE 序列
    type_counts: Dict[str, int] = {}  # 各 TYPE 出现次数
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
                type_sequence.append(current_type)
                type_counts[current_type] = type_counts.get(current_type, 0) + 1
    
    details: Dict[str, object] = {
        "gcode_path": str(gcode_path),
        "expected_value": expected_value,
        "config_value": config_value,
        "config_bool": config_bool,
        "total_lines": total_lines,
        "tool_changes_count": len(tool_changes),
        "interlocking_depth": interlocking_depth,
        "interlocking_beam_width": interlocking_beam_width,
        "interlocking_beam_layer_count": interlocking_beam_layer_count,
    }
    
    # 检查是否为多材料打印
    if len(tool_changes) == 0:
        # 非多材料模型，回退到 Level 1 配置对比
        detected_value = config_bool
        details["detection_method"] = "Level 1 (配置对比，非多材料模型)"
        details["detected_value"] = detected_value
        
        ok = (detected_value == expected_value)
        if ok:
            details["message"] = f"Level 1 通过: interlocking_beam={detected_value} (单材料模型，回退到配置对比)"
        else:
            details["message"] = f"Level 1 失败: expected={expected_value}, config={detected_value}"
        
        return ok, detected_value, details
    
    # Level 2 特征检测：分析墙体交替模式
    
    # 1. 统计墙体交替次数（Inner wall <-> Outer wall）
    wall_alternations = 0
    prev_wall_type = None
    for t in type_sequence:
        if t in ('Inner wall', 'Outer wall'):
            if prev_wall_type and prev_wall_type != t:
                wall_alternations += 1
            prev_wall_type = t
        elif t not in ('Gap infill',):  # Gap infill 通常在墙之间，不重置
            prev_wall_type = None
    
    # 2. 获取关键 TYPE 计数
    outer_wall_count = type_counts.get('Outer wall', 0)
    inner_wall_count = type_counts.get('Inner wall', 0)
    gap_infill_count = type_counts.get('Gap infill', 0)
    
    details["type_counts"] = type_counts
    details["wall_alternations"] = wall_alternations
    details["outer_wall_count"] = outer_wall_count
    details["inner_wall_count"] = inner_wall_count
    details["gap_infill_count"] = gap_infill_count
    
    # 3. 计算特征比率
    # 墙体交替比率 = 墙体交替次数 / 换料次数
    # 启用互锁时，该比率约为 3.8 (382/101)
    # 禁用互锁时，该比率约为 2.0 (198/101)
    alternation_ratio = wall_alternations / len(tool_changes) if tool_changes else 0
    details["alternation_ratio"] = alternation_ratio
    
    # Gap infill 比率 = Gap infill 次数 / 换料次数
    # 启用互锁时，该比率约为 2.3 (234/101)
    # 禁用互锁时，该比率约为 0.04 (4/101)
    gap_infill_ratio = gap_infill_count / len(tool_changes) if tool_changes else 0
    details["gap_infill_ratio"] = gap_infill_ratio
    
    details["detection_method"] = "Level 2 (特征检测)"
    
    # 4. 判定逻辑
    # 使用多个特征综合判断：
    # - 墙体交替比率 > 2.5 表示可能启用互锁
    # - Gap infill 比率 > 0.5 表示可能启用互锁
    # 
    # 阈值说明（基于实测数据）：
    # | 指标              | 启用互锁 | 禁用互锁 | 阈值  |
    # |-------------------|---------|---------|-------|
    # | alternation_ratio | ~3.8    | ~2.0    | 2.5   |
    # | gap_infill_ratio  | ~2.3    | ~0.04   | 0.5   |
    
    ALTERNATION_THRESHOLD = 2.5
    GAP_INFILL_THRESHOLD = 0.5
    
    # 综合判断：两个指标中有一个超过阈值即判定为启用
    feature_detected = (
        alternation_ratio > ALTERNATION_THRESHOLD or 
        gap_infill_ratio > GAP_INFILL_THRESHOLD
    )
    
    detected_value = feature_detected
    details["detected_value"] = detected_value
    details["thresholds"] = {
        "alternation_threshold": ALTERNATION_THRESHOLD,
        "gap_infill_threshold": GAP_INFILL_THRESHOLD,
    }
    details["feature_detected"] = feature_detected
    
    ok = (detected_value == expected_value)
    
    if ok:
        if feature_detected:
            details["message"] = (
                f"Level 2 通过: interlocking_beam={detected_value}, "
                f"墙体交替比率={alternation_ratio:.2f}>{ALTERNATION_THRESHOLD}, "
                f"Gap infill比率={gap_infill_ratio:.2f}>{GAP_INFILL_THRESHOLD}"
            )
        else:
            details["message"] = (
                f"Level 2 通过: interlocking_beam={detected_value}, "
                f"墙体交替比率={alternation_ratio:.2f}<={ALTERNATION_THRESHOLD}, "
                f"Gap infill比率={gap_infill_ratio:.2f}<={GAP_INFILL_THRESHOLD}"
            )
    else:
        details["message"] = (
            f"Level 2 失败: expected={expected_value}, detected={detected_value}, "
            f"墙体交替比率={alternation_ratio:.2f}, Gap infill比率={gap_infill_ratio:.2f}"
        )
    
    return ok, detected_value, details


# ================== interlocking_beam_width ==================

def parse_interlocking_beam_width(
        gcode_path: Path | str,
        expected_value: float,
) -> Tuple[bool, float, Dict[str, object]]:
    """
    解析 G-code，Level 1 配置对比 interlocking_beam_width。
    
    校验逻辑（Level 1 配置对比）：
    interlocking_beam_width 控制互锁梁的宽度（单位：mm）。
    该参数影响互锁结构的粗细，直接从配置读取。
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 interlocking_beam_width 值（单位：mm）

    返回:
        Tuple[bool, float, Dict[str, object]]:
            - ok: 检测结果是否与期望一致
            - detected_value: 解析出的值
            - details: 详细信息字典
    """
    gcode_path = Path(gcode_path)
    
    # 读取配置
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    config_value = cfg.get("interlocking_beam_width")

    # 归一化为浮点数（配置主导）
    if config_value is None:
        config_float = 0.8  # 默认值
    elif isinstance(config_value, (int, float)):
        config_float = float(config_value)
    else:
        try:
            config_float = float(str(config_value).strip())
        except ValueError:
            config_float = 0.8

    detected_value = config_float

    details: Dict[str, object] = {
        "gcode_path": str(gcode_path),
        "expected_value": expected_value,
        "config_value": config_value,
        "config_float": config_float,
        "detected_value": detected_value,
        "detection_method": "Level 1 (配置对比)",
    }

    # ------------------ Level 2 保守检测（估算并输出诊断） ------------------
    # 我们不会在保守模式下改变最终的 ok 判定（仍以配置为主），但会输出检测估算结果，
    # 便于后续调优与人为判断是否需要升级为严格模式。

    # 读取 TYPE 标记以做简单的统计：
    type_pattern = re.compile(r'^;TYPE:(.+)$')
    type_sequence: List[str] = []
    type_counts: Dict[str, int] = {}
    with open(gcode_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            m = type_pattern.match(line.strip())
            if m:
                t = m.group(1)
                type_sequence.append(t)
                type_counts[t] = type_counts.get(t, 0) + 1

    outer_wall_count = type_counts.get('Outer wall', 0)
    inner_wall_count = type_counts.get('Inner wall', 0)
    gap_infill_count = type_counts.get('Gap infill', 0)

    details.update({
        "type_counts": type_counts,
        "outer_wall_count": outer_wall_count,
        "inner_wall_count": inner_wall_count,
        "gap_infill_count": gap_infill_count,
    })

    # 尝试从配置读取线宽作为换算基准（若不存在，使用 0.42mm）
    line_width = _normalize_to_float(cfg.get('line_width') or cfg.get('inner_wall_line_width') or 0.42)
    details["line_width_used"] = line_width

    # 基本估算：以每个 Gap infill 对应的墙体循环数乘以线宽估算梁宽
    # 将 TYPE 序列按 'Gap infill' 切分为若干段，统计每段内的 wall loop 数
    segments: List[List[str]] = []
    current: List[str] = []
    for t in type_sequence:
        if t == 'Gap infill':
            # 将当前段（不含 Gap）收集并重置
            segments.append(current)
            current = []
        else:
            current.append(t)
    # 最后一个段也收集
    if current:
        segments.append(current)

    wall_counts_per_segment: List[int] = []
    for seg in segments:
        cnt = sum(1 for x in seg if x in ('Inner wall', 'Outer wall'))
        if cnt > 0:
            wall_counts_per_segment.append(cnt)

    # 计算统计量
    if wall_counts_per_segment:
        mean_loops = sum(wall_counts_per_segment) / len(wall_counts_per_segment)
        # 计算一致性：有多少段的循环数在 mean_loops +/- 1 之内
        within = sum(1 for v in wall_counts_per_segment if abs(v - mean_loops) <= 1)
        consistency_score = within / len(wall_counts_per_segment)
    else:
        mean_loops = 0.0
        consistency_score = 0.0

    # 估算宽度
    estimated_width = mean_loops * line_width

    # 简单规则判定 feature_confirmed：当一致性高且估算宽度为正时确认
    FEATURE_CONSISTENCY_THRESHOLD = 0.7
    FEATURE_MIN_WIDTH = 0.1
    feature_confirmed = (consistency_score >= FEATURE_CONSISTENCY_THRESHOLD and estimated_width >= FEATURE_MIN_WIDTH)

    details.update({
        "mean_wall_loops_per_gap": mean_loops,
        "wall_counts_per_segment": wall_counts_per_segment,
        "consistency_score": consistency_score,
        "estimated_width": estimated_width,
        "feature_confirmed": feature_confirmed,
        "feature_checks": {
            "consistency_threshold": FEATURE_CONSISTENCY_THRESHOLD,
            "min_estimated_width": FEATURE_MIN_WIDTH,
        }
    })

    # 保守模式：ok 仍以配置为准（保持兼容性），但在 details 中提供 Level 2 诊断信息
    details["detection_method"] = "Level 1 (配置对比) + Level 2 (保守诊断)"
    ok = abs(detected_value - expected_value) < 0.01

    if ok:
        details["message"] = (
            f"配置匹配: interlocking_beam_width={detected_value}mm; "
            f"L2估算: estimated_width={estimated_width:.3f}mm, consistency={consistency_score:.2f}, confirmed={feature_confirmed}"
        )
    else:
        details["message"] = (
            f"配置不匹配: expected={expected_value}mm, config={detected_value}mm; "
            f"L2估算: estimated_width={estimated_width:.3f}mm, consistency={consistency_score:.2f}, confirmed={feature_confirmed}"
        )

    return ok, detected_value, details


# ================== interlocking_orientation ==================

def parse_interlocking_orientation(
        gcode_path: Path | str,
        expected_value: float,
) -> Tuple[bool, float, Dict[str, object]]:
    """
    解析 G-code，Level 1 配置对比 interlocking_orientation。
    
    校验逻辑（Level 1 配置对比）：
    interlocking_orientation 控制互锁方向角度（单位：度）。
    该参数影响互锁齿的方向，直接从配置读取。
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 interlocking_orientation 值（单位：度）

    返回:
        Tuple[bool, float, Dict[str, object]]:
            - ok: 检测结果是否与期望一致
            - detected_value: 解析出的值
            - details: 详细信息字典
    """
    gcode_path = Path(gcode_path)
    
    # 读取配置
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    config_value = cfg.get("interlocking_orientation")
    
    # 归一化为浮点数
    if config_value is None:
        config_float = 0.0  # 默认值
    elif isinstance(config_value, (int, float)):
        config_float = float(config_value)
    else:
        try:
            config_float = float(str(config_value).strip())
        except ValueError:
            config_float = 0.0
    
    detected_value = config_float
    
    details: Dict[str, object] = {
        "gcode_path": str(gcode_path),
        "expected_value": expected_value,
        "config_value": config_value,
        "detected_value": detected_value,
        "detection_method": "Level 1 (配置对比)",
    }
    
    # 浮点数比较，容差 0.1 度
    ok = abs(detected_value - expected_value) < 0.1
    
    if ok:
        details["message"] = f"Level 1 通过: interlocking_orientation={detected_value}°"
    else:
        details["message"] = f"Level 1 失败: expected={expected_value}°, config={detected_value}°"
    
    return ok, detected_value, details


# ================== interlocking_beam_layer_count ==================

def parse_interlocking_beam_layer_count(
        gcode_path: Path | str,
        expected_value: int,
) -> Tuple[bool, int, Dict[str, object]]:
    """
    解析 G-code，Level 1 配置对比 interlocking_beam_layer_count。
    
    校验逻辑（Level 1 配置对比）：
    interlocking_beam_layer_count 控制互锁梁的层数。
    该参数影响互锁结构的高度，直接从配置读取。
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 interlocking_beam_layer_count 值

    返回:
        Tuple[bool, int, Dict[str, object]]:
            - ok: 检测结果是否与期望一致
            - detected_value: 解析出的值
            - details: 详细信息字典
    """
    gcode_path = Path(gcode_path)
    
    # 读取配置
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    config_value = cfg.get("interlocking_beam_layer_count")
    
    # 归一化为整数
    if config_value is None:
        config_int = 2  # 默认值
    elif isinstance(config_value, int):
        config_int = config_value
    elif isinstance(config_value, float):
        config_int = int(config_value)
    else:
        try:
            config_int = int(float(str(config_value).strip()))
        except ValueError:
            config_int = 2
    
    detected_value = config_int
    
    details: Dict[str, object] = {
        "gcode_path": str(gcode_path),
        "expected_value": expected_value,
        "config_value": config_value,
        "detected_value": detected_value,
        "detection_method": "Level 1 (配置对比)",
    }
    
    # 整数精确匹配
    ok = (detected_value == expected_value)
    
    if ok:
        details["message"] = f"Level 1 通过: interlocking_beam_layer_count={detected_value}"
    else:
        details["message"] = f"Level 1 失败: expected={expected_value}, config={detected_value}"
    
    return ok, detected_value, details


# ================== interlocking_depth ==================

def parse_interlocking_depth(
        gcode_path: Path | str,
        expected_value: float,
) -> Tuple[bool, float, Dict[str, object]]:
    """
    解析 G-code，Level 1 配置对比 interlocking_depth。
    
    校验逻辑（Level 1 配置对比）：
    interlocking_depth 控制互锁深度（单位：mm）。
    该参数影响互锁齿嵌入的深度，直接从配置读取。
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 interlocking_depth 值（单位：mm）

    返回:
        Tuple[bool, float, Dict[str, object]]:
            - ok: 检测结果是否与期望一致
            - detected_value: 解析出的值
            - details: 详细信息字典
    """
    gcode_path = Path(gcode_path)
    
    # 读取配置
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    config_value = cfg.get("interlocking_depth")
    
    # 归一化为浮点数
    if config_value is None:
        config_float = 2.0  # 默认值
    elif isinstance(config_value, (int, float)):
        config_float = float(config_value)
    else:
        try:
            config_float = float(str(config_value).strip())
        except ValueError:
            config_float = 2.0
    
    detected_value = config_float
    
    details: Dict[str, object] = {
        "gcode_path": str(gcode_path),
        "expected_value": expected_value,
        "config_value": config_value,
        "detected_value": detected_value,
        "detection_method": "Level 1 (配置对比)",
    }
    
    # 浮点数比较，容差 0.01mm
    ok = abs(detected_value - expected_value) < 0.01
    
    if ok:
        details["message"] = f"Level 1 通过: interlocking_depth={detected_value}mm"
    else:
        details["message"] = f"Level 1 失败: expected={expected_value}mm, config={detected_value}mm"
    
    return ok, detected_value, details


# ================== interlocking_boundary_avoidance ==================

def parse_interlocking_boundary_avoidance(
        gcode_path: Path | str,
        expected_value: float,
) -> Tuple[bool, float, Dict[str, object]]:
    """
    解析 G-code，Level 1 配置对比 interlocking_boundary_avoidance。
    
    校验逻辑（Level 1 配置对比）：
    interlocking_boundary_avoidance 控制边界避让距离（单位：mm）。
    该参数影响互锁齿与边界的距离，直接从配置读取。
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 interlocking_boundary_avoidance 值（单位：mm）

    返回:
        Tuple[bool, float, Dict[str, object]]:
            - ok: 检测结果是否与期望一致
            - detected_value: 解析出的值
            - details: 详细信息字典
    """
    gcode_path = Path(gcode_path)
    
    # 读取配置
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    config_value = cfg.get("interlocking_boundary_avoidance")
    
    # 归一化为浮点数
    if config_value is None:
        config_float = 0.0  # 默认值
    elif isinstance(config_value, (int, float)):
        config_float = float(config_value)
    else:
        try:
            config_float = float(str(config_value).strip())
        except ValueError:
            config_float = 0.0
    
    detected_value = config_float
    
    details: Dict[str, object] = {
        "gcode_path": str(gcode_path),
        "expected_value": expected_value,
        "config_value": config_value,
        "detected_value": detected_value,
        "detection_method": "Level 1 (配置对比)",
    }
    
    # 浮点数比较，容差 0.01mm
    ok = abs(detected_value - expected_value) < 0.01
    
    if ok:
        details["message"] = f"Level 1 通过: interlocking_boundary_avoidance={detected_value}mm"
    else:
        details["message"] = f"Level 1 失败: expected={expected_value}mm, config={detected_value}mm"
    
    return ok, detected_value, details


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

    ok = abs(detected_value - expected_value) < 0.01

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
