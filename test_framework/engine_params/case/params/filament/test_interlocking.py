from __future__ import annotations

from pathlib import Path

import pytest

from engine_params.src.gcode.filament.interlocking_check import parse_interlocking_beam


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
