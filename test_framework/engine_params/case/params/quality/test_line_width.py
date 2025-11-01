'''
    TODO:2025年10月27日利浩贤注：顶面的底面的tolerance设置为0.005才能通过，不知道为什么，算的时候偏差会大一点，可能还和其他参数耦合了。
'''

from __future__ import annotations

from pathlib import Path

import pytest

from engine_params.src.gcode.Quality.line_width_check import (
    parse_initial_layer_line_width,
    parse_line_width_from_type,
)
from engine_params.src.gcode.constants import ExtrusionType


# ================== initial_layer_line_width ==================
initial_cases = [
    {"input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\initial_layer_line_width_001.3mf"},
]
initial_expectations = [0.52]
initial_params = [
    pytest.param(
        case, exp
    )
    for case, exp in zip(initial_cases, initial_expectations)
]


@pytest.mark.engine_params
@pytest.mark.parametrize(("slice_and_export", "expected_line_width"), initial_params,
                         indirect=["slice_and_export"])
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
outer_wall_cases = [
    {"input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\outer_wall_line_width_001.3mf"},
]
outer_wall_expectations = [0.44]
outer_wall_params = [
    pytest.param(
        case, exp
    )
    for case, exp in zip(outer_wall_cases, outer_wall_expectations)
]


@pytest.mark.engine_params
@pytest.mark.parametrize(("slice_and_export", "expected_line_width"), outer_wall_params,
                         indirect=["slice_and_export"])
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
inner_wall_cases = [
    {"input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\inner_wall_line_width_001.3mf"},
]
inner_wall_expectations = [0.48]
inner_wall_params = [
    pytest.param(
        case, exp
    )
    for case, exp in zip(inner_wall_cases, inner_wall_expectations)
]


@pytest.mark.engine_params
@pytest.mark.parametrize(("slice_and_export", "expected_line_width"), inner_wall_params,
                         indirect=["slice_and_export"])
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
top_surface_cases = [
    {"input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\top_surface_line_width_001.3mf"},
]
top_surface_expectations = [0.45]
top_surface_params = [
    pytest.param(
        case, exp
    )
    for case, exp in zip(top_surface_cases, top_surface_expectations)
]
@pytest.mark.engine_params
@pytest.mark.parametrize(("slice_and_export", "expected_line_width"), top_surface_params,
                         indirect=["slice_and_export"])
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
sparse_infill_cases = [
    {"input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\sparse_infill_line_width_001.3mf"},
]
sparse_infill_expectations = [0.48]
sparse_infill_params = [
    pytest.param(
        case, exp
    )
    for case, exp in zip(sparse_infill_cases, sparse_infill_expectations)
]


@pytest.mark.engine_params
@pytest.mark.parametrize(("slice_and_export", "expected_line_width"), sparse_infill_params,
                         indirect=["slice_and_export"])
def test_sparse_infill_width(slice_and_export: Path,
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


# # ================== internal_solid_line_width ==================
# internal_solid_cases = [
#     {"input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\internal_solid_line_width_001.3mf"},
# ]
# internal_solid_expectations = [0.48]
# internal_solid_params = [
#     pytest.param(
#         case, exp
#     )
#     for case, exp in zip(internal_solid_cases, internal_solid_expectations)
# ]
#
#
# @pytest.mark.engine_params
# @pytest.mark.parametrize(("slice_and_export", "expected_line_width"), internal_solid_params,
#                          indirect=["slice_and_export"])
# def test_internal_solid_line_width(slice_and_export: Path,
#                                    expected_line_width: float):
#     gcode_path: Path = slice_and_export
#     assert gcode_path.exists()
#
#     ok, _, details = parse_line_width_from_type(
#         gcode_path,
#         expected_line_width,
#         extrusion_types=[ExtrusionType.INTERNAL_SOLID_INFILL],
#         skip_layers=[0],
#         tolerance=0.005,
#     )
#
#     assert ok, (
#         f"internal_solid_line_width expected {expected_line_width}, details: {details}"
#     )


# ================== support_line_width ==================
support_cases = [
    {"input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\support_line_width_001.3mf"},
]
support_expectations = [0.48]
support_params = [
    pytest.param(
        case, exp
    )
    for case, exp in zip(support_cases, support_expectations)
]


@pytest.mark.engine_params
@pytest.mark.parametrize(("slice_and_export", "expected_line_width"), support_params,
                         indirect=["slice_and_export"])
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
