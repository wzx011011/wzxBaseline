# engine_params/src/gcode/speed/other_layers_speed_check.py
from pathlib import Path
from typing import Tuple, Dict, Any, List

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