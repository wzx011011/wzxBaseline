"""
后处理脚本与备注 (Post-processing Scripts & Notes) 参数测试套件

包含以下参数的测试：
- post_process (特殊 - 无法直接通过G-code内容校验)
- notes (Level 1 配置对比 - 检测G-code头部注释)
"""
from __future__ import annotations

from pathlib import Path

import pytest

from engine_params.src.gcode.others.post_process_notes_check import (
    parse_post_process,
    parse_notes,
)


# ================== post_process ==================

@pytest.mark.engine_params
@pytest.mark.skip(reason="post_process cannot be validated through G-code content")
def test_post_process(
        slice_and_export: Path,
        expected_value: str,
):
    """测试 post_process 参数 (特殊 - 无法直接校验)
    
    注意：post_process 参数指定外部脚本路径，该脚本在 G-code 生成后执行。
    无法通过 G-code 内容反向推断脚本路径，需要基线对比或外部验证。
    """
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

    # 此测试始终跳过，因为无法通过 G-code 校验
    pytest.skip(details.get('message', 'Cannot validate through G-code'))


# ================== notes ==================

@pytest.mark.engine_params
def test_notes(
        slice_and_export: Path,
        expected_value: str,
):
    """测试 notes 参数 (Level 1 - 配置对比)"""
    # 跳过 notes_custom 测试用例（需要手动配置 3MF）
    if expected_value == "Test notes for G-code validation":
        pytest.skip("notes_custom requires manual 3MF configuration")
    
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
