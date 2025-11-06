from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from engine_params.src.gcode.GCodeParser import GCodeParser, Point
from engine_params.src.gcode.constants import ExtrusionType


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        raise ValueError("detect_narrow_internal_solid_infill 缺失配置值")
    if isinstance(value, (int, float)):
        return value != 0
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"detect_narrow_internal_solid_infill 无法解析为布尔值: {value!r}")


# ================== detect_narrow_internal_solid_infill ==================
def parse_detect_narrow_internal_solid_infill(
        gcode_path: Path | str,
        expected_enabled: bool,
        *,
        object_id: int = 0,
) -> Tuple[bool, Dict[str, Any]]:
    parser = GCodeParser(Path(gcode_path))
    cfg = parser.load_config()
    if "detect_narrow_internal_solid_infill" not in cfg:
        raise ValueError("CONFIG_BLOCK 缺少 detect_narrow_internal_solid_infill 字段")

    config_enabled = _coerce_bool(cfg["detect_narrow_internal_solid_infill"])
    expected_polyline_count = 3 if expected_enabled else 1

    layer_info = parser.extract_layers()
    total_layers = len(layer_info)

    contours = parser.get_type_contours_per_layer_by_object(
        object_id,
        types=[
            ExtrusionType.INTERNAL_SOLID_INFILL,
            ExtrusionType.SPARSE_INFILL,
            ExtrusionType.TOP_SURFACE,
            ExtrusionType.BOTTOM_SURFACE,
        ],
    )

    solid_layers: List[Dict[str, int]] = []
    violations: List[Dict[str, int]] = []

    for layer_idx, type_map in enumerate(contours or []):
        if layer_idx == 0 or layer_idx >= total_layers - 1:
            continue

        has_sparse = bool(type_map.get(ExtrusionType.SPARSE_INFILL))
        has_top = bool(type_map.get(ExtrusionType.TOP_SURFACE))
        has_bottom = bool(type_map.get(ExtrusionType.BOTTOM_SURFACE))
        solid_polys = type_map.get(ExtrusionType.INTERNAL_SOLID_INFILL) or []

        if not solid_polys or has_sparse or has_top or has_bottom:
            continue

        polyline_count = len(solid_polys)
        solid_layers.append({
            "layer_index": layer_idx,
            "polyline_count": polyline_count,
        })
        if polyline_count != expected_polyline_count:
            violations.append({
                "layer_index": layer_idx,
                "polyline_count": polyline_count,
                "expected": expected_polyline_count,
            })

    details: Dict[str, Any] = {
        "expected_enabled": expected_enabled,
        "config_enabled": config_enabled,
        "expected_polyline_count": expected_polyline_count,
        "solid_layers": solid_layers,
        "violations": violations,
    }

    ok = (config_enabled == expected_enabled) and not violations
    return ok, details


# ================== bridge_angle ==================
def parse_bridge_angle(
        gcode_path: Path | str,
        expected_bridge_angle: float,
        *,
        baseline_gcode: Path | str | None = None,
        tolerance: float = 1.0,
        object_id: int = 0,
) -> Tuple[bool, Optional[float], Dict[str, Any]]:
    """
    桥接角度校验：
      - expected_bridge_angle == 0：依赖基线 G-code，对 Bridge 轮廓做快照比对；
      - expected_bridge_angle != 0：取首条 Bridge polyline 的前两个点，计算与 X 轴的夹角。
    """
    parser = GCodeParser(Path(gcode_path))
    contours = parser.get_type_contours_per_layer_by_object(
        object_id,
        types=[ExtrusionType.BRIDGE],
    ) or []

    bridge_layers: List[Tuple[int, List[List[Point]]]] = []
    for idx, layer_map in enumerate(contours):
        polylines = layer_map.get(ExtrusionType.BRIDGE, [])
        if polylines:
            bridge_layers.append((idx, polylines))

    if not bridge_layers:
        raise ValueError("G-code 中未找到 Bridge 挤出层，无法校验 bridge_angle")

    details: Dict[str, Any] = {
        "bridge_layers": [idx for idx, _ in bridge_layers],
        "expected_bridge_angle": expected_bridge_angle,
        "mode": "angle" if expected_bridge_angle != 0.0 else "snapshot",
    }

    # 当期望为0°的时候，应该使用快照法
    if abs(expected_bridge_angle) < 1e-6:
        if not baseline_gcode:
            raise ValueError("expected_bridge_angle=0 时必须提供 baseline_gcode 进行快照比对")

        baseline_parser = GCodeParser(Path(baseline_gcode))
        baseline_layers = baseline_parser.get_type_contours_per_layer_by_object(
            object_id,
            types=[ExtrusionType.BRIDGE],
        ) or []

        bridge_layer_indices = {idx for idx, _ in bridge_layers}
        for idx, layer_map in enumerate(baseline_layers):
            if layer_map.get(ExtrusionType.BRIDGE):
                bridge_layer_indices.add(idx)

        def _layer_filter(layer_idx: int, total_layers: int) -> bool:
            return layer_idx in bridge_layer_indices

        ok, compare_details = GCodeParser.compare_type_contours(
            baseline_parser,
            parser,
            object_id=object_id,
            types=[ExtrusionType.BRIDGE],
            tolerance=tolerance,
            layer_filter=_layer_filter,
        )
        details["baseline_gcode"] = str(Path(baseline_gcode))
        details["compare_details"] = compare_details
        return ok, None, details

    layer_idx, polylines = bridge_layers[0]
    first_polyline = polylines[0]
    if len(first_polyline) < 2:
        raise ValueError(f"Bridge 层 {layer_idx} polyline 点数不足，无法计算角度")

    p0, p1 = first_polyline[0], first_polyline[1]
    dx = p1.x - p0.x
    dy = p1.y - p0.y
    angle = math.degrees(math.atan2(dy, dx))
    angle = angle % 360.0
    # 计算的是与X轴正方向的夹角角度
    if angle > 180.0:
        angle -= 360.0
    if angle < 0.0:
        angle += 180.0

    # 来个兜底逻辑，程序中的0°相当于自动计算桥接角度的占位符，计算出来的180°和0°角度应该归为0°。
    if abs(angle) < tolerance or abs(angle - 180.0) < tolerance:
        angle = 180.0

    actual_angle = angle
    ok = abs(actual_angle - expected_bridge_angle) <= tolerance

    details.update({
        "actual_bridge_angle": actual_angle,
        "layer_index": layer_idx,
        "point_pair": ((p0.x, p0.y), (p1.x, p1.y)),
        "tolerance": tolerance,
    })

    if (abs(actual_angle - 0.0) < tolerance or abs(
            actual_angle - 180.0) < tolerance) and expected_bridge_angle != 180.0:
        ok = False
        details.setdefault("errors", []).append(
            "Bridge 角度为 0°/180° 时，应将 expected_bridge_angle 设为 180° 以表示自动模式。"
        )

    return ok, actual_angle, details


# ================== minimum_sparse_infill_area ==================
def _inner_wall_area(polylines: List[List[Point]], line_width: float) -> Optional[float]:
    if not polylines:
        return None
    min_area = None
    for poly in polylines:
        if not poly:
            continue
        xs = [pt.x for pt in poly]
        ys = [pt.y for pt in poly]
        width = max(xs) - min(xs)
        height = max(ys) - min(ys)
        inner_width = max(width - line_width, 0.0)
        inner_height = max(height - line_width, 0.0)
        area = inner_width * inner_height
        if min_area is None or area < min_area:
            min_area = area
    return min_area


def parse_minimum_sparse_infill_area(
        gcode_path: Path | str,
        *,
        object_id: int = 0,
) -> Tuple[bool, Dict[str, Any]]:
    """
    校验 minimum_sparse_infill_area：
      - 仅对中间层（排除 top/bottom shell）计算面积
      - 面积 > 阈值时应存在 Internal solid infill，否则不应存在
    """
    parser = GCodeParser(Path(gcode_path))
    cfg = parser.load_config()

    threshold = float(cfg.get("minimum_sparse_infill_area", 0.0))
    bottom_shell_layers = int(cfg.get("bottom_shell_layers", 0))
    top_shell_layers = int(cfg.get("top_shell_layers", 0))
    line_width = float(cfg.get("inner_wall_line_width", 0.0))

    layer_info = parser.extract_layers()
    total_layers = len(layer_info)

    start_layer = max(bottom_shell_layers, 0)
    end_layer = max(total_layers - top_shell_layers, 0)
    valid_indices = range(start_layer, max(start_layer, end_layer))

    inner_contours = parser.get_type_contours_per_layer_by_object(
        object_id,
        types=[ExtrusionType.INNER_WALL],
    ) or []

    solid_contours = parser.get_type_contours_per_layer_by_object(
        object_id,
        types=[ExtrusionType.INTERNAL_SOLID_INFILL],
    ) or []

    violations: List[Dict[str, Any]] = []
    layer_reports: List[Dict[str, Any]] = []

    for layer_idx in valid_indices:
        if layer_idx >= len(inner_contours):
            break
        inner_polys = (inner_contours[layer_idx] or {}).get(ExtrusionType.INNER_WALL, [])
        # 以最内部内墙轮廓估算该层有效截面积
        area = _inner_wall_area(inner_polys, line_width)
        if area is None:
            continue

        expect_solid = area > threshold  # 超过阈值则期待出现 Internal solid infill
        actual_solid = bool(
            layer_idx < len(solid_contours)
            and (solid_contours[layer_idx] or {}).get(ExtrusionType.INTERNAL_SOLID_INFILL)
        )

        report = {
            "layer_index": layer_idx,
            "area": area,
            "expect_solid": expect_solid,
            "actual_solid": actual_solid,
        }
        layer_reports.append(report)
        if expect_solid != actual_solid:
            violations.append(report)

    details: Dict[str, Any] = {
        "threshold": threshold,
        "bottom_shell_layers": bottom_shell_layers,
        "top_shell_layers": top_shell_layers,
        "line_width": line_width,
        "layer_reports": layer_reports,
        "violations": violations,
    }

    ok = len(violations) == 0
    return ok, details


