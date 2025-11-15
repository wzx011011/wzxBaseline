# engine_params/src/gcode/speed/overhang_speed_check.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

from engine_params.src.gcode.GCodeParserEx import GCodeParserEx
from engine_params.src.gcode.constants import ExtrusionType

from dataclasses import dataclass
from typing import List, Tuple

# ================== 下面改写自C++ ==================

OVERLAPS = [90, 60, 35, 13, 12.99, 0]

@dataclass
class SpeedConfig:
    """对应 C++ 里的 ConfigOptionFloatsOrPercents 的一个元素."""
    value: float   # 如果 percent=False：mm/s；如果 percent=True：百分比值(0~100)
    percent: bool  # True 表示按 ext_perimeter_speed 的百分比解释

def build_dynamic_overhang_speeds(
    ref_speed: float,
    overhang_1_4_speed_abs: float,
    overhang_2_4_speed_abs: float,
    overhang_3_4_speed_abs: float,
    overhang_4_4_speed_abs: float,
    bridge_speed_abs: float,
) -> List[SpeedConfig]:
    """
    等价于 C++ 这段：

        ConfigOptionFloatsOrPercents dynamic_overhang_speeds(
            { (get_abs(overhang_1_4) < 0.5) ? FloatOrPercent{100, true}
                                             : FloatOrPercent{min(get_abs, ref)*100/ref, true},
              ...
              FloatOrPercent{min(bridge_speed, ref_speed)*100/ref_speed, true},
              FloatOrPercent{min(bridge_speed, ref_speed)*100/ref_speed, true} });

    这里所有返回的 SpeedConfig 都是 percent=True，value 为相对于 ref_speed 的百分比。
    """

    def _overhang_percent(v_abs: float) -> SpeedConfig:
        # C++: if (get_abs_value(...) < 0.5) -> {100, true}
        if v_abs < 0.5:
            return SpeedConfig(100.0, True)
        # 否则: { min(v_abs, ref_speed)*100/ref_speed, true }
        pct = min(v_abs, ref_speed) * 100.0 / ref_speed
        return SpeedConfig(pct, True)

    # 4 档 overhang_1_4 ~ overhang_4_4
    s1 = _overhang_percent(overhang_1_4_speed_abs)
    s2 = _overhang_percent(overhang_2_4_speed_abs)
    s3 = _overhang_percent(overhang_3_4_speed_abs)
    s4 = _overhang_percent(overhang_4_4_speed_abs)

    # bridge_speed 不做 <0.5 判断，直接 min(...) 后转百分比
    bridge_pct = min(bridge_speed_abs, ref_speed) * 100.0 / ref_speed
    s_bridge1 = SpeedConfig(bridge_pct, True)
    s_bridge2 = SpeedConfig(bridge_pct, True)

    return [s1, s2, s3, s4, s_bridge1, s_bridge2]

def build_speed_sections(
    width: float,
    overlaps: List[float],           # 百分比，例如 [90, 60, 35, ...]
    speeds: List[SpeedConfig],       # 每档对应的速度配置
    outer_wall_speed: float       # ref_speed / outer_wall_speed
) -> List[Tuple[float, float]]:
    """
    生成 speed_sections 数组：
    每个元素为 (distance, speed)，并按 C++ 逻辑做排序和“同 distance 取同一速度”的处理。
    """
    n = min(len(overlaps), len(speeds))
    sections: List[Tuple[float, float]] = []

    # 1. 先算出每一档的 (distance, speed)
    for i in range(n):
        # C++: distance = path.width * (1.0 - overlaps[i] / 100.0)
        distance = width * (1.0 - overlaps[i] / 100.0)

        cfg = speeds[i]
        # C++: speeds[i].percent ? ext_perimeter_speed * speed% / 100 : speed_abs
        if cfg.percent:
            speed = outer_wall_speed * cfg.value / 100.0
        else:
            speed = cfg.value

        sections.append((distance, speed))

    # 2. 排序：按 distance 升序，distance 相同则按 speed 降序
    sections.sort(key=lambda p: (p[0], -p[1]))

    # 3. 模拟 C++ 那段：
    #    对于相同 distance 的多条记录，把它们的 second 统一成同一个值
    #    （C++ 是先取最大 speed，然后后面的同 distance 都赋成这个 speed）
    adjusted: List[Tuple[float, float]] = []
    last_distance = float("inf")
    last_speed = 0.0

    for dist, spd in sections:
        if dist == last_distance:
            # 同一个 distance，用上一个 section 的 speed
            spd = last_speed
        else:
            last_distance = dist
            last_speed = spd
        adjusted.append((dist, spd))

    return adjusted


def calculate_speed(
    distance: float,
    speed_sections: List[Tuple[float, float]],
    original_speed: float
) -> float:
    """
    对应 C++ 的 calculate_speed(distance) 匿名函数。
    不考虑翘边降速，只根据 distance 和 speed_sections 计算目标速度。
    """

    d0, _ = speed_sections[0]
    d_last, v_last = speed_sections[-1]

    # C++: if (distance <= speed_sections.front().first)
    if distance <= d0:
        return round(original_speed)

    # C++: else if (distance >= speed_sections.back().first)
    if distance >= d_last:
        return round(v_last)

    # 否则在两个相邻区间之间插值
    section_idx = 0
    # C++: while (distance > speed_sections[section_idx + 1].first) section_idx++;
    while (section_idx + 1 < len(speed_sections) and
           distance > speed_sections[section_idx + 1][0]):
        section_idx += 1

    d1, v1 = speed_sections[section_idx]
    d2, v2 = speed_sections[section_idx + 1]

    # C++: t = (distance - d1) / (d2 - d1); clamp 到 [0,1]
    if d2 != d1:
        t = (distance - d1) / (d2 - d1)
    else:
        t = 0.0
    t = max(0.0, min(1.0, t))

    final_speed = (1.0 - t) * v1 + t * v2
    return round(final_speed)


# ================== bridge_speed ==================
def parse_bridge_speed(
        gcode_path: Path | str,
        expected_speed: float,
        tolerance: float = 1e-6,
) -> Tuple[bool, float, Dict[str, Any]]:
    """
    校验 Overhang wall（桥接）速度：
    - 通过 get_type_contours_per_layer(types=[OVERHANG_WALL], skip_layers=[0]) 获取外悬墙区域；
    - 检查每个 LayerRegion.feedrate 是否等于期望值（容差内）。
    """
    path_obj = Path(gcode_path)
    parser = GCodeParserEx(path_obj)

    layers = parser.get_type_contours_per_layer(
        types=[ExtrusionType.OVERHANG_WALL],
        skip_layers=[0],
    )

    matches: List[Dict[str, Any]] = []
    mismatches: List[Dict[str, Any]] = []
    missing_feedrate: List[Dict[str, Any]] = []
    actual_values: List[float] = []

    if not layers:
        details = {
            "expected": expected_speed,
            "tolerance": tolerance,
            "matches": matches,
            "mismatches": mismatches,
            "missing_feedrate": missing_feedrate,
            "actual_values_set": [],
            "checked_layers": [],
            "note": "No overhang wall regions parsed.",
            "match": False,
        }
        return False, expected_speed, details

    checked_layers: List[int] = []
    for layer in layers:
        if layer.index == 0:
            continue  # 安全过滤首层，确保报告中不含 layer 0
        checked_layers.append(layer.index)
        for oid, type_map in (layer.regions or {}).items():
            region = type_map.get(ExtrusionType.OVERHANG_WALL.value)
            if region is None:
                continue
            item = {
                "layer": layer.index,
                "object_id": oid,
                "type": ExtrusionType.OVERHANG_WALL.value,
                "expected": expected_speed,
                "tolerance": tolerance,
                "region_feedrate": region.feedrate,
            }
            if region.feedrate is None:
                item["status"] = "missing_feedrate"
                missing_feedrate.append(item)
                continue

            actual = float(region.feedrate)
            actual_values.append(actual)
            diff = actual - expected_speed
            item["diff"] = diff
            if abs(diff) <= tolerance:
                item["status"] = "ok"
                matches.append(item)
            else:
                item["status"] = "mismatch"
                mismatches.append(item)

    ok = (not mismatches and not missing_feedrate and matches)
    details = {
        "expected": expected_speed,
        "tolerance": tolerance,
        "matches": matches,
        "mismatches": mismatches,
        "missing_feedrate": missing_feedrate,
        "actual_values_set": sorted(set(actual_values)),
        "checked_layers": sorted({idx for idx in checked_layers if idx != 0}),
        "note": None,
        "match": ok,
    }
    return ok, expected_speed, details


# ================== internal_bridge_speed ==================
def parse_internal_bridge_speed(
        gcode_path: Path | str,
        expected_speed: float,
        tolerance: float = 1e-6,
) -> Tuple[bool, float, Dict[str, Any]]:
    """
    校验 Internal bridge 速度：检测 INTERNAL_BRIDGE 类型的 LayerRegion.feedrate 是否等于期望值（跳过首层）。
    """
    path_obj = Path(gcode_path)
    parser = GCodeParserEx(path_obj)

    layers = parser.get_type_contours_per_layer(
        types=[ExtrusionType.INTERNAL_BRIDGE],
        skip_layers=[0],
    )

    matches: List[Dict[str, Any]] = []
    mismatches: List[Dict[str, Any]] = []
    missing_feedrate: List[Dict[str, Any]] = []
    actual_values: List[float] = []
    checked_layers: List[int] = []

    if not layers:
        details = {
            "expected": expected_speed,
            "tolerance": tolerance,
            "matches": matches,
            "mismatches": mismatches,
            "missing_feedrate": missing_feedrate,
            "actual_values_set": [],
            "checked_layers": [],
            "note": "No internal bridge regions parsed.",
            "match": False,
        }
        return False, expected_speed, details

    for layer in layers:
        if layer.index == 0:
            continue  # 安全过滤首层，避免计入报告
        checked_layers.append(layer.index)
        for oid, type_map in (layer.regions or {}).items():
            region = type_map.get(ExtrusionType.INTERNAL_BRIDGE.value)
            if region is None:
                continue
            item = {
                "layer": layer.index,
                "object_id": oid,
                "type": ExtrusionType.INTERNAL_BRIDGE.value,
                "expected": expected_speed,
                "tolerance": tolerance,
                "region_feedrate": region.feedrate,
            }
            if region.feedrate is None:
                item["status"] = "missing_feedrate"
                missing_feedrate.append(item)
                continue

            actual = float(region.feedrate)
            actual_values.append(actual)
            diff = actual - expected_speed
            item["diff"] = diff
            if abs(diff) <= tolerance:
                item["status"] = "ok"
                matches.append(item)
            else:
                item["status"] = "mismatch"
                mismatches.append(item)

    ok = (not mismatches and not missing_feedrate and matches)
    details = {
        "expected": expected_speed,
        "tolerance": tolerance,
        "matches": matches,
        "mismatches": mismatches,
        "missing_feedrate": missing_feedrate,
        "actual_values_set": sorted(set(actual_values)),
        "checked_layers": sorted({idx for idx in checked_layers if idx != 0}),
        "note": None,
        "match": ok,
    }
    return ok, expected_speed, details


# ================== enable_overhang_speed ==================
# ================== overhang_totally_speed ==================
def parse_overhang_totally_speed(
        gcode_path: Path | str,
        expected_speed: float,
        tolerance: float = 1e-6,
) -> Tuple[bool, float, Dict[str, Any]]:
    """
    完全悬垂外墙速度：跳过首层，检查所有 Overhang wall 路径点 point.f 是否等于期望值。
    - 仅关注 Overhang wall 挤出类型。
    - 所有点都应满足期望值；缺失速度或超差即为不符合。
    """
    path_obj = Path(gcode_path)
    parser = GCodeParserEx(path_obj)

    layers = parser.get_type_contours_per_layer(
        types=[ExtrusionType.OVERHANG_WALL],
        skip_layers=[0],
    )

    matches: List[Dict[str, Any]] = []
    mismatches: List[Dict[str, Any]] = []
    missing_feedrate: List[Dict[str, Any]] = []
    checked_layers: List[int] = []
    actual_values: List[float] = []

    if not layers:
        details = {
            "expected": expected_speed,
            "tolerance": tolerance,
            "checked_layers": [],
            "matches": matches,
            "mismatches": mismatches,
            "missing_feedrate": missing_feedrate,
            "actual_values_set": [],
            "note": "No overhang wall regions parsed.",
            "match": False,
        }
        return False, expected_speed, details

    for layer in layers:
        if layer.index == 0:
            continue
        checked_layers.append(layer.index)
        for oid, type_map in (layer.regions or {}).items():
            region = type_map.get(ExtrusionType.OVERHANG_WALL.value)
            if region is None:
                continue
            for path_idx, path in enumerate(region.paths or []):
                for point_idx, pt in enumerate(path.points or []):
                    if pt.f is None:
                        missing_feedrate.append({
                            "layer": layer.index,
                            "object_id": oid,
                            "path_idx": path_idx,
                            "point_idx": point_idx,
                        })
                        continue
                    actual = float(pt.f)
                    actual_values.append(actual)
                    diff = actual - expected_speed
                    item = {
                        "layer": layer.index,
                        "object_id": oid,
                        "path_idx": path_idx,
                        "point_idx": point_idx,
                        "actual": actual,
                        "expected": expected_speed,
                        "diff": diff,
                        "tolerance": tolerance,
                    }
                    if abs(diff) <= tolerance:
                        item["status"] = "ok"
                        matches.append(item)
                    else:
                        item["status"] = "mismatch"
                        mismatches.append(item)

    ok = (not mismatches) and (not missing_feedrate) and bool(matches)
    details = {
        "expected": expected_speed,
        "tolerance": tolerance,
        "checked_layers": sorted({idx for idx in checked_layers if idx != 0}),
        "matches": matches,
        "mismatches": mismatches,
        "missing_feedrate": missing_feedrate,
        "actual_values_set": sorted(set(actual_values)),
        "note": None if matches else "No valid overhang wall points found.",
        "match": ok,
    }
    return ok, expected_speed, details


def parse_enable_overhang_speed(
        gcode_path: Path | str,
        expected_enabled: bool,
        tolerance: float = 1e-6,
) -> Tuple[bool, bool, Dict[str, Any]]:
    """
    检测 Overhang 速度是否启用：
    - 读取 outer_wall_speed（config），检查除首层外 OUTER_WALL 路径的点 feedrate；
    - 若存在点与 outer_wall_speed 不同（容差外），视为启用；否则视为未启用。
    """
    path_obj = Path(gcode_path)
    parser = GCodeParserEx(path_obj)

    cfg = parser.load_config() or {}
    ow_cfg = cfg.get("outer_wall_speed")
    try:
        outer_speed = float(ow_cfg.value) if ow_cfg is not None else None
    except (TypeError, ValueError, AttributeError):
        outer_speed = None

    if outer_speed is None:
        details = {
            "expected_enabled": expected_enabled,
            "outer_wall_speed": outer_speed,
            "tolerance": tolerance,
            "checked_layers": [],
            "mismatches": [],
            "missing_feedrate": [],
            "actual_enabled": None,
            "note": "outer_wall_speed missing/invalid in config.",
            "match": False,
        }
        return False, expected_enabled, details

    layers = parser.get_type_contours_per_layer(
        types=[ExtrusionType.OUTER_WALL],
        skip_layers=[0],
    )

    mismatches: List[Dict[str, Any]] = []
    missing_feedrate: List[Dict[str, Any]] = []
    checked_layers: List[int] = []

    for layer in layers:
        if layer.index == 0:
            continue  # 安全过滤首层
        checked_layers.append(layer.index)
        for oid, type_map in (layer.regions or {}).items():
            region = type_map.get(ExtrusionType.OUTER_WALL.value)
            if region is None:
                continue
            for path_idx, path in enumerate(region.paths or []):
                for point_idx, pt in enumerate(path.points or []):
                    if pt.f is None:
                        missing_feedrate.append({
                            "layer": layer.index,
                            "object_id": oid,
                            "path_idx": path_idx,
                            "point_idx": point_idx,
                        })
                        continue
                    actual = float(pt.f)
                    diff = actual - outer_speed
                    if abs(diff) > tolerance:
                        mismatches.append({
                            "layer": layer.index,
                            "object_id": oid,
                            "path_idx": path_idx,
                            "point_idx": point_idx,
                            "actual": actual,
                            "expected": outer_speed,
                            "diff": diff,
                        })

    actual_enabled = bool(mismatches)
    note = None
    if expected_enabled and not mismatches:
        note = "All outer wall points match outer_wall_speed; overhang speed not observed."
    elif not checked_layers:
        note = "No outer wall regions parsed."

    ok = (actual_enabled == expected_enabled) and (not missing_feedrate)
    details = {
        "expected_enabled": expected_enabled,
        "actual_enabled": actual_enabled,
        "outer_wall_speed": outer_speed,
        "tolerance": tolerance,
        "checked_layers": sorted({idx for idx in checked_layers if idx != 0}),
        "mismatches": mismatches,
        "missing_feedrate": missing_feedrate,
        "note": note,
        "match": ok,
    }
    return ok, expected_enabled, details


# ================== smooth_speed_discontinuity_area ==================
def parse_smooth_speed_discontinuity_area(
        gcode_path: Path | str,
        expected_enabled: bool,
        tolerance: float = 1e-6,
) -> Tuple[bool, bool, Dict[str, Any]]:
    """
    平滑悬垂速度：存在 Overhang wall 时，外墙路径速度应呈单调（增或减）以避免突变。
    - 跳过首层；只在含 Overhang wall 的层检查 OUTER_WALL 的 point.f。
    - 开启：每条外墙路径速度严格单调（容差内，允许微抖动）。
    - 关闭：至少出现一条非单调路径（存在过渡/拐点）。
    """
    path_obj = Path(gcode_path)
    parser = GCodeParserEx(path_obj)

    layers = parser.get_type_contours_per_layer(
        types=[ExtrusionType.OVERHANG_WALL, ExtrusionType.OUTER_WALL],
        skip_layers=[0],
    )

    layers_with_overhang: List[int] = []
    checked_layers: List[int] = []
    missing_feedrate: List[Dict[str, Any]] = []
    non_monotonic: List[Dict[str, Any]] = []
    monotonic_paths: List[Dict[str, Any]] = []

    def _is_monotonic(values: List[float]) -> bool:
        if len(values) < 2:
            return False
        diffs = [b - a for a, b in zip(values, values[1:])]
        inc = all(d >= -tolerance for d in diffs) and any(d > tolerance for d in diffs)
        dec = all(d <= tolerance for d in diffs) and any(d < -tolerance for d in diffs)
        return inc or dec

    if not layers:
        details = {
            "expected_enabled": expected_enabled,
            "actual_enabled": None,
            "checked_layers": [],
            "layers_with_overhang": [],
            "monotonic_paths": [],
            "non_monotonic": [],
            "missing_feedrate": [],
            "note": "No overhang wall regions parsed.",
            "match": False,
        }
        return False, expected_enabled, details

    for layer in layers:
        if layer.index == 0:
            continue
        checked_layers.append(layer.index)
        type_map_all = layer.regions or {}
        has_overhang = any(
            ExtrusionType.OVERHANG_WALL.value in (type_map or {})
            for type_map in type_map_all.values()
        )
        if not has_overhang:
            continue
        layers_with_overhang.append(layer.index)

        for oid, type_map in type_map_all.items():
            region = type_map.get(ExtrusionType.OUTER_WALL.value)
            if region is None:
                continue
            for path_idx, path in enumerate(region.paths or []):
                speeds: List[float] = []
                missing = False
                for point_idx, pt in enumerate(path.points or []):
                    if pt.f is None:
                        missing = True
                        missing_feedrate.append({
                            "layer": layer.index,
                            "object_id": oid,
                            "path_idx": path_idx,
                            "point_idx": point_idx,
                        })
                        continue
                    speeds.append(float(pt.f))
                if missing or not speeds:
                    continue

                if _is_monotonic(speeds):
                    monotonic_paths.append({
                        "layer": layer.index,
                        "object_id": oid,
                        "path_idx": path_idx,
                        "speeds_sample": speeds[:5],
                        "count": len(speeds),
                    })
                else:
                    non_monotonic.append({
                        "layer": layer.index,
                        "object_id": oid,
                        "path_idx": path_idx,
                        "speeds_sample": speeds[:5],
                        "count": len(speeds),
                    })

    actual_enabled = bool(monotonic_paths) and not non_monotonic
    if not expected_enabled and non_monotonic:
        actual_enabled = False
    if not expected_enabled and not non_monotonic:
        # 关闭时需要观察到非单调；若全部单调，实际表现为启用
        actual_enabled = True

    note = None
    if not layers_with_overhang:
        note = "No overhang wall regions parsed."
    elif expected_enabled and non_monotonic:
        note = "Found non-monotonic outer wall path while smooth mode expected."
    elif (not expected_enabled) and not non_monotonic:
        note = "All checked outer wall paths are monotonic; smooth mode observed while expected disabled."

    ok = (actual_enabled == expected_enabled) and not missing_feedrate
    details = {
        "expected_enabled": expected_enabled,
        "actual_enabled": actual_enabled,
        "checked_layers": sorted({idx for idx in checked_layers if idx != 0}),
        "layers_with_overhang": sorted(set(layers_with_overhang)),
        "monotonic_paths": monotonic_paths,
        "non_monotonic": non_monotonic,
        "missing_feedrate": missing_feedrate,
        "note": note,
        "match": ok,
    }
    return ok, expected_enabled, details


# ================== slowdown_for_curled_perimeters ==================
def parse_slowdown_for_curled_perimeters(
        gcode_path: Path | str,
        expected_enabled: bool,
        tolerance: float = 1e-6,
) -> Tuple[bool, bool, Dict[str, Any]]:
    """
    翘边模式：存在 Overhang wall 时，外墙应出现 overhang_4_4_speed（开启）或桥接速度（关闭）。
    - 跳过首层；遇到 Overhang wall 的层，检查同层 OUTER_WALL 点的 point.f。
    - 开启：必须出现至少一个点 == overhang_4_4_speed（容差内）。
    - 关闭：不得出现 overhang_4_4_speed，应出现 bridge_speed。
    """
    path_obj = Path(gcode_path)
    parser = GCodeParserEx(path_obj)

    cfg = parser.load_config() or {}
    overhang_speed = cfg.get("overhang_4_4_speed").value
    bridge_speed = cfg.get("bridge_speed").value

    if overhang_speed is None or bridge_speed is None:
        details = {
            "expected_enabled": expected_enabled,
            "actual_enabled": None,
            "overhang_4_4_speed": overhang_speed,
            "bridge_speed": bridge_speed,
            "tolerance": tolerance,
            "checked_layers": [],
            "layers_with_overhang": [],
            "mismatches": [],
            "missing_feedrate": [],
            "note": "Missing overhang_4_4_speed or bridge_speed in config.",
            "match": False,
        }
        return False, expected_enabled, details

    layers = parser.get_type_contours_per_layer(
        types=[ExtrusionType.OVERHANG_WALL, ExtrusionType.OUTER_WALL],
        skip_layers=[0],
    )

    layers_with_overhang: List[int] = []
    mismatches: List[Dict[str, Any]] = []
    missing_feedrate: List[Dict[str, Any]] = []
    checked_layers: List[int] = []
    found_overhang_speed = False
    found_bridge_speed = False

    for layer in layers:
        if layer.index == 0:
            continue
        checked_layers.append(layer.index)
        type_map_all = layer.regions or {}
        has_overhang = any(
            ExtrusionType.OVERHANG_WALL.value in (type_map or {})
            for type_map in type_map_all.values()
        )
        if not has_overhang:
            continue
        layers_with_overhang.append(layer.index)

        # 查找同层 OUTER_WALL
        for oid, type_map in type_map_all.items():
            region = type_map.get(ExtrusionType.OUTER_WALL.value)
            if region is None:
                continue
            for path_idx, path in enumerate(region.paths or []):
                for point_idx, pt in enumerate(path.points or []):
                    if pt.f is None:
                        missing_feedrate.append({
                            "layer": layer.index,
                            "object_id": oid,
                            "path_idx": path_idx,
                            "point_idx": point_idx,
                        })
                        continue
                    actual = float(pt.f)
                    if abs(actual - overhang_speed) <= tolerance:
                        found_overhang_speed = True
                    if abs(actual - bridge_speed) <= tolerance:
                        found_bridge_speed = True

                    if not expected_enabled and abs(actual - overhang_speed) <= tolerance:
                        mismatches.append({
                            "layer": layer.index,
                            "object_id": oid,
                            "path_idx": path_idx,
                            "point_idx": point_idx,
                            "actual": actual,
                            "expected": bridge_speed,
                            "reason": "overhang_speed_found_when_disabled",
                        })

    actual_enabled = found_overhang_speed
    note = None
    if not layers_with_overhang:
        note = "No overhang wall regions parsed."
    elif expected_enabled and not found_overhang_speed:
        note = "No outer wall point at overhang_4_4_speed detected."
    elif (not expected_enabled) and mismatches:
        note = "Found overhang_4_4_speed while expected disabled."
    elif (not expected_enabled) and not found_bridge_speed:
        note = "No bridge_speed point detected when disabled."

    ok = (actual_enabled == expected_enabled) and not missing_feedrate
    if not expected_enabled and mismatches:
        ok = False

    details = {
        "expected_enabled": expected_enabled,
        "actual_enabled": actual_enabled,
        "overhang_4_4_speed": overhang_speed,
        "bridge_speed": bridge_speed,
        "tolerance": tolerance,
        "checked_layers": sorted({idx for idx in checked_layers if idx != 0}),
        "layers_with_overhang": sorted(set(layers_with_overhang)),
        "found_overhang_speed": found_overhang_speed,
        "found_bridge_speed": found_bridge_speed,
        "mismatches": mismatches,
        "missing_feedrate": missing_feedrate,
        "note": note,
        "match": ok,
    }
    return ok, expected_enabled, details


# ================== overhang_speed_classic ==================
def parse_overhang_speed_classic(
        gcode_path: Path | str,
        expected_enabled: bool,
        tolerance: float = 1e-6,
) -> Tuple[bool, bool, Dict[str, Any]]:
    """
    经典悬垂速度：开启后，带 Overhang wall 的层，其外墙整条路径都应为 outer_wall_speed（无渐变）。
    - 跳过首层；仅在存在 Overhang wall 的层检查 OUTER_WALL 的点速度 point.f。
    - 开启：所有点均应等于 outer_wall_speed（容差内）。
    - 关闭：应存在至少一个点不等于 outer_wall_speed（出现平滑过渡）。
    """
    path_obj = Path(gcode_path)
    parser = GCodeParserEx(path_obj)

    cfg = parser.load_config() or {}

    def _to_float(v):
        try:
            return float(getattr(v, "value", v))
        except (TypeError, ValueError, AttributeError):
            return None

    outer_speed = _to_float(cfg.get("outer_wall_speed"))
    if outer_speed is None:
        details = {
            "expected_enabled": expected_enabled,
            "actual_enabled": None,
            "outer_wall_speed": outer_speed,
            "tolerance": tolerance,
            "checked_layers": [],
            "layers_with_overhang": [],
            "mismatches": [],
            "missing_feedrate": [],
            "note": "Missing outer_wall_speed in config.",
            "match": False,
        }
        return False, expected_enabled, details

    layers = parser.get_type_contours_per_layer(
        types=[ExtrusionType.OVERHANG_WALL, ExtrusionType.OUTER_WALL],
        skip_layers=[0],
    )

    layers_with_overhang: List[int] = []
    mismatches: List[Dict[str, Any]] = []
    missing_feedrate: List[Dict[str, Any]] = []
    checked_layers: List[int] = []

    for layer in layers:
        if layer.index == 0:
            continue
        checked_layers.append(layer.index)
        type_map_all = layer.regions or {}
        has_overhang = any(
            ExtrusionType.OVERHANG_WALL.value in (type_map or {})
            for type_map in type_map_all.values()
        )
        if not has_overhang:
            continue
        layers_with_overhang.append(layer.index)

        for oid, type_map in type_map_all.items():
            region = type_map.get(ExtrusionType.OUTER_WALL.value)
            if region is None:
                continue
            for path_idx, path in enumerate(region.paths or []):
                for point_idx, pt in enumerate(path.points or []):
                    if pt.f is None:
                        missing_feedrate.append({
                            "layer": layer.index,
                            "object_id": oid,
                            "path_idx": path_idx,
                            "point_idx": point_idx,
                        })
                        continue
                    actual = float(pt.f)
                    diff = actual - outer_speed
                    if abs(diff) > tolerance:
                        mismatches.append({
                            "layer": layer.index,
                            "object_id": oid,
                            "path_idx": path_idx,
                            "point_idx": point_idx,
                            "actual": actual,
                            "expected": outer_speed,
                            "diff": diff,
                        })

    # 开启经典：不允许 mismatch；关闭：需要至少一个 mismatch（出现过渡值）
    actual_enabled = not mismatches
    note = None
    if not layers_with_overhang:
        note = "No overhang wall regions parsed."
    elif expected_enabled and mismatches:
        note = "Found outer wall point not equal to outer_wall_speed while classic expected."
    elif (not expected_enabled) and not mismatches:
        note = "No smooth transition detected; classic mode observed while expected disabled."

    ok = (actual_enabled == expected_enabled) and not missing_feedrate
    details = {
        "expected_enabled": expected_enabled,
        "actual_enabled": actual_enabled,
        "outer_wall_speed": outer_speed,
        "tolerance": tolerance,
        "checked_layers": sorted({idx for idx in checked_layers if idx != 0}),
        "layers_with_overhang": sorted(set(layers_with_overhang)),
        "mismatches": mismatches,
        "missing_feedrate": missing_feedrate,
        "note": note,
        "match": ok,
    }
    return ok, expected_enabled, details
