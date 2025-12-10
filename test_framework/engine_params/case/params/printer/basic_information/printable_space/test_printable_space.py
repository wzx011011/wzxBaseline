import pytest
from pathlib import Path

from engine_params.src.gcode.printer.basic_information.basic_information_check import (
    parse_printable_area,
    parse_printable_height,
    parse_bed_exclude_area,
    parse_support_multi_bed_types,
    parse_nozzle_volume,
    parse_best_object_pos,
    parse_z_offset,
    parse_preferred_orientation,
)


@pytest.mark.engine_params
def test_printable_area(slice_and_export: Path, expected_value):
    """Level 1 - Config: 读取 G-code 配置块并与期望 printable_area 对比"""
    gcode_path = slice_and_export
    ok, actual, details = parse_printable_area(gcode_path, expected_value)
    assert ok, f"printable_area 期望 {expected_value}，实际 {actual}：{details}"


@pytest.mark.engine_params
def test_printable_height(slice_and_export: Path, expected_value):
    """Level 1 - Config: 读取 G-code 配置块并与期望 printable_height 对比"""
    gcode_path = slice_and_export
    ok, actual, details = parse_printable_height(gcode_path, expected_value)
    assert ok, f"printable_height 期望 {expected_value}，实际 {actual}：{details}"


@pytest.mark.engine_params
def test_bed_exclude_area(slice_and_export: Path, expected_value):
    """Level 1 - Config: 读取 G-code 配置块并与期望 bed_exclude_area 对比"""
    gcode_path = slice_and_export
    ok, actual, details = parse_bed_exclude_area(gcode_path, expected_value)
    assert ok, f"bed_exclude_area 期望 {expected_value}，实际 {actual}：{details}"


@pytest.mark.engine_params
def test_support_multi_bed_types(slice_and_export: Path, expected_value):
    """Level 1 - Config: 读取 G-code 配置块并与期望 support_multi_bed_types 对比"""
    gcode_path = slice_and_export
    ok, actual, details = parse_support_multi_bed_types(gcode_path, expected_value)
    assert ok, f"support_multi_bed_types 期望 {expected_value}，实际 {actual}：{details}"


@pytest.mark.engine_params
def test_nozzle_volume(slice_and_export: Path, expected_value):
    """Level 1 - Config: 读取 G-code 配置块并与期望 nozzle_volume 对比"""
    gcode_path = slice_and_export
    ok, actual, details = parse_nozzle_volume(gcode_path, expected_value)
    assert ok, f"nozzle_volume 期望 {expected_value}，实际 {actual}：{details}"


@pytest.mark.engine_params
def test_best_object_pos(slice_and_export: Path, expected_value):
    """Level 1 - Config: 读取 G-code 配置块并与期望 best_object_pos 对比"""
    gcode_path = slice_and_export
    ok, actual, details = parse_best_object_pos(gcode_path, expected_value)
    assert ok, f"best_object_pos 期望 {expected_value}，实际 {actual}：{details}"


@pytest.mark.engine_params
def test_z_offset(slice_and_export: Path, expected_value):
    """Level 1 - Config: 读取 G-code 配置块并与期望 z_offset 对比"""
    gcode_path = slice_and_export
    ok, actual, details = parse_z_offset(gcode_path, expected_value)
    assert ok, f"z_offset 期望 {expected_value}，实际 {actual}：{details}"


@pytest.mark.engine_params
def test_preferred_orientation(slice_and_export: Path, expected_value):
    """Level 1 - Config: 读取 G-code 配置块并与期望 preferred_orientation 对比"""
    gcode_path = slice_and_export
    ok, actual, details = parse_preferred_orientation(gcode_path, expected_value)
    assert ok, f"preferred_orientation 期望 {expected_value}，实际 {actual}：{details}"
