from __future__ import annotations

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


def parse_bottom_shell_layers(
        gcode_path: Path | str,
        expected_layers: int,
) -> Tuple[bool, int, List[Tuple[int, str, Dict[str, Any]]]]:
    """
    У��ģ���ײ�壨Bottom Surface + Internal solid infill���ܲ屨�㣩�Ƿ���������ɡ�
    ����
      - �ڵײ㲿���ҵ� Bottom surface ��ʼ���У�
      - ���Ϸ���� Internal solid infill ���㣬ֱ����ĳ�� first Sparse infill �����
      - ͳ֮ Bottom surface + Internal solid infill �ܲ屨�����Ӧ = expected_layers
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
