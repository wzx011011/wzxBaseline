from pathlib import Path
from engine_params.src.gcode.precision_check import (
    check_elefant_foot_compensation,
    parse_xy_hole_compensation, parse_xy_contour_compensation,
    parse_enable_arc_fitting,
)
from engine_params.src.gcode.process.quality.precision_check import (
    parse_slice_closing_radius,
    parse_resolution,
    parse_hole_to_polyhole,
    parse_hole_to_polyhole_threshold,
    parse_hole_to_polyhole_twisted,
    parse_precise_outer_wall,
    parse_precise_z_height,
)
from engine_params.src.gcode.constants import ExtrusionType
import pytest

# ================== elefant_foot_compensation ==================
@pytest.mark.engine_params
def test_elefant_foot_compensation(
    slice_and_export: Path,
    baseline_gcode: str | Path,
    expected_comp: float,
    tol: float,
):
    """
    验证第一层的象脚补偿：同时校验 Outer/Inner Walls，且只把带 E 的挤出行视作轮廓点。
    其它层不能补偿。
    """
    baseline_gcode = Path(baseline_gcode)
    assert baseline_gcode.exists(), f"baseline G-code 不存在：{baseline_gcode}"
    assert slice_and_export.exists(), f"tested G-code 不存在：{slice_and_export}"

    check_elefant_foot_compensation(
        baseline=baseline_gcode,
        tested=slice_and_export,
        expected_comp=expected_comp,
        tol=tol,
        max_layers=1
    )

# ================== elefant_foot_compensation_layers ==================

@pytest.mark.engine_params
def test_elefant_foot_compensation_layers(
    slice_and_export: Path,
    baseline_gcode: str | Path,
    expected_comp: float,
    tol: float,
    efc_layers: int
):
    """
    验证efc_layers的象脚补偿：同时校验 Outer/Inner Walls，且只把带 E 的挤出行视作轮廓点。
    efc_layers外的层不能补偿。
    """
    baseline_gcode = Path(baseline_gcode)
    assert baseline_gcode.exists(), f"baseline G-code 不存在：{baseline_gcode}"
    assert slice_and_export.exists(), f"tested G-code 不存在：{slice_and_export}"

    check_elefant_foot_compensation(
        baseline=baseline_gcode,
        tested=slice_and_export,
        expected_comp=expected_comp,
        tol=tol,
        max_layers=efc_layers
    )

# ================== xy_hole_compensation ==================
@pytest.mark.engine_params
def test_xy_hole_compensation(
        slice_and_export: Path,
        expected_offset: float,
        baseline_gcode: str | Path,
        tol: float,
):
    """
    说明：每一层将测试 G-code 的 XY 边界框与基准 G-code 对比，
    期望所有边界均在容差内向内收缩 |expected_offset| mm（参数为负时）
    或向外扩张 expected_offset mm（参数为正时）。
    """
    baseline_path = Path(baseline_gcode)
    assert baseline_path.exists(), f"baseline G-code 不存在: {baseline_path}"
    assert slice_and_export.exists(), f"tested G-code 不存在: {slice_and_export}"

    ok, details = parse_xy_hole_compensation(
        baseline=baseline_path,
        tested=slice_and_export,
        expected_offset=expected_offset,
        tolerance=tol,
        object_id=0,
    )

    assert ok, f"xy_hole_compensation 未达到期望: {details}"


# ================== xy_contour_compensation ==================

@pytest.mark.engine_params
def test_xy_contour_compensation(
        slice_and_export: Path,
        expected_offset: float,
        baseline_gcode: str | Path,
        tol: float
) -> None:
    """
    说明：
      - 逐层对“外轮廓族”的外墙（outer）与指定圈的内墙（inner_{k}）做 bbx 边界位移校验；
      - 期望：四边位移满足统一公式（Left/Bottom=-expected_offset, Right/Top=+expected_offset），允许 ±tol。
    """
    baseline_path = Path(baseline_gcode)
    assert baseline_path.exists(), f"baseline G-code 不存在: {baseline_path}"
    assert slice_and_export.exists(), f"tested G-code 不存在: {slice_and_export}"

    ok, details = parse_xy_contour_compensation(
        baseline=baseline_path,
        tested=slice_and_export,
        expected_offset=expected_offset,
        tolerance=tol,
        object_id=0,
    )
    assert ok, f"xy_contour_compensation 未达到期望: {details}"


# ================== enable_arc_fitting ==================

@pytest.mark.engine_params
def test_enable_arc_fitting(
        slice_and_export: Path,
        expected_enable: bool,
):
    """
    说明：enable_arc_fitting=0 时，内/外墙挤出块不应出现 G2/G3 圆弧指令。
    """
    assert slice_and_export.exists(), f"tested G-code 不存在: {slice_and_export}"

    ok, details = parse_enable_arc_fitting(
        gcode_path=slice_and_export,
        expected_enable=expected_enable,
        object_id=0,
    )
    assert ok, f"enable_arc_fitting 校验失败: {details}"



# ================== slice_closing_radius ==================
@pytest.mark.engine_params
def test_slice_closing_radius(slice_and_export: Path, expected_slice_closing_radius: float):
    """测试 slice_closing_radius 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_slice_closing_radius(gcode_path, expected_slice_closing_radius)
    assert ok, f"slice_closing_radius expected {expected_slice_closing_radius}, actual {actual}, details: {details}"


# ================== resolution ==================
@pytest.mark.engine_params
def test_resolution(slice_and_export: Path, expected_resolution: float):
    """测试 resolution 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_resolution(gcode_path, expected_resolution)
    assert ok, f"resolution expected {expected_resolution}, actual {actual}, details: {details}"


# ================== hole_to_polyhole ==================
@pytest.mark.engine_params
def test_hole_to_polyhole(slice_and_export: Path, expected_hole_to_polyhole: bool):
    """测试 hole_to_polyhole 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_hole_to_polyhole(gcode_path, expected_hole_to_polyhole)
    assert ok, f"hole_to_polyhole expected {expected_hole_to_polyhole}, actual {actual}, details: {details}"


# ================== hole_to_polyhole_threshold ==================
@pytest.mark.engine_params
def test_hole_to_polyhole_threshold(slice_and_export: Path, expected_hole_to_polyhole_threshold: float):
    """测试 hole_to_polyhole_threshold 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_hole_to_polyhole_threshold(gcode_path, expected_hole_to_polyhole_threshold)
    assert ok, f"hole_to_polyhole_threshold expected {expected_hole_to_polyhole_threshold}, actual {actual}, details: {details}"


# ================== hole_to_polyhole_twisted ==================
@pytest.mark.engine_params
def test_hole_to_polyhole_twisted(slice_and_export: Path, expected_hole_to_polyhole_twisted: bool):
    """测试 hole_to_polyhole_twisted 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_hole_to_polyhole_twisted(gcode_path, expected_hole_to_polyhole_twisted)
    assert ok, f"hole_to_polyhole_twisted expected {expected_hole_to_polyhole_twisted}, actual {actual}, details: {details}"


# ================== precise_outer_wall ==================
@pytest.mark.engine_params
def test_precise_outer_wall(slice_and_export: Path, expected_precise_outer_wall: bool):
    """测试 precise_outer_wall 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_precise_outer_wall(gcode_path, expected_precise_outer_wall)
    assert ok, f"precise_outer_wall expected {expected_precise_outer_wall}, actual {actual}, details: {details}"


# ================== precise_z_height ==================
@pytest.mark.engine_params
def test_precise_z_height(slice_and_export: Path, expected_precise_z_height: float):
    """测试 precise_z_height 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_precise_z_height(gcode_path, expected_precise_z_height)
    assert ok, f"precise_z_height expected {expected_precise_z_height}, actual {actual}, details: {details}"
