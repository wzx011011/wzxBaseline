"""
后处理脚本与备注 (Post-processing Scripts & Notes) 参数测试套件

包含以下参数的测试：
- post_process (特殊 - 无法直接通过G-code内容校验)
- notes (Level 1 配置对比 - 检测G-code头部注释)
"""
from __future__ import annotations

from pathlib import Path

import pytest

from engine_params.src.gcode.process.others.post_process_notes_check import (
    parse_post_process,
    parse_notes,
)


# ================== post_process ==================

@pytest.mark.engine_params
def test_post_process(
        slice_and_export: Path,
        expected_value: str,
):
    """验证方法：空脚本用例核对 CONFIG_BLOCK 未配置命令，并确认导出的
    G-code 没有后处理标记；非空脚本必须通过脚本约定的输出标记验证。"""
    # 验证方法：使用首层附着、外壳或多对象专用 3MF切片，解析导出文件名规则以及 G-code 头尾中的脚本/备注结果；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path = slice_and_export
    ok, actual_value, details = parse_post_process(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== post_process 特殊处理详情 ===")
    print(f"  期望脚本: {expected_value}")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  找到的标记: {details.get('found_markers', [])}")
    print(f"  提示: {details.get('note', 'N/A')}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 50)

    assert ok, f"post_process expected {expected_value!r}, actual {actual_value!r}, details={details}"


# ================== notes ==================

@pytest.mark.engine_params
def test_notes(
        slice_and_export: Path,
        expected_value: str,
):
    """验证方法：notes 是工程元数据、不会改变刀路；从实际 G-code 的
    CONFIG_BLOCK 读取完整备注并断言空值或自定义文本未丢失。"""
    # 验证方法：使用首层附着、外壳或多对象专用 3MF切片，解析导出文件名规则以及 G-code 头尾中的脚本/备注结果；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path = slice_and_export
    ok, actual_value, details = parse_notes(
        gcode_path,
        expected_value,
    )
    
    # 打印检测详情
    print(f"\n=== notes Level 1 检测详情 ===")
    print(f"  期望值: '{expected_value}'")
    print(f"  检测值: '{actual_value}'")
    print(f"  检测方法: {details.get('detection_method', 'N/A')}")
    print(f"  匹配类型: {details.get('match_type', 'N/A')}")
    print(f"  结果消息: {details.get('message', 'N/A')}")
    print("=" * 50)

    assert ok, (
        f"notes expected '{expected_value}', actual '{actual_value}', details: {details}"
    )
