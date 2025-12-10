from __future__ import annotations

import math
import mmap
from pathlib import Path
from typing import Any, Dict, List, Tuple

from engine_params.src.gcode.GCodeParser import (
    GCodeParser,
    TYPE_PREFIX,
    find_all,
    parse_type_name_at,
)
from engine_params.src.gcode.constants import ExtrusionType

THICKNESS_TOL = 1e-6


def parse_top_shell_layers(
        gcode_path: Path | str,
        expected_layers: int,
) -> Tuple[bool, int, List[Tuple[int, str, Dict[str, Any]]]]:
    """
    校验顶部壳层结构是否满足期望层数与顺序要求。
    规则：
      - 模型总层数必须大于 expected_layers；
      - 在最顶部 expected_layers 个层中，挤出类型顺序必须为：
            Internal bridge -> (expected_layers-2) * Internal solid infill -> Top surface；
      - Internal bridge 与 Top surface 均需各出现一次。
    返回:
        ok: 校验是否通过
        expected_layers: 原样返回期望层数
        bad_layers: [(layer_idx, reason, details)]
    """
    if expected_layers < 2:
        raise ValueError(f"expected_layers must be >= 2, got {expected_layers}")

    parser = GCodeParser(gcode_path)
    flat_wins = parser._layer_windows_flat()
    total_layers = len(flat_wins)
    if total_layers <= expected_layers:
        raise AssertionError(
            f"model layers ({total_layers}) must be greater than expected_layers ({expected_layers})"
        )

    target_start = total_layers - expected_layers
    target_indices = list(range(target_start, total_layers))

    relevant_types = {ExtrusionType.INTERNAL_BRIDGE.value, ExtrusionType.INTERNAL_SOLID_INFILL.value, ExtrusionType.TOP_SURFACE.value}
    layer_types: Dict[int, List[str]] = {}

    with parser.path.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        for idx in target_indices:
            start, end = flat_wins[idx]
            names: List[str] = []
            for pos in find_all(mm, TYPE_PREFIX, start, end):
                name = parse_type_name_at(mm, pos, end)
                if name in relevant_types:
                    names.append(name)
            layer_types[idx] = names

    bridge_idxs = [idx for idx in target_indices if ExtrusionType.INTERNAL_BRIDGE.value in layer_types.get(idx, [])]
    top_idxs = [idx for idx in target_indices if ExtrusionType.TOP_SURFACE.value in layer_types.get(idx, [])]
    solid_idxs = [
        idx
        for idx in target_indices
        if (
            ExtrusionType.INTERNAL_SOLID_INFILL.value in layer_types.get(idx, [])
            and idx not in bridge_idxs
            and idx not in top_idxs
        )
    ]

    bad_layers: List[Tuple[int, str, Dict[str, Any]]] = []

    if len(bridge_idxs) != 1:
        bad_layers.append((
            bridge_idxs[0] if bridge_idxs else -1,
            "bridge-count-mismatch",
            {"count": len(bridge_idxs), "expected": 1, "layers": bridge_idxs},
        ))
    if len(top_idxs) != 1:
        bad_layers.append((
            top_idxs[0] if top_idxs else -1,
            "top-surface-count-mismatch",
            {"count": len(top_idxs), "expected": 1, "layers": top_idxs},
        ))

    expected_solid = expected_layers - 2
    if len(solid_idxs) != expected_solid:
        bad_layers.append((
            solid_idxs[0] if solid_idxs else -1,
            "solid-count-mismatch",
            {"count": len(solid_idxs), "expected": expected_solid, "layers": solid_idxs},
        ))

    if not bad_layers:
        bridge_idx = bridge_idxs[0]
        top_idx = top_idxs[-1]
        expected_bridge_idx = target_indices[0]
        expected_top_idx = target_indices[-1]

        if bridge_idx != expected_bridge_idx:
            bad_layers.append((
                bridge_idx,
                "bridge-layer-mismatch",
                {"actual": bridge_idx, "expected": expected_bridge_idx},
            ))

        if top_idx != expected_top_idx:
            bad_layers.append((
                top_idx,
                "top-layer-mismatch",
                {"actual": top_idx, "expected": expected_top_idx},
            ))

        if not bad_layers:
            expected_solid_indices = target_indices[1:-1]
            if expected_solid != len(expected_solid_indices):
                bad_layers.append((
                    -1,
                    "invalid-expected-layers",
                    {
                        "expected_layers": expected_layers,
                        "expected_solid_layers": expected_solid,
                    },
                ))
            else:
                if solid_idxs != expected_solid_indices:
                    bad_layers.append((
                        solid_idxs[0] if solid_idxs else -1,
                        "solid-layer-sequence-mismatch",
                        {
                            "expected": expected_solid_indices,
                            "actual": solid_idxs,
                        },
                    ))

    ok = len(bad_layers) == 0
    return ok, expected_layers, bad_layers


def _to_float(value: Any, *, field: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be convertible to float, got {value!r}") from exc


def _to_int(value: Any, *, field: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be convertible to int, got {value!r}") from exc


# ================== helper utilities ==================
def _layer_height_or_default(
        layer_info: List[Tuple[Any, Any]],
        idx: int,
        default_height: float,
) -> float:
    if 0 <= idx < len(layer_info):
        _, h = layer_info[idx]
        if isinstance(h, (int, float)) and h > 0:
            return float(h)
    return default_height


def _sum_layer_heights(
        layer_info: List[Tuple[Any, Any]],
        indices: List[int],
        default_height: float,
) -> float:
    return sum(_layer_height_or_default(layer_info, idx, default_height) for idx in indices)


def _collect_top_shell_layers_desc(parser: GCodeParser) -> List[int]:
    flat_wins = parser._layer_windows_flat()
    total_layers = len(flat_wins)
    if total_layers == 0:
        return []

    layers_desc: List[int] = []
    collecting = False

    with parser.path.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        for idx in range(total_layers - 1, -1, -1):
            start, end = flat_wins[idx]
            has_top = False
            has_solid = False
            has_bridge = False
            has_sparse = False
            for pos in find_all(mm, TYPE_PREFIX, start, end):
                name = parse_type_name_at(mm, pos, end)
                if name == ExtrusionType.TOP_SURFACE.value:
                    has_top = True
                elif name == ExtrusionType.INTERNAL_SOLID_INFILL.value:
                    has_solid = True
                elif name == ExtrusionType.INTERNAL_BRIDGE.value:
                    has_bridge = True
                elif name == ExtrusionType.SPARSE_INFILL.value:
                    has_sparse = True

            valid_layer = has_top or has_solid or has_bridge

            if not collecting:
                if has_top:
                    collecting = True
                    layers_desc.append(idx)
                continue

            if collecting:
                if has_sparse and has_solid:
                    break
                if valid_layer:
                    layers_desc.append(idx)
                else:
                    break

    return layers_desc


def _collect_bottom_shell_layers(parser: GCodeParser) -> List[int]:
    flat_wins = parser._layer_windows_flat()
    total_layers = len(flat_wins)
    if total_layers == 0:
        return []

    relevant_main = {
        "Bottom surface",
        ExtrusionType.INTERNAL_SOLID_INFILL.value,
    }
    sparse_type = ExtrusionType.SPARSE_INFILL.value

    layers: List[int] = []
    collecting = False

    with parser.path.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        for idx, (start, end) in enumerate(flat_wins):
            names: List[str] = []
            for pos in find_all(mm, TYPE_PREFIX, start, end):
                name = parse_type_name_at(mm, pos, end)
                if name in relevant_main or name == sparse_type:
                    names.append(name)
            has_bottom = "Bottom surface" in names
            has_solid = ExtrusionType.INTERNAL_SOLID_INFILL.value in names
            has_sparse = sparse_type in names

            if not collecting:
                if has_bottom:
                    collecting = True
                    layers.append(idx)
                continue

            if has_sparse:
                break

            if has_bottom or has_solid:
                layers.append(idx)
            else:
                break

    return layers


# ================== top_shell_thickness ==================
def parse_top_shell_thickness(
        gcode_path: Path | str,
        expected_top_shell_thickness: float,
) -> Tuple[bool, int | None, Dict[str, Any]]:
    """
    校验顶部壳体厚度是否满足兜底规则：
      - 依据实际顶部壳体层（Top surface/Bridge/Internal solid infill）计算真实厚度
      - 如果真实厚度不足，则按默认层高补齐实心层数
      - 返回最终需要的层数以及实际厚度供测试断言
    """
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()

    if "layer_height" not in cfg:
        raise ValueError("CONFIG_BLOCK 缺失 layer_height 字段")
    default_layer_height = _to_float(cfg["layer_height"], field="layer_height")
    if default_layer_height <= 0:
        raise ValueError(f"layer_height must be > 0, got {default_layer_height}")

    if "top_shell_layers" not in cfg:
        raise ValueError("CONFIG_BLOCK 缺失 top_shell_layers 字段")
    thickness = _to_float(expected_top_shell_thickness, field="expected_top_shell_thickness")
    config_layers = max(0, _to_int(cfg["top_shell_layers"], field="top_shell_layers"))

    layer_info = parser.extract_layers()
    top_layers_desc = _collect_top_shell_layers_desc(parser)
    actual_layers = len(top_layers_desc)

    violations: List[Tuple[int, str, Dict[str, Any]]] = []
    if not top_layers_desc and (config_layers > 0 or thickness > THICKNESS_TOL):
        violations.append((-1, "no-top-shell-layers", {}))

    if config_layers > actual_layers:
        violations.append((-1, "top-shell-layer-shortage", {
            "config_layers": config_layers,
            "actual_layers": actual_layers,
        }))

    base_layers = top_layers_desc[:config_layers] if config_layers > 0 else []
    base_thickness = _sum_layer_heights(layer_info, base_layers, default_layer_height)

    required_layers = config_layers
    if base_thickness + THICKNESS_TOL < thickness:
        deficit = thickness - base_thickness
        extra_needed = int(math.ceil((deficit - THICKNESS_TOL) / default_layer_height))
        required_layers += max(extra_needed, 1)

    actual_thickness = _sum_layer_heights(layer_info, top_layers_desc, default_layer_height)

    if actual_layers != required_layers:
        violations.append((-1, "top-layer-count-mismatch", {
            "expected": required_layers,
            "actual": actual_layers,
        }))

    if actual_thickness + THICKNESS_TOL < thickness:
        violations.append((-1, "top-thickness-shortfall", {
            "expected_thickness": thickness,
            "actual_thickness": actual_thickness,
        }))

    ok = len(violations) == 0
    matched_layers = actual_layers if ok else None

    details: Dict[str, Any] = {
        "expected_top_shell_thickness": thickness,
        "layer_height": default_layer_height,
        "base_thickness": base_thickness,
        "config_top_shell_layers": config_layers,
        "layers_from_thickness": required_layers,
        "target_layers": required_layers,
        "actual_layers": actual_layers,
        "actual_thickness": actual_thickness,
        "violations": violations,
    }

    return ok, matched_layers, details


# ================== bottom_shell_thickness ==================
def parse_bottom_shell_thickness(
        gcode_path: Path | str,
        expected_bottom_shell_thickness: float,
) -> Tuple[bool, int | None, Dict[str, Any]]:
    """
    校验底部壳体厚度是否满足兜底规则：
      - 统计 Bottom surface + Internal solid infill 实际层厚
      - 若实际厚度不足，则根据默认层高推算需要补充的实心层
      - 返回最终层数与厚度，便于测试侧核对
    """
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()

    if "layer_height" not in cfg:
        raise ValueError("CONFIG_BLOCK 缺失 layer_height 字段")
    default_layer_height = _to_float(cfg["layer_height"], field="layer_height")
    if default_layer_height <= 0:
        raise ValueError(f"layer_height must be > 0, got {default_layer_height}")

    if "bottom_shell_layers" not in cfg:
        raise ValueError("CONFIG_BLOCK 缺失 bottom_shell_layers 字段")
    thickness = _to_float(expected_bottom_shell_thickness, field="expected_bottom_shell_thickness")

    config_layers = max(0, _to_int(cfg["bottom_shell_layers"], field="bottom_shell_layers"))
    layer_info = parser.extract_layers()
    bottom_layers = _collect_bottom_shell_layers(parser)
    actual_layers = len(bottom_layers)

    violations: List[Tuple[int, str, Dict[str, Any]]] = []
    if not bottom_layers and (config_layers > 0 or thickness > THICKNESS_TOL):
        violations.append((-1, "no-bottom-shell-layers", {}))
    if config_layers > actual_layers:
        violations.append((-1, "bottom-shell-layer-shortage", {
            "config_layers": config_layers,
            "actual_layers": actual_layers,
        }))

    base_layers = bottom_layers[:config_layers] if config_layers > 0 else []
    base_thickness = _sum_layer_heights(layer_info, base_layers, default_layer_height)

    required_layers = config_layers
    if base_thickness + THICKNESS_TOL < thickness:
        deficit = thickness - base_thickness
        extra_needed = int(math.ceil((deficit - THICKNESS_TOL) / default_layer_height))
        required_layers += max(extra_needed, 1)

    actual_thickness = _sum_layer_heights(layer_info, bottom_layers, default_layer_height)

    if actual_layers != required_layers:
        violations.append((-1, "bottom-layer-count-mismatch", {
            "expected": required_layers,
            "actual": actual_layers,
        }))

    if actual_thickness + THICKNESS_TOL < thickness:
        violations.append((-1, "bottom-thickness-shortfall", {
            "expected_thickness": thickness,
            "actual_thickness": actual_thickness,
        }))

    ok = len(violations) == 0
    matched_layers = actual_layers if ok else None

    details: Dict[str, Any] = {
        "expected_bottom_shell_thickness": thickness,
        "layer_height": default_layer_height,
        "base_thickness": base_thickness,
        "config_bottom_shell_layers": config_layers,
        "layers_from_thickness": required_layers,
        "target_layers": required_layers,
        "actual_layers": actual_layers,
        "actual_thickness": actual_thickness,
        "violations": violations,
    }

    return ok, matched_layers, details


# ================== top_bottom_infill_wall_overlap ==================
def parse_top_bottom_infill_wall_overlap(
        gcode_path: Path | str,
        baseline_gcode: Path | str,
        *,
        tolerance: float = 1e-6,
        object_id: int = 0,
) -> Tuple[bool, Dict[str, Any]]:
    """
    通过对比测试 G-code 与基线 G-code 的顶/底面轮廓来校验 top_bottom_infill_wall_overlap。
    """
    test_parser = GCodeParser(Path(gcode_path))
    baseline_parser = GCodeParser(Path(baseline_gcode))

    ok, details = GCodeParser.compare_type_contours(
        baseline_parser,
        test_parser,
        object_id=object_id,
        types=[ExtrusionType.TOP_SURFACE, ExtrusionType.BOTTOM_SURFACE],
        tolerance=tolerance,
    )
    details["baseline_gcode"] = str(Path(baseline_gcode))
    return ok, details


# ================== bottom_shell_layers ==================
def parse_bottom_shell_layers(
        gcode_path: Path | str,
        expected_layers: int,
) -> Tuple[bool, int, List[Tuple[int, str, Dict[str, Any]]]]:
    """
    校验底部壳体结构（Bottom surface + Internal solid infill）是否满足规则：
      - 必须存在 Bottom surface 层
      - Internal solid infill 需持续到遇到首层 Sparse infill
      - Bottom surface 与 Internal solid infill 的层数总和应为 expected_layers
    """
    if expected_layers <= 0:
        raise ValueError(f"expected_layers must be > 0, got {expected_layers}")

    parser = GCodeParser(gcode_path)
    flat_wins = parser._layer_windows_flat()
    total_layers = len(flat_wins)
    if total_layers == 0:
        return False, expected_layers, [(-1, "no-layers", {})]

    relevant_types = {
        "Bottom surface",
        ExtrusionType.INTERNAL_SOLID_INFILL.value,
        ExtrusionType.SPARSE_INFILL.value,
    }
    layer_types: Dict[int, List[str]] = {}

    with parser.path.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        for idx, (start, end) in enumerate(flat_wins):
            names: List[str] = []
            for pos in find_all(mm, TYPE_PREFIX, start, end):
                name = parse_type_name_at(mm, pos, end)
                if name in relevant_types:
                    names.append(name)
            layer_types[idx] = names

    bottom_start = None
    for idx in range(total_layers):
        types = layer_types.get(idx, [])
        if "Bottom surface" in types:
            bottom_start = idx
            break

    if bottom_start is None:
        return False, expected_layers, [(-1, "no-bottom-surface", {})]

    counted_layers = []
    for idx in range(bottom_start, total_layers):
        types = layer_types.get(idx, [])
        if ExtrusionType.SPARSE_INFILL.value in types:
            break
        if ("Bottom surface" in types) or (ExtrusionType.INTERNAL_SOLID_INFILL.value in types):
            counted_layers.append(idx)
        else:
            break

    total_count = len(counted_layers)
    bad_layers: List[Tuple[int, str, Dict[str, Any]]] = []

    if total_count != expected_layers:
        bad_layers.append((
            counted_layers[0] if counted_layers else bottom_start,
            "count-mismatch",
            {
                "count": total_count,
                "expected": expected_layers,
                "layers": counted_layers,
            },
        ))

    ok = len(bad_layers) == 0
    return ok, expected_layers, bad_layers
