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
