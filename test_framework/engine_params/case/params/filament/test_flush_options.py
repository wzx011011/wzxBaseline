"""
冲刷选项（Flush options）参数的测试用例模块

包含 flush_into_infill, flush_into_support, flush_into_objects 等参数的测试用例
"""
from __future__ import annotations
from pathlib import Path
import pytest
from engine_params.src.gcode.filament.filament_check import (
    parse_flush_into_infill,
    parse_flush_into_support,
)


# ================== flush_into_infill ==================
@pytest.mark.engine_params
def test_flush_into_infill(
        slice_and_export: Path,
        expected_value: bool,
) -> None:
    """
    测试 flush_into_infill 参数是否正确生效。
    
    校验逻辑（Level 2 特征检测）：
    检测换料后首个挤出块是否在填充区域。
    
    flush_into_infill 启用时的特征：
    1. 换料命令（T0/T1/T2...）之后
    2. 在 Prime tower 挤出完成后
    3. 首个模型挤出出现在填充区域（;TYPE:Sparse infill 或 ;TYPE:Internal solid infill）
    
    具体检测步骤：
    1. 定位所有换料命令（T0, T1, T2...）
    2. 在换料后，跳过 Prime tower 区域
    3. 记录进入模型打印后的首个 TYPE 标记
    4. 统计换料后首个 TYPE 为填充类型的比例
    5. 如果比例 > 40%，判定为 flush_into_infill 启用
    
    参数说明：
    - flush_into_infill: 冲刷到对象的填充
    - 类型: bool
    - 默认值: false
    - 将换料时的冲刷耗材用于打印填充部分，减少擦料塔浪费
    
    注意：
    - 需要启用 enable_prime_tower = true 才能生效
    - 需要多色模型才能触发换料操作
    - 如果没有换料操作，会回退到 Level 1 配置对比
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, detected_value, details = parse_flush_into_infill(
        gcode_path,
        expected_value,
    )

    assert ok, (
        f"flush_into_infill expected {expected_value}, detected={detected_value}, details: {details}"
    )


# ================== flush_into_support ==================
@pytest.mark.engine_params
def test_flush_into_support(
        slice_and_export: Path,
        expected_value: bool,
) -> None:
    """
    测试 flush_into_support 参数是否正确生效。
    
    校验逻辑（Level 2 特征检测）：
    检测换料后首个挤出块是否在支撑区域。
    
    flush_into_support 启用时的特征：
    1. 换料命令（T0/T1/T2...）之后
    2. 在 Prime tower 挤出完成后
    3. 首个模型挤出出现在支撑区域（;TYPE:Support 或 ;TYPE:Support interface）
    
    具体检测步骤：
    1. 定位所有换料命令（T0, T1, T2...）
    2. 在换料后，跳过 Prime tower 区域
    3. 记录进入模型打印后的首个 TYPE 标记
    4. 统计换料后首个 TYPE 为支撑类型的比例
    5. 如果比例 > 20%，判定为 flush_into_support 启用
    
    参数说明：
    - flush_into_support: 冲刷到对象的支撑
    - 类型: bool
    - 默认值: true（默认启用）
    - 将换料时的冲刷耗材用于支撑区域，减少擦料塔浪费
    
    注意：
    - flush_into_support 默认启用，测试禁用场景
    - 需要启用 enable_prime_tower = true 才能生效
    - 需要多色模型且有支撑结构才能触发换料操作
    - 如果没有换料操作，会回退到 Level 1 配置对比
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, detected_value, details = parse_flush_into_support(
        gcode_path,
        expected_value,
    )

    # 打印详细统计
    print(f"\n========== flush_into_support 检测结果 ==========")
    print(f"G-code: {gcode_path.name}")
    print(f"期望值: {expected_value}")
    print(f"检测值: {detected_value}")
    print(f"检测方法: {details.get('detection_method', 'N/A')}")
    print(f"换料次数: {details.get('tool_changes_count', 0)}")
    print(f"分析次数: {details.get('total_analyzed', 0)}")
    print(f"支撑次数: {details.get('support_count', 0)}")
    support_ratio = details.get('support_ratio', 0)
    if isinstance(support_ratio, float):
        print(f"支撑比例: {support_ratio:.1%}")
    print(f"阈值: {details.get('threshold', 'N/A')}")
    print(f"测试结果: {'通过' if ok else '失败'}")
    print(f"================================================\n")

    assert ok, (
        f"flush_into_support expected {expected_value}, detected={detected_value}, details: {details}"
    )
