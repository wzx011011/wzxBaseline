# tests/engine_params/speed/test_acceleration.py
from pathlib import Path
import pytest

from engine_params.src.gcode.constants import ExtrusionType
from engine_params.src.gcode.speed.acceleration_check import (
    parse_accel_to_decel_enable,
    parse_accel_to_decel_factor,
    parse_initial_layer_acceleration,
    parse_outer_wall_acceleration,
    parse_inner_wall_acceleration,
    parse_bridge_acceleration,
    parse_sparse_infill_acceleration,
    parse_internal_solid_infill_acceleration,
    parse_top_surface_acceleration,
    parse_default_acceleration,
    parse_travel_acceleration,
)


def _format_failure(details) -> str:
    lines = []
    param = details.get("parameter", "acceleration")
    lines.append(f"=== {param} acceleration check failed (velocity_limits.ACCEL) ===")
    layers_info = details.get("checked_layers") or []
    lines.append(
        f"  layers: {layers_info}  objects: {details.get('objects_total')}  "
        f"regions(total/checked): {details.get('regions_total')}/{details.get('regions_checked')}"
    )
    lines.append(
        f"  expected: {details.get('expected')}  tolerance: {details.get('tolerance')}  "
        f"target_types: {details.get('target_types')}  excluded_types: {details.get('excluded_types')}"
    )
    actual_set = details.get("actual_values_set") or []
    if actual_set:
        lines.append(f"  collected ACCEL values: {actual_set}")

    missing_limits = details.get("missing_velocity_limits") or []
    if missing_limits:
        lines.append("  regions missing velocity_limits (first 10):")
        for item in missing_limits[:10]:
            lines.append(f"    layer={item['layer']} oid={item['object_id']} type={item['type']}")
        if len(missing_limits) > 10:
            lines.append(f"    ... {len(missing_limits) - 10} more")

    missing_accel = details.get("missing_accel_key") or []
    if missing_accel:
        lines.append("  regions missing ACCEL (first 10):")
        for item in missing_accel[:10]:
            lines.append(
                f"    layer={item['layer']} oid={item['object_id']} type={item['type']} limits={item.get('velocity_limits')}"
            )
        if len(missing_accel) > 10:
            lines.append(f"    ... {len(missing_accel) - 10} more")

    missing_factor = details.get("missing_factor_key") or []
    if missing_factor:
        lines.append("  regions missing ACCEL_TO_DECEL (first 10):")
        for item in missing_factor[:10]:
            lines.append(
                f"    layer={item['layer']} oid={item['object_id']} type={item['type']} limits={item.get('velocity_limits')}"
            )
        if len(missing_factor) > 10:
            lines.append(f"    ... {len(missing_factor) - 10} more")

    mismatches = details.get("mismatches") or []
    if mismatches:
        lines.append("  mismatched ACCEL values (first 20):")
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
# ================== accel_to_decel_enable ==================
def test_accel_to_decel_enable(
        slice_and_export: Path,
        expected_accel_to_decel_enable: bool,
):
    """校验 ACCEL_TO_DECEL 是否按预期启用/禁用。"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_accel_to_decel_enable(
        gcode_path,
        expected_accel_to_decel_enable,
    )
    assert ok, _format_failure(details)


@pytest.mark.engine_params
# ================== default_acceleration ==================
def test_default_acceleration(
        slice_and_export: Path,
        expected_default_acceleration: float,
        tolerance: float,
):
    """除去特定挤出类型外，其余 LayerRegion 应遵循 default_acceleration。排除第一层"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    DEFAULT_ACCEL_EXCLUDED_TYPES = [
        ExtrusionType.OUTER_WALL,
        ExtrusionType.INNER_WALL,
        ExtrusionType.SPARSE_INFILL,
        ExtrusionType.TOP_SURFACE,
        ExtrusionType.BRIDGE,
        ExtrusionType.INTERNAL_SOLID_INFILL,
        ExtrusionType.OVERHANG_WALL,
        ExtrusionType.PRIME_TOWER
    ]

    ok, _, details = parse_default_acceleration(
        gcode_path,
        expected_default_acceleration,
        tolerance,
        exclude_types=DEFAULT_ACCEL_EXCLUDED_TYPES,
    )
    assert ok, _format_failure(details)


@pytest.mark.engine_params
# ================== accel_to_decel_factor ==================
def test_accel_to_decel_factor(
        slice_and_export: Path,
        expected_accel_to_decel_factor: float,
        tolerance: float,
):
    """校验 ACCEL_TO_DECEL / ACCEL 的比值。"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_accel_to_decel_factor(
        gcode_path,
        expected_accel_to_decel_factor,
        tolerance,
    )
    assert ok, _format_failure(details)


@pytest.mark.engine_params
# ================== initial_layer_acceleration ==================
def test_initial_layer_acceleration(
        slice_and_export: Path,
        expected_initial_layer_acceleration: float,
        tolerance: float,
):
    """Validate that all layer-0 regions respect initial_layer_acceleration (ACCEL in velocity_limits)."""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_initial_layer_acceleration(
        gcode_path,
        expected_initial_layer_acceleration,
        tolerance,
    )
    assert ok, _format_failure(details)


@pytest.mark.engine_params
# ================== outer_wall_acceleration ==================
def test_outer_wall_acceleration(
        slice_and_export: Path,
        expected_outer_wall_acceleration: float,
        tolerance: float,
):
    """Non-first-layer OUTER_WALL regions should use outer_wall_acceleration for ACCEL limits."""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_outer_wall_acceleration(
        gcode_path,
        expected_outer_wall_acceleration,
        tolerance,
    )
    assert ok, _format_failure(details)


@pytest.mark.engine_params
# ================== inner_wall_acceleration ==================
def test_inner_wall_acceleration(
        slice_and_export: Path,
        expected_inner_wall_acceleration: float,
        tolerance: float,
):
    """Non-first-layer INNER_WALL regions should match inner_wall_acceleration."""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_inner_wall_acceleration(
        gcode_path,
        expected_inner_wall_acceleration,
        tolerance,
    )
    assert ok, _format_failure(details)


@pytest.mark.engine_params
# ================== bridge_acceleration ==================
def test_bridge_acceleration(
        slice_and_export: Path,
        expected_bridge_acceleration: float,
        tolerance: float,
):
    """Bridge/Internal Bridge regions (except layer 0) should follow bridge_acceleration."""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_bridge_acceleration(
        gcode_path,
        expected_bridge_acceleration,
        tolerance,
    )
    assert ok, _format_failure(details)


@pytest.mark.engine_params
# ================== sparse_infill_acceleration ==================
def test_sparse_infill_acceleration(
        slice_and_export: Path,
        expected_sparse_infill_acceleration: float,
        tolerance: float,
):
    """Sparse infill regions (excluding layer 0) should respect sparse_infill_acceleration."""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_sparse_infill_acceleration(
        gcode_path,
        expected_sparse_infill_acceleration,
        tolerance,
    )
    assert ok, _format_failure(details)


@pytest.mark.engine_params
# ================== internal_solid_infill_acceleration ==================
def test_internal_solid_infill_acceleration(
        slice_and_export: Path,
        expected_internal_solid_infill_acceleration: float,
        tolerance: float,
):
    """Internal solid infill regions (excluding layer 0) should match the configured acceleration."""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_internal_solid_infill_acceleration(
        gcode_path,
        expected_internal_solid_infill_acceleration,
        tolerance,
    )
    assert ok, _format_failure(details)


@pytest.mark.engine_params
# ================== top_surface_acceleration ==================
def test_top_surface_acceleration(
        slice_and_export: Path,
        expected_top_surface_acceleration: float,
        tolerance: float,
):
    """Top surface regions on layers > 0 should follow top_surface_acceleration."""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_top_surface_acceleration(
        gcode_path,
        expected_top_surface_acceleration,
        tolerance,
    )
    assert ok, _format_failure(details)


@pytest.mark.engine_params
# ================== travel_acceleration ==================
def test_travel_acceleration(
        slice_and_export: Path,
        expected_travel_acceleration: float,
        tolerance: float,
):
    """Travel 点进给速度校验（跳过首层）。"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_travel_acceleration(
        gcode_path,
        expected_travel_acceleration,
        tolerance,
    )
    assert ok, _format_failure(details)
