from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

from engine_params.src.gcode.GCodeParser import GCodeParser
from engine_params.src.gcode.constants import ExtrusionType


def parse_wall_loops(
        gcode_path: Path | str,
        expected_wall_loops: int,
) -> Tuple[bool, int, List[Tuple[int, str, Dict[str, Any]]]]:
    """
    校验整件模型在有效打印层中实际生成的墙圈数是否与期望一致。
    - 依赖 GCodeParser.get_type_contours_per_layer 获取每层的内/外墙轮廓。
    - 忽略未出现墙体的层（如支撑或空层），默认跳过首层判断粘附结构带来的噪声。
    返回:
      ok: 是否所有参与检查的层都满足期望圈数。
      expected_wall_loops: 原样回传的期望圈数。
      bad_layers: [(layer_idx, reason, details)]
    """
    if expected_wall_loops <= 0:
        raise ValueError(f"expected_wall_loops must be positive, got {expected_wall_loops}")

    parser = GCodeParser(gcode_path)
    contours = parser.get_type_contours_per_layer(types=[ExtrusionType.OUTER_WALL.value, ExtrusionType.INNER_WALL.value], workers=0)
    if not contours:
        return False, expected_wall_loops, [(-1, "no-contours", {})]

    target_oid = 0
    bad_layers: List[Tuple[int, str, Dict[str, Any]]] = []
    inspected_layers = 0

    last_index = len(contours) - 1

    for layer_idx, layer_map in enumerate(contours):
        if layer_idx == 0 or layer_idx == last_index:
            # 首层与末层可能包含铺底/收尾结构，默认跳过
            continue
        obj_map = (layer_map or {}).get(target_oid, {})
        outer = obj_map.get(ExtrusionType.OUTER_WALL.value) or []
        inner = obj_map.get(ExtrusionType.INNER_WALL.value) or []

        loop_count = len(outer) + len(inner)
        if loop_count == 0:
            continue

        inspected_layers += 1
        if loop_count != expected_wall_loops:
            bad_layers.append((
                layer_idx,
                "loop-count-mismatch",
                {
                    "loop_count": loop_count,
                    "outer_count": len(outer),
                    "inner_count": len(inner),
                },
            ))

    if inspected_layers == 0:
        bad_layers.append((-1, "no-layer-with-walls", {}))

    ok = len(bad_layers) == 0
    return ok, expected_wall_loops, bad_layers
