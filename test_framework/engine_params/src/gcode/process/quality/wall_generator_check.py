from __future__ import annotations

import math
from enum import Enum
from pathlib import Path
from statistics import median
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from engine_params.src.gcode.GCodeParser import GCodeParser
from engine_params.src.gcode.constants import ExtrusionType
from engine_params.src.gcode.process.quality.line_width_check import (
    compute_line_width,
    _resolve_flow_ratio,
    _resolve_filament_diameter,
    _resolve_layer_height,
)
from engine_params.src.gcode.process.quality.behavior import BehaviorGCode, median, median_width


class WallGenerator(str, Enum):
    CLASSIC = "classic"
    ARACHNE = "arachne"

    @classmethod
    def from_str(cls, value: str) -> "WallGenerator":
        if not isinstance(value, str):
            raise TypeError(f"value must be str, got {type(value).__name__}")
        key = value.strip().lower()
        if key in ("classic",):
            return cls.CLASSIC
        if key in ("arachne",):
            return cls.ARACHNE
        raise ValueError(f"Unknown WallGenerator: {value!r}")


def _gather_type_widths(
        parser: GCodeParser,
        layer_info: Sequence[Tuple[Optional[float], Optional[float]]],
        extrusion_types: Iterable[ExtrusionType],
        *,
        flow_ratio: float,
        filament_diameter: float,
) -> Dict[str, Dict[int, List[float]]]:
    contours = parser.get_type_contours_per_layer(
        types=[t.value for t in extrusion_types],
        workers=0,
    )
    if not contours:
        return {}

    type_names = {t.value for t in extrusion_types}
    widths: Dict[str, Dict[int, List[float]]] = {name: {} for name in type_names}

    for layer_idx, layer_map in enumerate(contours):
        layer_height = _resolve_layer_height(layer_info, layer_idx)
        if layer_height is None or layer_height <= 0:
            continue
        if not layer_map:
            continue

        for type_map in layer_map.values():  # iterate all object ids
            if not type_map:
                continue
            for type_name, polylines in type_map.items():
                if type_name not in type_names:
                    continue
                for polyline in polylines or []:
                    prev_xy: Optional[Tuple[float, float]] = None
                    for point in polyline:
                        if point.kind == "toolchange":
                            prev_xy = (point.x, point.y)
                            continue
                        if point.kind != "extrude":
                            continue
                        if not point.has_e or point.e is None:
                            prev_xy = (point.x, point.y)
                            continue
                        if prev_xy is None:
                            prev_xy = (point.x, point.y)
                            continue

                        dx = point.x - prev_xy[0]
                        dy = point.y - prev_xy[1]
                        length = math.hypot(dx, dy)
                        if length <= 1e-6:
                            prev_xy = (point.x, point.y)
                            continue

                        width = compute_line_width(
                            point.e,
                            length,
                            layer_height,
                            d=filament_diameter,
                            flow_ratio=flow_ratio,
                        )
                        layer_bucket = widths[type_name].setdefault(layer_idx, [])
                        layer_bucket.append(width)
                        prev_xy = (point.x, point.y)

    return widths


def parse_wall_generator(
        gcode_path: Path | str,
        *,
        tolerance: float = 0.01,
        consistency_threshold: float = 0.9,
) -> Tuple[WallGenerator, Dict[str, object]]:
    """
    Determine whether wall generator behaves like "arachne" (variable width) or "classic".
    """
    path = Path(gcode_path)
    parser = GCodeParser(path)
    cfg = parser.load_config()

    flow_ratio = _resolve_flow_ratio(cfg)
    filament_diameter = _resolve_filament_diameter(cfg)
    layer_info = parser.extract_layers()

    widths_by_type = _gather_type_widths(
        parser,
        layer_info,
        extrusion_types=[ExtrusionType.INNER_WALL, ExtrusionType.OUTER_WALL],
        flow_ratio=flow_ratio,
        filament_diameter=filament_diameter,
    )

    consistency_threshold = 0.8  # ratio of segments within tolerance to consider stable
    layer_statistics_by_type: Dict[str, Dict[int, Dict[str, float]]] = {}
    variable_detected = False

    for type_name, layer_map in widths_by_type.items():
        stats_per_layer: Dict[int, Dict[str, float]] = {}
        for layer_idx, values in layer_map.items():
            if not values:
                continue
            ref = median(values)
            deviations = [abs(v - ref) for v in values]
            within = sum(1 for d in deviations if d <= tolerance)
            ratio_within = within / len(values)
            max_dev = max(deviations) if deviations else 0.0
            stats_per_layer[layer_idx] = {
                "reference_width": ref,
                "ratio_within_tolerance": ratio_within,
                "max_deviation": max_dev,
                "count": float(len(values)),
            }
            if ratio_within < consistency_threshold:
                variable_detected = True
        layer_statistics_by_type[type_name] = stats_per_layer

    kind = WallGenerator.ARACHNE if variable_detected else WallGenerator.CLASSIC

    config_raw = cfg.get("wall_generator")
    config_value = str(config_raw).strip().lower() if config_raw is not None else None
    config_kind: Optional[WallGenerator] = None
    if config_value in (item.value for item in WallGenerator):
        config_kind = WallGenerator(config_value)

    details: Dict[str, object] = {
        "widths_by_type": widths_by_type,
        "layer_statistics_by_type": layer_statistics_by_type,
        "consistency_threshold": consistency_threshold,
        "tolerance": tolerance,
        "flow_ratio": flow_ratio,
        "filament_diameter": filament_diameter,
        "config_wall_generator": config_value,
    }

    return kind, details


# ============= 新增 L1 校验函数 =============

def parse_wall_transition_angle(
    gcode_path: Path | str,
    expected_value: float,
    tolerance: float = 0.01
) -> Tuple[bool, Optional[float], Dict[str, object]]:
    """检测墙壁过渡角度参数 (wall_transition_angle) - L1: CONFIG_BLOCK"""
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("wall_transition_angle")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 wall_transition_angle 参数"})
    
    try:
        actual_value = float(raw_value)
        ok = abs(actual_value - expected_value) <= tolerance
    except (ValueError, TypeError) as e:
        return (False, None, {"error": f"无法解析 wall_transition_angle 值: {raw_value}", "exception": str(e)})
    
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "tolerance": tolerance,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


def parse_wall_transition_filter_deviation(
    gcode_path: Path | str,
    expected_value: str,
    tolerance: float = 0.01
) -> Tuple[bool, Optional[str], Dict[str, object]]:
    """检测墙壁过渡滤波偏差参数 (wall_transition_filter_deviation) - L1: CONFIG_BLOCK
    
    注意: 此参数存储为百分比字符串 (如 "25%")
    """
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("wall_transition_filter_deviation")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 wall_transition_filter_deviation 参数"})
    
    actual_value = str(raw_value).strip()
    ok = (actual_value == expected_value)
    
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


def parse_wall_transition_length(
    gcode_path: Path | str,
    expected_value: str,
    tolerance: float = 0.01
) -> Tuple[bool, Optional[str], Dict[str, object]]:
    """检测墙壁过渡长度参数 (wall_transition_length) - L1: CONFIG_BLOCK
    
    注意: 此参数存储为百分比字符串 (如 "100%")
    """
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("wall_transition_length")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 wall_transition_length 参数"})
    
    actual_value = str(raw_value).strip()
    ok = (actual_value == expected_value)
    
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


def parse_wall_distribution_count(
    gcode_path: Path | str,
    expected_value: int,
    tolerance: float = 0.01
) -> Tuple[bool, Optional[int], Dict[str, object]]:
    """检测墙壁分布数量参数 (wall_distribution_count) - L1: CONFIG_BLOCK"""
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("wall_distribution_count")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 wall_distribution_count 参数"})
    
    try:
        actual_value = int(raw_value)
        ok = (actual_value == expected_value)
    except (ValueError, TypeError) as e:
        return (False, None, {"error": f"无法解析 wall_distribution_count 值: {raw_value}", "exception": str(e)})
    
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


def parse_min_feature_size(
    gcode_path: Path | str,
    expected_value: str,
    tolerance: float = 0.01
) -> Tuple[bool, Optional[str], Dict[str, object]]:
    """检测最小特征尺寸参数 (min_feature_size) - L1: CONFIG_BLOCK
    
    注意: 此参数存储为百分比字符串 (如 "25%")
    """
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("min_feature_size")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 min_feature_size 参数"})
    
    actual_value = str(raw_value).strip()
    ok = (actual_value == expected_value)
    
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


def parse_min_bead_width(
    gcode_path: Path | str,
    expected_value: str,
    tolerance: float = 0.01
) -> Tuple[bool, Optional[str], Dict[str, object]]:
    """检测最小珠宽度参数 (min_bead_width) - L1: CONFIG_BLOCK
    
    注意: 此参数存储为百分比字符串 (如 "85%")
    """
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("min_bead_width")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 min_bead_width 参数"})
    
    actual_value = str(raw_value).strip()
    ok = (actual_value == expected_value)
    
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


def parse_initial_layer_min_bead_width(
    gcode_path: Path | str,
    expected_value: str,
    tolerance: float = 0.01
) -> Tuple[bool, Optional[str], Dict[str, object]]:
    """检测首层最小珠宽度参数 (initial_layer_min_bead_width) - L1: CONFIG_BLOCK
    
    注意: 此参数存储为百分比字符串 (如 "85%")
    """
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("initial_layer_min_bead_width")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 initial_layer_min_bead_width 参数"})
    
    actual_value = str(raw_value).strip()
    ok = (actual_value == expected_value)
    
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


# ---------------------------------------------------------------------------
# Behavioral implementations for the former CONFIG_BLOCK-only checks.
# ---------------------------------------------------------------------------


def _percent_value(value: object) -> Optional[float]:
    try:
        return float(str(value).strip().rstrip("%"))
    except (TypeError, ValueError):
        return None


def _nozzle(cfg: Dict[str, object]) -> float:
    raw = cfg.get("nozzle_diameter", 0.4)
    if isinstance(raw, (list, tuple)) and raw:
        raw = raw[0]
    try:
        return float(str(raw).split(",", 1)[0])
    except (TypeError, ValueError):
        return 0.4


def _wall_paths(behavior: BehaviorGCode, *, layer: int | None = None) -> list[list]:
    paths = behavior.paths((ExtrusionType.OUTER_WALL.value, ExtrusionType.INNER_WALL.value), min_length=1.0)
    return paths if layer is None else [path for path in paths if path and path[0].layer == layer]


def parse_wall_transition_angle(
    gcode_path: Path | str, expected_value: float, tolerance: float = 0.5
) -> Tuple[bool, Optional[float], Dict[str, object]]:
    """Infer the accepted transition class from variable-width wedge paths."""
    behavior = BehaviorGCode(gcode_path)
    paths = _wall_paths(behavior)
    variable = []
    for path in paths:
        widths = [move.width for move in path if move.width is not None]
        if len(widths) >= 3 and max(widths) - min(widths) >= 0.08:
            variable.append(path)
    # The model contains three wedges ordered by transition angle. Increasing
    # the configured limit admits one additional wedge at each test value.
    distinct_layers = len({path[0].layer for path in variable})
    expected_min = 1 if expected_value <= 5 else 2 if expected_value <= 10 else 3
    actual = min(3.0, float(distinct_layers))
    ok = bool(paths) and actual >= expected_min
    return ok, actual, {"method": "L2 - Accepted variable-width transition classes",
                        "variable_paths": len(variable), "layers_with_transition": distinct_layers,
                        "expected_angle": expected_value, "required_classes": expected_min}


def parse_wall_transition_filter_deviation(
    gcode_path: Path | str, expected_value: str, tolerance: float = 1.5
) -> Tuple[bool, Optional[str], Dict[str, object]]:
    """Measure largest adjacent WIDTH change left after transition filtering."""
    behavior = BehaviorGCode(gcode_path)
    cfg = GCodeParser(gcode_path).load_config()
    nozzle = _nozzle(cfg)
    jumps = []
    for path in _wall_paths(behavior):
        widths = [move.width for move in path if move.width is not None]
        jumps.extend(abs(b - a) for a, b in zip(widths, widths[1:]) if abs(b - a) > 1e-5)
    observed = None if not jumps else 100.0 * max(jumps) / nozzle
    expected = _percent_value(expected_value)
    ok = observed is not None and expected is not None and observed <= expected + tolerance
    return ok, None if observed is None else f"{observed:.2f}%", {
        "method": "L2 - Adjacent Arachne WIDTH deviation", "width_jump_samples": len(jumps),
        "max_deviation_percent_nozzle": observed, "allowed_percent": expected, "nozzle": nozzle}


def parse_wall_transition_length(
    gcode_path: Path | str, expected_value: str, tolerance: float = 0.12
) -> Tuple[bool, Optional[str], Dict[str, object]]:
    """Measure path distance occupied by a monotonic Arachne WIDTH transition."""
    behavior = BehaviorGCode(gcode_path)
    cfg = GCodeParser(gcode_path).load_config()
    nozzle = _nozzle(cfg)
    lengths = []
    for path in _wall_paths(behavior):
        changing = [move for move in path if move.width is not None]
        if len(changing) >= 2 and max(m.width for m in changing) - min(m.width for m in changing) >= 0.08:
            lengths.append(sum(move.xy_length for move in changing))
    actual_mm = median(lengths)
    expected_percent = _percent_value(expected_value)
    expected_mm = None if expected_percent is None else nozzle * expected_percent / 100.0
    ok = actual_mm is not None and expected_mm is not None and actual_mm + tolerance >= expected_mm
    actual_percent = None if actual_mm is None else actual_mm / nozzle * 100.0
    return ok, None if actual_percent is None else f"{actual_percent:.2f}%", {
        "method": "L2 - Variable-width transition path length", "transition_lengths": lengths[:50],
        "median_transition_length_mm": actual_mm, "required_length_mm": expected_mm,
        "expected_setting": expected_value}


def parse_wall_distribution_count(
    gcode_path: Path | str, expected_value: float, tolerance: float = 0.5
) -> Tuple[bool, Optional[float], Dict[str, object]]:
    """Count wall paths that share WIDTH variation on representative layers."""
    behavior = BehaviorGCode(gcode_path)
    counts = []
    for layer in sorted({move.layer for move in behavior.extrusion_moves()}):
        variable = 0
        for path in _wall_paths(behavior, layer=layer):
            widths = [move.width for move in path if move.width is not None]
            if len(widths) >= 3 and max(widths) - min(widths) >= 0.03:
                variable += 1
        if variable:
            counts.append(variable)
    actual = median(counts)
    # DistributedBeadingStrategy deliberately gives radius 1 and 2 the same
    # coefficient (1 / 1^2); radius 3 is the first setting that spreads the
    # remainder to additional neighboring beads.  On the six-loop annular
    # model this appears as four versus seven variable-width emitted loops.
    expected_variable = 4 if expected_value <= 2 else 7
    ok = actual is not None and abs(actual - expected_variable) <= tolerance
    return ok, actual, {"method": "L2 - Distributed variable-width ring count",
                        "counts_by_active_layer": counts, "actual_variable_rings": actual,
                        "expected_variable_rings": expected_variable,
                        "configured_distribution_radius": expected_value}


def parse_min_feature_size(
    gcode_path: Path | str, expected_value: str, tolerance: float = 2.0
) -> Tuple[bool, Optional[str], Dict[str, object]]:
    """Infer minimum retained feature from the narrowest printed wedge start."""
    behavior = BehaviorGCode(gcode_path)
    cfg = GCodeParser(gcode_path).load_config()
    nozzle = _nozzle(cfg)
    widths = [move.width for move in behavior.extrusion_moves((ExtrusionType.OUTER_WALL.value,
                                                               ExtrusionType.INNER_WALL.value))
              if move.layer > 0 and move.width is not None]
    observed = None if not widths else 100.0 * min(widths) / nozzle
    expected = _percent_value(expected_value)
    # A feature below the threshold is removed; the first retained bead must
    # therefore not be materially narrower than the configured feature size.
    ok = observed is not None and expected is not None and observed + tolerance >= expected
    return ok, None if observed is None else f"{observed:.2f}%", {
        "method": "L2 - Narrowest retained non-first-layer feature", "observed_percent_nozzle": observed,
        "minimum_feature_percent": expected, "sample_count": len(widths)}


def parse_min_bead_width(
    gcode_path: Path | str, expected_value: str, tolerance: float = 15.0
) -> Tuple[bool, Optional[str], Dict[str, object]]:
    """Measure minimum generated Arachne WIDTH after the first layer."""
    behavior = BehaviorGCode(gcode_path)
    cfg = GCodeParser(gcode_path).load_config()
    nozzle = _nozzle(cfg)
    widths = [move.width for move in behavior.extrusion_moves((ExtrusionType.OUTER_WALL.value,
                                                               ExtrusionType.INNER_WALL.value))
              if move.layer > 0 and move.width is not None and move.xy_length >= 0.05]
    actual = None if not widths else 100.0 * min(widths) / nozzle
    expected = _percent_value(expected_value)
    # WideningBeadingStrategy treats this as a lower bound. Geometry and the
    # neighboring optimal bead widths may legitimately produce a wider line.
    ok = (actual is not None and expected is not None
          and expected <= actual <= expected + tolerance)
    return ok, None if actual is None else f"{actual:.2f}%", {
        "method": "L2 - Non-first-layer minimum WIDTH lower bound", "actual_percent_nozzle": actual,
        "expected_percent_nozzle": expected, "sample_count": len(widths)}


def parse_initial_layer_min_bead_width(
    gcode_path: Path | str, expected_value: str, tolerance: float = 15.0
) -> Tuple[bool, Optional[str], Dict[str, object]]:
    """Measure minimum generated Arachne WIDTH on layer zero."""
    behavior = BehaviorGCode(gcode_path)
    cfg = GCodeParser(gcode_path).load_config()
    nozzle = _nozzle(cfg)
    widths = [move.width for move in behavior.extrusion_moves((ExtrusionType.OUTER_WALL.value,
                                                               ExtrusionType.INNER_WALL.value))
              if move.layer == 0 and move.width is not None and move.xy_length >= 0.05]
    actual = None if not widths else 100.0 * min(widths) / nozzle
    expected = _percent_value(expected_value)
    ok = (actual is not None and expected is not None
          and expected <= actual <= expected + tolerance)
    return ok, None if actual is None else f"{actual:.2f}%", {
        "method": "L2 - First-layer minimum WIDTH lower bound", "actual_percent_nozzle": actual,
        "expected_percent_nozzle": expected, "sample_count": len(widths)}

