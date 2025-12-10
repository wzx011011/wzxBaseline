# tests/engine_params/speed/test_initial_layer_speed.py
from pathlib import Path
import pytest

from engine_params.src.gcode.process.speed.initial_layer_speed_check import (
    parse_initial_layer_speed,
    parse_initial_layer_infill_speed,
    parse_initial_layer_travel_speed,
    parse_slow_down_layers
)

# ================== initial_layer_speed ==================
def _format_failure_speed(details) -> str:
    lines = []
    lines.append("=== initial_layer_speed 校验失败（仅首层，已跳过 PRIME_TOWER/其他跳过类型） ===")
    lines.append(f"  目标首层: {details.get('checked_layer')}")
    lines.append(f"  首层 Region 总数: {details.get('regions_total')}, 参与校验: {details.get('regions_checked')}")
    lines.append(f"  期望值: {details.get('expected')}  容差: {details.get('tolerance')}")
    if "actual_values_set" in details:
        lines.append(f"  解析到的全局速度集合(去重): {details['actual_values_set']}")
    lines.append(f"  跳过类型: {details.get('regions_skipped_types')}")

    by_type = details.get("by_type", {})
    if by_type:
        lines.append("  —— 按类型聚合 ——")
        for t, agg in by_type.items():
            lines.append(f"    {t}: count={agg['count']} mismatch={agg['mismatch']} missing={agg['missing']} values={agg['values']}")

    miss = details.get("missing_feedrate_regions", [])
    if miss:
        lines.append("  —— 缺失 region.feedrate 的区域 ——")
        for m in miss[:100]:
            lines.append(f"    L{m['layer']} OID={m['object_id']} TYPE={m['type']} (regionF=None)")
        if len(miss) > 100:
            lines.append(f"    ... 以及 {len(miss)-100} 个更多")

    bad = details.get("mismatches", [])
    if bad:
        lines.append("  —— 与期望不匹配的区域 ——")
        for m in bad[:200]:
            lines.append(
                f"    L{m['layer']} OID={m['object_id']} TYPE={m['type']} "
                f"regionF={m['region_feedrate']} diff={m.get('diff', 'NA'):+.6f}"
            )
        if len(bad) > 200:
            lines.append(f"    ... 以及 {len(bad)-200} 个更多")

    note = details.get("note")
    if note:
        lines.append(f"  Note: {note}")

    return "\n".join(lines)


@pytest.mark.engine_params
def test_initial_layer_speed(slice_and_export: Path, expected_initial_layer_speed: float, tolerance: float):
    """
    首层速度检查：
    - 仅比对 LayerRegion.feedrate
    - 跳过 PRIME_TOWER、SKIRT、BOTTOM_SURFACE
    - 失败时打印出具体是哪些 Region 失配或缺失全局速度
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, expected, details = parse_initial_layer_speed(
        gcode_path,
        expected_initial_layer_speed,
        tolerance,
    )
    assert ok, _format_failure_speed(details)


# ================== initial_layer_infill_speed ==================
@pytest.mark.engine_params
def test_initial_layer_infill_speed(slice_and_export: Path, expected_initial_layer_infill_speed: float, tolerance: float):
    """
    首层填充速度检查：
    - 仅比对首层 BOTTOM_SURFACE 类型的 LayerRegion.feedrate
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, expected, details = parse_initial_layer_infill_speed(
        gcode_path,
        expected_initial_layer_infill_speed,
        tolerance,
    )
    assert ok, f"details={details}"

# ================== initial_layer_travel_speed ==================
def _format_failure_travel_speed(details) -> str:
    """
    格式化initial_layer_travel_speed校验失败时的错误信息：
    - 仅检查首层中返回的paths中点的kind为travel的点
    """
    lines = []
    lines.append("=== initial_layer_travel_speed 校验失败（仅首层，检查返回的paths中点的kind为travel的点） ===")
    lines.append(f"  目标首层: {details.get('checked_layer')}")
    lines.append(f"  首层所有点总数: {details.get('points_total')}, 检查travel点数量: {details.get('points_checked')}")
    lines.append(f"  实际找到travel点数量: {details.get('travel_points_count')}")
    lines.append(f"  期望值: {details.get('expected')}  容差: {details.get('tolerance')}")
    if "actual_values_set" in details and details['actual_values_set']:
        lines.append(f"  解析到的速度集合(去重): {details['actual_values_set']}")

    bad = details.get("mismatches", [])
    if bad:
        lines.append("  —— 与期望不匹配的travel点 ——")
        for m in bad[:200]:
            lines.append(
                f"    L{m['layer']} IDX={m['index']} X={m['x']} Y={m['y']} Z={m['z']} "
                f"F={m['f']} diff={m.get('diff', 'NA'):+.6f}"
            )
        if len(bad) > 200:
            lines.append(f"    ... 以及 {len(bad)-200} 个更多")
    elif details.get('points_checked', 0) == 0:
        lines.append("  未找到任何travel类型的点进行校验！")

    note = details.get("note")
    if note:
        lines.append(f"  Note: {note}")

    return "\n".join(lines)

@pytest.mark.engine_params
def test_initial_layer_travel_speed(slice_and_export: Path, expected_initial_layer_travel_speed: float, tolerance: float):
    """
    首层移动速度检查：
    - 比对首层中返回的paths中点的kind为travel的点的f值
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, expected, details = parse_initial_layer_travel_speed(
        gcode_path,
        expected_initial_layer_travel_speed,
        tolerance,
    )
    assert ok, _format_failure_travel_speed(details)

# ================== slow_down_layers ==================
@pytest.mark.engine_params
def test_slow_down_layers(slice_and_export: Path, expected_slow_down_layers: int, tolerance: float):
    """慢速打印层数校验：验证差值算法应用到各挤出类型后与期望一致。"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, expected, details = parse_slow_down_layers(
        gcode_path,
        expected_slow_down_layers,
        tolerance,
    )
    assert ok, f"details={details}"
