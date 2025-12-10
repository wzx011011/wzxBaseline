import pytest
from pathlib import Path

from engine_params.src.gcode.printer.basic_information.basic_information_check import (
    parse_pellet_modded_printer,
    parse_disable_m73,
    parse_use_relative_e_distances,
    parse_machine_load_filament_time,
    parse_machine_unload_filament_time,
    parse_time_cost,
    parse_multicolor_method,
)


@pytest.mark.engine_params
def test_pellet_modded_printer(slice_and_export: Path, expected_value):
    """Level 1 - Config: 读取 G-code 配置块并与期望 pellet_modded_printer 对比"""
    gcode_path = slice_and_export
    ok, actual, details = parse_pellet_modded_printer(gcode_path, expected_value)
    assert ok, f"pellet_modded_printer 期望 {expected_value}，实际 {actual}：{details}"


@pytest.mark.engine_params
def test_disable_m73(slice_and_export: Path, expected_value):
    """Level 1 - Config: 读取 G-code 配置块并与期望 disable_m73 对比"""
    gcode_path = slice_and_export
    ok, actual, details = parse_disable_m73(gcode_path, expected_value)
    assert ok, f"disable_m73 期望 {expected_value}，实际 {actual}：{details}"


@pytest.mark.engine_params
def test_use_relative_e_distances(slice_and_export: Path, expected_value):
    """Level 1 - Config: 读取 G-code 配置块并与期望 use_relative_e_distances 对比"""
    gcode_path = slice_and_export
    ok, actual, details = parse_use_relative_e_distances(gcode_path, expected_value)
    assert ok, f"use_relative_e_distances 期望 {expected_value}，实际 {actual}：{details}"


@pytest.mark.engine_params
def test_machine_load_filament_time(slice_and_export: Path, expected_value):
    """Level 1 - Config: 读取 G-code 配置块并与期望 machine_load_filament_time 对比"""
    gcode_path = slice_and_export
    ok, actual, details = parse_machine_load_filament_time(gcode_path, expected_value)
    assert ok, f"machine_load_filament_time 期望 {expected_value}，实际 {actual}：{details}"


@pytest.mark.engine_params
def test_machine_unload_filament_time(slice_and_export: Path, expected_value):
    """Level 1 - Config: 读取 G-code 配置块并与期望 machine_unload_filament_time 对比"""
    gcode_path = slice_and_export
    ok, actual, details = parse_machine_unload_filament_time(gcode_path, expected_value)
    assert ok, f"machine_unload_filament_time 期望 {expected_value}，实际 {actual}：{details}"


@pytest.mark.engine_params
def test_time_cost(slice_and_export: Path, expected_value):
    """Level 1 - Config: 读取 G-code 配置块并与期望 time_cost 对比"""
    gcode_path = slice_and_export
    ok, actual, details = parse_time_cost(gcode_path, expected_value)
    assert ok, f"time_cost 期望 {expected_value}，实际 {actual}：{details}"


@pytest.mark.engine_params
def test_multicolor_method(slice_and_export: Path, expected_value):
    """Level 1 - Config: 读取 G-code 配置块并与期望 multicolor_method 对比"""
    gcode_path = slice_and_export
    ok, actual, details = parse_multicolor_method(gcode_path, expected_value)
    assert ok, f"multicolor_method 期望 {expected_value}，实际 {actual}：{details}"
