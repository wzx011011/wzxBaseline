"""
边缘 (Brim) 参数测试套件

包含以下参数的测试：
- brim_type (Level 1 配置对比)
- brim_width (Level 1 配置对比)
- brim_object_gap (Level 1 配置对比)
- brim_ears_max_angle (Level 1 配置对比)
- brim_ears_detection_length (Level 1 配置对比)
"""
from __future__ import annotations

from pathlib import Path

import pytest

from engine_params.src.gcode.process.others.brim_check import (
    parse_brim_type,
    parse_brim_width,
    parse_brim_object_gap,
    parse_brim_ears_max_angle,
    parse_brim_ears_detection_length,
)


# ================== brim_type ==================

@pytest.mark.engine_params
def test_brim_type(
        slice_and_export: Path,
        expected_value: str,
):
    """测试 brim_type 参数 (Level 1 - 配置对比)"""
    # 验证方法：使用首层附着、外壳或多对象专用 3MF切片，解析首层 Brim 路径的存在性、圈数、边界和对象间隙；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path = slice_and_export
    ok, actual_value, details = parse_brim_type(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== brim_type Level 1 检测详情 ===")
    print(f"  期望值: {expected_value}")
    print(f"  检测值: {actual_value}")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 45)

    assert ok, (
        f"brim_type expected {expected_value}, actual {actual_value}, details: {details}"
    )


# ================== brim_width ==================

@pytest.mark.engine_params
def test_brim_width(
        slice_and_export: Path,
        expected_value: float,
):
    """测试 brim_width 参数 (Level 1 - 配置对比)"""
    # 验证方法：使用首层附着、外壳或多对象专用 3MF切片，解析首层 Brim 路径的存在性、圈数、边界和对象间隙；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path = slice_and_export
    ok, actual_value, details = parse_brim_width(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== brim_width Level 1 检测详情 ===")
    print(f"  期望值: {expected_value}mm")
    print(f"  检测值: {actual_value}mm")
    print(f"  容差: ±0.1mm")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 45)

    assert ok, (
        f"brim_width expected {expected_value}mm, actual {actual_value}mm, details: {details}"
    )


# ================== brim_object_gap ==================

@pytest.mark.engine_params
def test_brim_object_gap(
        slice_and_export: Path,
        expected_value: float,
):
    """测试 brim_object_gap 参数 (Level 1 - 配置对比)"""
    # 验证方法：使用首层附着、外壳或多对象专用 3MF切片，解析首层 Brim 路径的存在性、圈数、边界和对象间隙；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path = slice_and_export
    ok, actual_value, details = parse_brim_object_gap(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== brim_object_gap Level 1 检测详情 ===")
    print(f"  期望值: {expected_value}mm")
    print(f"  检测值: {actual_value}mm")
    print(f"  容差: ±0.01mm")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 45)

    assert ok, (
        f"brim_object_gap expected {expected_value}mm, actual {actual_value}mm, details: {details}"
    )


# ================== brim_ears_max_angle ==================

@pytest.mark.engine_params
def test_brim_ears_max_angle(
        slice_and_export: Path,
        expected_value: float,
):
    """测试 brim_ears_max_angle 参数 (Level 1 - 配置对比)"""
    # 验证方法：使用首层附着、外壳或多对象专用 3MF切片，解析首层 Brim 路径的存在性、圈数、边界和对象间隙；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path = slice_and_export
    ok, actual_value, details = parse_brim_ears_max_angle(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== brim_ears_max_angle Level 1 检测详情 ===")
    print(f"  期望值: {expected_value}°")
    print(f"  检测值: {actual_value}°")
    print(f"  容差: ±0.1°")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 45)

    assert ok, (
        f"brim_ears_max_angle expected {expected_value}°, actual {actual_value}°, details: {details}"
    )


# ================== brim_ears_detection_length ==================

@pytest.mark.engine_params
def test_brim_ears_detection_length(
        slice_and_export: Path,
        expected_value: float,
):
    """测试 brim_ears_detection_length 参数 (Level 1 - 配置对比)"""
    # 验证方法：使用首层附着、外壳或多对象专用 3MF切片，解析首层 Brim 路径的存在性、圈数、边界和对象间隙；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path = slice_and_export
    ok, actual_value, details = parse_brim_ears_detection_length(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== brim_ears_detection_length Level 1 检测详情 ===")
    print(f"  期望值: {expected_value}mm")
    print(f"  检测值: {actual_value}mm")
    print(f"  容差: ±0.1mm")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 45)

    assert ok, (
        f"brim_ears_detection_length expected {expected_value}mm, actual {actual_value}mm, details: {details}"
    )
