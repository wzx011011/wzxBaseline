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
    验证方法：
    1. 仅解析首层（layer 0）的内墙、外墙、间隙填充、Brim 和支撑 Region。
    2. 读取各 Region.feedrate（mm/s），与 initial_layer_speed 期望值比较。
    通过标准：至少检查到一个目标 Region，feedrate 不缺失，且全部在容差范围内。
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
    验证方法：
    1. 仅解析首层（layer 0）的 BOTTOM_SURFACE（底面填充）Region。
    2. 读取 Region.feedrate（mm/s），与 initial_layer_infill_speed 期望值比较。
    通过标准：至少检查到一个底面 Region，feedrate 不缺失，且全部在容差范围内。
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
    验证方法：
    1. 通过 get_motion_paths_for_layer(0) 获取首层运动点，筛选 kind=travel 且非料塔的点。
    2. 读取每个移动点的实际 F 速度（已换算为 mm/s），与期望值比较。
    通过标准：至少检查到一个 travel 点，且所有点的速度都在容差范围内。
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
    """
    验证方法：
    1. 读取前 N 层墙和填充 Region；N 为 expected_slow_down_layers。
    2. 按“首层速度 → 正常层速度”线性插值，计算每一层、每种类型的期望速度。
    3. 将计算结果与对应 Region.feedrate 逐一比较。
    通过标准：至少检查到一个 Region，feedrate 不缺失，且全部符合插值结果。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, expected, details = parse_slow_down_layers(
        gcode_path,
        expected_slow_down_layers,
        tolerance,
    )
    assert ok, f"details={details}"
