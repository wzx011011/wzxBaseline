"""
Skirt 相关参数的 G-code 解析与校验模块

包含 skirt_type, skirt_loops, skirt_distance, skirt_height, skirt_speed, draft_shield 等参数的解析函数

Level 1 校验逻辑（配置对比）：
- skirt_loops: 读取配置中的 skirt_loops 值
- skirt_distance: 读取配置中的 skirt_distance 值
- skirt_height: 读取配置中的 skirt_height 值
- skirt_speed: 读取配置中的 initial_layer_speed 值

Level 2 校验逻辑（特征检测）：
- skirt_type: 检测 Skirt/Brim 类型路径的覆盖率
- draft_shield: 检测 draft_shield 的启用状态（与 skirt_type 密切相关）
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Tuple

from engine_params.src.gcode.GCodeParser import GCodeParser


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


def _normalize_to_int(value: object | None) -> int:
    """将配置值归一化为整数"""
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    try:
        return int(float(str(value).strip()))
    except ValueError:
        return 0


# ================== skirt_type ==================

def parse_skirt_type(
        gcode_path: Path | str,
        expected_value: str,
) -> Tuple[bool, str, Dict[str, object]]:
    """
    解析 G-code，Level 2 特征检测 skirt_type。
    
    校验逻辑（Level 1 配置对比）：
    skirt_type 控制裙边类型，Creality Print 的枚举值：
    - "combined": 组合模式（普通裙边）
    - "auto": 自动模式
    - 其他可能的值需要根据实际 G-code 确认
    
    检测方法：
    直接从配置读取 skirt_type 参数值
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 skirt_type 值 ("normal" 或 "shield")

    返回:
        Tuple[bool, str, Dict[str, object]]:
            - ok: 检测结果是否与期望一致
            - detected_value: 解析出的值
            - details: 详细信息字典
    """
    gcode_path = Path(gcode_path)
    
    # 读取配置
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    
    # 读取 skirt_type 配置
    config_value = cfg.get("skirt_type")
    detected_value = str(config_value).strip() if config_value else "combined"
    
    details: Dict[str, object] = {
        "gcode_path": str(gcode_path),
        "expected_value": expected_value,
        "config_value": config_value,
        "detected_value": detected_value,
        "detection_method": "Level 1 (配置对比)",
    }
    
    ok = (detected_value == expected_value)
    
    if ok:
        details["message"] = f"Level 1 通过: skirt_type={detected_value}"
    else:
        details["message"] = f"Level 1 失败: expected={expected_value}, config={detected_value}"
    
    return ok, detected_value, details


# ================== skirt_loops ==================

def parse_skirt_loops(
        gcode_path: Path | str,
        expected_value: int,
) -> Tuple[bool, int, Dict[str, object]]:
    """
    解析 G-code，Level 1 配置对比 skirt_loops。
    
    校验逻辑（Level 1 配置对比）：
    skirt_loops 控制裙边圈数，直接从配置读取。
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 skirt_loops 值

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
    config_value = cfg.get("skirt_loops")
    
    detected_value = _normalize_to_int(config_value)
    
    details: Dict[str, object] = {
        "gcode_path": str(gcode_path),
        "expected_value": expected_value,
        "config_value": config_value,
        "detected_value": detected_value,
        "detection_method": "Level 1 (配置对比)",
    }
    
    ok = (detected_value == expected_value)
    
    if ok:
        details["message"] = f"Level 1 通过: skirt_loops={detected_value}"
    else:
        details["message"] = f"Level 1 失败: expected={expected_value}, config={detected_value}"
    
    return ok, detected_value, details


# ================== skirt_distance ==================

def parse_skirt_distance(
        gcode_path: Path | str,
        expected_value: float,
) -> Tuple[bool, float, Dict[str, object]]:
    """
    解析 G-code，Level 1 配置对比 skirt_distance。
    
    校验逻辑（Level 1 配置对比）：
    skirt_distance 控制裙边与模型的距离（单位：mm），直接从配置读取。
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 skirt_distance 值（单位：mm）

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
    config_value = cfg.get("skirt_distance")
    
    detected_value = _normalize_to_float(config_value)
    
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
        details["message"] = f"Level 1 通过: skirt_distance={detected_value}mm"
    else:
        details["message"] = f"Level 1 失败: expected={expected_value}mm, config={detected_value}mm"
    
    return ok, detected_value, details


# ================== skirt_height ==================

def parse_skirt_height(
        gcode_path: Path | str,
        expected_value: int,
) -> Tuple[bool, int, Dict[str, object]]:
    """
    解析 G-code，Level 1 配置对比 skirt_height。
    
    校验逻辑（Level 1 配置对比）：
    skirt_height 控制裙边高度（层数），直接从配置读取。
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 skirt_height 值（层数）

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
    config_value = cfg.get("skirt_height")
    
    detected_value = _normalize_to_int(config_value)
    
    details: Dict[str, object] = {
        "gcode_path": str(gcode_path),
        "expected_value": expected_value,
        "config_value": config_value,
        "detected_value": detected_value,
        "detection_method": "Level 1 (配置对比)",
    }
    
    ok = (detected_value == expected_value)
    
    if ok:
        details["message"] = f"Level 1 通过: skirt_height={detected_value} 层"
    else:
        details["message"] = f"Level 1 失败: expected={expected_value} 层, config={detected_value} 层"
    
    return ok, detected_value, details


# ================== skirt_speed ==================

def parse_skirt_speed(
        gcode_path: Path | str,
        expected_value: float,
) -> Tuple[bool, float, Dict[str, object]]:
    """
    解析 G-code，Level 1 配置对比 skirt_speed。
    
    校验逻辑（Level 1 配置对比）：
    直接从配置读取 skirt_speed。
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 skirt_speed 值（单位：mm/s）

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
    
    # 直接读取 skirt_speed 配置
    config_value = cfg.get("skirt_speed")
    
    detected_value = _normalize_to_float(config_value)
    
    details: Dict[str, object] = {
        "gcode_path": str(gcode_path),
        "expected_value": expected_value,
        "config_value": config_value,
        "detected_value": detected_value,
        "detection_method": "Level 1 (配置对比)",
    }
    
    # 浮点数比较，容差 0.1 mm/s
    ok = abs(detected_value - expected_value) < 0.1
    
    if ok:
        details["message"] = f"Level 1 通过: skirt_speed={detected_value} mm/s"
    else:
        details["message"] = f"Level 1 失败: expected={expected_value} mm/s, config={detected_value} mm/s"
    
    return ok, detected_value, details


# ================== draft_shield ==================

def parse_draft_shield(
        gcode_path: Path | str,
        expected_value: str,
) -> Tuple[bool, str, Dict[str, object]]:
    """
    解析 G-code，Level 1 配置对比 draft_shield。
    
    校验逻辑（Level 1 配置对比）：
    draft_shield 控制挡板类型，Creality Print 的枚举值：
    - "disabled": 禁用挡板
    - "limited": 限制高度的挡板
    - "enabled": 全高度挡板
    
    直接从配置读取 draft_shield 值。
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 draft_shield 值 ("disabled"/"limited"/"enabled")

    返回:
        Tuple[bool, str, Dict[str, object]]:
            - ok: 检测结果是否与期望一致
            - detected_value: 解析出的值
            - details: 详细信息字典
    """
    gcode_path = Path(gcode_path)
    
    # 读取配置
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    
    # 读取 draft_shield 配置
    draft_shield_config = cfg.get("draft_shield", "disabled")
    
    # 归一化配置值
    detected_value = str(draft_shield_config).strip().lower()
    if detected_value not in ("disabled", "limited", "enabled"):
        detected_value = "disabled"  # 默认值
    
    details: Dict[str, object] = {
        "gcode_path": str(gcode_path),
        "expected_value": expected_value,
        "config_value": draft_shield_config,
        "detected_value": detected_value,
        "detection_method": "Level 1 (配置对比)",
    }
    
    ok = (detected_value == expected_value)
    
    if ok:
        details["message"] = f"Level 1 通过: draft_shield={detected_value}"
    else:
        details["message"] = f"Level 1 失败: expected={expected_value}, config={detected_value}"
    
    return ok, detected_value, details


# ================== min_skirt_length ==================

def parse_min_skirt_length(
        gcode_path: Path | str,
        expected_value: float,
) -> Tuple[bool, float, Dict[str, object]]:
    """
    解析 G-code，Level 1 配置对比 min_skirt_length。
    
    校验逻辑（Level 1 配置对比）：
    min_skirt_length 控制裙边的最小长度（单位：mm）。
    直接从配置读取 min_skirt_length。
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 min_skirt_length 值（单位：mm）

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
    
    # 读取 min_skirt_length 配置
    config_value = cfg.get("min_skirt_length")
    
    detected_value = _normalize_to_float(config_value)
    
    details: Dict[str, object] = {
        "gcode_path": str(gcode_path),
        "expected_value": expected_value,
        "config_value": config_value,
        "detected_value": detected_value,
        "detection_method": "Level 1 (配置对比)",
    }
    
    # 浮点数比较，容差 1 mm
    ok = abs(detected_value - expected_value) < 1.0
    
    if ok:
        details["message"] = f"Level 1 通过: min_skirt_length={detected_value} mm"
    else:
        details["message"] = f"Level 1 失败: expected={expected_value} mm, config={detected_value} mm"
    
    return ok, detected_value, details
