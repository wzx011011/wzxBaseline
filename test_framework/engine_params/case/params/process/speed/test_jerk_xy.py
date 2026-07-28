# tests/engine_params/speed/test_jerk_xy.py
from pathlib import Path
import pytest

from engine_params.src.gcode.constants import ExtrusionType
from engine_params.src.gcode.process.speed.jerk_xy_check import (
    parse_outer_wall_jerk,
    parse_inner_wall_jerk,
    parse_top_surface_acceleration,
    parse_initial_layer_jerk,
    parse_infill_jerk,
    parse_default_jerk,
)


def _format_corner_failure(details) -> str:
    lines = []
    param = details.get("parameter")
    lines.append(f"=== {param} square-corner velocity 校验失败 ===")
    lines.append(
        f"  layers: {details.get('checked_layers')}  objects: {details.get('objects_total')}  "
        f"regions(total/checked): {details.get('regions_total')}/{details.get('regions_checked')}"
    )
    lines.append(
        f"  expected: {details.get('expected')}  tolerance: {details.get('tolerance')}  "
        f"target_types: {details.get('target_types')}  layer_indices: {details.get('layer_indices')}  "
        f"skip_layers: {details.get('skip_layers')}"
    )

    actual_values = details.get("actual_values_set") or []
    if actual_values:
        lines.append(f"  collected values: {actual_values}")

    missing_limits = details.get("missing_velocity_limits") or []
    if missing_limits:
        lines.append("  缺少 velocity_limits 的区域 (最多 10 条):")
        for item in missing_limits[:10]:
            lines.append(f"    layer={item['layer']} oid={item['object_id']} type={item['type']}")
        if len(missing_limits) > 10:
            lines.append(f"    ... {len(missing_limits) - 10} more")

    missing_corner = details.get("missing_corner_key") or []
    if missing_corner:
        lines.append("  缺少 SQUARE_CORNER_VELOCITY 的区域 (最多 10 条):")
        for item in missing_corner[:10]:
            lines.append(f"    layer={item['layer']} oid={item['object_id']} type={item['type']}")
        if len(missing_corner) > 10:
            lines.append(f"    ... {len(missing_corner) - 10} more")

    mismatches = details.get("mismatches") or []
    if mismatches:
        lines.append("  不匹配的区域 (最多 20 条):")
        for item in mismatches[:20]:
            diff = item.get("diff")
            diff_str = f"{diff:+.6f}" if isinstance(diff, (int, float)) else diff
            lines.append(
                f"    layer={item['layer']} oid={item['object_id']} type={item['type']} "
                f"actual={item.get('actual')} diff={diff_str}"
            )
        if len(mismatches) > 20:
            lines.append(f"    ... {len(mismatches) - 20} more")

    note = details.get("note")
    if note:
        lines.append(f"  note: {note}")

    return "\n".join(lines)


@pytest.mark.engine_params
# ================== outer_wall_jerk ==================
def test_outer_wall_jerk(
        slice_and_export: Path,
        expected_outer_wall_jerk: float,
        tolerance: float,
):
    """
    验证方法：
    1. 跳过首层，仅筛选 OUTER_WALL（外墙）Region。
    2. 从 velocity_limits 读取 SQUARE_CORNER_VELOCITY，作为外墙 Jerk 实际值。
    通过标准：至少存在一个外墙 Region，该字段不缺失，且全部在容差范围内。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_outer_wall_jerk(
        gcode_path,
        expected_outer_wall_jerk,
        tolerance,
    )
    assert ok, _format_corner_failure(details)


@pytest.mark.engine_params
# ================== inner_wall_jerk ==================
def test_inner_wall_jerk(
        slice_and_export: Path,
        expected_inner_wall_jerk: float,
        tolerance: float,
):
    """
    验证方法：
    1. 跳过首层，仅筛选 INNER_WALL（内墙）Region。
    2. 从 velocity_limits 读取 SQUARE_CORNER_VELOCITY，作为内墙 Jerk 实际值。
    通过标准：至少存在一个内墙 Region，该字段不缺失，且全部在容差范围内。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_inner_wall_jerk(
        gcode_path,
        expected_inner_wall_jerk,
        tolerance,
    )
    assert ok, _format_corner_failure(details)


@pytest.mark.engine_params
# ================== top_surface_acceleration ==================
def test_top_surface_acceleration(
        slice_and_export: Path,
        expected_top_surface_acceleration: float,
        tolerance: float,
):
    """
    验证方法：
    1. 跳过首层，仅筛选 TOP_SURFACE（顶面）Region。
    2. 从 velocity_limits 读取 SQUARE_CORNER_VELOCITY 并与期望值比较。
    通过标准：至少存在一个顶面 Region，该字段不缺失，且全部在容差范围内。
    注意：函数名沿用历史命名 acceleration，实际验证的是顶面 Jerk。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_top_surface_acceleration(
        gcode_path,
        expected_top_surface_acceleration,
        tolerance,
    )
    assert ok, _format_corner_failure(details)


@pytest.mark.engine_params
# ================== initial_layer_jerk ==================
def test_initial_layer_jerk(
        slice_and_export: Path,
        expected_initial_layer_jerk: float,
        tolerance: float,
):
    """
    验证方法：
    1. 仅解析首层（layer 0）的全部 LayerRegion。
    2. 从 velocity_limits 读取 SQUARE_CORNER_VELOCITY，作为首层 Jerk 实际值。
    通过标准：至少检查到一个 Region，该字段不缺失，且全部在容差范围内。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_initial_layer_jerk(
        gcode_path,
        expected_initial_layer_jerk,
        tolerance,
    )
    assert ok, _format_corner_failure(details)


INFILL_JERK_TYPES = [
    ExtrusionType.SPARSE_INFILL,
    ExtrusionType.INTERNAL_SOLID_INFILL,
    ExtrusionType.IRONING,
    ExtrusionType.INTERNAL_BRIDGE,
]

DEFAULT_JERK_TYPES = [
    ExtrusionType.GAP_INFILL,
    ExtrusionType.SUPPORT,
    ExtrusionType.SUPPORT_INTERFACE,
]


@pytest.mark.engine_params
# ================== default_jerk ==================
def test_default_jerk(
        slice_and_export: Path,
        expected_default_jerk: float,
        tolerance: float,
):
    """
    验证方法：
    1. 跳过首层，筛选 GAP_INFILL、SUPPORT、SUPPORT_INTERFACE Region。
    2. 从 velocity_limits 读取 SQUARE_CORNER_VELOCITY，作为默认 Jerk 实际值。
    通过标准：至少检查到一个目标 Region，该字段不缺失，且全部在容差范围内。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_default_jerk(
        gcode_path,
        expected_default_jerk,
        tolerance,
    )
    assert ok, _format_corner_failure(details)


@pytest.mark.engine_params
# ================== infill_jerk ==================
def test_infill_jerk(
        slice_and_export: Path,
        expected_infill_jerk: float,
        tolerance: float,
):
    """
    验证方法：
    1. 跳过首层，筛选稀疏填充、内部实心填充、熨烫和内部桥接 Region。
    2. 从 velocity_limits 读取 SQUARE_CORNER_VELOCITY，作为填充 Jerk 实际值。
    通过标准：至少检查到一个目标 Region，该字段不缺失，且全部在容差范围内。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_infill_jerk(
        gcode_path,
        expected_infill_jerk,
        tolerance,
        extrusion_types=INFILL_JERK_TYPES,
    )
    assert ok, _format_corner_failure(details)
