#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Travel speed check module"""
from collections.abc import Mapping
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
    actual_config_speed: Optional[float]
    config_match: bool
    tolerance: float
    skipped_layers: List[int]
    checked_points: int
    actual_speed_values: List[float]
    invalid_points: List[InvalidPoint]
    note: Optional[str]


class TravelSpeedResult(TypedDict):
    passed: bool
    details: TravelSpeedDetails


def parse_travel_speed(parser: Any, expected_speed: float, tolerance: float = 0.0) -> TravelSpeedResult:
    """
    核对 CONFIG_BLOCK 的 travel_speed，并确认除首层外存在可解析的 travel 路径。
    ``get_motion_paths`` 返回 ``{layer_index: [Point3D, ...]}``；兼容测试替身
    使用的 mapping 点，同时要求至少检查到一个 travel 点。
    """
    skipped_layers = [0]
    invalid_points: List[InvalidPoint] = []

    cfg = parser.load_config() or {}
    config_value = cfg.get("travel_speed")
    try:
        actual_config_speed = float(getattr(config_value, "value", config_value))
    except (TypeError, ValueError):
        actual_config_speed = None
    config_match = (
        actual_config_speed is not None
        and abs(actual_config_speed - expected_speed) <= tolerance
    )

    layers = parser.get_motion_paths(skip_layers=skipped_layers)

    checked_points = 0
    actual_speed_values = set()
    for layer_idx, path in sorted(layers.items()):
        for point_idx, pt in enumerate(path):
            kind = pt.get("kind") if isinstance(pt, Mapping) else getattr(pt, "kind", None)
            if kind != "travel":
                continue
            checked_points += 1
            actual = pt.get("f") if isinstance(pt, Mapping) else getattr(pt, "f", None)
            if actual is None:
                invalid_points.append({
                    "layer_index": layer_idx,
                    "point_index": point_idx,
                    "expected_speed": expected_speed,
                    "actual_speed": float("nan"),
                    "tolerance": tolerance,
                    "error": "missing f",
                })
                continue

            actual = float(actual)
            actual_speed_values.add(actual)

    if actual_config_speed is None:
        note = "travel_speed missing or invalid in CONFIG_BLOCK."
    elif not config_match:
        note = "CONFIG_BLOCK travel_speed does not match the expected value."
    elif not checked_points:
        note = "No travel points found outside the first layer."
    else:
        note = None

    return {
        "passed": config_match and checked_points > 0 and not invalid_points,
        "details": {
            "expected_speed": expected_speed,
            "actual_config_speed": actual_config_speed,
            "config_match": config_match,
            "tolerance": tolerance,
            "skipped_layers": skipped_layers,
            "checked_points": checked_points,
            "actual_speed_values": sorted(actual_speed_values),
            "invalid_points": invalid_points,
            "note": note,
        },
    }
