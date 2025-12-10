#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Travel speed check module"""
from typing import Any, List, TypedDict, Optional

# ================== travel_speed ==================
class InvalidPoint(TypedDict):
    layer_index: int
    point_index: int
    expected_speed: float
    actual_speed: float
    tolerance: float
    error: Optional[str]


class TravelSpeedDetails(TypedDict):
    expected_speed: float
    tolerance: float
    skipped_layers: List[int]
    invalid_points: List[InvalidPoint]


class TravelSpeedResult(TypedDict):
    passed: bool
    details: TravelSpeedDetails


def parse_travel_speed(parser: Any, expected_speed: float, tolerance: float = 0.0) -> TravelSpeedResult:
    """
    检查除首层外所有层的 travel 路径速度是否在容差内。
    不做类型检查与异常捕获，默认 parser 数据合法。
    """
    skipped_layers = [0]
    invalid_points: List[InvalidPoint] = []

    layers = parser.get_motion_paths(skip_layers=skipped_layers)

    # enumerate 从 1 开始，让索引与真实层号匹配（因跳过了第 0 层）
    for layer_idx, path in enumerate(layers, start=1):
        for point_idx, pt in enumerate(path):
            if pt.get("kind") != "travel":
                continue
            if "f" not in pt:
                invalid_points.append({
                    "layer_index": layer_idx,
                    "point_index": point_idx,
                    "expected_speed": expected_speed,
                    "actual_speed": float("nan"),
                    "tolerance": tolerance,
                    "error": "missing f",
                })
                continue

            actual = pt["f"]  # 假设为数值
            if abs(actual - expected_speed) > tolerance:
                invalid_points.append({
                    "layer_index": layer_idx,
                    "point_index": point_idx,
                    "expected_speed": expected_speed,
                    "actual_speed": actual,
                    "tolerance": tolerance,
                    "error": None,
                })

    return {
        "passed": not invalid_points,
        "details": {
            "expected_speed": expected_speed,
            "tolerance": tolerance,
            "skipped_layers": skipped_layers,
            "invalid_points": invalid_points,
        },
    }
