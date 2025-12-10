# engine_params/src/gcode/speed/initial_layer_speed_check.py
from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple, List, Any, Set, Optional

from engine_params.src.gcode.GCodeParserEx import GCodeParserEx, ParsedConfig
from engine_params.src.gcode.constants import ExtrusionType

# ================== initial_layer_speed ==================

# 仅核对这些首层类型（以枚举传入）
TARGET_TYPES: Set[ExtrusionType] = {
    ExtrusionType.INNER_WALL,
    ExtrusionType.OUTER_WALL,
    ExtrusionType.GAP_INFILL,
    ExtrusionType.BRIM,
    ExtrusionType.SUPPORT,
}


def parse_initial_layer_speed(
        gcode_path: Path | str,
        expected_speed: float,
        tolerance: float = 1e-6,
) -> Tuple[bool, float, Dict[str, Any]]:
    """
    仅检查首层 (layer 0) 中 TARGET_TYPES 的 LayerRegion.feedrate（mm/s）是否等于期望值。
    - 解析器会用 TARGET_TYPES 过滤类型；因此无需在此处二次过滤或维护“跳过列表”（如 PRIME_TOWER）。
    """
    path_obj = Path(gcode_path)
    parser = GCodeParserEx(path_obj)

    # 只解析首层，且仅请求我们关心的类型（以“枚举集合”传入）
    layers = parser.get_type_contours_per_layer(
        types=TARGET_TYPES,
        layer_indices=[0],
    )

    mismatches: List[Dict[str, Any]] = []
    matches: List[Dict[str, Any]] = []
    missing_feedrate_regions: List[Dict[str, Any]] = []
    actual_values_all: List[float] = []

    if not layers:
        details = {
            "checked_layer": 0,
            "regions_total": 0,
            "regions_checked": 0,
            "types_requested": sorted([t.value for t in TARGET_TYPES]),
            "expected": expected_speed,
            "tolerance": tolerance,
            "mismatches": mismatches,
            "matches": matches,
            "missing_feedrate_regions": missing_feedrate_regions,
            "actual_values_set": [],
            "by_type": {},
            "match": False,
            "note": "No layers parsed; check slicing output or markers.",
        }
        return False, expected_speed, details

    first_layer = layers[0]
    by_type: Dict[str, Dict[str, Any]] = {}
    total_regions = 0
    checked_regions = 0

    for oid, region_map in (first_layer.regions or {}).items():
        for rtype, region in (region_map or {}).items():
            # 这里的 rtype 已经被解析器按 TARGET_TYPES 过滤后转换成规范字符串（如 "Inner wall"）
            total_regions += 1
            checked_regions += 1

            item = {
                "layer": first_layer.index,
                "object_id": oid,
                "type": rtype,  # 规范显示值
                "region_feedrate": region.feedrate,  # mm/s
                "expected": expected_speed,  # mm/s
                "tolerance": tolerance,
            }

            if region.feedrate is None:
                item["status"] = "missing_region_feedrate"
                missing_feedrate_regions.append(item)
            else:
                actual = float(region.feedrate)
                actual_values_all.append(actual)
                diff = actual - float(expected_speed)
                item["diff"] = diff
                if abs(diff) <= tolerance:
                    item["status"] = "ok"
                    matches.append(item)
                else:
                    item["status"] = "mismatch"
                    mismatches.append(item)

            agg = by_type.setdefault(rtype, {"count": 0, "mismatch": 0, "missing": 0, "values": set()})
            agg["count"] += 1
            if region.feedrate is None:
                agg["missing"] += 1
            else:
                agg["values"].add(float(region.feedrate))
                if item["status"] == "mismatch":
                    agg["mismatch"] += 1

    for rtype, agg in by_type.items():
        agg["values"] = sorted(list(agg["values"]))

    details = {
        "checked_layer": 0,
        "regions_total": total_regions,
        "regions_checked": checked_regions,
        "types_requested": sorted([t.value for t in TARGET_TYPES]),
        "expected": expected_speed,
        "tolerance": tolerance,
        "mismatches": mismatches,
        "matches": matches,
        "missing_feedrate_regions": missing_feedrate_regions,
        "actual_values_set": sorted(list(set(actual_values_all))),
        "by_type": by_type,
        "match": (len(mismatches) == 0 and len(missing_feedrate_regions) == 0 and checked_regions > 0),
    }

    ok = details["match"]
    return ok, expected_speed, details


# ================== initial_layer_infill_speed ==================

def parse_initial_layer_infill_speed(
        gcode_path: Path | str,
        expected_speed: float,
        tolerance: float = 1e-6,
) -> Tuple[bool, float, Dict[str, Any]]:
    """
    只检查首层 (layer 0) 的 initial_layer_infill_speed 是否与期望一致。
    参与核对的类型：BOTTOM_SURFACE
    """
    path_obj = Path(gcode_path)
    parser = GCodeParserEx(path_obj)

    # 直接传递BOTTOM_SURFACE类型，只解析首层，加速
    layers = parser.get_type_contours_per_layer(types=[ExtrusionType.BOTTOM_SURFACE], layer_indices=[0])
    mismatches: List[Dict[str, Any]] = []
    matches: List[Dict[str, Any]] = []
    missing_feedrate_regions: List[Dict[str, Any]] = []
    actual_values_all: List[float] = []

    if not layers:
        details = {
            "checked_layer": 0,
            "regions_total": 0,
            "regions_checked": 0,
            "regions_skipped_types": [],
            "expected": expected_speed,
            "tolerance": tolerance,
            "mismatches": mismatches,
            "matches": matches,
            "missing_feedrate_regions": missing_feedrate_regions,
            "actual_values_set": [],
            "by_type": {},
            "match": False,
            "note": "No layers parsed; check slicing output or markers.",
        }
        return False, expected_speed, details

    first_layer = layers[0]
    by_type: Dict[str, Dict[str, Any]] = {}
    total_regions = 0
    checked_regions = 0

    # 直接遍历所有BOTTOM_SURFACE类型的区域
    for oid, region_map in (first_layer.regions or {}).items():
        for rtype, region in (region_map or {}).items():
            total_regions += 1
            checked_regions += 1

            item = {
                "layer": first_layer.index,
                "object_id": oid,
                "type": rtype,
                "region_feedrate": region.feedrate,
                "expected": expected_speed,
                "tolerance": tolerance,
            }

            if region.feedrate is None:
                item["status"] = "missing_region_feedrate"
                missing_feedrate_regions.append(item)
            else:
                actual_values_all.append(float(region.feedrate))
                diff = float(region.feedrate) - float(expected_speed)
                item["diff"] = diff
                if abs(diff) <= tolerance:
                    item["status"] = "ok"
                    matches.append(item)
                else:
                    item["status"] = "mismatch"
                    mismatches.append(item)

            agg = by_type.setdefault(rtype, {"count": 0, "mismatch": 0, "missing": 0, "values": set()})
            agg["count"] += 1
            if region.feedrate is None:
                agg["missing"] += 1
            else:
                agg["values"].add(float(region.feedrate))
                if item["status"] == "mismatch":
                    agg["mismatch"] += 1

    for rtype, agg in by_type.items():
        agg["values"] = sorted(list(agg["values"]))

    details = {
        "checked_layer": 0,
        "regions_total": total_regions,
        "regions_checked": checked_regions,
        "regions_skipped_types": [],
        "expected": expected_speed,
        "tolerance": tolerance,
        "mismatches": mismatches,
        "matches": matches,
        "missing_feedrate_regions": missing_feedrate_regions,
        "actual_values_set": sorted(list(set(actual_values_all))),
        "by_type": by_type,
        "match": (len(mismatches) == 0 and len(missing_feedrate_regions) == 0 and checked_regions > 0),
    }

    ok = details["match"]
    return ok, expected_speed, details


# ================== initial_layer_travel_speed ==================

def parse_initial_layer_travel_speed(
        gcode_path: Path | str,
        expected_speed: float,
        tolerance: float = 1e-6,
) -> Tuple[bool, float, Dict[str, Any]]:
    """
    检查首层 (layer 1) 中返回的paths中点的kind为travel的点的f值是否与期望值一致。
    
    参数
    ----
    gcode_path : Path | str
        G-code 文件路径。
    expected_speed : float
        期望的初始层移动速度值（mm/s）。
    tolerance : float
        容差值，默认为 1e-6。

    返回
    ----
    (ok, expected, details) : Tuple[bool, float, Dict[str, Any]]
        - ok : bool
            校验是否通过。
        - expected : float
            原样返回的 `expected_speed`。
        - details : Dict[str, Any]
            细节信息字典，包含检查的详细结果。
    """
    path_obj = Path(gcode_path)
    parser = GCodeParserEx(path_obj)

    # 调用 get_motion_paths_for_layer 获取首层（layer_index=0）的所有运动路径点
    motion_path = parser.get_motion_paths_for_layer(layer_index=0)

    mismatches: List[Dict[str, Any]] = []
    travel_points_count = 0
    actual_values_all: List[float] = []

    if not motion_path:
        details = {
            "checked_layer": 0,
            "travel_points_count": travel_points_count,
            "expected": expected_speed,
            "tolerance": tolerance,
            "mismatches": mismatches,
            "actual_values_set": [],
            "match": False,
            "note": "No motion paths parsed for layer 1; check slicing output or layer index.",
        }
        return False, expected_speed, details

    points_total = len(motion_path)
    points_checked = 0

    # 遍历所有点，筛选出 kind 为 'travel' 的点
    for idx, point in enumerate(motion_path):
        if point.kind == "travel" and point.extrusion_type != ExtrusionType.PRIME_TOWER.value:
            points_checked += 1
            travel_points_count += 1

            item = {
                "layer": 1,
                "index": idx,  # 记录点在motion_path中的序号
                "x": point.x,
                "y": point.y,
                "z": point.z,
                "f": point.f,
                "expected": expected_speed,
                "tolerance": tolerance,
            }

            actual = float(point.f)
            actual_values_all.append(actual)
            diff = actual - float(expected_speed)
            item["diff"] = diff

            if abs(diff) > tolerance:
                item["status"] = "mismatch"
                mismatches.append(item)

    details = {
        "checked_layer": 0,
        "points_total": points_total,
        "points_checked": points_checked,
        "travel_points_count": travel_points_count,
        "expected": expected_speed,
        "tolerance": tolerance,
        "mismatches": mismatches,
        "actual_values_set": sorted(list(set(actual_values_all))) if actual_values_all else [],
        "match": (len(mismatches) == 0 and points_checked > 0),
    }

    ok = details["match"]
    return ok, expected_speed, details


# ================== slow_down_layers ==================

def parse_slow_down_layers(
        gcode_path: Path | str,
        expected_layers: int,
        tolerance: float = 1e-6,
) -> Tuple[bool, int, Dict[str, Any]]:
    """
    校验慢速打印层数：首层起按线性插值逐层提升到正常速度（同类型对比）。
    - max_layers=expected_layers 读取前若干层的 LayerRegion.feedrate。
    - 层 i 期望值：V0 + (Vn-V0)/N * min(i, N)，其中 V0 来自 initial_layer_*，Vn 为对应正常速度。
    - 类型映射：
        OUTER_WALL/INNER_WALL -> initial_layer_speed 对比 outer_wall_speed/inner_wall_speed
        SPARSE_INFILL/INTERNAL_SOLID_INFILL -> initial_layer_infill_speed 对比 sparse_infill_speed/solid_infill_speed
    """
    path_obj = Path(gcode_path)
    parser = GCodeParserEx(path_obj)

    N = int(expected_layers)
    layers = parser.get_type_contours_per_layer(max_layers=N, use_cache_when_all_types=False)

    type_pairs = {
        ExtrusionType.OUTER_WALL.value: ("initial_layer_speed", "outer_wall_speed"),
        ExtrusionType.INNER_WALL.value: ("initial_layer_speed", "inner_wall_speed"),
        ExtrusionType.SPARSE_INFILL.value: ("initial_layer_infill_speed", "sparse_infill_speed"),
        ExtrusionType.INTERNAL_SOLID_INFILL.value: ("initial_layer_infill_speed", "solid_infill_speed"),
    }

    def _expected_for_type(tname: str) -> Tuple[float, float] | None:
        pair = type_pairs.get(tname)
        if not pair:
            return None
        cfg0 = parser.get_config(pair[0])
        cfgn = parser.get_config(pair[1])
        try:
            v0 = float(cfg0.value) if cfg0 is not None else None
            vn = float(cfgn.value) if cfgn is not None else None
        except (TypeError, ValueError):
            v0 = vn = None
        if v0 is None or vn is None:
            return None
        return v0, vn

    total_regions = 0
    checked_regions = 0
    matches: List[Dict[str, Any]] = []
    mismatches: List[Dict[str, Any]] = []
    missing_feedrate: List[Dict[str, Any]] = []
    skipped_types: Set[str] = set()
    actual_values: List[float] = []
    by_type: Dict[str, Dict[str, Any]] = {}

    for layer in layers:
        i = layer.index
        for oid, type_map in (layer.regions or {}).items():
            for tname, region in (type_map or {}).items():
                total_regions += 1
                pair_vals = _expected_for_type(tname)
                if pair_vals is None:
                    skipped_types.add(tname)
                    continue
                v0, vn = pair_vals
                denom = max(1, N)
                target = v0 + (vn - v0) * min(i, N) / denom

                item = {
                    "layer": i,
                    "object_id": oid,
                    "type": tname,
                    "expected": target,
                    "tolerance": tolerance,
                    "v0": v0,
                    "vn": vn,
                }

                by_type.setdefault(tname, {"regions": 0, "mismatch": 0, "missing": 0, "values": set()})
                by_type[tname]["regions"] += 1

                if region.feedrate is None:
                    item["status"] = "missing_feedrate"
                    missing_feedrate.append(item)
                    by_type[tname]["missing"] += 1
                    continue

                actual = float(region.feedrate)
                actual_values.append(actual)
                diff = actual - target
                item["actual"] = actual
                item["diff"] = diff

                if abs(diff) <= tolerance:
                    item["status"] = "ok"
                    matches.append(item)
                else:
                    item["status"] = "mismatch"
                    mismatches.append(item)
                    by_type[tname]["mismatch"] += 1

                checked_regions += 1
                by_type[tname]["values"].add(actual)

    for t, agg in by_type.items():
        agg["values"] = sorted(agg.get("values", []))

    details = {
        "checked_layer": None,
        "checked_layers": sorted({ly.index for ly in layers}),
        "regions_total": total_regions,
        "regions_checked": checked_regions,
        "expected_layers": N,
        "expected": N,
        "tolerance": tolerance,
        "matches": matches,
        "mismatches": mismatches,
        "missing_feedrate_regions": missing_feedrate,
        "actual_values_set": sorted(set(actual_values)),
        "by_type": by_type,
        "skipped_types": sorted(skipped_types),
        "note": None if layers else "No layers parsed.",
        "match": (checked_regions > 0 and not mismatches and not missing_feedrate),
    }
    ok = details["match"]
    return ok, N, details
