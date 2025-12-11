import pytest
from pathlib import Path

from engine_params.src.gcode.printer.basic_information.basic_information_check import (
    parse_fan_speedup_time,
    parse_fan_kickstart,
)


@pytest.mark.engine_params
def test_fan_speedup_time(slice_and_export: Path, expected_value):
    """Level 1 - Config: 读取 G-code 配置块并与期望 fan_speedup_time 对比"""
    gcode_path = slice_and_export
    ok, actual, details = parse_fan_speedup_time(gcode_path, expected_value)
    assert ok, f"fan_speedup_time 期望 {expected_value}，实际 {actual}：{details}"


@pytest.mark.engine_params
def test_fan_kickstart(slice_and_export: Path, expected_value):
    """Level 1 - Config: 读取 G-code 配置块并与期望 fan_kickstart 对比"""
    gcode_path = slice_and_export
    ok, actual, details = parse_fan_kickstart(gcode_path, expected_value)
    assert ok, f"fan_kickstart 期望 {expected_value}，实际 {actual}：{details}"
