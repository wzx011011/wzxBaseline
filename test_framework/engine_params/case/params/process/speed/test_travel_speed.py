#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Travel speed test module
"""

from pathlib import Path

from engine_params.src.gcode.GCodeParserEx import GCodeParserEx
from engine_params.src.gcode.process.speed.travel_speed_check import parse_travel_speed

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
    error_msg.append(f"  Config speed: {details['actual_config_speed']}")
    error_msg.append(f"  Tolerance: {details['tolerance']}")
    if details.get('note'):
        error_msg.append(f"  Note: {details['note']}")
    
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


def test_travel_speed(
        slice_and_export: Path,
        expected_travel_speed: float,
        tolerance: float,
) -> None:
    """
    验证方法：
    1. 完成切片并解析导出的 G-code，获取除首层外的全部运动路径。
    2. 核对 CONFIG_BLOCK 中 travel_speed 与期望值，并确认非首层存在 travel 点。
    3. 汇总逐点实际 F 作为诊断信息，不要求所有移动都等于配置值，因为 Z 移动、
       回抽及动态限速可以合法使用其他速度。
    通过标准：配置值匹配、至少解析到一个 travel 点，且速度字段不缺失。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    parser = GCodeParserEx(gcode_path)
    result = parse_travel_speed(parser, expected_travel_speed, tolerance)
    
    # 断言校验结果
    assert result['passed'], _format_failure_travel_speed(result['details'])
