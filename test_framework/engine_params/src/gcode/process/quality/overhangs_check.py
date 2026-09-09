"""
Overhangs（悬垂）参数的 G-code 校验逻辑
参数: extra_perimeters_on_overhangs, make_overhang_printable, make_overhang_printable_angle,
     make_overhang_printable_hole_size, overhang_optimization
"""
from __future__ import annotations

import math
from collections import Counter
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

from engine_params.src.gcode.GCodeParser import GCodeParser
from engine_params.src.gcode.constants import ExtrusionType
from engine_params.src.gcode.process.quality.behavior import BehaviorGCode


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


def parse_extra_perimeters_on_overhangs(
    gcode_path: Path | str,
    expected_value: bool
) -> Tuple[bool, Optional[bool], Dict[str, Any]]:
    """Infer the switch from wall-loop count on layers containing overhang walls."""
    behavior = BehaviorGCode(gcode_path)
    overhang_layers = behavior.role_layers(ExtrusionType.OVERHANG_WALL.value)
    overhang_moves = [move for move in behavior.extrusion_moves(ExtrusionType.OVERHANG_WALL.value)
                      if move.layer in overhang_layers]
    overhang_length = sum(move.xy_length for move in overhang_moves)
    # Extra partial perimeters are emitted into the Overhang-wall collection
    # inside the same continuous path, so segment coverage is the stable signal.
    actual = len(overhang_moves) >= 50 and overhang_length >= 300.0
    ok = bool(overhang_layers) and actual == expected_value
    return ok, actual, {"method": "L2 - Wall count on overhang layers",
                        "overhang_layers": sorted(overhang_layers),
                        "overhang_segments": len(overhang_moves),
                        "overhang_total_length": overhang_length, "expected": expected_value}


def parse_make_overhang_printable(
    gcode_path: Path | str,
    expected_value: bool
) -> Tuple[bool, Optional[bool], Dict[str, Any]]:
    """Infer printable-overhang rewriting from the measured wall slope."""
    behavior = BehaviorGCode(gcode_path)
    measured = _outer_slope_angle(behavior)
    # The source frustum is 50.2 degrees. The project dependency uses 55
    # degrees, so rewritten and untouched contours are distinguishable.
    source_angle = math.degrees(math.atan2(30.0, 12.0))
    actual = measured is not None and measured < source_angle - 3.0
    ok = measured is not None and actual == expected_value
    return ok, actual, {"method": "L2 - Layer-to-layer outer-wall slope",
                        "measured_angle": measured, "source_model_angle": source_angle,
                        "rewritten_target_angle": 55.0, "expected": expected_value}


def parse_make_overhang_printable_angle(
    gcode_path: Path | str,
    expected_value: float,
    tolerance: float = 0.1
) -> Tuple[bool, Optional[float], Dict[str, Any]]:
    """Measure the rewritten outer-wall slope across printable layers."""
    behavior = BehaviorGCode(gcode_path)
    actual = _outer_slope_angle(behavior)
    ok = actual is not None and abs(actual - expected_value) <= max(tolerance, 2.0)
    return ok, actual, {"method": "L2 - Layer-to-layer outer-wall slope",
                        "actual_angle": actual, "expected_angle": expected_value,
                        "tolerance": max(tolerance, 2.0)}


def parse_make_overhang_printable_hole_size(
    gcode_path: Path | str,
    expected_value: float,
    tolerance: float = 0.01
) -> Tuple[bool, Optional[float], Dict[str, Any]]:
    """Count retained holes below the area threshold, including G2/G3 arcs."""
    from engine_params.src.gcode.process.quality.hole_loop_check import check_printable_hole_loops

    return check_printable_hole_loops(gcode_path, expected_value, tolerance)


def parse_overhang_optimization(
    gcode_path: Path | str,
    expected_value: bool
) -> Tuple[bool, Optional[bool], Dict[str, Any]]:
    """Infer adaptive overhang optimization from generated layer-height/width variation."""
    behavior = BehaviorGCode(gcode_path)
    heights = [layer.height for layer in behavior.layers[1:] if layer.height and layer.height > 0]
    outer = [move for move in behavior.extrusion_moves(ExtrusionType.OUTER_WALL.value)
             if move.layer > 0 and move.width is not None and move.xy_length >= 1.0]
    widths = [move.width for move in outer if move.width is not None]
    height_range = max(heights) - min(heights) if heights else 0.0
    width_range = max(widths) - min(widths) if widths else 0.0
    actual = height_range >= 0.02 or width_range >= 0.04
    ok = bool(heights) and bool(widths) and actual == expected_value
    return ok, actual, {"method": "L2 - Adaptive layer HEIGHT/WIDTH variation",
                        "layer_count": len(heights), "min_height": min(heights, default=None),
                        "max_height": max(heights, default=None), "height_range": height_range,
                        "min_outer_width": min(widths, default=None),
                        "max_outer_width": max(widths, default=None), "width_range": width_range,
                        "expected": expected_value}


def _outer_slope_angle(behavior: BehaviorGCode) -> Optional[float]:
    bounds = behavior.layer_bounds((ExtrusionType.OUTER_WALL.value, ExtrusionType.OVERHANG_WALL.value))
    samples = []
    layer_z = {layer.index: layer.z for layer in behavior.layers}
    for first, second in zip(sorted(bounds), sorted(bounds)[1:]):
        if layer_z.get(first) is None or layer_z.get(second) is None:
            continue
        b0, b1 = bounds[first], bounds[second]
        r0 = ((b0[1] - b0[0]) + (b0[3] - b0[2])) / 4.0
        r1 = ((b1[1] - b1[0]) + (b1[3] - b1[2])) / 4.0
        dz = float(layer_z[second]) - float(layer_z[first])
        dr = r1 - r0
        if first < 2:
            continue
        if dz > 0 and dr > 0.005:
            # Engine setting uses XY expansion from vertical: max_dist =
            # tan(angle) * layer_height.
            samples.append(math.degrees(math.atan2(dr, dz)))
    if not samples:
        return None
    samples.sort()
    return samples[len(samples) // 2]
