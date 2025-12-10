from pathlib import Path

import pytest

from engine_params.src.gcode.process.quality.wall_and_surfaces_check import *

# ================== wall_sequence ==================

@pytest.mark.engine_params
def test_wall_sequence(slice_and_export: Path,
                       expected_sequence: WallStyle):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ret: tuple[bool, WallStyle, list[tuple[int, WallStyle, list[str]]]] = parse_wall_sequence(
        gcode_path, expected_style=expected_sequence
    )

    assert ret[0], f"gcode中的墙顺序不是期望的{expected_sequence}顺序，而是{ret[2]}。"

# ================== is_infill_first ==================


@pytest.mark.engine_params
def test_is_infill_first(slice_and_export: Path,
                        expected_first: bool):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ret = parse_is_infill_first(gcode_path, expected_first=expected_first)

    assert ret[0], f"输入期望is_infill_first =={ret[1]}，然而gcode的解析情况是{ret[2]}。"


# ================== wall_direction ==================

@pytest.mark.engine_params
def test_wall_direction(slice_and_export: Path,
                        expected_direction: WallDirection):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ret = parse_wall_directions(gcode_path, expected_dir=expected_direction)

    assert ret[0], f"gcode中的墙打印顺序不是期望的{ret[1]}顺序，而是{ret[2]}。"

# ================== only_one_wall_top ==================

@pytest.mark.engine_params
def test_only_one_wall_top(slice_and_export: Path,
                        expected_only_one_wall_top: bool):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ret = parse_only_one_wall_top(gcode_path, expected_only_one_wall_top=expected_only_one_wall_top)

    assert ret[0], f"期望顶面单层墙，而{ret[2]}。" if {ret[1]} else f"期望顶面不是单层墙，而{ret[2]}。"

# ================== one_wall_first_layer ==================

@pytest.mark.engine_params
def test_one_wall_first_layer(slice_and_export: Path,
                              expected_only_one_wall_first_layer: bool):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ret = parse_one_wall_first_layer(
        gcode_path, expected_one_wall_first_layer=expected_only_one_wall_first_layer
    )

    assert ret[0], (
        f"one_wall_first_layer expected {expected_only_one_wall_first_layer}, details {ret[2]}"
    )


# ================== top_solid_infill_flow_ratio ==================

@pytest.mark.engine_params
def test_top_solid_infill_flow_ratio(
    slice_and_export: Path,
    expected_ratio: float,
    baseline_gcode: str | Path,
    tol: float,
):
    gcode_path: Path = slice_and_export
    baseline_path = Path(baseline_gcode)
    assert gcode_path.exists()
    assert baseline_path.exists()

    ok, ratio, details = parse_top_solid_infill_flow_ratio(
        tested_gcode=gcode_path,
        baseline_gcode=baseline_path,
        expected_ratio=expected_ratio,
        tol=tol,
    )

    assert ok, (
        f"top_solid_infill_flow_ratio expected {expected_ratio}, actual {ratio}, details: {details}"
    )


# ================== bottom_solid_infill_flow_ratio ==================

@pytest.mark.engine_params
def test_bottom_solid_infill_flow_ratio(
    slice_and_export: Path,
    expected_ratio: float,
    baseline_gcode: str | Path,
    tol: float,
):
    gcode_path: Path = slice_and_export
    baseline_path = Path(baseline_gcode)
    assert gcode_path.exists()
    assert baseline_path.exists()

    ok, ratio, details = parse_bottom_solid_infill_flow_ratio(
        tested_gcode=gcode_path,
        baseline_gcode=baseline_path,
        expected_ratio=expected_ratio,
        tol=tol,
    )

    assert ok, (
        f"bottom_infill_flow_ratio expected {expected_ratio}, actual {ratio}, details: {details}"
    )
