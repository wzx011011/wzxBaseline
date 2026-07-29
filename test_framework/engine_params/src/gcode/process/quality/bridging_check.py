from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, Optional, Tuple, Any

from engine_params.src.gcode.GCodeParser import GCodeParser
from engine_params.src.gcode.constants import ExtrusionType
from engine_params.src.gcode.process.quality.behavior import (
    BehaviorGCode,
    circular_distance_180,
    dominant_angle,
    median,
    median_e_per_mm,
    median_height,
    median_speed,
    median_width,
)
from engine_params.src.gcode.process.quality.line_width_check import (
    _resolve_filament_diameter,
    _resolve_flow_ratio,
)


def _extract_last_extrude_e(parser: GCodeParser, type_value: str) -> Optional[float]:
    """Return the last extrude-point E for the given TYPE across all layers."""
    contours = parser.get_type_contours_per_layer(types=[type_value], workers=0)
    if not contours:
        return None

    last_e: Optional[float] = None
    for layer_map in contours:
        if not layer_map:
            continue
        for oid, type_map in (layer_map or {}).items():
            polylines = (type_map or {}).get(type_value) or []
            for poly in polylines or []:
                for pt in poly:
                    if pt.kind == "extrude" and pt.e is not None:
                        last_e = pt.e
    return last_e


def parse_internal_bridge_flow(
        tested_gcode: Path | str,
        baseline_gcode: Path | str,
        expected_ratio: float,
        *,
        tol: float = 1e-3,
) -> Tuple[bool, Optional[float], Dict[str, object]]:
    """
    Compare the last Internal bridge extrude E between tested and baseline G-code.
    """
    tested_path = Path(tested_gcode)
    baseline_path = Path(baseline_gcode)

    tested_parser = GCodeParser(tested_path)
    baseline_parser = GCodeParser(baseline_path)

    tested_e = _extract_last_extrude_e(tested_parser, ExtrusionType.INTERNAL_BRIDGE.value)
    baseline_e = _extract_last_extrude_e(baseline_parser, ExtrusionType.INTERNAL_BRIDGE.value)

    ratio: Optional[float] = None
    ok = False
    if tested_e is not None and baseline_e is not None and abs(baseline_e) > 1e-9:
        ratio = tested_e / baseline_e
        ok = math.isclose(ratio, expected_ratio, rel_tol=tol, abs_tol=tol)

    details: Dict[str, object] = {
        "tested_gcode": str(tested_path),
        "baseline_gcode": str(baseline_path),
        "tested_e": tested_e,
        "baseline_e": baseline_e,
        "ratio": ratio,
        "expected_ratio": expected_ratio,
        "tolerance": tol,
    }

    return ok, ratio, details


# ============= G-code behavior checks =============


def parse_bridge_angle(
    gcode_path: Path | str,
    expected_angle: float,
    tolerance: float = 0.1
) -> Tuple[bool, Optional[float], Dict[str, Any]]:
    """Infer the bridge angle from long Bridge extrusion vectors."""
    behavior = BehaviorGCode(gcode_path)
    moves = behavior.extrusion_moves(ExtrusionType.BRIDGE.value)
    actual_angle = dominant_angle(moves, min_length=2.0)
    diff = None if actual_angle is None else circular_distance_180(actual_angle, expected_angle)
    ok = diff is not None and diff <= max(tolerance, 2.0)
    return ok, actual_angle, {
        "method": "L2 - Bridge path direction",
        "bridge_segments": len(moves), "actual_angle": actual_angle,
        "expected_angle": expected_angle, "angular_error": diff,
    }


def parse_bridge_flow(
    gcode_path: Path | str,
    expected_flow: float,
    tolerance: float = 0.01
) -> Tuple[bool, Optional[float], Dict[str, Any]]:
    """Infer bridge flow from generated spacing and equivalent cross-section."""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    behavior = BehaviorGCode(gcode_path)
    moves = behavior.extrusion_moves(ExtrusionType.BRIDGE.value)
    width = median_width(moves)
    e_per_mm = median_e_per_mm(moves)
    nozzle = _first_float(cfg.get("nozzle_diameter"), 0.4)
    long_moves = [move for move in moves if move.xy_length >= 4.0]
    angle = dominant_angle(long_moves, min_length=4.0)
    spacing = None
    if angle is not None:
        normal = math.radians(angle + 90.0)
        offsets = sorted({
            round(((move.x0 + move.x) / 2.0) * math.cos(normal)
                  + ((move.y0 + move.y) / 2.0) * math.sin(normal), 3)
            for move in long_moves
        })
        gaps = [b - a for a, b in zip(offsets, offsets[1:]) if 0.05 < b - a < 2.0]
        spacing = median(gaps)
    layer_height = _first_float(cfg.get("layer_height"), 0.2)
    height = median_height(moves)
    inferred = None
    if width is not None and height is not None:
        # Flow::with_flow_ratio keeps spacing fixed. WIDTH/HEIGHT describe an
        # equivalent rounded-rectangle cross-section, including virtual height
        # changes used to encode bridge volume without changing layer Z.
        actual_area = height * (width - height) + math.pi * height * height / 4.0
        base_width = _first_float(
            cfg.get("internal_solid_infill_line_width", cfg.get("line_width")), 0.42
        )
        base_area = layer_height * (base_width - layer_height) + math.pi * layer_height * layer_height / 4.0
        if base_area > 0:
            inferred = actual_area / base_area
    observed_volume = None
    if e_per_mm is not None:
        filament = _resolve_filament_diameter(cfg)
        observed_volume = e_per_mm * math.pi * (filament / 2) ** 2 * _resolve_flow_ratio(cfg)
    allowed = max(tolerance, 0.035)
    ok = inferred is not None and abs(inferred - expected_flow) <= allowed and observed_volume is not None
    return ok, inferred, {
        "method": "L2 - Bridge WIDTH and extrusion volume",
        "bridge_segments": len(moves), "median_width": width, "median_height": height,
        "median_spacing": spacing, "layer_height": layer_height, "nozzle": nozzle,
        "inferred_bridge_flow": inferred, "expected_bridge_flow": expected_flow,
        "observed_mm3_per_mm": observed_volume, "tolerance": allowed,
    }


def parse_bridge_density(
    gcode_path: Path | str,
    expected_density: str,
) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """Infer bridge density from adjacent parallel line spacing."""
    behavior = BehaviorGCode(gcode_path)
    moves = [m for m in behavior.extrusion_moves(ExtrusionType.BRIDGE.value) if m.xy_length >= 4]
    angle = dominant_angle(moves, min_length=4)
    width = median_width(moves)
    spacing = None
    if angle is not None:
        normal = math.radians(angle + 90)
        offsets = sorted({round(((m.x0 + m.x) / 2) * math.cos(normal) + ((m.y0 + m.y) / 2) * math.sin(normal), 3) for m in moves})
        gaps = [b - a for a, b in zip(offsets, offsets[1:]) if 0.05 < b - a < 5]
        spacing = median(gaps)
    inferred = None if width is None or spacing is None else min(100.0, 100.0 * width / spacing)
    expected_percent = _percent(expected_density)
    ok = inferred is not None and expected_percent is not None and abs(inferred - expected_percent) <= 15.0
    return ok, None if inferred is None else f"{inferred:.1f}%", {
        "method": "L2 - Bridge line spacing",
        "long_bridge_segments": len(moves), "median_width": width, "median_spacing": spacing,
        "inferred_density_percent": inferred, "expected_density_percent": expected_percent,
    }


def parse_bridge_speed(
    gcode_path: Path | str,
    expected_speed: float,
    tolerance: float = 0.1
) -> Tuple[bool, Optional[float], Dict[str, Any]]:
    """Read the feed rate carried by long Bridge extrusion moves."""
    behavior = BehaviorGCode(gcode_path)
    moves = behavior.extrusion_moves(ExtrusionType.BRIDGE.value)
    actual_speed = median_speed(moves, min_length=2.0)
    ok = actual_speed is not None and abs(actual_speed - expected_speed) <= max(tolerance, 0.2)
    return ok, actual_speed, {
        "method": "L2 - Bridge G1 feed rate", "bridge_segments": len(moves),
        "actual_speed_mm_s": actual_speed, "expected_speed_mm_s": expected_speed,
    }


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


def _first_float(value: Any, default: float) -> float:
    if isinstance(value, (list, tuple)) and value:
        value = value[0]
    text = str(value).split(",", 1)[0].strip().rstrip("%")
    try:
        return float(text)
    except (TypeError, ValueError):
        return default


def _percent(value: Any) -> Optional[float]:
    try:
        return float(str(value).strip().rstrip("%"))
    except (TypeError, ValueError):
        return None


def parse_thick_bridges(
    gcode_path: Path | str,
    expected_value: bool,
) -> Tuple[bool, Optional[bool], Dict[str, Any]]:
    """Infer thick bridge mode from generated bridge height/width ratio."""
    behavior = BehaviorGCode(gcode_path)
    moves = behavior.extrusion_moves(ExtrusionType.BRIDGE.value)
    width, height = median_width(moves), median_height(moves)
    ratio = None if width is None or height is None or width <= 0 else height / width
    actual = None if ratio is None else ratio >= 0.65
    ok = actual is not None and actual == expected_value
    return ok, actual, {"method": "L2 - Bridge HEIGHT/WIDTH ratio", "width": width,
                        "height": height, "height_width_ratio": ratio, "expected": expected_value}


def parse_dont_filter_internal_bridges(
    gcode_path: Path | str,
    expected_value: str,
) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """Classify the internal-bridge filtering result by retained path coverage."""
    behavior = BehaviorGCode(gcode_path)
    moves = behavior.extrusion_moves(ExtrusionType.INTERNAL_BRIDGE.value)
    layers = sorted({move.layer for move in moves})
    candidate_layer = layers[0] if layers else None
    candidate_moves = [move for move in moves if move.layer == candidate_layer]
    coverage = sum(move.xy_length for move in candidate_moves)
    # The model contains four narrow roof cavities. PrintObject's disabled,
    # limited and no-filter branches retain progressively more of the first
    # internal-bridge candidate surface. A later roof layer is common control
    # geometry and is deliberately excluded.
    inferred = "disabled" if coverage < 820.0 else "limited" if coverage < 840.0 else "nofilter"
    expected = str(expected_value).strip().lower()
    return inferred == expected, inferred, {
        "method": "L2 - Retained Internal Bridge candidate coverage",
        "candidate_layer": candidate_layer, "candidate_segments": len(candidate_moves),
        "candidate_total_length": coverage, "expected": expected,
    }


def parse_thick_internal_bridges(
    gcode_path: Path | str,
    expected_value: bool,
) -> Tuple[bool, Optional[bool], Dict[str, Any]]:
    """Infer thick internal bridge mode from its HEIGHT/WIDTH ratio."""
    behavior = BehaviorGCode(gcode_path)
    moves = behavior.extrusion_moves(ExtrusionType.INTERNAL_BRIDGE.value)
    width, height = median_width(moves), median_height(moves)
    ratio = None if width is None or height is None or width <= 0 else height / width
    actual = None if ratio is None else ratio >= 0.65
    return actual is not None and actual == expected_value, actual, {
        "method": "L2 - Internal Bridge HEIGHT/WIDTH ratio", "width": width,
        "height": height, "height_width_ratio": ratio, "expected": expected_value,
    }


def parse_internal_bridge_speed(
    gcode_path: Path | str,
    expected_speed: str,
) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """Validate Internal Bridge feed rate, including percent-of-bridge-speed semantics."""
    behavior = BehaviorGCode(gcode_path)
    moves = behavior.extrusion_moves(ExtrusionType.INTERNAL_BRIDGE.value)
    actual = median_speed(moves, min_length=1.0)
    cfg = GCodeParser(gcode_path).load_config()
    bridge_speed = _first_float(cfg.get("bridge_speed"), 0.0)
    percent = _percent(expected_speed)
    expected = None if percent is None else bridge_speed * percent / 100.0
    ok = actual is not None and expected is not None and abs(actual - expected) <= 0.3
    return ok, None if actual is None else f"{actual:.3f}", {
        "method": "L2 - Internal Bridge G1 feed rate", "actual_speed_mm_s": actual,
        "bridge_speed_mm_s": bridge_speed, "expected_setting": expected_speed,
        "expected_speed_mm_s": expected, "segments": len(moves),
    }


def parse_counterbore_hole_bridging(
    gcode_path: Path | str,
    expected_value: str,
) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """Classify counterbore treatment from bridge coverage at the stepped hole."""
    behavior = BehaviorGCode(gcode_path)
    moves = behavior.extrusion_moves(ExtrusionType.BRIDGE.value)
    layers = sorted({move.layer for move in moves})
    transition_layer = layers[0] if layers else None
    transition_moves = [move for move in moves if move.layer == transition_layer]
    total = sum(move.xy_length for move in transition_moves)
    # On the designed annular step: partially bridged covers only bridgeable
    # sectors, sacrificial-layer fills the annulus, and none leaves the native
    # overhang/perimeter treatment. Their emitted bridge coverage is distinct.
    if total > 380.0:
        inferred = "sacrificiallayer"
    elif total < 270.0:
        inferred = "partiallybridge"
    else:
        inferred = "none"
    expected = str(expected_value).strip().lower()
    return inferred == expected, inferred, {
        "method": "L2 - Counterbore transition-layer bridge coverage",
        "transition_layer": transition_layer, "bridge_segments": len(transition_moves),
        "bridge_total_length": total, "expected": expected,
    }

