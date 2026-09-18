from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine_params.src.gcode.process.filament.interlocking_check import (
    parse_interlocking_beam,
    parse_interlocking_beam_width,
    parse_interlocking_orientation,
    parse_interlocking_beam_layer_count,
    parse_interlocking_depth,
    parse_interlocking_boundary_avoidance,
    parse_mmu_segmented_region_max_width,
)


def _assert_geometry(parser, gcode_path, expected_value, baseline_id):
    ok, actual, details = parser(gcode_path, expected_value, baseline_id=baseline_id)
    print(json.dumps(details, ensure_ascii=False, indent=2))
    assert ok, f"{baseline_id}: expected {expected_value}, config {actual}: {details}"


@pytest.mark.engine_params
def test_interlocking_beam(slice_and_export: Path, expected_value: bool, geometry_baseline: str):
    """Compare actual per-material outer contours with the reviewed 7.2.2 reference."""
    _assert_geometry(parse_interlocking_beam, slice_and_export, expected_value, geometry_baseline)


@pytest.mark.engine_params
def test_interlocking_beam_width(slice_and_export: Path, expected_value: float, geometry_baseline: str):
    """Compare actual per-material outer contours with the reviewed 7.2.2 reference."""
    _assert_geometry(parse_interlocking_beam_width, slice_and_export, expected_value, geometry_baseline)


@pytest.mark.engine_params
def test_interlocking_orientation(slice_and_export: Path, expected_value: float, geometry_baseline: str):
    """Compare actual per-material outer contours with the reviewed 7.2.2 reference."""
    _assert_geometry(parse_interlocking_orientation, slice_and_export, expected_value, geometry_baseline)


@pytest.mark.engine_params
def test_interlocking_beam_layer_count(slice_and_export: Path, expected_value: int, geometry_baseline: str):
    """Compare actual per-material outer contours with the reviewed 7.2.2 reference."""
    _assert_geometry(parse_interlocking_beam_layer_count, slice_and_export, expected_value, geometry_baseline)


@pytest.mark.engine_params
def test_interlocking_depth(slice_and_export: Path, expected_value: float, geometry_baseline: str):
    """Compare actual per-material outer contours with the reviewed 7.2.2 reference."""
    _assert_geometry(parse_interlocking_depth, slice_and_export, expected_value, geometry_baseline)


@pytest.mark.engine_params
def test_interlocking_boundary_avoidance(slice_and_export: Path, expected_value: float, geometry_baseline: str):
    """Compare actual per-material outer contours with the reviewed 7.2.2 reference."""
    _assert_geometry(parse_interlocking_boundary_avoidance, slice_and_export, expected_value, geometry_baseline)


# ================== mmu_segmented_region_max_width ==================

@pytest.mark.engine_params
def test_mmu_segmented_region_max_width(
        slice_and_export: Path,
        expected_value: float,
):
    # 保留分段区域原有配置/多材料路径检查；不作为联锁榫卯的几何验收。
    gcode_path = slice_and_export
    ok, actual_value, details = parse_mmu_segmented_region_max_width(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== mmu_segmented_region_max_width 检测详情 ===")
    print(f"  期望值: {expected_value}mm")
    print(f"  检测值: {actual_value}mm")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  换料次数: {details.get('tool_changes_count', 0)}")
    print(f"  换料密度: {details.get('tool_change_density', 0):.6f}")
    print(f"  Gap infill 次数: {details.get('gap_infill_count', 0)}")
    print(f"  Gap infill 比率: {details.get('gap_infill_ratio', 0):.2f}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 50)

    assert ok, (
        f"mmu_segmented_region_max_width expected {expected_value}mm, actual {actual_value}mm, details: {details}"
    )
