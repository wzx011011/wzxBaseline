from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from engine_params.src.gcode.GCodeParser import GCodeParser, Point
from engine_params.src.gcode.GCodeParserEx import GCodeParserEx
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




# ================== infill_combination ==================
def parse_infill_combination(
        gcode_path: Path | str,
        expected_enabled: bool,
        expected_interval: Optional[int] = None,
) -> Tuple[bool, bool, Dict[str, Any]]:
    """
    稀疏填充合并：N = int(nozzle_diameter / layer_height)，
    检查相邻稀疏填充所在层的层号差是否为 N（跳过首层）。
    """
    path_obj = Path(gcode_path)
    parser = GCodeParserEx(path_obj)

    cfg = parser.load_config() or {}
    nozzle_cfg = cfg.get("nozzle_diameter")

    def _to_float(v) -> Optional[float]:
        try:
            return float(getattr(v, "value", v))
        except (TypeError, ValueError):
            return None

    nozzle_diameter = _to_float(nozzle_cfg)
    if nozzle_diameter is None or nozzle_diameter <= 0:
        details = {
            "expected_enabled": expected_enabled,
            "nozzle_diameter": nozzle_diameter,
            "layer_height": None,
            "interval_N": None,
            "sparse_layers": [],
            "diffs": [],
            "note": "Invalid nozzle_diameter in config.",
            "match": False,
        }
        return False, expected_enabled, details

    layers_meta = parser.extract_layers()
    layer_height = None
    for _, h in layers_meta:
        if h and h > 0:
            layer_height = float(h)
            break

    if layer_height is None or layer_height <= 0:
        details = {
            "expected_enabled": expected_enabled,
            "nozzle_diameter": nozzle_diameter,
            "layer_height": layer_height,
            "interval_N": None,
            "sparse_layers": [],
            "diffs": [],
            "note": "Cannot resolve layer_height.",
            "match": False,
        }
        return False, expected_enabled, details

    interval_N = int(nozzle_diameter / layer_height)
    interval_N = max(1, interval_N)

    layers = parser.get_type_contours_per_layer(types=[ExtrusionType.SPARSE_INFILL], skip_layers=[0])
    sparse_layers: List[int] = []
    for layer in layers:
        for _oid, type_map in (layer.regions or {}).items():
            if type_map.get(ExtrusionType.SPARSE_INFILL.value):
                sparse_layers.append(layer.index)
                break
    sparse_layers = sorted(set(sparse_layers))

    diffs = [b - a for a, b in zip(sparse_layers, sparse_layers[1:])]
    expect_diff = interval_N
    # 顶层前的最后一个稀疏填充层可能因壳层封顶而提前一层，只用
    # 完整的中间周期判断合并是否真正生效。
    periodic_diffs = diffs[:-1] if len(diffs) > 1 and diffs[-1] < expect_diff else diffs
    all_good = bool(periodic_diffs) and all(d == expect_diff for d in periodic_diffs)
    actual_enabled = all_good

    details = {
        "expected_enabled": expected_enabled,
        "actual_enabled": actual_enabled,
        "nozzle_diameter": nozzle_diameter,
        "layer_height": layer_height,
        "interval_N": interval_N,
        "expected_diff": expect_diff,
        "sparse_layers": sparse_layers,
        "diffs": diffs,
        "periodic_diffs": periodic_diffs,
        "expected_interval": expected_interval,
        "note": None if sparse_layers else "No sparse infill layers detected.",
        "match": (actual_enabled == expected_enabled) and (expected_interval is None or expect_diff == expected_interval),
    }

    return details["match"], expected_enabled, details


# ================== ensure_vertical_shell_thickness ==================
def parse_ensure_vertical_shell_thickness(
        gcode_path: Path | str,
        expected_value: str,
        baseline_gcode: Path | str,
        *,
        tolerance: float = 1e-6,
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    ensure_vertical_shell_thickness 快照校验：与基线 G-code 逐层对比外/内墙轮廓。
    - 轮廓点顺序可能不同，使用坐标匹配（容差）消除顺序影响。
    - 仅对比 Outer/Inner wall 轮廓，要求点数相等且坐标落在容差内。
    """
    path_obj = Path(gcode_path)
    baseline_obj = Path(baseline_gcode)
    parser_test = GCodeParserEx(path_obj)
    parser_base = GCodeParserEx(baseline_obj)

    target_types = [ExtrusionType.OUTER_WALL, ExtrusionType.INNER_WALL]
    type_names = [t.value for t in target_types]

    def _extract(parser: GCodeParserEx) -> Dict[int, Dict[str, List[List[Tuple[float, float]]]]]:
        """提取每层指定挤出类型的轮廓坐标。"""
        layers = parser.get_type_contours_per_layer(types=target_types) or []
        out: Dict[int, Dict[str, List[List[Tuple[float, float]]]]] = {}
        for layer in layers:
            for _oid, type_map in (layer.regions or {}).items():
                for tname, region in (type_map or {}).items():
                    if tname not in type_names or not region:
                        continue
                    for path in region.paths or []:
                        pts = [(p.x, p.y) for p in (path.points or [])]
                        out.setdefault(layer.index, {}).setdefault(tname, []).append(pts)
        return out

    base_layers = _extract(parser_base)
    test_layers = _extract(parser_test)

    def _points_match(base_pts: List[Tuple[float, float]], cand_pts: List[Tuple[float, float]]) -> bool:
        """忽略点顺序的匹配，逐点寻找未使用的近邻。"""
        if len(base_pts) != len(cand_pts):
            return False
        used: set[int] = set()
        for bx, by in base_pts:
            found = False
            for idx, (cx, cy) in enumerate(cand_pts):
                if idx in used:
                    continue
                if abs(bx - cx) <= tolerance and abs(by - cy) <= tolerance:
                    used.add(idx)
                    found = True
                    break
            if not found:
                return False
        return True

    mismatches: List[Dict[str, Any]] = []
    checked_layers: List[int] = []

    all_layer_indices = sorted(set(base_layers.keys()) | set(test_layers.keys()))

    for layer_idx in all_layer_indices:
        base_map = base_layers.get(layer_idx, {})
        test_map = test_layers.get(layer_idx, {})
        checked_layers.append(layer_idx)

        for tname in type_names:
            base_polys = list(base_map.get(tname, []))
            test_polys = list(test_map.get(tname, []))

            if not base_polys and not test_polys:
                continue

            if len(base_polys) != len(test_polys):
                mismatches.append({
                    "layer": layer_idx,
                    "type": tname,
                    "reason": "polyline-count-mismatch",
                    "baseline_polylines": len(base_polys),
                    "test_polylines": len(test_polys),
                })
                continue

            # 逐条 polyline 进行无序匹配
            remaining = test_polys.copy()
            for base_idx, base_poly in enumerate(base_polys):
                found_idx = None
                for cand_idx, cand_poly in enumerate(remaining):
                    if _points_match(base_poly, cand_poly):
                        found_idx = cand_idx
                        break
                if found_idx is not None:
                    remaining.pop(found_idx)
                else:
                    mismatches.append({
                        "layer": layer_idx,
                        "type": tname,
                        "reason": "polyline-mismatch",
                        "polyline_index": base_idx,
                        "baseline_points": len(base_poly),
                        "test_candidates": len(test_polys),
                    })
                    break

            if remaining:
                mismatches.append({
                    "layer": layer_idx,
                    "type": tname,
                    "reason": "extra-polylines",
                    "extra_count": len(remaining),
                })

    ok = not mismatches
    details = {
        "expected_value": expected_value,
        "baseline_gcode": str(baseline_obj),
        "tolerance": tolerance,
        "checked_layers": checked_layers,
        "mismatches": mismatches,
        "match": ok,
    }
    return ok, expected_value, details
