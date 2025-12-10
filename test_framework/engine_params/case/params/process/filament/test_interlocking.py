from __future__ import annotations

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


# ================== interlocking_beam ==================

@pytest.mark.engine_params
def test_interlocking_beam(
        slice_and_export: Path,
        expected_value: bool,
):
    gcode_path = slice_and_export
    ok, actual_value, details = parse_interlocking_beam(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== interlocking_beam Level 2 检测详情 ===")
    print(f"  期望值: {expected_value}")
    print(f"  检测值: {actual_value}")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  换料次数: {details.get('tool_changes_count', 0)}")
    print(f"  墙体交替次数: {details.get('wall_alternations', 0)}")
    print(f"  墙体交替比率: {details.get('alternation_ratio', 0):.2f} (阈值: 2.5)")
    print(f"  Gap infill 次数: {details.get('gap_infill_count', 0)}")
    print(f"  Gap infill 比率: {details.get('gap_infill_ratio', 0):.2f} (阈值: 0.5)")
    print(f"  特征检测结果: {details.get('feature_detected', False)}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 45)

    assert ok, (
        f"interlocking_beam expected {expected_value}, actual {actual_value}, details: {details}"
    )


# ================== mmu_segmented_region_max_width ==================

@pytest.mark.engine_params
def test_mmu_segmented_region_max_width(
        slice_and_export: Path,
        expected_value: float,
):
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


# ================== interlocking_beam_width ==================

@pytest.mark.engine_params
def test_interlocking_beam_width(
        slice_and_export: Path,
        expected_value: float,
):
    gcode_path = slice_and_export
    ok, actual_value, details = parse_interlocking_beam_width(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== interlocking_beam_width Level 1 检测详情 ===")
    print(f"  期望值: {expected_value}mm")
    print(f"  检测值: {actual_value}mm")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 50)

    assert ok, (
        f"interlocking_beam_width expected {expected_value}mm, actual {actual_value}mm, details: {details}"
    )


# ================== interlocking_orientation ==================

@pytest.mark.engine_params
def test_interlocking_orientation(
        slice_and_export: Path,
        expected_value: float,
):
    gcode_path = slice_and_export
    ok, actual_value, details = parse_interlocking_orientation(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== interlocking_orientation Level 1 检测详情 ===")
    print(f"  期望值: {expected_value}°")
    print(f"  检测值: {actual_value}°")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 50)

    assert ok, (
        f"interlocking_orientation expected {expected_value}°, actual {actual_value}°, details: {details}"
    )


# ================== interlocking_beam_layer_count ==================

@pytest.mark.engine_params
def test_interlocking_beam_layer_count(
        slice_and_export: Path,
        expected_value: int,
):
    gcode_path = slice_and_export
    ok, actual_value, details = parse_interlocking_beam_layer_count(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== interlocking_beam_layer_count Level 1 检测详情 ===")
    print(f"  期望值: {expected_value}")
    print(f"  检测值: {actual_value}")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 55)

    assert ok, (
        f"interlocking_beam_layer_count expected {expected_value}, actual {actual_value}, details: {details}"
    )


# ================== interlocking_depth ==================

@pytest.mark.engine_params
def test_interlocking_depth(
        slice_and_export: Path,
        expected_value: float,
):
    gcode_path = slice_and_export
    ok, actual_value, details = parse_interlocking_depth(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== interlocking_depth Level 1 检测详情 ===")
    print(f"  期望值: {expected_value}mm")
    print(f"  检测值: {actual_value}mm")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 50)

    assert ok, (
        f"interlocking_depth expected {expected_value}mm, actual {actual_value}mm, details: {details}"
    )


# ================== interlocking_boundary_avoidance ==================

@pytest.mark.engine_params
def test_interlocking_boundary_avoidance(
        slice_and_export: Path,
        expected_value: float,
):
    gcode_path = slice_and_export
    ok, actual_value, details = parse_interlocking_boundary_avoidance(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== interlocking_boundary_avoidance Level 1 检测详情 ===")
    print(f"  期望值: {expected_value}mm")
    print(f"  检测值: {actual_value}mm")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 60)

    assert ok, (
        f"interlocking_boundary_avoidance expected {expected_value}mm, actual {actual_value}mm, details: {details}"
    )
