"""
互锁结构相关参数的G-code解析与校验模块

包含 interlocking_beam 等互锁相关参数的解析函数

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
