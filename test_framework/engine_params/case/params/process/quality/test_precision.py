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
    """验证切片轮廓的闭缝半径。

    C3DSlicer 将该值传给 ``PrintObjectSlice`` 的 closing operation；规划检查窄缝内轮廓，
    小于闭合尺度的缝应消失，大于阈值的缝应保留，并与零半径基准比较。
    3MF 在同一薄板上布置 0.04/0.08/0.12 mm 三条贯穿狭缝以跨越测试值。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_slice_closing_radius(gcode_path, expected_slice_closing_radius)
    assert ok, f"slice_closing_radius expected {expected_slice_closing_radius}, actual {actual}, details: {details}"


# ================== resolution ==================
@pytest.mark.engine_params
def test_resolution(slice_and_export: Path, expected_resolution: float):
    """验证轮廓简化分辨率。

    C3DSlicer 在 Layer/LayerRegion 中按该容差执行多边形 simplify；规划统计曲线外墙的
    顶点数和相对高精度基准的最大偏差，容差增大时段数减少且几何误差不超过设置量级。
    3MF 使用高细分正弦波边和圆弧边，避免普通立方体无法触发简化。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_resolution(gcode_path, expected_resolution)
    assert ok, f"resolution expected {expected_resolution}, actual {actual}, details: {details}"


# ================== hole_to_polyhole ==================
@pytest.mark.engine_params
def test_hole_to_polyhole(slice_and_export: Path, expected_hole_to_polyhole: bool):
    """验证圆孔是否转换为尺寸补偿后的规则多边形孔。

    C3DSlicer ``_transform_hole_to_polyholes`` 会识别多于 8 点的近圆孔并外扩多边形半径；
    规划比较孔内墙的边数、等边性和内切直径，开启时应形成稳定规则多边形且目标孔径更准。
    3MF 使用高分段的 6/10 mm 竖直圆孔，孔壁高度不少于 5 层。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_hole_to_polyhole(gcode_path, expected_hole_to_polyhole)
    assert ok, f"hole_to_polyhole expected {expected_hole_to_polyhole}, actual {actual}, details: {details}"


# ================== hole_to_polyhole_threshold ==================
@pytest.mark.engine_params
def test_hole_to_polyhole_threshold(slice_and_export: Path, expected_hole_to_polyhole_threshold: float):
    """验证圆孔识别的允许径向变化阈值。

    C3DSlicer 同时比较顶点半径和边中点半径的最大变化；规划在开启 polyhole 时检查
    轻微椭圆/扰动孔是否被转换，变化小于阈值者转换、超过者保持原轮廓。
    3MF 并列放置真圆、轻微椭圆和波纹孔，径向误差跨越 0.01/0.02 mm。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_hole_to_polyhole_threshold(gcode_path, expected_hole_to_polyhole_threshold)
    assert ok, f"hole_to_polyhole_threshold expected {expected_hole_to_polyhole_threshold}, actual {actual}, details: {details}"


# ================== hole_to_polyhole_twisted ==================
@pytest.mark.engine_params
def test_hole_to_polyhole_twisted(slice_and_export: Path, expected_hole_to_polyhole_twisted: bool):
    """验证相邻层多边形孔是否交替旋转。

    C3DSlicer 在 polyhole 转换时携带 twist 标记；规划提取每层孔内墙顶点方位，开启时
    相邻层规则多边形相位交替，关闭时相位保持一致。
    3MF 使用高分段直圆孔柱，固定层高并保证至少 12 个连续孔壁层。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_hole_to_polyhole_twisted(gcode_path, expected_hole_to_polyhole_twisted)
    assert ok, f"hole_to_polyhole_twisted expected {expected_hole_to_polyhole_twisted}, actual {actual}, details: {details}"


# ================== precise_outer_wall ==================
@pytest.mark.engine_params
def test_precise_outer_wall(slice_and_export: Path, expected_precise_outer_wall: bool):
    """验证内墙先打印时的外墙定位补偿。

    C3DSlicer 仅在 ``wall_sequence=InnerOuter`` 时用实际 width 而非 spacing 修正外墙偏移；
    规划测量外墙与最近内墙的中心距；开启时应接近两种线宽之和的一半，关闭时
    使用压扁后的 spacing，中心距更小。3MF 使用 24 mm 方盒和明显不同的内外墙线宽。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_precise_outer_wall(gcode_path, expected_precise_outer_wall)
    assert ok, f"precise_outer_wall expected {expected_precise_outer_wall}, actual {actual}, details: {details}"


# ================== precise_z_height ==================
@pytest.mark.engine_params
def test_precise_z_height(slice_and_export: Path, expected_precise_z_height: float):
    """验证末层 Z 是否精确贴合模型高度。

    C3DSlicer 将该开关传给 ``generate_object_layers``；规划解析所有打印层 Z，开启时
    最后一层应精确到模型顶高且允许调整末层层高，关闭时保持名义层高步进。
    3MF 使用高度不能被层高整除的方柱（例如 10.13 mm），避免两种模式结果相同。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_precise_z_height(gcode_path, expected_precise_z_height)
    assert ok, f"precise_z_height expected {expected_precise_z_height}, actual {actual}, details: {details}"
