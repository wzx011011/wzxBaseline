from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

from engine_params.src.gcode.GCodeParser import GCodeParser
from engine_params.src.gcode.GCodeParserEx import GCodeParserEx
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
    contours = parser.get_type_contours_per_layer(
        types=[ExtrusionType.OUTER_WALL.value, ExtrusionType.INNER_WALL.value], workers=0)
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


# ================== alternate_extra_wall ==================
def parse_alternate_extra_wall(
        gcode_path: Path | str,
        expected_on: bool,
        *,
        target_oid: Optional[int] = 0
) -> Tuple[bool, str, List[Tuple[int, str, Dict[str, Any]]]]:
    """
    校验alternate_extra_wall功能是否正确。
    
    当expected_on=True时：
    - 从底部开始，内墙额外添加内墙数为：0、1、0、1......
    - 因此，layer_index为奇数的内墙数目要比上一层的内墙数目多1
    - layer_index为偶数的内墙数目比上一层的内墙数目少1
    
    当expected_on=False时：
    - 所有层的内墙数目应该保持一致
    
    返回:
      ok: 是否所有相邻层的内墙数目变化符合预期。
      message: 结果消息。
      bad_layers: [(layer_idx, reason, details)]
    """
    parser = GCodeParserEx(gcode_path)
    # 使用get_type_contours_per_layer获取每层的内墙轮廓
    layers = parser.get_type_contours_per_layer(types=[ExtrusionType.INNER_WALL], workers=0)

    if not layers:
        return False, "no-contours", [(-1, "no-contours", {})]

    bad_layers: List[Tuple[int, str, Dict[str, Any]]] = []
    last_inner_count = None

    # 遍历所有层
    for layer in layers:
        layer_idx = layer.index

        # 检查是否有目标object_id的regions
        if target_oid not in layer.regions:
            continue

        # 获取目标object_id的类型映射
        type_map = layer.regions[target_oid]

        # 检查是否有内墙类型
        if ExtrusionType.INNER_WALL not in type_map:
            continue

        # 通过LayerRegion的paths的len来获得内墙数目
        current_inner_count = len(type_map[ExtrusionType.INNER_WALL].paths)

        # 跳过内墙数目为0的层
        if current_inner_count == 0:
            continue

        # 对于第一层，只记录内墙数目
        if last_inner_count is None:
            last_inner_count = current_inner_count
            continue

        if expected_on:
            # 当expected_on=True时，检查交替模式
            # 奇数层应该比上一层多1，偶数层应该比上一层少1
            expected_diff = 1 if layer_idx % 2 == 1 else -1
            actual_diff = current_inner_count - last_inner_count

            if actual_diff != expected_diff:
                bad_layers.append((
                    layer_idx,
                    "inner-wall-count-mismatch",
                    {
                        "current_inner_count": current_inner_count,
                        "last_inner_count": last_inner_count,
                        "expected_diff": expected_diff,
                        "actual_diff": actual_diff
                    },
                ))
        else:
            # 当expected_on=False时，检查所有层内墙数目是否一致
            if current_inner_count != last_inner_count:
                bad_layers.append((
                    layer_idx,
                    "inner-wall-count-not-equal",
                    {
                        "current_inner_count": current_inner_count,
                        "expected_inner_count": last_inner_count
                    },
                ))

        # 更新上一层的内墙数目
        last_inner_count = current_inner_count

    ok = len(bad_layers) == 0
    if ok:
        if expected_on:
            message = "All layers have correct alternating inner wall pattern"
        else:
            message = "All layers have consistent inner wall count"
    else:
        if expected_on:
            message = "Some layers have incorrect inner wall pattern"
        else:
            message = "Some layers have inconsistent inner wall count"
    
    return ok, message, bad_layers
