"""
特殊模式 (Special mode) 参数测试套件

包含以下参数的测试：
- slicing_mode (Level 1 配置对比)
- print_sequence (Level 1 配置对比)
- print_order (Level 1 配置对比)
- spiral_mode (Level 2 特征检测 - Z轴连续性)
- spiral_mode_smooth (Level 1 配置对比)
- spiral_mode_max_xy_smoothing (Level 1 配置对比)
- ignore_inner_color (Level 1 配置对比)
- timelapse_type (Level 1 配置对比)
- fuzzy_skin (Level 2/3 特征检测 - 路径偏差分析)
- fuzzy_skin_point_distance (Level 1 配置对比)
- fuzzy_skin_thickness (Level 1 配置对比)
- fuzzy_skin_first_layer (Level 1 配置对比)
"""
from __future__ import annotations

from pathlib import Path

import pytest

from engine_params.src.gcode.process.others.special_mode_check import (
    parse_slicing_mode,
    parse_print_sequence,
    parse_print_order,
    parse_spiral_mode,
    parse_spiral_mode_smooth,
    parse_spiral_mode_max_xy_smoothing,
    parse_ignore_inner_color,
    parse_timelapse_type,
    parse_fuzzy_skin,
    parse_fuzzy_skin_point_distance,
    parse_fuzzy_skin_thickness,
    parse_fuzzy_skin_first_layer,
)


# ================== slicing_mode ==================

@pytest.mark.engine_params
def test_slicing_mode(
        slice_and_export: Path,
        expected_value: str,
):
    """测试 slicing_mode 参数 (Level 1 - 配置对比)"""
    gcode_path = slice_and_export
    ok, actual_value, details = parse_slicing_mode(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== slicing_mode Level 1 检测详情 ===")
    print(f"  期望值: {expected_value}")
    print(f"  检测值: {actual_value}")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 45)

    assert ok, (
        f"slicing_mode expected {expected_value}, actual {actual_value}, details: {details}"
    )


# ================== print_sequence ==================

@pytest.mark.engine_params
def test_print_sequence(
        slice_and_export: Path,
        expected_value: str,
):
    """测试 print_sequence 参数 (Level 1 - 配置对比)"""
    gcode_path = slice_and_export
    ok, actual_value, details = parse_print_sequence(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== print_sequence Level 1 检测详情 ===")
    print(f"  期望值: {expected_value}")
    print(f"  检测值: {actual_value}")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 45)

    assert ok, (
        f"print_sequence expected {expected_value}, actual {actual_value}, details: {details}"
    )


# ================== print_order ==================

@pytest.mark.engine_params
def test_print_order(
        slice_and_export: Path,
        expected_value: str,
):
    """测试 print_order 参数 (Level 1 - 配置对比)"""
    gcode_path = slice_and_export
    ok, actual_value, details = parse_print_order(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== print_order Level 1 检测详情 ===")
    print(f"  期望值: {expected_value}")
    print(f"  检测值: {actual_value}")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 45)

    assert ok, (
        f"print_order expected {expected_value}, actual {actual_value}, details: {details}"
    )


# ================== spiral_mode ==================

@pytest.mark.engine_params
def test_spiral_mode(
        slice_and_export: Path,
        expected_value: bool,
):
    """测试 spiral_mode 参数 (Level 2 - Z轴连续性检测)"""
    gcode_path = slice_and_export
    ok, actual_value, details = parse_spiral_mode(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== spiral_mode Level 2 检测详情 ===")
    print(f"  期望值: {expected_value}")
    print(f"  检测值: {actual_value}")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  Z轴递增次数: {details.get('z_increments', 0)}")
    print(f"  Z轴跳跃次数: {details.get('z_jumps', 0)}")
    print(f"  Z轴连续性: {details.get('z_continuity', 0):.2%}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 45)

    assert ok, (
        f"spiral_mode expected {expected_value}, actual {actual_value}, details: {details}"
    )


# ================== spiral_mode_smooth ==================

@pytest.mark.engine_params
def test_spiral_mode_smooth(
        slice_and_export: Path,
        expected_value: bool,
):
    """测试 spiral_mode_smooth 参数 (Level 1 - 配置对比)"""
    gcode_path = slice_and_export
    ok, actual_value, details = parse_spiral_mode_smooth(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== spiral_mode_smooth Level 1 检测详情 ===")
    print(f"  期望值: {expected_value}")
    print(f"  检测值: {actual_value}")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 45)

    assert ok, (
        f"spiral_mode_smooth expected {expected_value}, actual {actual_value}, details: {details}"
    )


# ================== spiral_mode_max_xy_smoothing ==================

@pytest.mark.engine_params
def test_spiral_mode_max_xy_smoothing(
        slice_and_export: Path,
        expected_value: float,
):
    """测试 spiral_mode_max_xy_smoothing 参数 (Level 1 - 配置对比)"""
    gcode_path = slice_and_export
    ok, actual_value, details = parse_spiral_mode_max_xy_smoothing(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== spiral_mode_max_xy_smoothing Level 1 检测详情 ===")
    print(f"  期望值: {expected_value}%")
    print(f"  检测值: {actual_value}%")
    print(f"  容差: ±1.0%")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 45)

    assert ok, (
        f"spiral_mode_max_xy_smoothing expected {expected_value}%, actual {actual_value}%, details: {details}"
    )


# ================== ignore_inner_color ==================

@pytest.mark.engine_params
def test_ignore_inner_color(
        slice_and_export: Path,
        expected_value: bool,
):
    """测试 ignore_inner_color 参数 (Level 1 - 配置对比)"""
    gcode_path = slice_and_export
    ok, actual_value, details = parse_ignore_inner_color(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== ignore_inner_color Level 1 检测详情 ===")
    print(f"  期望值: {expected_value}")
    print(f"  检测值: {actual_value}")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 45)

    assert ok, (
        f"ignore_inner_color expected {expected_value}, actual {actual_value}, details: {details}"
    )


# ================== timelapse_type ==================

@pytest.mark.engine_params
def test_timelapse_type(
        slice_and_export: Path,
        expected_value: int,
):
    """测试 timelapse_type 参数 (Level 1 - 配置对比)"""
    gcode_path = slice_and_export
    ok, actual_value, details = parse_timelapse_type(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== timelapse_type Level 1 检测详情 ===")
    print(f"  期望值: {expected_value}")
    print(f"  检测值: {actual_value}")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 45)

    assert ok, (
        f"timelapse_type expected {expected_value}, actual {actual_value}, details: {details}"
    )


# ================== fuzzy_skin ==================

@pytest.mark.engine_params
def test_fuzzy_skin(
        slice_and_export: Path,
        expected_value: str,
):
    """测试 fuzzy_skin 参数 (Level 2/3 - 路径偏差分析)"""
    gcode_path = slice_and_export
    ok, actual_value, details = parse_fuzzy_skin(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== fuzzy_skin Level 2/3 检测详情 ===")
    print(f"  期望值: {expected_value}")
    print(f"  检测值: {actual_value}")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  外墙路径标准差: {details.get('outer_wall_std', 0):.4f}mm")
    print(f"  判定阈值: {details.get('threshold', 0):.4f}mm")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 45)

    assert ok, (
        f"fuzzy_skin expected {expected_value}, actual {actual_value}, details: {details}"
    )


# ================== fuzzy_skin_point_distance ==================

@pytest.mark.engine_params
def test_fuzzy_skin_point_distance(
        slice_and_export: Path,
        expected_value: float,
):
    """测试 fuzzy_skin_point_distance 参数 (Level 1 - 配置对比)"""
    gcode_path = slice_and_export
    ok, actual_value, details = parse_fuzzy_skin_point_distance(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== fuzzy_skin_point_distance Level 1 检测详情 ===")
    print(f"  期望值: {expected_value}mm")
    print(f"  检测值: {actual_value}mm")
    print(f"  容差: ±0.1mm")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 45)

    assert ok, (
        f"fuzzy_skin_point_distance expected {expected_value}mm, actual {actual_value}mm, details: {details}"
    )


# ================== fuzzy_skin_thickness ==================

@pytest.mark.engine_params
def test_fuzzy_skin_thickness(
        slice_and_export: Path,
        expected_value: float,
):
    """测试 fuzzy_skin_thickness 参数 (Level 1 - 配置对比)"""
    gcode_path = slice_and_export
    ok, actual_value, details = parse_fuzzy_skin_thickness(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== fuzzy_skin_thickness Level 1 检测详情 ===")
    print(f"  期望值: {expected_value}mm")
    print(f"  检测值: {actual_value}mm")
    print(f"  容差: ±0.01mm")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 45)

    assert ok, (
        f"fuzzy_skin_thickness expected {expected_value}mm, actual {actual_value}mm, details: {details}"
    )


# ================== fuzzy_skin_first_layer ==================

@pytest.mark.engine_params
def test_fuzzy_skin_first_layer(
        slice_and_export: Path,
        expected_value: bool,
):
    """测试 fuzzy_skin_first_layer 参数 (Level 1 - 配置对比)"""
    gcode_path = slice_and_export
    ok, actual_value, details = parse_fuzzy_skin_first_layer(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== fuzzy_skin_first_layer Level 1 检测详情 ===")
    print(f"  期望值: {expected_value}")
    print(f"  检测值: {actual_value}")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 45)

    assert ok, (
        f"fuzzy_skin_first_layer expected {expected_value}, actual {actual_value}, details: {details}"
    )
