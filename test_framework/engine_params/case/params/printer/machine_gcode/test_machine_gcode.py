import pytest
from pathlib import Path

from engine_params.src.gcode.printer.basic_information.basic_information_check import (
    parse_machine_start_gcode,
    parse_machine_end_gcode,
    parse_printing_by_object_gcode,
    parse_before_layer_change_gcode,
    parse_layer_change_gcode,
    parse_time_lapse_gcode,
    parse_change_filament_gcode,
    parse_change_extrusion_role_gcode,
    parse_machine_pause_gcode,
    parse_template_custom_gcode,
)


@pytest.mark.engine_params
def test_machine_start_gcode(slice_and_export: Path, expected_value):
    """Level 1 - Config: 读取 G-code 配置块并与期望 machine_start_gcode 对比"""
    gcode_path = slice_and_export
    ok, actual, details = parse_machine_start_gcode(gcode_path, expected_value)
    assert ok, f"machine_start_gcode 期望 {expected_value}，实际 {actual}：{details}"


@pytest.mark.engine_params
def test_machine_end_gcode(slice_and_export: Path, expected_value):
    """Level 1 - Config: 读取 G-code 配置块并与期望 machine_end_gcode 对比"""
    gcode_path = slice_and_export
    ok, actual, details = parse_machine_end_gcode(gcode_path, expected_value)
    assert ok, f"machine_end_gcode 期望 {expected_value}，实际 {actual}：{details}"


@pytest.mark.engine_params
def test_printing_by_object_gcode(slice_and_export: Path, expected_value):
    """Level 1 - Config: 读取 G-code 配置块并与期望 printing_by_object_gcode 对比"""
    gcode_path = slice_and_export
    ok, actual, details = parse_printing_by_object_gcode(gcode_path, expected_value)
    assert ok, f"printing_by_object_gcode 期望 {expected_value}，实际 {actual}：{details}"


@pytest.mark.engine_params
def test_before_layer_change_gcode(slice_and_export: Path, expected_value):
    """Level 1 - Config: 读取 G-code 配置块并与期望 before_layer_change_gcode 对比"""
    gcode_path = slice_and_export
    ok, actual, details = parse_before_layer_change_gcode(gcode_path, expected_value)
    assert ok, f"before_layer_change_gcode 期望 {expected_value}，实际 {actual}：{details}"


@pytest.mark.engine_params
def test_layer_change_gcode(slice_and_export: Path, expected_value):
    """Level 1 - Config: 读取 G-code 配置块并与期望 layer_change_gcode 对比"""
    gcode_path = slice_and_export
    ok, actual, details = parse_layer_change_gcode(gcode_path, expected_value)
    assert ok, f"layer_change_gcode 期望 {expected_value}，实际 {actual}：{details}"


@pytest.mark.engine_params
def test_time_lapse_gcode(slice_and_export: Path, expected_value):
    """Level 1 - Config: 读取 G-code 配置块并与期望 time_lapse_gcode 对比"""
    gcode_path = slice_and_export
    ok, actual, details = parse_time_lapse_gcode(gcode_path, expected_value)
    assert ok, f"time_lapse_gcode 期望 {expected_value}，实际 {actual}：{details}"


@pytest.mark.engine_params
def test_change_filament_gcode(slice_and_export: Path, expected_value):
    """Level 1 - Config: 读取 G-code 配置块并与期望 change_filament_gcode 对比"""
    gcode_path = slice_and_export
    ok, actual, details = parse_change_filament_gcode(gcode_path, expected_value)
    assert ok, f"change_filament_gcode 期望 {expected_value}，实际 {actual}：{details}"


@pytest.mark.engine_params
def test_change_extrusion_role_gcode(slice_and_export: Path, expected_value):
    """Level 1 - Config: 读取 G-code 配置块并与期望 change_extrusion_role_gcode 对比"""
    gcode_path = slice_and_export
    ok, actual, details = parse_change_extrusion_role_gcode(gcode_path, expected_value)
    assert ok, f"change_extrusion_role_gcode 期望 {expected_value}，实际 {actual}：{details}"


@pytest.mark.engine_params
def test_machine_pause_gcode(slice_and_export: Path, expected_value):
    """Level 1 - Config: 读取 G-code 配置块并与期望 machine_pause_gcode 对比"""
    gcode_path = slice_and_export
    ok, actual, details = parse_machine_pause_gcode(gcode_path, expected_value)
    assert ok, f"machine_pause_gcode 期望 {expected_value}，实际 {actual}：{details}"


@pytest.mark.engine_params
def test_template_custom_gcode(slice_and_export: Path, expected_value):
    """Level 1 - Config: 读取 G-code 配置块并与期望 template_custom_gcode 对比"""
    gcode_path = slice_and_export
    ok, actual, details = parse_template_custom_gcode(gcode_path, expected_value)
    assert ok, f"template_custom_gcode 期望 {expected_value}，实际 {actual}：{details}"
