# engine_params/src/gcode/speed/acceleration_check.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from engine_params.src.gcode.GCodeParserEx import GCodeParserEx
from engine_params.src.gcode.constants import ACCEL_KEY, ExtrusionType

ACCEL_TO_DECEL_KEY = "ACCEL_TO_DECEL"

TypeSeq = Optional[Sequence[ExtrusionType | str | bytes]]


def _canonical_type_names(types: TypeSeq, *, default: Optional[str] = "<all>") -> List[str]:
    if not types:
        return [default] if default is not None else []
    names = set()
    for t in types:
        if isinstance(t, ExtrusionType):
            names.add(t.value)
        else:
            canon = ExtrusionType.to_str(t)
            names.add(canon if canon else str(t))
    return sorted(names)


def _parse_acceleration_common(
        gcode_path: Path | str,
        expected_acceleration: float,
        tolerance: float,
        *,
        parameter: str,
        target_types: TypeSeq = None,
        layer_indices: Optional[Sequence[int]] = None,
        skip_layers: Optional[Sequence[int]] = None,
        exclude_types: TypeSeq = None,
) -> Tuple[bool, float, Dict[str, Any]]:
    """
    通用的加速度检查逻辑：
    1. 通过 `get_type_contours_per_layer` 选取需要验证的 LayerRegion（支持类型、层范围与跳过层等过滤）。
    2. 可传入 `exclude_types`，在同一批 LayerRegion 中跳过部分挤出类型（例如 default_acceleration 需要排除墙/桥等挤出）。
    3. 遍历所有候选 Region：
       - 记录 velocity_limits 是否存在、ACCEL 是否可解析、以及与期望值的偏差。
       - 使用 by_object / by_type 聚合统计，方便失败时快速定位。
    4. 汇总详情（checked layers、region 计数、缺失项、去重的实际值等），供上层测试格式化输出。
    """
    path_obj = Path(gcode_path)
    parser = GCodeParserEx(path_obj)

    type_names = _canonical_type_names(target_types)
    if exclude_types:
        excluded_names = _canonical_type_names(exclude_types, default=None)
        exclude_filter = set(excluded_names)
    else:
        excluded_names = []
        exclude_filter = set()
    expected_val = float(expected_acceleration)

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
            "excluded_types": excluded_names,
            "checked_layers": [],
            "checked_layer": None,
            "skip_layers": list(skip_layers or []),
            "layer_indices": list(layer_indices or []),
            "objects_total": 0,
            "regions_total": 0,
            "regions_checked": 0,
            "expected": expected_val,
            "tolerance": tolerance,
            "matches": [],
            "mismatches": [],
            "missing_velocity_limits": [],
            "missing_accel_key": [],
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
    missing_accel: List[Dict[str, Any]] = []
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
                if exclude_filter and type_name in exclude_filter:
                    continue

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
                     "missing_accel": 0, "values": set()},
                )
                obj_agg["regions"] += 1

                type_agg = by_type.setdefault(
                    type_name,
                    {"regions": 0, "checked": 0, "mismatch": 0, "missing_limits": 0,
                     "missing_accel": 0, "values": set()},
                )
                type_agg["regions"] += 1

                if not limits:
                    record["status"] = "missing_velocity_limits"
                    missing_limits.append(record)
                    obj_agg["missing_limits"] += 1
                    type_agg["missing_limits"] += 1
                    continue

                accel_val = limits.get(ACCEL_KEY)
                if accel_val is None:
                    record["status"] = "missing_accel_key"
                    missing_accel.append(record)
                    obj_agg["missing_accel"] += 1
                    type_agg["missing_accel"] += 1
                    continue

                try:
                    actual = float(accel_val)
                except (TypeError, ValueError):
                    actual = None

                if actual is None:
                    record["status"] = "invalid_accel_value"
                    record["actual"] = accel_val
                    missing_accel.append(record)
                    obj_agg["missing_accel"] += 1
                    type_agg["missing_accel"] += 1
                    continue

                obj_agg["checked"] += 1
                type_agg["checked"] += 1
                checked_regions += 1
                obj_agg["values"].add(actual)
                type_agg["values"].add(actual)
                actual_values.append(actual)

                diff = actual - expected_val
                record["actual"] = actual
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

    def _finalize_summary(summary: Dict[str, Any]) -> Dict[str, Any]:
        result = dict(summary)
        values = result.pop("values", set())
        result["values"] = sorted(values)
        return result

    summary_by_object = {oid: _finalize_summary(agg) for oid, agg in by_object.items()}
    summary_by_type = {typ: _finalize_summary(agg) for typ, agg in by_type.items()}

    checked_layers_sorted = sorted(set(layers_seen))
    checked_layer = checked_layers_sorted[0] if len(checked_layers_sorted) == 1 else None

    ok = checked_regions > 0 and not mismatches and not missing_limits and not missing_accel
    note = None
    if not ok and total_regions == 0:
        note = "No regions found for the requested types."

    details = {
        "parameter": parameter,
        "target_types": type_names,
        "excluded_types": excluded_names,
        "checked_layers": checked_layers_sorted,
        "checked_layer": checked_layer,
        "skip_layers": list(skip_layers or []),
        "layer_indices": list(layer_indices or []),
        "objects_total": len(objects_seen),
        "regions_total": total_regions,
        "regions_checked": checked_regions,
        "expected": expected_val,
        "tolerance": tolerance,
        "matches": matches,
        "mismatches": mismatches,
        "missing_velocity_limits": missing_limits,
        "missing_accel_key": missing_accel,
        "actual_values_set": sorted(set(actual_values)),
        "by_object": summary_by_object,
        "by_type": summary_by_type,
        "note": note,
        "match": ok,
    }
    return ok, expected_val, details


def parse_initial_layer_acceleration(
        gcode_path: Path | str,
        expected_acceleration: float,
        tolerance: float = 1e-6,
) -> Tuple[bool, float, Dict[str, Any]]:
    return _parse_acceleration_common(
        gcode_path,
        expected_acceleration,
        tolerance,
        parameter="initial_layer_acceleration",
        target_types=None,
        layer_indices=[0],
    )


def parse_outer_wall_acceleration(
        gcode_path: Path | str,
        expected_acceleration: float,
        tolerance: float = 1e-6,
) -> Tuple[bool, float, Dict[str, Any]]:
    return _parse_acceleration_common(
        gcode_path,
        expected_acceleration,
        tolerance,
        parameter="outer_wall_acceleration",
        target_types=[ExtrusionType.OUTER_WALL],
        skip_layers=[0],
    )


def parse_inner_wall_acceleration(
        gcode_path: Path | str,
        expected_acceleration: float,
        tolerance: float = 1e-6,
) -> Tuple[bool, float, Dict[str, Any]]:
    return _parse_acceleration_common(
        gcode_path,
        expected_acceleration,
        tolerance,
        parameter="inner_wall_acceleration",
        target_types=[ExtrusionType.INNER_WALL],
        skip_layers=[0],
    )


def parse_bridge_acceleration(
        gcode_path: Path | str,
        expected_acceleration: float,
        tolerance: float = 1e-6,
) -> Tuple[bool, float, Dict[str, Any]]:
    return _parse_acceleration_common(
        gcode_path,
        expected_acceleration,
        tolerance,
        parameter="bridge_acceleration",
        target_types=[ExtrusionType.BRIDGE, ExtrusionType.INTERNAL_BRIDGE],
        skip_layers=[0],
    )


def parse_sparse_infill_acceleration(
        gcode_path: Path | str,
        expected_acceleration: float,
        tolerance: float = 1e-6,
) -> Tuple[bool, float, Dict[str, Any]]:
    return _parse_acceleration_common(
        gcode_path,
        expected_acceleration,
        tolerance,
        parameter="sparse_infill_acceleration",
        target_types=[ExtrusionType.SPARSE_INFILL],
        skip_layers=[0],
    )


def parse_internal_solid_infill_acceleration(
        gcode_path: Path | str,
        expected_acceleration: float,
        tolerance: float = 1e-6,
) -> Tuple[bool, float, Dict[str, Any]]:
    return _parse_acceleration_common(
        gcode_path,
        expected_acceleration,
        tolerance,
        parameter="internal_solid_infill_acceleration",
        target_types=[ExtrusionType.INTERNAL_SOLID_INFILL],
        skip_layers=[0],
    )


def parse_top_surface_acceleration(
        gcode_path: Path | str,
        expected_acceleration: float,
        tolerance: float = 1e-6,
) -> Tuple[bool, float, Dict[str, Any]]:
    return _parse_acceleration_common(
        gcode_path,
        expected_acceleration,
        tolerance,
        parameter="top_surface_acceleration",
        target_types=[ExtrusionType.TOP_SURFACE],
        skip_layers=[0],
    )


def parse_accel_to_decel_enable(
        gcode_path: Path | str,
        expected_enable: bool,
) -> Tuple[bool, bool, Dict[str, Any]]:
    """
    校验 ACCEL_TO_DECEL 开关：
    - 当 expected_enable=True 时，所有 LayerRegion.velocity_limits 中都应包含 ACCEL_TO_DECEL 键（且值非 None）
    - 当 expected_enable=False 时，所有 LayerRegion.velocity_limits 中都不应包含有效的 ACCEL_TO_DECEL 值
    """
    path_obj = Path(gcode_path)
    parser = GCodeParserEx(path_obj)

    layers = parser.get_type_contours_per_layer()
    if not layers:
        details = {
            "parameter": "accel_to_decel_enable",
            "target_types": ["<all>"],
            "checked_layers": [],
            "checked_layer": None,
            "skip_layers": [],
            "layer_indices": [],
            "objects_total": 0,
            "regions_total": 0,
            "regions_checked": 0,
            "expected": expected_enable,
            "tolerance": None,
            "expected_enable": expected_enable,
            "matches": [],
            "mismatches": [],
            "missing_velocity_limits": [],
            "missing_accel_key": [],
            "actual_values_set": [],
            "by_object": {},
            "by_type": {},
            "note": "No layers returned for the given filter.",
            "match": False,
        }
        return False, expected_enable, details

    total_regions = 0
    objects_seen = set()
    layers_seen = []
    matches: List[Dict[str, Any]] = []
    mismatches: List[Dict[str, Any]] = []
    actual_values: List[float] = []

    for layer in layers:
        layers_seen.append(layer.index)
        region_map = layer.regions or {}
        for oid, type_map in (region_map or {}).items():
            objects_seen.add(oid)
            for type_name, region in (type_map or {}).items():
                total_regions += 1
                limits = region.velocity_limits or {}
                raw_value = limits.get(ACCEL_TO_DECEL_KEY)
                if isinstance(raw_value, str):
                    raw_value_stripped = raw_value.strip()
                    raw_value = raw_value if raw_value_stripped else None
                has_value = raw_value is not None
                numeric_value = None
                if raw_value is not None:
                    try:
                        numeric_value = float(raw_value)
                        actual_values.append(numeric_value)
                    except (TypeError, ValueError):
                        # 将无法解析的字符串视为有值，仅用于记录
                        pass

                actual_enable = has_value
                record = {
                    "parameter": "accel_to_decel_enable",
                    "layer": layer.index,
                    "object_id": oid,
                    "type": type_name,
                    "actual_value": raw_value,
                    "expected_enable": expected_enable,
                    "actual_enable": actual_enable,
                }

                if actual_enable == expected_enable:
                    record["status"] = "ok"
                    matches.append(record)
                else:
                    record["status"] = "mismatch"
                    mismatches.append(record)

    checked_layers_sorted = sorted(set(layers_seen))
    ok = (total_regions > 0) and (not mismatches)

    details = {
        "parameter": "accel_to_decel_enable",
        "target_types": ["<all>"],
        "checked_layers": checked_layers_sorted,
        "checked_layer": None if len(checked_layers_sorted) != 1 else checked_layers_sorted[0],
        "skip_layers": [],
        "layer_indices": [],
        "objects_total": len(objects_seen),
        "regions_total": total_regions,
        "regions_checked": total_regions,
        "expected": expected_enable,
        "tolerance": None,
        "expected_enable": expected_enable,
        "matches": matches,
        "mismatches": mismatches,
        "missing_velocity_limits": [],
        "missing_accel_key": [],
        "actual_values_set": sorted(set(actual_values)),
        "by_object": {},
        "by_type": {},
        "note": None if ok else "ACCEL_TO_DECEL presence does not match expected enable flag.",
        "match": ok,
    }
    return ok, expected_enable, details


def parse_accel_to_decel_factor(
        gcode_path: Path | str,
        expected_factor: float,
        tolerance: float = 1e-6,
) -> Tuple[bool, float, Dict[str, Any]]:
    """
    校验 ACCEL_TO_DECEL / ACCEL 的比值是否为期望的 factor。
    - 遍历所有 LayerRegion（不跳过任何层/类型），需要 velocity_limits 同时包含 ACCEL 与 ACCEL_TO_DECEL。
    - 当任意一个键缺失或 ACCEL 为 0 时视为缺失，直接记录错误。
    """
    path_obj = Path(gcode_path)
    parser = GCodeParserEx(path_obj)

    layers = parser.get_type_contours_per_layer()
    expected_val = float(expected_factor)

    if not layers:
        details = {
            "parameter": "accel_to_decel_factor",
            "target_types": ["<all>"],
            "excluded_types": [],
            "checked_layers": [],
            "checked_layer": None,
            "skip_layers": [],
            "layer_indices": [],
            "objects_total": 0,
            "regions_total": 0,
            "regions_checked": 0,
            "expected": expected_val,
            "tolerance": tolerance,
            "matches": [],
            "mismatches": [],
            "missing_velocity_limits": [],
            "missing_accel_key": [],
            "missing_factor_key": [],
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
    missing_accel: List[Dict[str, Any]] = []
    missing_factor: List[Dict[str, Any]] = []
    actual_values: List[float] = []
    objects_seen = set()
    layers_seen = []
    by_object: Dict[int, Dict[str, Any]] = {}
    by_type: Dict[str, Dict[str, Any]] = {}

    def _agg(target: Dict, key: int | str):
        return target.setdefault(
            key,
            {
                "regions": 0,
                "checked": 0,
                "mismatch": 0,
                "missing_limits": 0,
                "missing_accel": 0,
                "missing_factor": 0,
                "values": set(),
            },
        )

    for layer in layers:
        layers_seen.append(layer.index)
        region_map = layer.regions or {}
        for oid, type_map in (region_map or {}).items():
            objects_seen.add(oid)
            for type_name, region in (type_map or {}).items():
                total_regions += 1
                limits = dict(region.velocity_limits or {})
                record = {
                    "parameter": "accel_to_decel_factor",
                    "layer": layer.index,
                    "object_id": oid,
                    "type": type_name,
                    "velocity_limits": limits,
                    "expected": expected_val,
                }

                obj_agg = _agg(by_object, oid)
                type_agg = _agg(by_type, type_name)
                obj_agg["regions"] += 1
                type_agg["regions"] += 1

                if not limits:
                    record["status"] = "missing_velocity_limits"
                    missing_limits.append(record)
                    obj_agg["missing_limits"] += 1
                    type_agg["missing_limits"] += 1
                    continue

                accel_val = limits.get(ACCEL_KEY)
                factor_val = limits.get(ACCEL_TO_DECEL_KEY)

                try:
                    accel_numeric = float(accel_val) if accel_val is not None else None
                except (TypeError, ValueError):
                    accel_numeric = None

                try:
                    factor_numeric = float(factor_val) if factor_val is not None else None
                except (TypeError, ValueError):
                    factor_numeric = None

                if accel_numeric is None or accel_numeric == 0:
                    record["status"] = "missing_accel_key"
                    record["actual_accel"] = accel_val
                    missing_accel.append(record)
                    obj_agg["missing_accel"] += 1
                    type_agg["missing_accel"] += 1
                    continue

                if factor_numeric is None:
                    record["status"] = "missing_factor_key"
                    record["actual_factor_value"] = factor_val
                    missing_factor.append(record)
                    obj_agg["missing_factor"] += 1
                    type_agg["missing_factor"] += 1
                    continue

                actual_ratio = factor_numeric / accel_numeric if accel_numeric else None
                if actual_ratio is None:
                    record["status"] = "invalid_ratio"
                    missing_factor.append(record)
                    obj_agg["missing_factor"] += 1
                    type_agg["missing_factor"] += 1
                    continue

                obj_agg["checked"] += 1
                type_agg["checked"] += 1
                checked_regions += 1
                obj_agg["values"].add(actual_ratio)
                type_agg["values"].add(actual_ratio)
                actual_values.append(actual_ratio)

                diff = actual_ratio - expected_val
                record["actual_ratio"] = actual_ratio
                record["actual_accel"] = accel_numeric
                record["actual_factor_value"] = factor_numeric
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

    ok = checked_regions > 0 and not mismatches and not missing_limits and not missing_accel and not missing_factor
    note = None
    if not ok and checked_regions == 0:
        note = "No region produced a valid ACCEL and ACCEL_TO_DECEL pair."

    details = {
        "parameter": "accel_to_decel_factor",
        "target_types": ["<all>"],
        "excluded_types": [],
        "checked_layers": checked_layers_sorted,
        "checked_layer": None if len(checked_layers_sorted) != 1 else checked_layers_sorted[0],
        "skip_layers": [],
        "layer_indices": [],
        "objects_total": len(objects_seen),
        "regions_total": total_regions,
        "regions_checked": checked_regions,
        "expected": expected_val,
        "tolerance": tolerance,
        "matches": matches,
        "mismatches": mismatches,
        "missing_velocity_limits": missing_limits,
        "missing_accel_key": missing_accel,
        "missing_factor_key": missing_factor,
        "actual_values_set": sorted(set(actual_values)),
        "by_object": summary_by_object,
        "by_type": summary_by_type,
        "note": note,
        "match": ok,
    }
    return ok, expected_val, details


def parse_default_acceleration(
        gcode_path: Path | str,
        expected_acceleration: float,
        tolerance: float = 1e-6,
        *,
        exclude_types: TypeSeq = None,
) -> Tuple[bool, float, Dict[str, Any]]:
    return _parse_acceleration_common(
        gcode_path,
        expected_acceleration,
        tolerance,
        parameter="default_acceleration",
        target_types=None,
        skip_layers=[0],
        exclude_types=exclude_types,
    )
