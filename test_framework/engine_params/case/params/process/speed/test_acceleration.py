# tests/engine_params/speed/test_acceleration.py
from pathlib import Path
import pytest

from engine_params.src.gcode.constants import ExtrusionType
from engine_params.src.gcode.process.speed.acceleration_check import (
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
    """
    验证方法：
    1. 解析全部层、全部挤出类型的 LayerRegion.velocity_limits。
    2. 根据 ACCEL_TO_DECEL 键是否存在，判断加减速功能在实际 G-code 中是否启用。
    通过标准：所有 Region 的启用状态都与期望一致，且至少解析到一个 Region。
    """
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
    """
    验证方法：
    1. 跳过首层以及已有专用加速度的墙、填充、桥接、顶面、悬垂和料塔类型。
    2. 读取剩余 Region 的 velocity_limits.ACCEL，与 default_acceleration 逐一比较。
    通过标准：至少检查到一个 Region，ACCEL 不缺失，且全部在容差范围内。
    """
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
    """
    验证方法：
    1. 遍历全部层和全部 Region，同时读取 ACCEL 与 ACCEL_TO_DECEL。
    2. 计算每个 Region 的 ACCEL_TO_DECEL / ACCEL，并与期望因子比较。
    通过标准：两个字段均存在、ACCEL 非 0，且所有比值都在容差范围内。
    """
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
    """
    验证方法：
    1. 仅解析首层（layer 0）的全部 LayerRegion。
    2. 读取每个 Region 的 velocity_limits.ACCEL，与首层加速度期望值比较。
    通过标准：至少检查到一个 Region，ACCEL 不缺失，且全部在容差范围内。
    """
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
    """
    验证方法：
    1. 跳过首层，仅筛选 OUTER_WALL（外墙）Region。
    2. 读取 velocity_limits.ACCEL，与外墙加速度期望值逐一比较。
    通过标准：至少存在一个外墙 Region，ACCEL 不缺失，且全部在容差范围内。
    """
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
    """
    验证方法：
    1. 跳过首层，仅筛选 INNER_WALL（内墙）Region。
    2. 读取 velocity_limits.ACCEL，与内墙加速度期望值逐一比较。
    通过标准：至少存在一个内墙 Region，ACCEL 不缺失，且全部在容差范围内。
    """
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
    """
    验证方法：
    1. 跳过首层，筛选 BRIDGE 和 INTERNAL_BRIDGE Region。
    2. 读取 velocity_limits.ACCEL，与桥接加速度期望值逐一比较。
    通过标准：至少存在一个桥接 Region，ACCEL 不缺失，且全部在容差范围内。
    """
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
    """
    验证方法：
    1. 跳过首层，仅筛选 SPARSE_INFILL（稀疏填充）Region。
    2. 读取 velocity_limits.ACCEL，与稀疏填充加速度期望值逐一比较。
    通过标准：至少存在一个目标 Region，ACCEL 不缺失，且全部在容差范围内。
    """
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
    """
    验证方法：
    1. 跳过首层，仅筛选 INTERNAL_SOLID_INFILL（内部实心填充）Region。
    2. 读取 velocity_limits.ACCEL，与内部实心填充加速度期望值逐一比较。
    通过标准：至少存在一个目标 Region，ACCEL 不缺失，且全部在容差范围内。
    """
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
    """
    验证方法：
    1. 跳过首层，仅筛选 TOP_SURFACE（顶面）Region。
    2. 读取 velocity_limits.ACCEL，与顶面加速度期望值逐一比较。
    通过标准：至少存在一个顶面 Region，ACCEL 不缺失，且全部在容差范围内。
    """
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
    """
    验证方法：
    1. 跳过首层，通过 get_motion_paths 获取 kind=travel 的移动点。
    2. 读取每个移动点继承的 velocity_limits.ACCEL；这里校验的是加速度，不是 F 速度。
    通过标准：至少存在一个 travel 点，ACCEL 不缺失，且全部在容差范围内。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_travel_acceleration(
        gcode_path,
        expected_travel_acceleration,
        tolerance,
    )
    assert ok, _format_failure(details)
