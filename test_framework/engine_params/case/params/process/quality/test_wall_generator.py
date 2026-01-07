from __future__ import annotations

from pathlib import Path

import pytest

from engine_params.src.gcode.process.quality.wall_generator_check import (
    WallGenerator,
    parse_wall_generator,
    parse_wall_transition_angle,
    parse_wall_transition_filter_deviation,
    parse_wall_transition_length,
    parse_wall_distribution_count,
    parse_min_feature_size,
    parse_min_bead_width,
    parse_initial_layer_min_bead_width,
)

# ================== wall_generator ==================

@pytest.mark.engine_params
def test_wall_generator(
        slice_and_export: Path,
        expected_generator: str,
        consistency_threshold: float
):
    """
    consistency_threshold 表示在线宽检测中，单层内“线宽落在容差范围内”的挤出段所占比例。
    当单层合格比例低于该阈值，就视为该层存在明显的可变线宽（倾向于判定为 arachne 墙）。
    """

    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    actual_generator, details = parse_wall_generator(
        gcode_path,
        tolerance=0.01,
        consistency_threshold=consistency_threshold,
    )

    assert actual_generator == WallGenerator.from_str(expected_generator), (
        f"wall_generator expected {expected_generator}, actual {actual_generator}, details: {details}"
    )


# ================== wall_transition_angle ==================
@pytest.mark.engine_params
def test_wall_transition_angle(slice_and_export: Path, expected_wall_transition_angle: float):
    """测试 wall_transition_angle 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_wall_transition_angle(gcode_path, expected_wall_transition_angle)
    assert ok, f"wall_transition_angle expected {expected_wall_transition_angle}, actual {actual}, details: {details}"


# ================== wall_transition_filter_deviation ==================
@pytest.mark.engine_params
def test_wall_transition_filter_deviation(slice_and_export: Path, expected_wall_transition_filter_deviation: str):
    """测试 wall_transition_filter_deviation 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_wall_transition_filter_deviation(gcode_path, expected_wall_transition_filter_deviation)
    assert ok, f"wall_transition_filter_deviation expected {expected_wall_transition_filter_deviation}, actual {actual}, details: {details}"


# ================== wall_transition_length ==================
@pytest.mark.engine_params
def test_wall_transition_length(slice_and_export: Path, expected_wall_transition_length: str):
    """测试 wall_transition_length 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_wall_transition_length(gcode_path, expected_wall_transition_length)
    assert ok, f"wall_transition_length expected {expected_wall_transition_length}, actual {actual}, details: {details}"


# ================== wall_distribution_count ==================
@pytest.mark.engine_params
def test_wall_distribution_count(slice_and_export: Path, expected_wall_distribution_count: float):
    """测试 wall_distribution_count 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_wall_distribution_count(gcode_path, expected_wall_distribution_count)
    assert ok, f"wall_distribution_count expected {expected_wall_distribution_count}, actual {actual}, details: {details}"


# ================== min_feature_size ==================
@pytest.mark.engine_params
def test_min_feature_size(slice_and_export: Path, expected_min_feature_size: str):
    """测试 min_feature_size 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_min_feature_size(gcode_path, expected_min_feature_size)
    assert ok, f"min_feature_size expected {expected_min_feature_size}, actual {actual}, details: {details}"


# ================== min_bead_width ==================
@pytest.mark.engine_params
def test_min_bead_width(slice_and_export: Path, expected_min_bead_width: str):
    """测试 min_bead_width 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_min_bead_width(gcode_path, expected_min_bead_width)
    assert ok, f"min_bead_width expected {expected_min_bead_width}, actual {actual}, details: {details}"


# ================== initial_layer_min_bead_width ==================
@pytest.mark.engine_params
def test_initial_layer_min_bead_width(slice_and_export: Path, expected_initial_layer_min_bead_width: str):
    """测试 initial_layer_min_bead_width 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_initial_layer_min_bead_width(gcode_path, expected_initial_layer_min_bead_width)
    assert ok, f"initial_layer_min_bead_width expected {expected_initial_layer_min_bead_width}, actual {actual}, details: {details}"
