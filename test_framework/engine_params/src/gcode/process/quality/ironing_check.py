"""
Ironing（熨烫）参数的 G-code 校验逻辑 - 新增 L1 校验函数
参数: ironing_type, ironing_pattern, ironing_flow, ironing_spacing, ironing_speed, ironing_angle
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

from engine_params.src.gcode.GCodeParser import GCodeParser
from engine_params.src.gcode.process.quality.ironing_type_check import (
    parse_ironing_type as _parse_ironing_type_l2_impl,
)
from engine_params.src.gcode.constants import ExtrusionType
from engine_params.src.gcode.process.quality.behavior import (
    BehaviorGCode,
    circular_distance_180,
    dominant_angle,
    median,
    median_height,
    median_speed,
    median_width,
    nearest_distances,
)


# ============= G-code behavior checks =============

def parse_ironing_type_l1(
    gcode_path: Path | str,
    expected_value: str
) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """Validate which surface layers actually contain Ironing extrusion."""
    behavior = BehaviorGCode(gcode_path)
    ironing_layers = behavior.role_layers(ExtrusionType.IRONING.value)
    top_layers = behavior.role_layers(ExtrusionType.TOP_SURFACE.value)
    expected = str(expected_value).strip().lower()
    if "no" in expected:
        ok = not ironing_layers
        inferred = "no ironing" if ok else "unexpected ironing"
    elif "solid" in expected:
        non_top = ironing_layers - top_layers
        ok = bool(ironing_layers) and bool(non_top)
        inferred = "solid" if ok else "top"
    else:
        ok = bool(ironing_layers) and ironing_layers <= top_layers
        inferred = "top" if ok else "solid"
    return ok, inferred, {
        "method": "L2 - Ironing layer coverage", "ironing_layers": sorted(ironing_layers),
        "top_surface_layers": sorted(top_layers), "expected": expected,
    }


def parse_ironing_pattern(
    gcode_path: Path | str,
    expected_value: str
) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """Classify Ironing geometry as parallel zig-zag or concentric loops."""
    behavior = BehaviorGCode(gcode_path)
    paths = behavior.paths(ExtrusionType.IRONING.value, min_length=1.0)
    closed = 0
    for path in paths:
        if path and ((path[-1].x - path[0].x0) ** 2 + (path[-1].y - path[0].y0) ** 2) ** 0.5 <= 0.3:
            closed += 1
    closed_ratio = closed / len(paths) if paths else 0.0
    inferred = "concentric" if closed_ratio >= 0.5 else "zig-zag"
    expected = str(expected_value).strip().lower()
    aliases = {"rectilinear": "zig-zag", "zigzag": "zig-zag"}
    expected = aliases.get(expected, expected)
    return bool(paths) and inferred == expected, inferred, {
        "method": "L2 - Ironing path topology", "path_count": len(paths),
        "closed_paths": closed, "closed_ratio": closed_ratio, "expected": expected,
    }


def parse_ironing_flow(
    gcode_path: Path | str,
    expected_value: str
) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """Infer Ironing flow from emitted bead area divided by swept line area."""
    behavior = BehaviorGCode(gcode_path)
    moves = behavior.extrusion_moves(ExtrusionType.IRONING.value)
    ironing_height = median_height(moves)
    ironing_width = median_width(moves)
    normal_heights = [layer.height for layer in behavior.layers if layer.height and layer.height > 0]
    layer_height = median(normal_heights)
    long_moves = [move for move in moves if move.xy_length >= 2.0]
    angle = dominant_angle(long_moves, min_length=2.0)
    spacing = None
    if angle is not None:
        normal = math.radians(angle + 90.0)
        offsets = [
            ((move.x0 + move.x) / 2.0) * math.cos(normal)
            + ((move.y0 + move.y) / 2.0) * math.sin(normal)
            for move in long_moves
        ]
        spacing = median([gap for gap in nearest_distances(offsets) if 0.02 <= gap <= 1.0])
    inferred = None
    if (ironing_height is not None and ironing_width is not None
            and layer_height is not None and spacing is not None and layer_height * spacing > 0):
        bead_area = (ironing_height * (ironing_width - ironing_height)
                     + math.pi * ironing_height * ironing_height / 4.0)
        inferred = 100.0 * bead_area / (layer_height * spacing)
    expected = _percent(expected_value)
    ok = inferred is not None and expected is not None and abs(inferred - expected) <= 1.0
    return ok, None if inferred is None else f"{inferred:.2f}%", {
        "method": "L2 - Ironing bead-area/swept-area ratio",
        "ironing_height": ironing_height, "ironing_width": ironing_width,
        "actual_line_spacing": spacing, "nominal_layer_height": layer_height,
        "inferred_percent": inferred, "expected_percent": expected,
    }


def parse_ironing_spacing(
    gcode_path: Path | str,
    expected_value: float,
    tolerance: float = 0.01
) -> Tuple[bool, Optional[float], Dict[str, Any]]:
    """Measure perpendicular distance between adjacent long Ironing lines."""
    behavior = BehaviorGCode(gcode_path)
    moves = [m for m in behavior.extrusion_moves(ExtrusionType.IRONING.value) if m.xy_length >= 2]
    angle = dominant_angle(moves, min_length=2)
    spacing = None
    if angle is not None:
        normal = math.radians(angle + 90)
        offsets = [((m.x0 + m.x) / 2) * math.cos(normal) + ((m.y0 + m.y) / 2) * math.sin(normal) for m in moves]
        gaps = [gap for gap in nearest_distances(offsets) if 0.02 <= gap <= 1.0]
        spacing = median(gaps)
    ok = spacing is not None and abs(spacing - expected_value) <= max(tolerance, 0.02)
    return ok, spacing, {"method": "L2 - Ironing line spacing", "line_count": len(moves),
                         "dominant_angle": angle, "actual_spacing": spacing, "expected_spacing": expected_value}


def parse_ironing_speed(
    gcode_path: Path | str,
    expected_value: float,
    tolerance: float = 0.1
) -> Tuple[bool, Optional[float], Dict[str, Any]]:
    """Read feed rate from long Ironing extrusion moves."""
    behavior = BehaviorGCode(gcode_path)
    moves = behavior.extrusion_moves(ExtrusionType.IRONING.value)
    actual = median_speed(moves, min_length=2.0)
    ok = actual is not None and abs(actual - expected_value) <= max(tolerance, 0.2)
    return ok, actual, {"method": "L2 - Ironing G1 feed rate", "segments": len(moves),
                        "actual_speed_mm_s": actual, "expected_speed_mm_s": expected_value}


def parse_ironing_angle(
    gcode_path: Path | str,
    expected_value: float,
    tolerance: float = 0.1
) -> Tuple[bool, Optional[float], Dict[str, Any]]:
    """Infer Ironing angle from long extrusion vectors."""
    behavior = BehaviorGCode(gcode_path)
    moves = behavior.extrusion_moves(ExtrusionType.IRONING.value)
    actual = dominant_angle(moves, min_length=2.0)
    diff = None if actual is None else min(
        circular_distance_180(actual, expected_value),
        # Fill generators may express the line normal instead of line axis.
        circular_distance_180(actual, expected_value + 90.0),
    )
    ok = diff is not None and diff <= max(tolerance, 2.0)
    return ok, actual, {"method": "L2 - Ironing path direction", "segments": len(moves),
                        "actual_angle": actual, "expected_angle": expected_value, "angular_error": diff}


def parse_ironing_type(
    gcode_path: Path | str,
    expected_value: str
) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    return parse_ironing_type_l1(gcode_path, expected_value)


def parse_ironing_type_l2(
    gcode_path: Path | str,
    *,
    workers: int = 0,
) -> list[dict[int, list[bytes | str]]]:
    return _parse_ironing_type_l2_impl(gcode_path, workers=workers)


def _percent(value: object) -> Optional[float]:
    try:
        return float(str(value).strip().rstrip("%"))
    except (TypeError, ValueError):
        return None
