"""
冲刷选项（Flush options）参数的测试用例模块

包含 flush_into_infill, flush_into_support, flush_into_objects 等参数的测试用例
"""
from __future__ import annotations
from pathlib import Path
import pytest
from engine_params.src.gcode.filament.filament_check import (
    parse_flush_into_infill,
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
