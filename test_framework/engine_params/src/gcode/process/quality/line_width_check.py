from __future__ import annotations

import math
import warnings
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union

from engine_params.src.gcode.GCodeParser import GCodeParser, Point
from engine_params.src.gcode.constants import ExtrusionType


def compute_line_width(E: float, L: float, h: float, d: float = 1.75, flow_ratio: float = 0.95) -> float:
    """
    根据挤出量计算线宽的通用公式:
        w = (E * π * d^2) / (4 * L * h * flow_ratio) + h * (4 - π) / 4

    参数单位均为毫米(mm)。
      - E: 当前段挤出的耗材长度。
      - L: 段的空间路径长度。
      - h: 层高。
      - d: 耗材直径(默认 1.75mm)。
      - flow_ratio: 流量比例(>0)。

    返回线宽 w (mm)。
    当 L、h、d 或 flow_ratio 非法(≤0)时抛出 ValueError。
    """

    if L <= 0:
        raise ValueError("L must be > 0")
    if h <= 0:
        raise ValueError("h must be > 0")
    if d <= 0:
        raise ValueError("d must be > 0")
    if flow_ratio <= 0:
        raise ValueError("flow_ratio must be > 0")

    term1 = (E * math.pi * (d ** 2)) / (4.0 * L * h * flow_ratio)
    term2 = h * (4.0 - math.pi) / 4.0
    return term1 + term2


ExtrusionTypeLike = Union[ExtrusionType, str]


def _resolve_flow_ratio(cfg: Dict[str, object]) -> float:
    raw = cfg.get("filament_flow_ratio")
    if raw is None:
        return 1.0

    values: List[float] = []
    if isinstance(raw, (int, float)):
        values = [float(raw)]
    elif isinstance(raw, str):
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        for p in parts:
            try:
                values.append(float(p))
            except ValueError:
                continue
    elif isinstance(raw, (list, tuple)):
        for item in raw:
            try:
                values.append(float(str(item).strip()))
            except ValueError:
                continue

    if not values:
        return 1.0
    if len(values) > 1:
        warnings.warn(
            f"检测到多个耗材流量系数 {values}，默认使用第一个值 {values[0]}",
            RuntimeWarning,
            stacklevel=2,
        )
    return values[0]


def _resolve_filament_diameter(cfg: Dict[str, object]) -> float:
    raw = cfg.get("filament_diameter")
    if raw is None:
        return 1.75

    values: List[float] = []
    if isinstance(raw, (int, float)):
        values = [float(raw)]
    elif isinstance(raw, str):
        parts = [p.strip() for p in raw.replace(";", ",").split(",") if p.strip()]
        for part in parts:
            try:
                values.append(float(part))
            except ValueError:
                continue
    elif isinstance(raw, (list, tuple)):
        for item in raw:
            try:
                values.append(float(str(item).strip()))
            except ValueError:
                continue

    if not values:
        return 1.75
    if len(values) > 1:
        warnings.warn(
            f"检测到多个耗材直径 {values}，默认使用第一个值 {values[0]}",
            RuntimeWarning,
            stacklevel=2,
        )
    return values[0]


def _resolve_layer_height(layer_info: Sequence[Tuple[Optional[float], Optional[float]]], layer_idx: int) -> Optional[
    float]:
    if not layer_info or layer_idx < 0 or layer_idx >= len(layer_info):
        return None
    z, h = layer_info[layer_idx]
    if h is not None and h > 0:
        return h
    if z is not None:
        if layer_idx > 0:
            prev_z, _ = layer_info[layer_idx - 1]
            if prev_z is not None:
                diff = z - prev_z
                if diff > 0:
                    return diff
        for nxt in range(layer_idx + 1, len(layer_info)):
            next_z, _ = layer_info[nxt]
            if next_z is not None:
                diff = next_z - z
                if diff > 0:
                    return diff
    return None


def _to_type_names(extrusion_types: Optional[Union[ExtrusionTypeLike, Sequence[ExtrusionTypeLike]]]) -> Optional[
    List[str]]:
    if extrusion_types is None:
        return None

    def _one(name: ExtrusionTypeLike) -> str:
        if isinstance(name, ExtrusionType):
            return name.value
        return str(name)

    # Handle single value (enum or string)
    if isinstance(extrusion_types, (ExtrusionType, str)):
        return [_one(extrusion_types)]

    names: List[str] = []
    for item in extrusion_types:
        names.append(_one(item))
    return names or None


def _normalize_layer_indices(layer_indices: Optional[Iterable[int]], total_layers: int) -> Tuple[List[int], List[int]]:
    if layer_indices is None:
        return list(range(total_layers)), []

    valid: set[int] = set()
    missing: List[int] = []

    for raw_idx in layer_indices:
        if not isinstance(raw_idx, int):
            missing.append(raw_idx)
            continue
        idx = raw_idx if raw_idx >= 0 else total_layers + raw_idx
        if 0 <= idx < total_layers:
            valid.add(idx)
        else:
            missing.append(raw_idx)

    return sorted(valid), missing


def parse_line_width_from_type(
        gcode_path: Path | str,
        expected_line_width: float,
        *,
        extrusion_types: Optional[Sequence[ExtrusionTypeLike]] = None,
        layer_indices: Optional[Sequence[int]] = None,
        skip_layers: Optional[Sequence[int]] = None,
        filament_diameter: float = 1.75,
        tolerance: float = 0.02,
        object_id: int = 0,
) -> Tuple[bool, float, Dict[str, object]]:
    """
    逐段计算（从 G-code 中按点对点的挤出段求长度与挤出量）在【指定挤出类型】下的线宽，
    并与期望值进行比较，返回校验是否通过及详细差异信息。

    参数
    ----
    gcode_path : Path | str
        G-code 文件路径。用于初始化内部 GCodeParser 并读取配置/层信息/路径数据。

    expected_line_width : float
        期望的线宽（单位：mm）。对每一段计算出的线宽都会与该值比较。

    extrusion_types : Optional[Sequence[ExtrusionTypeLike]]，关键字参数
        需要参与校验的挤出类型过滤器（例如：outer/inner wall、infill、support 等）。
        - 传 None（默认）表示不过滤，校验所有挤出类型。
        - 类型元素可为内部定义的枚举/字符串等（ExtrusionTypeLike）。

    layer_indices : Optional[Sequence[int]]，关键字参数
        仅校验的层索引集合（0-based）。如果为 None，则根据解析到的总层数自动取全量层。
        会与 `skip_layers` 联合生效：先确定有效层，再从中剔除跳过层。📣当使用-1的时候，
        代表最后一层。

    skip_layers : Optional[Sequence[int]]，关键字参数
        需要显式跳过的层索引集合（0-based）。仅在其索引合法且位于总层数范围内时生效。

    filament_diameter : float，关键字参数，默认 1.75
        耗材直径（单位：mm）。用于由挤出长度 E 反算体积流、进而反推线宽。
        要求 > 0。

    tolerance : float，关键字参数，默认 0.02
        允许误差（单位：mm）。若 |计算线宽 - 期望线宽| > tolerance，则记为异常段。
        要求 >= 0。

    object_id : int，关键字参数，默认 0
        在多对象（multi-object）G-code 中要检查的对象 ID。仅遍历该对象的路径。
        若该层下对象不存在对应路径则跳过。

    返回
    ----
    (ok, expected, details) : Tuple[bool, float, Dict[str, object]]
        - ok : bool
            校验是否通过。满足“至少检查到一段挤出 + 无异常段”条件才为 True。
        - expected : float
            原样返回的 `expected_line_width`，便于上层调用保持统一接口。
        - details : Dict[str, object]
            细节信息字典，包含：
            * "bad_segments": List[Dict[str, object]]
                所有不满足误差容限的段，每项包含：
                {
                    "layer": 层索引,
                    "type": 挤出类型名,
                    "polyline_index": 该层内多段折线的索引,
                    "point_index": 在折线中的点索引（对应本段终点）,
                    "width": 反算得到的线宽（mm）,
                    "expected": 期望线宽（mm）,
                    "length": 段长度（mm）,
                    "extrusion": 段对应的 E 增量（mm，未启用体积挤出时为进料长度）,
                    "height": 层高（mm）,
                    "flow_ratio": 从配置解析得到的流量倍率（dimensionless）
                }
                若完全没有可检查的挤出段，会追加一条
                {"reason": "no-segments", "message": "..."} 的记录。
            * "checked_segments": int
                实际参与计算与比较的段数量。
            * "missing_layers": List[int]
                解析过程中不可用/缺失的层索引（例如层号越界或不存在）。
            * "skipped_layers": List[int]
                被显式跳过的层索引（来自 `skip_layers`）。
            * "unresolved_layer_heights": List[int]
                未能解析出有效层高（<=0 或 None）的层索引，这些层被跳过。
            * "flow_ratio": float
                从 G-code 配置中解析得到的全局流量倍率（用于反算线宽时修正）。
            * "tolerance": float
                本次使用的容差（mm）。
            * "layer_indices": List[int]
                最终参与校验的层索引列表（考虑过滤与跳过之后的结果）。
            * "type_filter": Union[List[str], Literal["all"]]
                实际生效的挤出类型过滤器（字符串名列表或 "all"）。

    说明
    ----
    - 线宽反算公式使用 `compute_line_width(E, L, h, d=filament_diameter, flow_ratio=flow_ratio)`，
      其中 E 为该段的正向挤出长度（未开启体积挤出模式时为进料长度，单位 mm），
      L 为段的 XY 投影长度（mm），h 为层高（mm），d 为耗材直径（mm）。
    - 仅统计 point.kind == "extrude" 且携带挤出量（has_e）的段；换刀点/toolchange 会重置上一点。
    - 当未检查到任何有效段时，`ok` 为 False，并在 "bad_segments" 中补充 "no-segments" 原因。
    """
    if expected_line_width <= 0:
        raise ValueError("expected_line_width must be > 0")
    if filament_diameter <= 0:
        raise ValueError("filament_diameter must be > 0")
    if tolerance < 0:
        raise ValueError("tolerance must be >= 0")

    path_obj = Path(gcode_path)
    parser = GCodeParser(path_obj)

    cfg = parser.load_config()
    flow_ratio = _resolve_flow_ratio(cfg)

    layer_info = parser.extract_layers()
    type_names = _to_type_names(extrusion_types)

    contours = parser.get_type_contours_per_layer(types=type_names if type_names else None, workers=0)
    total_layers = len(contours)

    valid_layers, missing_layers = _normalize_layer_indices(layer_indices, total_layers)
    skip_set = {
        idx for idx in (skip_layers or [])
        if isinstance(idx, int) and 0 <= idx < total_layers
    }
    valid_layers = [idx for idx in valid_layers if idx not in skip_set]

    bad_segments: List[Dict[str, object]] = []
    unresolved_layer_heights: set[int] = set()
    segments_checked = 0

    for layer_idx in valid_layers:
        layer_map = contours[layer_idx] or {}
        obj_map = layer_map.get(object_id, {})
        if not obj_map:
            continue

        layer_height = _resolve_layer_height(layer_info, layer_idx)
        if layer_height is None or layer_height <= 0:
            unresolved_layer_heights.add(layer_idx)
            continue

        for type_name, polylines in obj_map.items():
            if type_names is not None and type_name not in type_names:
                continue

            # 校验闭合轮廓线 polylines 的点
            for poly_idx, polyline in enumerate(polylines or []):
                prev_xy: Optional[Tuple[float, float]] = None

                for point_idx, point in enumerate(polyline):
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
                    if abs(length) <= 1e-6:
                        # 不知道为什么打印支撑面的时候，有时候会有些几乎不会动的运动（换刀点到挤出点的长度为几乎0或者就是0）...
                        # 这种情况下做跳过处理
                        continue
                        # print("layer_idx = ", layer_idx, "poly_idx = ", poly_idx, "point_idx = ", point_idx)
                    # assert length > 0.0
                    width = compute_line_width(
                        point.e,
                        length,
                        layer_height,
                        d=filament_diameter,
                        flow_ratio=flow_ratio,
                    )

                    segments_checked += 1
                    segment_info = {
                        "layer": layer_idx,
                        "type": type_name,
                        "polyline_index": poly_idx,
                        "point_index": point_idx,
                        "width": width,
                        "expected": expected_line_width,
                        "length": length,
                        "extrusion": point.e,
                        "height": layer_height,
                        "flow_ratio": flow_ratio,
                    }

                    if abs(width - expected_line_width) > tolerance:
                        bad_segments.append(segment_info)

                    prev_xy = (point.x, point.y)

    if segments_checked == 0:
        bad_segments.append({
            "reason": "no-segments",
            "expected": expected_line_width,
            "message": "no extrusion segments available for width check",
        })

    details: Dict[str, object] = {
        "bad_segments": bad_segments,
        "checked_segments": segments_checked,
        "missing_layers": missing_layers,
        "skipped_layers": sorted(skip_set),
        "unresolved_layer_heights": sorted(unresolved_layer_heights),
        "flow_ratio": flow_ratio,
        "tolerance": tolerance,
        "layer_indices": valid_layers,
        "type_filter": type_names if type_names is not None else "all",
    }

    ok = segments_checked > 0 and not bad_segments
    return ok, expected_line_width, details


def parse_initial_layer_line_width(
        gcode_path: Path | str,
        expected_line_width: float,
        *,
        extrusion_types: Optional[Sequence[ExtrusionTypeLike]] = None,
        tolerance: float = 0.001,
        object_id: int = 0,
) -> Tuple[bool, float, Dict[str, object]]:
    """
    Convenience wrapper for initial_layer_line_width: checks layer 0 polylines
    and reads filament diameter from the configuration.
    """
    path_obj = Path(gcode_path)
    parser = GCodeParser(path_obj)
    cfg = parser.load_config()
    # 从gcode中读取耗材直径
    effective_diameter = _resolve_filament_diameter(cfg)

    return parse_line_width_from_type(
        gcode_path,
        expected_line_width,
        extrusion_types=extrusion_types,
        layer_indices=[0],
        filament_diameter=effective_diameter,
        tolerance=tolerance,
        object_id=object_id,
    )


# ============= 新增 L1 校验函数 =============

def parse_line_width(
    gcode_path: Path | str,
    expected_value: float,
    tolerance: float = 0.01
) -> Tuple[bool, Optional[float], Dict[str, object]]:
    """检测默认线宽参数 (line_width) - L1: CONFIG_BLOCK"""
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("line_width")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 line_width 参数"})
    
    try:
        actual_value = float(raw_value)
        ok = abs(actual_value - expected_value) <= tolerance
    except (ValueError, TypeError) as e:
        return (False, None, {"error": f"无法解析 line_width 值: {raw_value}", "exception": str(e)})
    
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "tolerance": tolerance,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


def parse_internal_solid_infill_line_width(
    gcode_path: Path | str,
    expected_value: float,
    tolerance: float = 0.01
) -> Tuple[bool, Optional[float], Dict[str, object]]:
    """检测内部实心填充线宽参数 (internal_solid_infill_line_width) - L1: CONFIG_BLOCK"""
    parser = GCodeParser(str(gcode_path))
    config = parser.load_config()
    
    raw_value = config.get("internal_solid_infill_line_width")
    if raw_value is None:
        return (False, None, {"error": "未在 G-code 配置中找到 internal_solid_infill_line_width 参数"})
    
    try:
        actual_value = float(raw_value)
        ok = abs(actual_value - expected_value) <= tolerance
    except (ValueError, TypeError) as e:
        return (False, None, {"error": f"无法解析 internal_solid_infill_line_width 值: {raw_value}", "exception": str(e)})
    
    details = {
        "config_value": actual_value,
        "expected": expected_value,
        "tolerance": tolerance,
        "method": "L1 - CONFIG_BLOCK"
    }
    return (ok, actual_value, details)


if __name__ == "__main__":
    w = compute_line_width(1.37489, 18.186, 0.2, 1.75, 0.95)
    print(w)

