"""
Precision（精度）参数的 G-code 校验逻辑
参数: slice_closing_radius, resolution, hole_to_polyhole, hole_to_polyhole_threshold,
     hole_to_polyhole_twisted, precise_outer_wall, precise_z_height
"""
from __future__ import annotations

import math
import statistics
from collections import Counter
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

from engine_params.src.gcode.GCodeParser import GCodeParser
from engine_params.src.gcode.constants import ExtrusionType
from engine_params.src.gcode.process.quality.behavior import BehaviorGCode, median_width, path_bbox


def _parse_bool_value(raw_value: Any, param_name: str) -> Tuple[bool, Optional[bool], Dict[str, Any]]:
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


def parse_slice_closing_radius(
    gcode_path: Path | str,
    expected_value: float,
    tolerance: float = 0.001
) -> Tuple[bool, Optional[float], Dict[str, Any]]:
    """Count islands left after closing the designed 0.04/0.08/0.12 mm gaps."""
    behavior = BehaviorGCode(gcode_path)
    middle = len(behavior.layers) // 2
    paths = [path for path in behavior.paths(ExtrusionType.OUTER_WALL.value, min_length=5.0)
             if path and path[0].layer == middle]
    island_count = len(paths)
    expected_islands = 1 + sum(gap > 2.0 * expected_value + tolerance for gap in (0.04, 0.08, 0.12))
    ok = island_count == expected_islands
    return ok, float(island_count), {"method": "L2 - Post-slice island count",
                                     "observed_islands": island_count, "expected_islands": expected_islands,
                                     "designed_gaps": [0.04, 0.08, 0.12], "closing_radius": expected_value}


def parse_resolution(
    gcode_path: Path | str,
    expected_value: float,
    tolerance: float = 0.001
) -> Tuple[bool, Optional[float], Dict[str, Any]]:
    """Measure maximum chord sagitta of the generated circular perimeter."""
    behavior = BehaviorGCode(gcode_path)
    candidates = _hole_or_circle_paths(behavior, min_diameter=10.0, max_diameter=16.0)
    path = max(candidates, key=len, default=[])
    bbox = path_bbox(path)
    sagitta = None
    if path and bbox:
        radius = ((bbox[1] - bbox[0]) + (bbox[3] - bbox[2])) / 4.0
        cx, cy = (bbox[0] + bbox[1]) / 2.0, (bbox[2] + bbox[3]) / 2.0
        angles = sorted({math.atan2(move.y - cy, move.x - cx) % (2 * math.pi) for move in path})
        if len(angles) >= 3:
            gaps = [b - a for a, b in zip(angles, angles[1:] + [angles[0] + 2 * math.pi])]
            sagitta = radius * (1.0 - math.cos(max(gaps) / 2.0))
    ok = sagitta is not None and sagitta <= expected_value * 1.6 + tolerance
    return ok, sagitta, {"method": "L2 - Circular-path chord sagitta", "segments": len(path),
                          "observed_sagitta": sagitta, "resolution_limit": expected_value}


def parse_hole_to_polyhole(
    gcode_path: Path | str,
    expected_value: bool
) -> Tuple[bool, Optional[bool], Dict[str, Any]]:
    """Classify the hole by the number and regularity of its perimeter edges."""
    behavior = BehaviorGCode(gcode_path)
    paths = _hole_or_circle_paths(behavior, min_diameter=8.0, max_diameter=12.0)
    path = max(paths, key=len, default=[])
    lengths = [move.xy_length for move in path if move.xy_length > 0.02]
    cv = statistics.pstdev(lengths) / statistics.mean(lengths) if len(lengths) > 2 else None
    actual = bool(lengths) and len(lengths) <= 40 and cv is not None and cv < 0.25
    arc_evidence = behavior.arc_count(ExtrusionType.OUTER_WALL.value)
    ok = actual == expected_value and (bool(path) or arc_evidence > 0)
    return ok, actual, {"method": "L2 - Hole polygon edge topology", "edge_count": len(lengths),
                        "edge_length_cv": cv, "outer_wall_arc_count": arc_evidence,
                        "expected": expected_value}


def parse_hole_to_polyhole_threshold(
    gcode_path: Path | str,
    expected_value: float,
    tolerance: float = 0.001
) -> Tuple[bool, Optional[float], Dict[str, Any]]:
    """Count which of the three slightly distorted holes became regular polyholes."""
    behavior = BehaviorGCode(gcode_path)
    paths = _hole_or_circle_paths(behavior, min_diameter=4.5, max_diameter=7.0)
    middle = len(behavior.layers) // 2
    paths = [path for path in paths if path and path[0].layer == middle]
    converted = sum(8 <= len(path) <= 40 for path in paths)
    # radial deviations in the designed model straddle both tested margins.
    expected_converted = sum(deviation < expected_value + tolerance for deviation in (0.005, 0.015, 0.03))
    ok = converted == expected_converted
    return ok, float(converted), {"method": "L2 - Converted-hole count", "observed_converted": converted,
                                  "expected_converted": expected_converted, "candidate_paths": len(paths),
                                  "radial_deviations": [0.005, 0.015, 0.03], "threshold": expected_value}


def parse_hole_to_polyhole_twisted(
    gcode_path: Path | str,
    expected_value: bool
) -> Tuple[bool, Optional[bool], Dict[str, Any]]:
    """Detect alternating polygon orientation across consecutive hole layers."""
    behavior = BehaviorGCode(gcode_path)
    paths = _hole_or_circle_paths(behavior, min_diameter=8.0, max_diameter=12.0)
    by_layer = {}
    for path in paths:
        if not path or path[0].layer in by_layer:
            continue
        bbox = path_bbox(path)
        if not bbox:
            continue
        cx, cy = (bbox[0] + bbox[1]) / 2.0, (bbox[2] + bbox[3]) / 2.0
        by_layer[path[0].layer] = math.degrees(math.atan2(path[0].y0 - cy, path[0].x0 - cx)) % 360
    deltas = [abs(((b - a + 180) % 360) - 180) for a, b in zip(by_layer.values(), list(by_layer.values())[1:])]
    alternating = sum(delta > 1.0 for delta in deltas) >= max(1, len(deltas) // 2) if deltas else False
    ok = len(by_layer) >= 3 and alternating == expected_value
    return ok, alternating, {"method": "L2 - Per-layer polyhole phase", "phase_by_layer": by_layer,
                             "phase_deltas": deltas, "expected": expected_value}


def parse_precise_outer_wall(
    gcode_path: Path | str,
    expected_value: bool
) -> Tuple[bool, Optional[bool], Dict[str, Any]]:
    """Infer precise placement from outer-to-nearest-inner wall center spacing."""
    behavior = BehaviorGCode(gcode_path)
    outer_paths = behavior.paths(ExtrusionType.OUTER_WALL.value, min_length=20.0)
    inner_paths = behavior.paths(ExtrusionType.INNER_WALL.value, min_length=20.0)
    middle = len(behavior.layers) // 2
    outer_boxes = [path_bbox(path) for path in outer_paths if path and path[0].layer == middle]
    inner_boxes = [path_bbox(path) for path in inner_paths if path and path[0].layer == middle]
    outer_spans = [((box[1] - box[0]) + (box[3] - box[2])) / 2.0 for box in outer_boxes if box]
    inner_spans = [((box[1] - box[0]) + (box[3] - box[2])) / 2.0 for box in inner_boxes if box]
    center_spacing = None
    if outer_spans and inner_spans:
        center_spacing = (max(outer_spans) - max(inner_spans)) / 2.0
    actual = center_spacing is not None and center_spacing >= 0.42
    ok = center_spacing is not None and actual == expected_value
    return ok, actual, {"method": "L2 - Outer/nearest-inner wall center spacing",
                        "outer_centerline_span": max(outer_spans, default=None),
                        "nearest_inner_centerline_span": max(inner_spans, default=None),
                        "center_spacing": center_spacing, "classification_threshold": 0.42,
                        "expected": expected_value}


def parse_precise_z_height(
    gcode_path: Path | str,
    expected_value: bool,
    tolerance: float = 0.01
) -> Tuple[bool, Optional[float], Dict[str, Any]]:
    """Infer precise-Z mode from the final printed layer against 10.13 mm model height."""
    behavior = BehaviorGCode(gcode_path)
    zs = [layer.z for layer in behavior.layers if layer.z is not None]
    last_z = max(zs) if zs else None
    error = None if last_z is None else abs(last_z - 10.13)
    actual = error is not None and error <= max(tolerance, 0.015)
    ok = actual == expected_value if error is not None else False
    return ok, last_z, {"method": "L2 - Final layer Z", "last_layer_z": last_z,
                        "model_height": 10.13, "height_error": error, "inferred_enabled": actual,
                        "expected": expected_value}


def _hole_or_circle_paths(
    behavior: BehaviorGCode, *, min_diameter: float, max_diameter: float
) -> list[list]:
    middle = len(behavior.layers) // 2
    result = []
    for path in behavior.paths(ExtrusionType.OUTER_WALL.value, min_length=1.0):
        if not path or abs(path[0].layer - middle) > 2:
            continue
        bbox = path_bbox(path)
        if not bbox:
            continue
        diameter = ((bbox[1] - bbox[0]) + (bbox[3] - bbox[2])) / 2.0
        if min_diameter <= diameter <= max_diameter:
            result.append(path)
    return result
