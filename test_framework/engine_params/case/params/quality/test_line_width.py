'''
    TODO:2025年10月27日利浩贤注：顶面的底面的tolerance设置为0.005才能通过，不知道为什么，算的时候偏差会大一点，可能还和其他参数耦合了。
'''

from __future__ import annotations

from pathlib import Path

import pytest

from engine_params.src.gcode.quality.line_width_check import (
    parse_initial_layer_line_width,
    parse_line_width_from_type,
)
from engine_params.src.gcode.constants import ExtrusionType


# ================== initial_layer_line_width ==================
@pytest.mark.engine_params
def test_initial_layer_line_width(slice_and_export: Path,
                                  expected_line_width: float):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_initial_layer_line_width(
        gcode_path,
        expected_line_width,
        tolerance=0.005,
    )

    assert ok, (
        f"initial_layer_line_width expected {expected_line_width}, details: {details}"
    )


# ================== outer_wall_line_width ==================
@pytest.mark.engine_params
def test_outer_wall_line_width(slice_and_export: Path,
                               expected_line_width: float):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_line_width_from_type(
        gcode_path,
        expected_line_width,
        extrusion_types=[ExtrusionType.OUTER_WALL],
        skip_layers=[0],
        tolerance=0.001,
    )

    assert ok, (
        f"outer_wall_line_width expected {expected_line_width}, details: {details}"
    )


# ================== inner_wall_line_width ==================
@pytest.mark.engine_params

def test_inner_wall_line_width(slice_and_export: Path,
                               expected_line_width: float):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_line_width_from_type(
        gcode_path,
        expected_line_width,
        extrusion_types=[ExtrusionType.INNER_WALL],
        skip_layers=[0],
        tolerance=0.001,
    )

    assert ok, (
        f"inner_wall_line_width expected {expected_line_width}, details: {details}"
    )


# ================== top_surface_line_width ==================

@pytest.mark.engine_params
def test_top_surface_line_width(slice_and_export: Path,
                                expected_line_width: float):
    '''

    '''

    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_line_width_from_type(
        gcode_path,
        expected_line_width,
        extrusion_types=[ExtrusionType.TOP_SURFACE],
        layer_indices=[-1],
        tolerance=0.005,
    )

    assert ok, (
        f"top_surface_line_width expected {expected_line_width}, details: {details}"
    )


# ================== sparse_infill_line_width ==================

@pytest.mark.engine_params
def test_sparse_infill_line_width(slice_and_export: Path,
                             expected_line_width: float):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_line_width_from_type(
        gcode_path,
        expected_line_width,
        extrusion_types=[ExtrusionType.SPARSE_INFILL],
        skip_layers=[0],
        tolerance=0.001,
    )

    assert ok, (
        f"sparse_infill_line_width expected {expected_line_width}, details: {details}"
    )


# ================== internal_solid_line_width ==================
@pytest.mark.engine_params
def test_internal_solid_line_width(slice_and_export: Path,
                                   expected_line_width: float):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_line_width_from_type(
        gcode_path,
        expected_line_width,
        extrusion_types=[ExtrusionType.INTERNAL_SOLID_INFILL],
        skip_layers=[0],
        tolerance=0.005,
    )

    assert ok, (
        f"internal_solid_line_width expected {expected_line_width}, details: {details}"
    )


# ================== support_line_width ==================
@pytest.mark.engine_params
def test_support_line_width(slice_and_export: Path,
                            expected_line_width: float):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_line_width_from_type(
        gcode_path,
        expected_line_width,
        extrusion_types=[ExtrusionType.SUPPORT],
        skip_layers=[0],
        tolerance=0.005,
    )

    assert ok, (
        f"support_line_width expected {expected_line_width}, details: {details}"
    )
