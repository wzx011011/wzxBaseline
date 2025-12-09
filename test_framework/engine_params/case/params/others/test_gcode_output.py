"""
G代码输出 (G-code output) 参数测试套件

包含以下参数的测试：
- reduce_infill_retraction (Level 2 特征检测 - 填充区域回抽统计)
- gcode_add_line_number (Level 2 特征检测 - 行号格式检测)
- gcode_comments (Level 2 特征检测 - 注释行占比)
- gcode_label_objects (Level 2 特征检测 - EXCLUDE_OBJECT标记检测)
- exclude_object (Level 2 特征检测 - 同 gcode_label_objects)
- filename_format (特殊 - 无法通过G-code校验)
"""
from __future__ import annotations

from pathlib import Path

import pytest

from engine_params.src.gcode.others.gcode_output_check import (
    parse_reduce_infill_retraction,
    parse_gcode_add_line_number,
    parse_gcode_comments,
    parse_gcode_label_objects,
    parse_exclude_object,
    parse_filename_format,
)


# ================== reduce_infill_retraction ==================

@pytest.mark.engine_params
def test_reduce_infill_retraction(
        slice_and_export: Path,
        expected_value: bool,
):
    """测试 reduce_infill_retraction 参数 (Level 2 - 填充区域回抽统计)"""
    gcode_path = slice_and_export
    ok, actual_value, details = parse_reduce_infill_retraction(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== reduce_infill_retraction Level 2 检测详情 ===")
    print(f"  期望值: {expected_value}")
    print(f"  检测值: {actual_value}")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  填充区域行数: {details.get('infill_lines', 0)}")
    print(f"  填充回抽次数: {details.get('infill_retractions', 0)}")
    print(f"  总回抽次数: {details.get('total_retractions', 0)}")
    print(f"  填充回抽率: {details.get('infill_retraction_rate', 'N/A')}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 50)

    assert ok, (
        f"reduce_infill_retraction expected {expected_value}, actual {actual_value}, details: {details}"
    )


# ================== gcode_add_line_number ==================

@pytest.mark.engine_params
def test_gcode_add_line_number(
        slice_and_export: Path,
        expected_value: bool,
):
    """测试 gcode_add_line_number 参数 (Level 2 - 行号格式检测)"""
    gcode_path = slice_and_export
    ok, actual_value, details = parse_gcode_add_line_number(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== gcode_add_line_number Level 2 检测详情 ===")
    print(f"  期望值: {expected_value}")
    print(f"  检测值: {actual_value}")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  总行数: {details.get('total_lines', 0)}")
    print(f"  带行号行数: {details.get('lines_with_number', 0)}")
    print(f"  行号率: {details.get('line_number_rate', 'N/A')}")
    print(f"  阈值: {details.get('threshold', 'N/A')}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 50)

    assert ok, (
        f"gcode_add_line_number expected {expected_value}, actual {actual_value}, details: {details}"
    )


# ================== gcode_comments ==================

@pytest.mark.engine_params
def test_gcode_comments(
        slice_and_export: Path,
        expected_value: bool,
):
    """测试 gcode_comments 参数 (Level 2 - 注释行占比检测)"""
    gcode_path = slice_and_export
    ok, actual_value, details = parse_gcode_comments(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== gcode_comments Level 2 检测详情 ===")
    print(f"  期望值: {expected_value}")
    print(f"  检测值: {actual_value}")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  G-code 行数: {details.get('total_gcode_lines', 0)}")
    print(f"  行尾注释行数: {details.get('inline_comment_lines', 0)}")
    print(f"  行尾注释率: {details.get('inline_comment_rate', 'N/A')}")
    print(f"  阈值: {details.get('threshold', 'N/A')}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 50)

    assert ok, (
        f"gcode_comments expected {expected_value}, actual {actual_value}, details: {details}"
    )


# ================== gcode_label_objects ==================

@pytest.mark.engine_params
def test_gcode_label_objects(
        slice_and_export: Path,
        expected_value: bool,
):
    """测试 gcode_label_objects 参数 (Level 2 - EXCLUDE_OBJECT标记检测)"""
    gcode_path = slice_and_export
    ok, actual_value, details = parse_gcode_label_objects(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== gcode_label_objects Level 2 检测详情 ===")
    print(f"  期望值: {expected_value}")
    print(f"  检测值: {actual_value}")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  has_printing_object: {details.get('has_printing_object', False)}")
    print(f"  has_stop_printing: {details.get('has_stop_printing', False)}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 50)

    assert ok, (
        f"gcode_label_objects expected {expected_value}, actual {actual_value}, details: {details}"
    )


# ================== exclude_object ==================

@pytest.mark.engine_params
def test_exclude_object(
        slice_and_export: Path,
        expected_value: bool,
):
    """测试 exclude_object 参数 (Level 2 - EXCLUDE_OBJECT标记检测)"""
    gcode_path = slice_and_export
    ok, actual_value, details = parse_exclude_object(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== exclude_object Level 2 检测详情 ===")
    print(f"  G-code路径: {gcode_path}")
    print(f"  期望值: {expected_value}")
    print(f"  检测值: {actual_value}")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  has_start: {details.get('has_start', False)}")
    print(f"  has_end: {details.get('has_end', False)}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 50)

    assert ok, (
        f"exclude_object expected {expected_value}, actual {actual_value}, details: {details}"
    )


# ================== filename_format ==================

@pytest.mark.engine_params
@pytest.mark.skip(reason="filename_format cannot be validated through G-code content")
def test_filename_format(
        slice_and_export: Path,
        expected_value: str,
):
    """测试 filename_format 参数 (特殊 - 无法通过G-code校验)
    
    注意：此参数影响输出文件名格式，无法通过 G-code 内容校验。
    需要在文件系统层面检查输出文件名是否符合模板格式。
    """
    gcode_path = slice_and_export
    ok, actual_value, details = parse_filename_format(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== filename_format 特殊处理详情 ===")
    print(f"  期望格式: {expected_value}")
    print(f"  实际文件名: {details.get('actual_filename', 'N/A')}")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  提示: {details.get('note', 'N/A')}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 50)

    # 此测试始终跳过，因为无法通过 G-code 校验
    pytest.skip(details.get('message', 'Cannot validate through G-code'))
