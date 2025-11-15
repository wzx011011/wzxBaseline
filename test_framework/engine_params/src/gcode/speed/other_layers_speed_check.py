# engine_params/src/gcode/speed/other_layers_speed_check.py
from pathlib import Path
from typing import Tuple, Dict, Any, List, Optional
import math

from engine_params.src.gcode.GCodeParserEx import GCodeParserEx
from engine_params.src.gcode.constants import ExtrusionType


# ================== sparse_infill_speed ==================
def parse_sparse_infill_speed(
        gcode_path: Path | str,
        expected_speed: float,
        tolerance: float = 1e-6,
) -> Tuple[bool, float, Dict[str, Any]]:
    """
    检查所有层的稀疏填充(SPARSE_INFILL)速度是否与期望一致。
    只检查SPARSE_INFILL类型的LayerRegion.feedrate
    """
    path_obj = Path(gcode_path)
    parser = GCodeParserEx(path_obj)

    # 直接传递SPARSE_INFILL类型，获取所有层的数据
    layers = parser.get_type_contours_per_layer(types=[ExtrusionType.SPARSE_INFILL], skip_layers=[0])

    mismatches: List[Dict[str, Any]] = []
    matches: List[Dict[str, Any]] = []
    missing_feedrate_regions: List[Dict[str, Any]] = []
    actual_values_all: List[float] = []

    if not layers:
        details = {
            "layers_count": 0,
            "regions_total": 0,
            "regions_checked": 0,
            "expected": expected_speed,
            "tolerance": tolerance,
            "mismatches": mismatches,
            "matches": matches,
            "missing_feedrate_regions": missing_feedrate_regions,
            "actual_values_set": [],
            "by_type": {},
            "by_layer": {},
            "match": False,
            "note": "No layers parsed; check slicing output or markers.",
        }
        return False, expected_speed, details

    by_type: Dict[str, Dict[str, Any]] = {}
    by_layer: Dict[int, Dict[str, Any]] = {}
    total_regions = 0
    checked_regions = 0

    # 遍历所有层的SPARSE_INFILL类型区域
    for layer in layers:
        layer_idx = layer.index
        layer_agg = by_layer.setdefault(layer_idx, {"count": 0, "mismatch": 0, "missing": 0, "values": set()})
        
        for oid, region_map in (layer.regions or {}).items():
            for rtype, region in (region_map or {}).items():
                total_regions += 1
                checked_regions += 1
                
                item = {
                    "layer": layer_idx,
                    "object_id": oid,
                    "type": rtype,
                    "region_feedrate": region.feedrate,
                    "expected": expected_speed,
                    "tolerance": tolerance,
                }

                if region.feedrate is None:
                    item["status"] = "missing_region_feedrate"
                    missing_feedrate_regions.append(item)
                    layer_agg["missing"] += 1
                else:
                    actual_value = float(region.feedrate)
                    actual_values_all.append(actual_value)
                    diff = actual_value - float(expected_speed)
                    item["diff"] = diff
                    
                    layer_agg["values"].add(actual_value)
                    
                    if abs(diff) <= tolerance:
                        item["status"] = "ok"
                        matches.append(item)
                    else:
                        item["status"] = "mismatch"
                        mismatches.append(item)
                        layer_agg["mismatch"] += 1

                agg = by_type.setdefault(rtype, {"count": 0, "mismatch": 0, "missing": 0, "values": set()})
                agg["count"] += 1
                if region.feedrate is None:
                    agg["missing"] += 1
                else:
                    agg["values"].add(float(region.feedrate))
                    if item["status"] == "mismatch":
                        agg["mismatch"] += 1
                
                layer_agg["count"] += 1

    # 统计最终结果
    actual_values_set = sorted(list(set(actual_values_all)))
    is_ok = len(mismatches) == 0 and len(missing_feedrate_regions) == 0

    # 准备返回的详细信息
    details = {
        "layers_count": len(layers),
        "regions_total": total_regions,
        "regions_checked": checked_regions,
        "expected": expected_speed,
        "tolerance": tolerance,
        "mismatches": mismatches,
        "matches": matches,
        "missing_feedrate_regions": missing_feedrate_regions,
        "actual_values_set": actual_values_set,
        "by_type": by_type,
        "by_layer": by_layer,
        "match": is_ok,
    }

    return is_ok, expected_speed, details


# ================== solid_infill_speed ==================
def parse_solid_infill_speed(
        gcode_path: Path | str,
        expected_speed: float,
        tolerance: float = 1e-6,
) -> Tuple[bool, float, Dict[str, Any]]:
    """
    检查所有层的实体填充(SOLID_INTERNAL_INFILL)速度是否与期望一致。
    只检查SOLID_INTERNAL_INFILL类型的LayerRegion.feedrate
    """
    path_obj = Path(gcode_path)
    parser = GCodeParserEx(path_obj)

    # 直接传递SOLID_INTERNAL_INFILL类型，获取所有层的数据
    layers = parser.get_type_contours_per_layer(types=[ExtrusionType.INTERNAL_SOLID_INFILL], skip_layers=[0])

    mismatches: List[Dict[str, Any]] = []
    matches: List[Dict[str, Any]] = []
    missing_feedrate_regions: List[Dict[str, Any]] = []
    actual_values_all: List[float] = []

    if not layers:
        details = {
            "layers_count": 0,
            "regions_total": 0,
            "regions_checked": 0,
            "expected": expected_speed,
            "tolerance": tolerance,
            "mismatches": mismatches,
            "matches": matches,
            "missing_feedrate_regions": missing_feedrate_regions,
            "actual_values_set": [],
            "by_type": {},
            "by_layer": {},
            "match": False,
            "note": "No layers parsed; check slicing output or markers.",
        }
        return False, expected_speed, details

    by_type: Dict[str, Dict[str, Any]] = {}
    by_layer: Dict[int, Dict[str, Any]] = {}
    total_regions = 0
    checked_regions = 0

    # 遍历所有层的SOLID_INTERNAL_INFILL类型区域
    for layer in layers:
        layer_idx = layer.index
        layer_agg = by_layer.setdefault(layer_idx, {"count": 0, "mismatch": 0, "missing": 0, "values": set()})
        
        for oid, region_map in (layer.regions or {}).items():
            for rtype, region in (region_map or {}).items():
                total_regions += 1
                checked_regions += 1
                
                item = {
                    "layer": layer_idx,
                    "object_id": oid,
                    "type": rtype,
                    "region_feedrate": region.feedrate,
                    "expected": expected_speed,
                    "tolerance": tolerance,
                }

                if region.feedrate is None:
                    item["status"] = "missing_region_feedrate"
                    missing_feedrate_regions.append(item)
                    layer_agg["missing"] += 1
                else:
                    actual_value = float(region.feedrate)
                    actual_values_all.append(actual_value)
                    diff = actual_value - float(expected_speed)
                    item["diff"] = diff
                    
                    layer_agg["values"].add(actual_value)
                    
                    if abs(diff) <= tolerance:
                        item["status"] = "ok"
                        matches.append(item)
                    else:
                        item["status"] = "mismatch"
                        mismatches.append(item)
                        layer_agg["mismatch"] += 1

                agg = by_type.setdefault(rtype, {"count": 0, "mismatch": 0, "missing": 0, "values": set()})
                agg["count"] += 1
                if region.feedrate is None:
                    agg["missing"] += 1
                else:
                    agg["values"].add(float(region.feedrate))
                    if item["status"] == "mismatch":
                        agg["mismatch"] += 1
                
                layer_agg["count"] += 1

    # 统计最终结果
    actual_values_set = sorted(list(set(actual_values_all)))
    is_ok = len(mismatches) == 0 and len(missing_feedrate_regions) == 0

    # 准备返回的详细信息
    details = {
        "layers_count": len(layers),
        "regions_total": total_regions,
        "regions_checked": checked_regions,
        "expected": expected_speed,
        "tolerance": tolerance,
        "mismatches": mismatches,
        "matches": matches,
        "missing_feedrate_regions": missing_feedrate_regions,
        "actual_values_set": actual_values_set,
        "by_type": by_type,
        "by_layer": by_layer,
        "match": is_ok,
    }

    return is_ok, expected_speed, details


# ================== top_surface_speed ==================
def parse_top_surface_speed(
        gcode_path: Path | str,
        expected_speed: float,
        tolerance: float = 1e-6,
) -> Tuple[bool, float, Dict[str, Any]]:
    """
    检查所有层的顶面(TOP_SURFACE)速度是否与期望一致。
    只检查TOP_SURFACE类型的LayerRegion.feedrate
    """
    path_obj = Path(gcode_path)
    parser = GCodeParserEx(path_obj)

    # 直接传递TOP_SURFACE类型，获取所有层的数据
    layers = parser.get_type_contours_per_layer(types=[ExtrusionType.TOP_SURFACE], skip_layers=[0])

    mismatches: List[Dict[str, Any]] = []
    matches: List[Dict[str, Any]] = []
    missing_feedrate_regions: List[Dict[str, Any]] = []
    actual_values_all: List[float] = []

    if not layers:
        details = {
            "layers_count": 0,
            "regions_total": 0,
            "regions_checked": 0,
            "expected": expected_speed,
            "tolerance": tolerance,
            "mismatches": mismatches,
            "matches": matches,
            "missing_feedrate_regions": missing_feedrate_regions,
            "actual_values_set": [],
            "by_type": {},
            "by_layer": {},
            "match": False,
            "note": "No layers parsed; check slicing output or markers.",
        }
        return False, expected_speed, details

    by_type: Dict[str, Dict[str, Any]] = {}
    by_layer: Dict[int, Dict[str, Any]] = {}
    total_regions = 0
    checked_regions = 0

    # 遍历所有层的TOP_SURFACE类型区域
    for layer in layers:
        layer_idx = layer.index
        layer_agg = by_layer.setdefault(layer_idx, {"count": 0, "mismatch": 0, "missing": 0, "values": set()})
        
        for oid, region_map in (layer.regions or {}).items():
            for rtype, region in (region_map or {}).items():
                total_regions += 1
                checked_regions += 1
                
                item = {
                    "layer": layer_idx,
                    "object_id": oid,
                    "type": rtype,
                    "region_feedrate": region.feedrate,
                    "expected": expected_speed,
                    "tolerance": tolerance,
                }

                if region.feedrate is None:
                    item["status"] = "missing_region_feedrate"
                    missing_feedrate_regions.append(item)
                    layer_agg["missing"] += 1
                else:
                    actual_value = float(region.feedrate)
                    actual_values_all.append(actual_value)
                    diff = actual_value - float(expected_speed)
                    item["diff"] = diff
                    
                    layer_agg["values"].add(actual_value)
                    
                    if abs(diff) <= tolerance:
                        item["status"] = "ok"
                        matches.append(item)
                    else:
                        item["status"] = "mismatch"
                        mismatches.append(item)
                        layer_agg["mismatch"] += 1

                agg = by_type.setdefault(rtype, {"count": 0, "mismatch": 0, "missing": 0, "values": set()})
                agg["count"] += 1
                if region.feedrate is None:
                    agg["missing"] += 1
                else:
                    agg["values"].add(float(region.feedrate))
                    if item["status"] == "mismatch":
                        agg["mismatch"] += 1
                
                layer_agg["count"] += 1

    # 统计最终结果
    actual_values_set = sorted(list(set(actual_values_all)))
    is_ok = len(mismatches) == 0 and len(missing_feedrate_regions) == 0

    # 准备返回的详细信息
    details = {
        "layers_count": len(layers),
        "regions_total": total_regions,
        "regions_checked": checked_regions,
        "expected": expected_speed,
        "tolerance": tolerance,
        "mismatches": mismatches,
        "matches": matches,
        "missing_feedrate_regions": missing_feedrate_regions,
        "actual_values_set": actual_values_set,
        "by_type": by_type,
        "by_layer": by_layer,
        "match": is_ok,
    }

    return is_ok, expected_speed, details


# ================== gap_infill_speed ==================
def parse_gap_infill_speed(
        gcode_path: Path | str,
        expected_speed: float,
        tolerance: float = 1e-6,
) -> Tuple[bool, float, Dict[str, Any]]:
    """
    检查所有层的间隙填充(GAP_INFILL)速度是否与期望一致。
    只检查GAP_INFILL类型的LayerRegion.feedrate
    """
    path_obj = Path(gcode_path)
    parser = GCodeParserEx(path_obj)

    # 直接传递GAP_INFILL类型，获取所有层的数据
    layers = parser.get_type_contours_per_layer(types=[ExtrusionType.GAP_INFILL], skip_layers=[0])

    mismatches: List[Dict[str, Any]] = []
    matches: List[Dict[str, Any]] = []
    missing_feedrate_regions: List[Dict[str, Any]] = []
    actual_values_all: List[float] = []

    if not layers:
        details = {
            "layers_count": 0,
            "regions_total": 0,
            "regions_checked": 0,
            "expected": expected_speed,
            "tolerance": tolerance,
            "mismatches": mismatches,
            "matches": matches,
            "missing_feedrate_regions": missing_feedrate_regions,
            "actual_values_set": [],
            "by_type": {},
            "by_layer": {},
            "match": False,
            "note": "No layers parsed; check slicing output or markers.",
        }
        return False, expected_speed, details

    by_type: Dict[str, Dict[str, Any]] = {}
    by_layer: Dict[int, Dict[str, Any]] = {}
    total_regions = 0
    checked_regions = 0

    # 遍历所有层的GAP_INFILL类型区域
    for layer in layers:
        layer_idx = layer.index
        layer_agg = by_layer.setdefault(layer_idx, {"count": 0, "mismatch": 0, "missing": 0, "values": set()})
        
        for oid, region_map in (layer.regions or {}).items():
            for rtype, region in (region_map or {}).items():
                total_regions += 1
                checked_regions += 1
                
                item = {
                    "layer": layer_idx,
                    "object_id": oid,
                    "type": rtype,
                    "region_feedrate": region.feedrate,
                    "expected": expected_speed,
                    "tolerance": tolerance,
                }

                if region.feedrate is None:
                    item["status"] = "missing_region_feedrate"
                    missing_feedrate_regions.append(item)
                    layer_agg["missing"] += 1
                else:
                    actual_value = float(region.feedrate)
                    actual_values_all.append(actual_value)
                    diff = actual_value - float(expected_speed)
                    item["diff"] = diff
                    
                    layer_agg["values"].add(actual_value)
                    
                    if abs(diff) <= tolerance:
                        item["status"] = "ok"
                        matches.append(item)
                    else:
                        item["status"] = "mismatch"
                        mismatches.append(item)
                        layer_agg["mismatch"] += 1

                agg = by_type.setdefault(rtype, {"count": 0, "mismatch": 0, "missing": 0, "values": set()})
                agg["count"] += 1
                if region.feedrate is None:
                    agg["missing"] += 1
                else:
                    agg["values"].add(float(region.feedrate))
                    if item["status"] == "mismatch":
                        agg["mismatch"] += 1
                
                layer_agg["count"] += 1

    # 统计最终结果
    actual_values_set = sorted(list(set(actual_values_all)))
    is_ok = len(mismatches) == 0 and len(missing_feedrate_regions) == 0

    # 准备返回的详细信息
    details = {
        "layers_count": len(layers),
        "regions_total": total_regions,
        "regions_checked": checked_regions,
        "expected": expected_speed,
        "tolerance": tolerance,
        "mismatches": mismatches,
        "matches": matches,
        "missing_feedrate_regions": missing_feedrate_regions,
        "actual_values_set": actual_values_set,
        "by_type": by_type,
        "by_layer": by_layer,
        "match": is_ok,
    }

    return is_ok, expected_speed, details


# ================== inner_wall_speed ==================
def parse_inner_wall_speed(
        gcode_path: Path | str,
        expected_speed: float,
        tolerance: float = 1e-6,
) -> Tuple[bool, float, Dict[str, Any]]:
    """
    检查所有层的内层壁(INNER_WALL)速度是否与期望一致。
    只检查INNER_WALL类型的LayerRegion.feedrate
    """
    path_obj = Path(gcode_path)
    parser = GCodeParserEx(path_obj)

    # 直接传递INNER_WALL类型，获取所有层的数据
    layers = parser.get_type_contours_per_layer(types=[ExtrusionType.INNER_WALL],skip_layers=[0])

    mismatches: List[Dict[str, Any]] = []
    matches: List[Dict[str, Any]] = []
    missing_feedrate_regions: List[Dict[str, Any]] = []
    actual_values_all: List[float] = []

    if not layers:
        details = {
            "layers_count": 0,
            "regions_total": 0,
            "regions_checked": 0,
            "expected": expected_speed,
            "tolerance": tolerance,
            "mismatches": mismatches,
            "matches": matches,
            "missing_feedrate_regions": missing_feedrate_regions,
            "actual_values_set": [],
            "by_type": {},
            "by_layer": {},
            "match": False,
            "note": "No layers parsed; check slicing output or markers.",
        }
        return False, expected_speed, details

    by_type: Dict[str, Dict[str, Any]] = {}
    by_layer: Dict[int, Dict[str, Any]] = {}
    total_regions = 0
    checked_regions = 0

    # 遍历所有层的INNER_WALL类型区域
    for layer in layers:
        layer_idx = layer.index
        layer_agg = by_layer.setdefault(layer_idx, {"count": 0, "mismatch": 0, "missing": 0, "values": set()})
        
        for oid, region_map in (layer.regions or {}).items():
            for rtype, region in (region_map or {}).items():
                total_regions += 1
                checked_regions += 1
                
                item = {
                    "layer": layer_idx,
                    "object_id": oid,
                    "type": rtype,
                    "region_feedrate": region.feedrate,
                    "expected": expected_speed,
                    "tolerance": tolerance,
                }

                if region.feedrate is None:
                    item["status"] = "missing_region_feedrate"
                    missing_feedrate_regions.append(item)
                    layer_agg["missing"] += 1
                else:
                    actual_value = float(region.feedrate)
                    actual_values_all.append(actual_value)
                    diff = actual_value - float(expected_speed)
                    item["diff"] = diff
                    
                    layer_agg["values"].add(actual_value)
                    
                    if abs(diff) <= tolerance:
                        item["status"] = "ok"
                        matches.append(item)
                    else:
                        item["status"] = "mismatch"
                        mismatches.append(item)
                        layer_agg["mismatch"] += 1

                agg = by_type.setdefault(rtype, {"count": 0, "mismatch": 0, "missing": 0, "values": set()})
                agg["count"] += 1
                if region.feedrate is None:
                    agg["missing"] += 1
                else:
                    agg["values"].add(float(region.feedrate))
                    if item["status"] == "mismatch":
                        agg["mismatch"] += 1
                
                layer_agg["count"] += 1

    # 统计最终结果
    actual_values_set = sorted(list(set(actual_values_all)))
    is_ok = len(mismatches) == 0 and len(missing_feedrate_regions) == 0

    # 准备返回的详细信息
    details = {
        "layers_count": len(layers),
        "regions_total": total_regions,
        "regions_checked": checked_regions,
        "expected": expected_speed,
        "tolerance": tolerance,
        "mismatches": mismatches,
        "matches": matches,
        "missing_feedrate_regions": missing_feedrate_regions,
        "actual_values_set": actual_values_set,
        "by_type": by_type,
        "by_layer": by_layer,
        "match": is_ok,
    }

    return is_ok, expected_speed, details


# ================== outer_wall_speed ==================
def parse_outer_wall_speed(
        gcode_path: Path | str,
        expected_speed: float,
        tolerance: float = 1e-6,
) -> Tuple[bool, float, Dict[str, Any]]:
    """
    检查所有层的外层壁(OUTER_WALL)速度是否与期望一致。
    只检查OUTER_WALL类型的LayerRegion.feedrate
    """
    path_obj = Path(gcode_path)
    parser = GCodeParserEx(path_obj)

    # 直接传递OUTER_WALL类型，获取所有层的数据
    layers = parser.get_type_contours_per_layer(types=[ExtrusionType.OUTER_WALL],skip_layers=[0])

    mismatches: List[Dict[str, Any]] = []
    matches: List[Dict[str, Any]] = []
    missing_feedrate_regions: List[Dict[str, Any]] = []
    actual_values_all: List[float] = []

    if not layers:
        details = {
            "layers_count": 0,
            "regions_total": 0,
            "regions_checked": 0,
            "expected": expected_speed,
            "tolerance": tolerance,
            "mismatches": mismatches,
            "matches": matches,
            "missing_feedrate_regions": missing_feedrate_regions,
            "actual_values_set": [],
            "by_type": {},
            "by_layer": {},
            "match": False,
            "note": "No layers parsed; check slicing output or markers.",
        }
        return False, expected_speed, details

    by_type: Dict[str, Dict[str, Any]] = {}
    by_layer: Dict[int, Dict[str, Any]] = {}
    total_regions = 0
    checked_regions = 0

    # 遍历所有层的OUTER_WALL类型区域
    for layer in layers:
        layer_idx = layer.index
        layer_agg = by_layer.setdefault(layer_idx, {"count": 0, "mismatch": 0, "missing": 0, "values": set()})
        
        for oid, region_map in (layer.regions or {}).items():
            for rtype, region in (region_map or {}).items():
                total_regions += 1
                checked_regions += 1
                
                item = {
                    "layer": layer_idx,
                    "object_id": oid,
                    "type": rtype,
                    "region_feedrate": region.feedrate,
                    "expected": expected_speed,
                    "tolerance": tolerance,
                }

                if region.feedrate is None:
                    item["status"] = "missing_region_feedrate"
                    missing_feedrate_regions.append(item)
                    layer_agg["missing"] += 1
                else:
                    actual_value = float(region.feedrate)
                    actual_values_all.append(actual_value)
                    diff = actual_value - float(expected_speed)
                    item["diff"] = diff
                    
                    layer_agg["values"].add(actual_value)
                    
                    if abs(diff) <= tolerance:
                        item["status"] = "ok"
                        matches.append(item)
                    else:
                        item["status"] = "mismatch"
                        mismatches.append(item)
                        layer_agg["mismatch"] += 1

                agg = by_type.setdefault(rtype, {"count": 0, "mismatch": 0, "missing": 0, "values": set()})
                agg["count"] += 1
                if region.feedrate is None:
                    agg["missing"] += 1
                else:
                    agg["values"].add(float(region.feedrate))
                    if item["status"] == "mismatch":
                        agg["mismatch"] += 1
                
                layer_agg["count"] += 1

    # 整理values为有序列表
    for rtype, agg in by_type.items():
        agg["values"] = sorted(list(agg["values"]))
    
    for layer_idx, agg in by_layer.items():
        agg["values"] = sorted(list(agg["values"]))

    details = {
        "layers_count": len(layers),
        "regions_total": total_regions,
        "regions_checked": checked_regions,
        "expected": expected_speed,
        "tolerance": tolerance,
        "mismatches": mismatches,
        "matches": matches,
        "missing_feedrate_regions": missing_feedrate_regions,
        "actual_values_set": sorted(list(set(actual_values_all))),
        "by_type": by_type,
        "by_layer": by_layer,
        "match": (len(mismatches) == 0 and len(missing_feedrate_regions) == 0 and checked_regions > 0),
    }

    ok = details["match"]
    return ok, expected_speed, details


# ================== small_perimeter_threshold ==================
def parse_small_perimeter_threshold(
        gcode_path: Path | str,
        expected_threshold: float,
        tolerance: float = 1e-6,
) -> Tuple[bool, float, Dict[str, Any]]:
    """
    当墙周长小于阈值（阈值含义为圆半径，需转 2πr）时应应用 small_perimeter_speed。
    - small_perimeter_speed 若为百分比，基于 outer_wall_speed。
    - OUTER_WALL 使用 outer_wall_speed，INNER_WALL 使用 inner_wall_speed 作为“原本”速度。
    仅检查 OUTER_WALL / INNER_WALL，首层跳过。
    """
    path_obj = Path(gcode_path)
    parser = GCodeParserEx(path_obj)

    cfg = parser.load_config() or {}
    sp_cfg = cfg.get("small_perimeter_speed")
    ow_cfg = cfg.get("outer_wall_speed")
    iw_cfg = cfg.get("inner_wall_speed")
    try:
        outer_speed = float(ow_cfg.value) if ow_cfg is not None else None
    except (TypeError, ValueError, AttributeError):
        outer_speed = None
    try:
        inner_speed = float(iw_cfg.value) if iw_cfg is not None else None
    except (TypeError, ValueError, AttributeError):
        inner_speed = None

    if sp_cfg is None or outer_speed is None or inner_speed is None:
        details = {
            "layers_count": 0,
            "regions_total": 0,
            "regions_checked": 0,
            "expected_threshold": expected_threshold,
            "tolerance": tolerance,
            "matches": [],
            "mismatches": [],
            "missing_feedrate": [],
            "missing_config": True,
            "note": "small_perimeter_speed 或 outer_wall_speed/inner_wall_speed 缺失/非法。",
            "match": False,
        }
        return False, expected_threshold, details

    try:
        sp_val = float(sp_cfg.value)
        sp_is_percent = bool(getattr(sp_cfg, "is_percent", False))
    except (TypeError, ValueError, AttributeError):
        sp_val = None
        sp_is_percent = False

    if sp_val is None:
        details = {
            "layers_count": 0,
            "expected_threshold": expected_threshold,
            "tolerance": tolerance,
            "matches": [],
            "mismatches": [],
            "missing_feedrate": [],
            "missing_config": True,
            "note": "small_perimeter_speed 值非法。",
            "match": False,
        }
        return False, expected_threshold, details

    # small_perimeter_speed 可能是百分比；阈值含义为“圆半径”，需换算成周长再比较
    small_speed = outer_speed * sp_val if sp_is_percent else sp_val
    expected_threshold_val = float(expected_threshold)
    expected_circumference = 2 * math.pi * expected_threshold_val

    layers = parser.get_type_contours_per_layer(
        types=[ExtrusionType.OUTER_WALL, ExtrusionType.INNER_WALL],
        skip_layers=[0],
    )

    matches: List[Dict[str, Any]] = []
    mismatches: List[Dict[str, Any]] = []
    missing_feedrate: List[Dict[str, Any]] = []
    actual_values: List[float] = []
    perimeters: List[float] = []

    regions_total = 0
    regions_checked = 0

    def _perimeter(path_points) -> Optional[float]:
        # path 末点与首点不重合，需补上闭合段
        pts = path_points or []
        if len(pts) < 2:
            return None
        dist = 0.0
        for a, b in zip(pts, pts[1:]):
            dist += math.hypot(b.x - a.x, b.y - a.y)
        dist += math.hypot(pts[0].x - pts[-1].x, pts[0].y - pts[-1].y)
        return dist

    if not layers:
        details = {
            "layers_count": 0,
            "expected_threshold": expected_threshold_val,
            "tolerance": tolerance,
            "matches": matches,
            "mismatches": mismatches,
            "missing_feedrate": missing_feedrate,
            "actual_values_set": [],
            "perimeters_sample": [],
            "small_speed": small_speed,
            "outer_wall_speed": outer_speed,
            "match": False,
            "note": "No layers parsed; check slicing output or markers.",
        }
        return False, expected_threshold_val, details

    for layer in layers:
        for oid, region_map in (layer.regions or {}).items():
            for rtype, region in (region_map or {}).items():
                regions_total += 1
                for path in region.paths or []:
                    perim = _perimeter(path.points)
                    if perim is None:
                        continue
                    perimeters.append(perim)
                    # OUTER 用 outer_wall_speed，INNER 用 inner_wall_speed 作为基准
                    base_speed = outer_speed if rtype == ExtrusionType.OUTER_WALL.value else inner_speed
                    expected_speed = small_speed if perim < expected_circumference else base_speed
                    actual = region.feedrate
                    # 优先 Region.feedrate，缺失时尝试路径首点 feedrate
                    if actual is None and path.points:
                        actual = path.points[0].feedrate
                    if actual is None:
                        missing_feedrate.append({
                            "layer": layer.index,
                            "object_id": oid,
                            "type": rtype,
                            "perimeter": perim,
                        })
                        continue

                    regions_checked += 1
                    actual_val = float(actual)
                    actual_values.append(actual_val)
                    diff = actual_val - expected_speed
                    item = {
                        "layer": layer.index,
                        "object_id": oid,
                        "type": rtype,
                        "perimeter": perim,
                        "expected_speed": expected_speed,
                        "actual_speed": actual_val,
                        "circumference_threshold": expected_circumference,
                        "threshold_radius": expected_threshold_val,
                        "tolerance": tolerance,
                        "diff": diff,
                    }
                    if abs(diff) <= tolerance:
                        item["status"] = "ok"
                        matches.append(item)
                    else:
                        item["status"] = "mismatch"
                        mismatches.append(item)

    ok = regions_checked > 0 and not mismatches and not missing_feedrate
    details = {
        "layers_count": len(layers),
        "expected_threshold": expected_threshold_val,
        "expected_circumference": expected_circumference,
        "tolerance": tolerance,
        "matches": matches,
        "mismatches": mismatches,
        "missing_feedrate": missing_feedrate,
        "actual_values_set": sorted(set(actual_values)),
        "perimeters_sample": sorted(perimeters)[:10],
        "small_speed": small_speed,
        "outer_wall_speed": outer_speed,
        "match": ok,
    }

    return ok, expected_threshold_val, details


# ================== small_perimeter_speed ==================
def parse_small_perimeter_speed(
        gcode_path: Path | str,
        expected_speed: float,
        tolerance: float = 1e-6,
) -> Tuple[bool, float, Dict[str, Any]]:
    """
    微小轮廓减速：当墙周长 < 2πr（r=small_perimeter_threshold）时，速度应为期望值；否则保持原本墙速。
    - OUTER_WALL 基准 outer_wall_speed，INNER_WALL 基准 inner_wall_speed。
    - 跳过首层，闭合周长需补首尾段。
    """
    path_obj = Path(gcode_path)
    parser = GCodeParserEx(path_obj)

    cfg = parser.load_config() or {}
    th_cfg = cfg.get("small_perimeter_threshold")
    ow_cfg = cfg.get("outer_wall_speed")
    iw_cfg = cfg.get("inner_wall_speed")

    try:
        radius = float(th_cfg.value) if th_cfg is not None else None
    except (TypeError, ValueError, AttributeError):
        radius = None
    try:
        outer_speed = float(ow_cfg.value) if ow_cfg is not None else None
    except (TypeError, ValueError, AttributeError):
        outer_speed = None
    try:
        inner_speed = float(iw_cfg.value) if iw_cfg is not None else None
    except (TypeError, ValueError, AttributeError):
        inner_speed = None

    if radius is None or outer_speed is None or inner_speed is None:
        details = {
            "layers_count": 0,
            "expected_speed": expected_speed,
            "tolerance": tolerance,
            "matches": [],
            "mismatches": [],
            "missing_feedrate": [],
            "note": "small_perimeter_threshold/outer_wall_speed/inner_wall_speed 缺失或非法。",
            "match": False,
        }
        return False, expected_speed, details

    circumference = 2 * math.pi * radius
    layers = parser.get_type_contours_per_layer(
        types=[ExtrusionType.OUTER_WALL, ExtrusionType.INNER_WALL],
        skip_layers=[0],
    )

    matches: List[Dict[str, Any]] = []
    mismatches: List[Dict[str, Any]] = []
    missing_feedrate: List[Dict[str, Any]] = []
    actual_values: List[float] = []
    perimeters: List[float] = []
    regions_checked = 0

    def _perimeter(path_points) -> Optional[float]:
        # path 末点与首点不重合，需补上闭合段
        pts = path_points or []
        if len(pts) < 2:
            return None
        dist = 0.0
        for a, b in zip(pts, pts[1:]):
            dist += math.hypot(b.x - a.x, b.y - a.y)
        dist += math.hypot(pts[0].x - pts[-1].x, pts[0].y - pts[-1].y)
        return dist

    if not layers:
        details = {
            "layers_count": 0,
            "expected_speed": expected_speed,
            "tolerance": tolerance,
            "matches": matches,
            "mismatches": mismatches,
            "missing_feedrate": missing_feedrate,
            "actual_values_set": [],
            "perimeters_sample": [],
            "circumference": circumference,
            "radius": radius,
            "match": False,
            "note": "No layers parsed; check slicing output or markers.",
        }
        return False, expected_speed, details

    for layer in layers:
        for oid, region_map in (layer.regions or {}).items():
            for rtype, region in (region_map or {}).items():
                for path in region.paths or []:
                    perim = _perimeter(path.points)
                    if perim is None:
                        continue
                    perimeters.append(perim)
                    base_speed = outer_speed if rtype == ExtrusionType.OUTER_WALL.value else inner_speed
                    target_speed = expected_speed if perim < circumference else base_speed

                    actual = region.feedrate
                    # 优先 Region.feedrate，缺失时尝试路径首点 feedrate
                    if actual is None and path.points:
                        actual = path.points[0].feedrate
                    if actual is None:
                        missing_feedrate.append({
                            "layer": layer.index,
                            "object_id": oid,
                            "type": rtype,
                            "perimeter": perim,
                        })
                        continue

                    regions_checked += 1
                    actual_val = float(actual)
                    actual_values.append(actual_val)
                    diff = actual_val - target_speed
                    item = {
                        "layer": layer.index,
                        "object_id": oid,
                        "type": rtype,
                        "perimeter": perim,
                        "expected_speed": target_speed,
                        "actual_speed": actual_val,
                        "radius": radius,
                        "circumference": circumference,
                        "tolerance": tolerance,
                        "diff": diff,
                    }
                    if abs(diff) <= tolerance:
                        item["status"] = "ok"
                        matches.append(item)
                    else:
                        item["status"] = "mismatch"
                        mismatches.append(item)

    ok = regions_checked > 0 and not mismatches and not missing_feedrate
    details = {
        "layers_count": len(layers),
        "expected_speed": expected_speed,
        "circumference": circumference,
        "radius": radius,
        "tolerance": tolerance,
        "matches": matches,
        "mismatches": mismatches,
        "missing_feedrate": missing_feedrate,
        "actual_values_set": sorted(set(actual_values)),
        "perimeters_sample": sorted(perimeters)[:10],
        "match": ok,
    }

    return ok, expected_speed, details
