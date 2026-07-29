"""
裙边 (Skirt) 参数测试套件

包含以下参数的测试：
- skirt_type (Level 2 特征检测 - 覆盖率分析)
- skirt_loops (Level 1 配置对比)
- skirt_distance (Level 1 配置对比)
- skirt_height (Level 1 配置对比)
- skirt_speed (Level 1 配置对比)
- draft_shield (Level 2 特征检测 - 可复用 skirt_type 逻辑)
"""
from __future__ import annotations

from pathlib import Path

import pytest

from engine_params.src.gcode.process.others.skirt_type_check import (
    parse_skirt_type,
    parse_skirt_loops,
    parse_skirt_distance,
    parse_skirt_height,
    parse_skirt_speed,
    parse_min_skirt_length,
    parse_draft_shield,
)


# ================== skirt_type ==================

@pytest.mark.engine_params
def test_skirt_type(
        slice_and_export: Path,
        expected_value: str,
):
    """测试 skirt_type 参数 (Level 2 - 覆盖率分析)"""
    # 验证方法：使用首层附着、外壳或多对象专用 3MF切片，解析Skirt 路径的层数、圈数、边界距离、挤出长度和速度；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path = slice_and_export
    ok, actual_value, details = parse_skirt_type(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== skirt_type Level 2 检测详情 ===")
    print(f"  期望值: {expected_value}")
    print(f"  检测值: {actual_value}")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  Skirt 层数: {details.get('skirt_layers', 0)}")
    print(f"  总层数: {details.get('total_layers', 0)}")
    print(f"  覆盖率: {details.get('skirt_coverage', 0):.2%} (阈值: 50%)")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 45)

    assert ok, (
        f"skirt_type expected {expected_value}, actual {actual_value}, details: {details}"
    )


# ================== skirt_loops ==================

@pytest.mark.engine_params
def test_skirt_loops(
        slice_and_export: Path,
        expected_value: int,
):
    """测试 skirt_loops 参数 (Level 1 - 配置对比)"""
    # 验证方法：使用首层附着、外壳或多对象专用 3MF切片，解析Skirt 路径的层数、圈数、边界距离、挤出长度和速度；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path = slice_and_export
    ok, actual_value, details = parse_skirt_loops(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== skirt_loops Level 1 检测详情 ===")
    print(f"  期望值: {expected_value}")
    print(f"  检测值: {actual_value}")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 45)

    assert ok, (
        f"skirt_loops expected {expected_value}, actual {actual_value}, details: {details}"
    )


# ================== skirt_distance ==================

@pytest.mark.engine_params
def test_skirt_distance(
        slice_and_export: Path,
        expected_value: float,
):
    """测试 skirt_distance 参数 (Level 1 - 配置对比)"""
    # 验证方法：使用首层附着、外壳或多对象专用 3MF切片，解析Skirt 路径的层数、圈数、边界距离、挤出长度和速度；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path = slice_and_export
    ok, actual_value, details = parse_skirt_distance(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== skirt_distance Level 1 检测详情 ===")
    print(f"  期望值: {expected_value}mm")
    print(f"  检测值: {actual_value}mm")
    print(f"  容差: ±0.1mm")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 45)

    assert ok, (
        f"skirt_distance expected {expected_value}mm, actual {actual_value}mm, details: {details}"
    )


# ================== skirt_height ==================

@pytest.mark.engine_params
def test_skirt_height(
        slice_and_export: Path,
        expected_value: int,
):
    """测试 skirt_height 参数 (Level 1 - 配置对比)"""
    # 验证方法：使用首层附着、外壳或多对象专用 3MF切片，解析Skirt 路径的层数、圈数、边界距离、挤出长度和速度；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path = slice_and_export
    ok, actual_value, details = parse_skirt_height(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== skirt_height Level 1 检测详情 ===")
    print(f"  期望值: {expected_value}")
    print(f"  检测值: {actual_value}")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 45)

    assert ok, (
        f"skirt_height expected {expected_value}, actual {actual_value}, details: {details}"
    )


# ================== skirt_speed ==================

@pytest.mark.engine_params
def test_skirt_speed(
        slice_and_export: Path,
        expected_value: float,
):
    """测试 skirt_speed 参数 (Level 1 - 配置对比)"""
    # 验证方法：使用首层附着、外壳或多对象专用 3MF切片，解析Skirt 路径的层数、圈数、边界距离、挤出长度和速度；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path = slice_and_export
    ok, actual_value, details = parse_skirt_speed(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== skirt_speed Level 1 检测详情 ===")
    print(f"  期望值: {expected_value}mm/s")
    print(f"  检测值: {actual_value}mm/s")
    print(f"  容差: ±1.0mm/s")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 45)

    assert ok, (
        f"skirt_speed expected {expected_value}mm/s, actual {actual_value}mm/s, details: {details}"
    )


# ================== min_skirt_length ==================

@pytest.mark.engine_params
def test_min_skirt_length(
        slice_and_export: Path,
        expected_value: float,
):
    """测试 min_skirt_length 参数 (Level 1 - 配置对比)"""
    # 验证方法：使用首层附着、外壳或多对象专用 3MF切片，解析Skirt 路径的层数、圈数、边界距离、挤出长度和速度；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path = slice_and_export
    ok, actual_value, details = parse_min_skirt_length(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== min_skirt_length Level 1 检测详情 ===")
    print(f"  期望值: {expected_value}mm")
    print(f"  检测值: {actual_value}mm")
    print(f"  容差: ±1.0mm")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 45)

    assert ok, (
        f"min_skirt_length expected {expected_value}mm, actual {actual_value}mm, details: {details}"
    )


# ================== draft_shield ==================

@pytest.mark.engine_params
def test_draft_shield(
        slice_and_export: Path,
        expected_value: str,
):
    """测试 draft_shield 参数 (Level 1 - 配置对比)"""
    # 验证方法：使用首层附着、外壳或多对象专用 3MF切片，解析Skirt 路径的层数、圈数、边界距离、挤出长度和速度；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path = slice_and_export
    ok, actual_value, details = parse_draft_shield(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== draft_shield Level 1 检测详情 ===")
    print(f"  期望值: {expected_value}")
    print(f"  检测值: {actual_value}")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  配置值: {details.get('config_value', 'N/A')}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 45)

    assert ok, (
        f"draft_shield expected {expected_value}, actual {actual_value}, details: {details}"
    )

