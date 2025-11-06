# tests/engine_params/speed/test_jerk_xy.py
from pathlib import Path
import pytest

from engine_params.src.gcode.constants import ExtrusionType
from engine_params.src.gcode.speed.jerk_xy_check import (
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
def test_outer_wall_jerk(
        slice_and_export: Path,
        expected_outer_wall_jerk: float,
        tolerance: float,
):
    """非首层 OUTER_WALL 的 SQUARE_CORNER_VELOCITY 应与期望值一致。"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_outer_wall_jerk(
        gcode_path,
        expected_outer_wall_jerk,
        tolerance,
    )
    assert ok, _format_corner_failure(details)


@pytest.mark.engine_params
def test_inner_wall_jerk(
        slice_and_export: Path,
        expected_inner_wall_jerk: float,
        tolerance: float,
):
    """非首层 INNER_WALL 的 SQUARE_CORNER_VELOCITY 应与期望值一致。"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_inner_wall_jerk(
        gcode_path,
        expected_inner_wall_jerk,
        tolerance,
    )
    assert ok, _format_corner_failure(details)


@pytest.mark.engine_params
def test_top_surface_acceleration(
        slice_and_export: Path,
        expected_top_surface_acceleration: float,
        tolerance: float,
):
    """非首层 TOP_SURFACE 的 SQUARE_CORNER_VELOCITY 应与期望值一致。"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_top_surface_acceleration(
        gcode_path,
        expected_top_surface_acceleration,
        tolerance,
    )
    assert ok, _format_corner_failure(details)
@pytest.mark.engine_params
def test_initial_layer_jerk(
        slice_and_export: Path,
        expected_initial_layer_jerk: float,
        tolerance: float,
):
    """首层所有 LayerRegion 的 SQUARE_CORNER_VELOCITY 应与期望值一致。"""
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
def test_default_jerk(
        slice_and_export: Path,
        expected_default_jerk: float,
        tolerance: float,
):
    """非首层 GAP/SUPPORT 类型 region 的 SQUARE_CORNER_VELOCITY 应符合期望。"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_default_jerk(
        gcode_path,
        expected_default_jerk,
        tolerance,
    )
    assert ok, _format_corner_failure(details)


@pytest.mark.engine_params
def test_infill_jerk(
        slice_and_export: Path,
        expected_infill_jerk: float,
        tolerance: float,
):
    """首层 INFILL/IRONING/BRIDGE 类 LayerRegion 的 SQUARE_CORNER_VELOCITY 应符合期望。"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_infill_jerk(
        gcode_path,
        expected_infill_jerk,
        tolerance,
        extrusion_types=INFILL_JERK_TYPES,
    )
    assert ok, _format_corner_failure(details)
