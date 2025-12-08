"""
边缘 (Brim) 参数校验模块

包含以下参数的校验函数：
- brim_type: Level 1 配置读取
- brim_width: Level 1 配置读取
- brim_object_gap: Level 1 配置读取
- brim_ears_max_angle: Level 1 配置读取
- brim_ears_detection_length: Level 1 配置读取
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

from engine_params.src.gcode.GCodeParser import GCodeParser


def _normalize_to_float(val: object) -> float:
    """将配置值规范化为 float"""
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        return float(val)
    return 0.0


def _normalize_to_int(val: object) -> int:
    """将配置值规范化为 int"""
    if isinstance(val, (int, float)):
        return int(val)
    if isinstance(val, str):
        return int(float(val))
    return 0


# ================== brim_type ==================

def parse_brim_type(
        gcode_path: Path | str,
        expected_value: str,
) -> Tuple[bool, str, Dict[str, object]]:
    """
    解析 G-code，Level 1 配置对比 brim_type。
    
    校验逻辑（Level 1 配置对比）：
    直接从配置读取 brim_type。
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 brim_type 值

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
    
    # 直接读取 brim_type 配置
    config_value = cfg.get("brim_type")
    
    detected_value = str(config_value) if config_value else ""
    
    details: Dict[str, object] = {
        "gcode_path": str(gcode_path),
        "expected_value": expected_value,
        "config_value": config_value,
        "detected_value": detected_value,
        "detection_method": "Level 1 (配置对比)",
    }
    
    ok = detected_value == expected_value
    
    if ok:
        details["message"] = f"Level 1 通过: brim_type={detected_value}"
    else:
        details["message"] = f"Level 1 失败: expected={expected_value}, config={detected_value}"
    
    return ok, detected_value, details


# ================== brim_width ==================

def parse_brim_width(
        gcode_path: Path | str,
        expected_value: float,
) -> Tuple[bool, float, Dict[str, object]]:
    """
    解析 G-code，Level 1 配置对比 brim_width。
    
    校验逻辑（Level 1 配置对比）：
    直接从配置读取 brim_width。
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 brim_width 值（单位：mm）

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
    
    # 直接读取 brim_width 配置
    config_value = cfg.get("brim_width")
    
    detected_value = _normalize_to_float(config_value)
    
    details: Dict[str, object] = {
        "gcode_path": str(gcode_path),
        "expected_value": expected_value,
        "config_value": config_value,
        "detected_value": detected_value,
        "detection_method": "Level 1 (配置对比)",
    }
    
    # 浮点数比较，容差 0.1 mm
    ok = abs(detected_value - expected_value) < 0.1
    
    if ok:
        details["message"] = f"Level 1 通过: brim_width={detected_value} mm"
    else:
        details["message"] = f"Level 1 失败: expected={expected_value}mm, config={detected_value}mm"
    
    return ok, detected_value, details


# ================== brim_object_gap ==================

def parse_brim_object_gap(
        gcode_path: Path | str,
        expected_value: float,
) -> Tuple[bool, float, Dict[str, object]]:
    """
    解析 G-code，Level 1 配置对比 brim_object_gap。
    
    校验逻辑（Level 1 配置对比）：
    直接从配置读取 brim_object_gap。
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 brim_object_gap 值（单位：mm）

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
    
    # 直接读取 brim_object_gap 配置
    config_value = cfg.get("brim_object_gap")
    
    detected_value = _normalize_to_float(config_value)
    
    details: Dict[str, object] = {
        "gcode_path": str(gcode_path),
        "expected_value": expected_value,
        "config_value": config_value,
        "detected_value": detected_value,
        "detection_method": "Level 1 (配置对比)",
    }
    
    # 浮点数比较，容差 0.01 mm
    ok = abs(detected_value - expected_value) < 0.01
    
    if ok:
        details["message"] = f"Level 1 通过: brim_object_gap={detected_value} mm"
    else:
        details["message"] = f"Level 1 失败: expected={expected_value}mm, config={detected_value}mm"
    
    return ok, detected_value, details


# ================== brim_ears_max_angle ==================

def parse_brim_ears_max_angle(
        gcode_path: Path | str,
        expected_value: float,
) -> Tuple[bool, float, Dict[str, object]]:
    """
    解析 G-code，Level 1 配置对比 brim_ears_max_angle。
    
    校验逻辑（Level 1 配置对比）：
    直接从配置读取 brim_ears_max_angle。
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 brim_ears_max_angle 值（单位：度）

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
    
    # 直接读取 brim_ears_max_angle 配置
    config_value = cfg.get("brim_ears_max_angle")
    
    detected_value = _normalize_to_float(config_value)
    
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
        details["message"] = f"Level 1 通过: brim_ears_max_angle={detected_value}°"
    else:
        details["message"] = f"Level 1 失败: expected={expected_value}°, config={detected_value}°"
    
    return ok, detected_value, details


# ================== brim_ears_detection_length ==================

def parse_brim_ears_detection_length(
        gcode_path: Path | str,
        expected_value: float,
) -> Tuple[bool, float, Dict[str, object]]:
    """
    解析 G-code，Level 1 配置对比 brim_ears_detection_length。
    
    校验逻辑（Level 1 配置对比）：
    直接从配置读取 brim_ears_detection_length。
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 brim_ears_detection_length 值（单位：mm）

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
    
    # 直接读取 brim_ears_detection_length 配置
    config_value = cfg.get("brim_ears_detection_length")
    
    detected_value = _normalize_to_float(config_value)
    
    details: Dict[str, object] = {
        "gcode_path": str(gcode_path),
        "expected_value": expected_value,
        "config_value": config_value,
        "detected_value": detected_value,
        "detection_method": "Level 1 (配置对比)",
    }
    
    # 浮点数比较，容差 0.1 mm
    ok = abs(detected_value - expected_value) < 0.1
    
    if ok:
        details["message"] = f"Level 1 通过: brim_ears_detection_length={detected_value} mm"
    else:
        details["message"] = f"Level 1 失败: expected={expected_value}mm, config={detected_value}mm"
    
    return ok, detected_value, details
