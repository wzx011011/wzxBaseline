#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Travel speed test module
"""

import os
from typing import Dict, Any

from engine_params.src.gcode.speed.travel_speed_check import parse_travel_speed

# ================== travel_speed ==================
def _format_failure_travel_speed(details) -> str:
    """
    格式化travel_speed校验失败时的错误信息
    
    Args:
        details: 包含失败详情的字典
    
    Returns:
        str: 格式化的错误信息
    """
    error_msg = []
    error_msg.append(f"Travel speed check failed!")
    error_msg.append(f"  Expected speed: {details['expected_speed']}")
    error_msg.append(f"  Tolerance: {details['tolerance']}")
    
    # 添加跳过的层信息
    if 'skipped_layers' in details:
        error_msg.append(f"  Skipped layers: {details['skipped_layers']}")
    
    # 列出所有无效点
    if details.get('invalid_points'):
        error_msg.append("  Invalid points:")
        for point in details['invalid_points']:
            error_msg.append(f"    Layer {point['layer_index']}, Point {point['point_index']}:")
            error_msg.append(f"      Expected: {point['expected_speed']}, Actual: {point['actual_speed']}")
    
    return '\n'.join(error_msg)


def test_travel_speed(gcode_parser: Any, input_3mf: str, expected_travel_speed: float, tolerance: float = 0.0) -> None:
    """
    测试travel_speed参数
    
    Args:
        gcode_parser: GCode解析器实例
        input_3mf: 输入的3MF文件路径
        expected_travel_speed: 期望的travel速度值
        tolerance: 容差范围，默认为0
    """
    # 验证输入文件存在
    assert os.path.exists(input_3mf), f"Input file not found: {input_3mf}"
    
    # 调用解析函数进行校验
    result = parse_travel_speed(gcode_parser, expected_travel_speed, tolerance)
    
    # 断言校验结果
    assert result['passed'], _format_failure_travel_speed(result['details'])