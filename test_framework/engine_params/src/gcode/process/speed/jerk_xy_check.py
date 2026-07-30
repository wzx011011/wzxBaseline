# engine_params/src/gcode/speed/jerk_xy_check.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from engine_params.src.gcode.GCodeParserEx import GCodeParserEx
from engine_params.src.gcode.constants import SQUARE_CORNER_KEY, ExtrusionType


TypeSeq = Optional[Sequence[ExtrusionType | str | bytes]]


def _canonical_type_names(types: TypeSeq) -> List[str]:
    if not types:
        return ["<all>"]
    names = set()
    for t in types:
        if isinstance(t, ExtrusionType):
            names.add(t.value)
        else:
            canon = ExtrusionType.to_str(t)
            names.add(canon if canon else str(t))
    return sorted(names)


def _parse_square_corner_common(
        gcode_path: Path | str,
        expected_value: float,
        tolerance: float,
        *,
        parameter: str,
        target_types: TypeSeq = None,
        layer_indices: Optional[Sequence[int]] = None,
        skip_layers: Optional[Sequence[int]] = None,
) -> Tuple[bool, float, Dict[str, Any]]:
    """
    通用的 square-corner velocity 检查逻辑：
    1. 使用 GCodeParserEx 获取 LayerRegion（可按类型过滤，并支持 skip_layers=[0]）。
    2. 遍历 Region，检查 velocity_limits 中的 SQUARE_CORNER_VELOCITY 与期望值是否一致。
    3. 收集缺失/不匹配明细，方便失败时输出定位信息。
    """
    path_obj = Path(gcode_path)
    parser = GCodeParserEx(path_obj)

    type_names = _canonical_type_names(target_types)
    expected_val = float(expected_value)

    kwargs: Dict[str, Any] = {}
    if target_types:
        kwargs["types"] = target_types
    if layer_indices is not None:
        kwargs["layer_indices"] = list(layer_indices)
    if skip_layers:
        kwargs["skip_layers"] = list(skip_layers)

    layers = parser.get_type_contours_per_layer(**kwargs)
    if not layers:
        details = {
            "parameter": parameter,
            "target_types": type_names,
            "checked_layers": [],
            "checked_layer": None,
            "layer_indices": list(layer_indices or []),
            "skip_layers": list(skip_layers or []),
            "objects_total": 0,
            "regions_total": 0,
            "regions_checked": 0,
            "expected": expected_val,
            "tolerance": tolerance,
            "matches": [],
            "mismatches": [],
            "missing_velocity_limits": [],
            "missing_corner_key": [],
            "actual_values_set": [],
            "by_object": {},
            "by_type": {},
            "note": "No layers returned for the given filter.",
            "match": False,
        }
        return False, expected_val, details

    total_regions = 0
    checked_regions = 0
    matches: List[Dict[str, Any]] = []
    mismatches: List[Dict[str, Any]] = []
    missing_limits: List[Dict[str, Any]] = []
    missing_corner: List[Dict[str, Any]] = []
    actual_values: List[float] = []
    objects_seen = set()
    layers_seen = []
    by_object: Dict[int, Dict[str, Any]] = {}
    by_type: Dict[str, Dict[str, Any]] = {}

    for layer in layers:
        layers_seen.append(layer.index)
        region_map = layer.regions or {}
        for oid, type_map in (region_map or {}).items():
            objects_seen.add(oid)
            for type_name, region in (type_map or {}).items():
                total_regions += 1
                limits = dict(region.velocity_limits or {})
                record = {
                    "parameter": parameter,
                    "layer": layer.index,
                    "object_id": oid,
                    "type": type_name,
                    "velocity_limits": limits,
                    "expected": expected_val,
                }

                obj_agg = by_object.setdefault(
                    oid,
                    {"regions": 0, "checked": 0, "mismatch": 0, "missing_limits": 0,
                     "missing_corner": 0, "values": set()},
                )
                obj_agg["regions"] += 1

                type_agg = by_type.setdefault(
                    type_name,
                    {"regions": 0, "checked": 0, "mismatch": 0, "missing_limits": 0,
                     "missing_corner": 0, "values": set()},
                )
                type_agg["regions"] += 1

                if not limits:
                    record["status"] = "missing_velocity_limits"
                    missing_limits.append(record)
                    obj_agg["missing_limits"] += 1
                    type_agg["missing_limits"] += 1
                    continue

                corner_val = limits.get(SQUARE_CORNER_KEY)
                try:
                    corner_numeric = float(corner_val) if corner_val is not None else None
                except (TypeError, ValueError):
                    corner_numeric = None

                if corner_numeric is None:
                    record["status"] = "missing_corner_key"
                    record["actual_corner_value"] = corner_val
                    missing_corner.append(record)
                    obj_agg["missing_corner"] += 1
                    type_agg["missing_corner"] += 1
                    continue

                obj_agg["checked"] += 1
                type_agg["checked"] += 1
                checked_regions += 1
                obj_agg["values"].add(corner_numeric)
                type_agg["values"].add(corner_numeric)
                actual_values.append(corner_numeric)

                diff = corner_numeric - expected_val
                record["actual"] = corner_numeric
                record["diff"] = diff
                record["tolerance"] = tolerance

                if abs(diff) <= tolerance:
                    record["status"] = "ok"
                    matches.append(record)
                else:
                    record["status"] = "mismatch"
                    mismatches.append(record)
                    obj_agg["mismatch"] += 1
                    type_agg["mismatch"] += 1

    def _finalize(summary: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(summary)
        values = out.pop("values", set())
        out["values"] = sorted(values)
        return out

    summary_by_object = {oid: _finalize(agg) for oid, agg in by_object.items()}
    summary_by_type = {typ: _finalize(agg) for typ, agg in by_type.items()}
    checked_layers_sorted = sorted(set(layers_seen))
    checked_layer = checked_layers_sorted[0] if len(checked_layers_sorted) == 1 else None

    ok = checked_regions > 0 and not mismatches and not missing_limits and not missing_corner
    note = None
    if checked_regions == 0:
        note = "No regions with valid SQUARE_CORNER_VELOCITY were found."

    details = {
        "parameter": parameter,
        "target_types": type_names,
        "checked_layers": checked_layers_sorted,
        "checked_layer": checked_layer,
        "layer_indices": list(layer_indices or []),
        "skip_layers": list(skip_layers or []),
        "objects_total": len(objects_seen),
        "regions_total": total_regions,
        "regions_checked": checked_regions,
        "expected": expected_val,
        "tolerance": tolerance,
        "matches": matches,
        "mismatches": mismatches,
        "missing_velocity_limits": missing_limits,
        "missing_corner_key": missing_corner,
        "actual_values_set": sorted(set(actual_values)),
        "by_object": summary_by_object,
        "by_type": summary_by_type,
        "note": note,
        "match": ok,
    }
    return ok, expected_val, details


def parse_outer_wall_jerk(
        gcode_path: Path | str,
        expected_value: float,
        tolerance: float = 1e-6,
) -> Tuple[bool, float, Dict[str, Any]]:
    return _parse_square_corner_common(
        gcode_path,
        expected_value,
        tolerance,
        parameter="outer_wall_jerk",
        target_types=[ExtrusionType.OUTER_WALL],
        skip_layers=[0],
    )


def parse_inner_wall_jerk(
        gcode_path: Path | str,
        expected_value: float,
        tolerance: float = 1e-6,
) -> Tuple[bool, float, Dict[str, Any]]:
    return _parse_square_corner_common(
        gcode_path,
        expected_value,
        tolerance,
        parameter="inner_wall_jerk",
        target_types=[ExtrusionType.INNER_WALL],
        skip_layers=[0],
    )


def parse_default_jerk(
        gcode_path: Path | str,
        expected_value: float,
        tolerance: float = 1e-6,
) -> Tuple[bool, float, Dict[str, Any]]:
    return _parse_square_corner_common(
        gcode_path,
        expected_value,
        tolerance,
        parameter="default_jerk",
        target_types=[
            ExtrusionType.GAP_INFILL,
            ExtrusionType.SUPPORT,
            ExtrusionType.SUPPORT_INTERFACE,
        ],
        skip_layers=[0],
    )


def parse_infill_jerk(
        gcode_path: Path | str,
        expected_value: float,
        tolerance: float = 1e-6,
        *,
        extrusion_types: Sequence[ExtrusionType | str | bytes],
) -> Tuple[bool, float, Dict[str, Any]]:
    return _parse_square_corner_common(
        gcode_path,
        expected_value,
        tolerance,
        parameter="infill_jerk",
        target_types=extrusion_types,
        skip_layers=[0],
    )


def parse_initial_layer_jerk(
        gcode_path: Path | str,
        expected_value: float,
        tolerance: float = 1e-6,
) -> Tuple[bool, float, Dict[str, Any]]:
    return _parse_square_corner_common(
        gcode_path,
        expected_value,
        tolerance,
        parameter="initial_layer_jerk",
        target_types=None,
        layer_indices=[0],
    )


def parse_top_surface_jerk(
        gcode_path: Path | str,
        expected_value: float,
        tolerance: float = 1e-6,
) -> Tuple[bool, float, Dict[str, Any]]:
    return _parse_square_corner_common(
        gcode_path,
        expected_value,
        tolerance,
        parameter="top_surface_jerk",
        target_types=[ExtrusionType.TOP_SURFACE],
        skip_layers=[0],
    )


# Compatibility for callers outside the parameter suite.
parse_top_surface_acceleration = parse_top_surface_jerk
