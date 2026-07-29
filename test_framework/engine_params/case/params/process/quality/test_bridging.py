from __future__ import annotations

from pathlib import Path

import pytest

from engine_params.src.gcode.process.quality.bridging_check import (
    parse_internal_bridge_flow,
    parse_bridge_angle,
    parse_bridge_flow,
    parse_bridge_density,
    parse_bridge_speed,
    parse_thick_bridges,
    parse_dont_filter_internal_bridges,
    parse_thick_internal_bridges,
    parse_internal_bridge_speed,
    parse_counterbore_hole_bridging,
)


# ================== internal_bridge_flow ==================
@pytest.mark.engine_params
def test_internal_bridge_flow(
    slice_and_export: Path,
    expected_ratio: float,
    baseline_gcode: str | Path,
    tol: float,
):
    gcode_path: Path = slice_and_export
    baseline_path = Path(baseline_gcode)
    assert gcode_path.exists()
    assert baseline_path.exists()

    ok, ratio, details = parse_internal_bridge_flow(
        tested_gcode=gcode_path,
        baseline_gcode=baseline_path,
        expected_ratio=expected_ratio,
        tol=tol,
    )

    assert ok, (
        f"internal_bridge_flow expected {expected_ratio}, actual {ratio}, details: {details}"
    )


# ================== bridge_angle ==================
@pytest.mark.engine_params
def test_bridge_angle(slice_and_export: Path, expected_bridge_angle: float):
    """验证桥接铺线方向。

    C3DSlicer 在 ``LayerRegion.cpp`` 中把该角度写入 bridge surface；规划从
    Bridge 挤出段的 XY 主方向反算角度并与期望值比较。3MF 使用双桥墩加矩形跨梁，
    跨空面保持方正且足够大，使 0/45/90 度路径都能稳定出现。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_bridge_angle(gcode_path, expected_bridge_angle)
    assert ok, f"bridge_angle expected {expected_bridge_angle}, actual {actual}, details: {details}"


# ================== bridge_flow ==================
@pytest.mark.engine_params
def test_bridge_flow(slice_and_export: Path, expected_bridge_flow: float):
    """验证外部桥接流量倍率。

    C3DSlicer 通过 ``bridging_flow(...).with_flow_ratio`` 调整桥接段单位长度挤出量；
    规划对同一桥面 Bridge 段统计 ``E/XY长度``，与基准值的比率应等于期望倍率。
    3MF 使用固定跨度和固定桥接线宽的双桥墩模型，排除首层及非桥接挤出。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_bridge_flow(gcode_path, expected_bridge_flow)
    assert ok, f"bridge_flow expected {expected_bridge_flow}, actual {actual}, details: {details}"


# ================== bridge_density ==================
@pytest.mark.engine_params
def test_bridge_density(slice_and_export: Path, expected_bridge_density: float):
    """验证桥接填充密度。

    C3DSlicer 将 ``bridge_density`` 作为桥面填充密度；规划在同一 Bridge 层统计
    平行桥接线数量和相邻线中心距，密度增大时线数增加、间距按目标比例减小。
    3MF 使用宽度不少于 20 mm 的单一矩形桥面，避免边缘线占比过高。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_bridge_density(gcode_path, expected_bridge_density)
    assert ok, f"bridge_density expected {expected_bridge_density}, actual {actual}, details: {details}"


# ================== bridge_speed ==================
@pytest.mark.engine_params
def test_bridge_speed(slice_and_export: Path, expected_bridge_speed: float):
    """验证外部桥接段速度。

    C3DSlicer 在 ``GCode.cpp`` 中为 Bridge role 选择 ``bridge_speed``；规划读取
    Bridge 挤出块内的 ``G1 F`` 并换算为 mm/s，所有稳定挤出段应等于期望速度。
    3MF 使用长直桥面，确保过滤加减速端点后仍有足够恒速样本。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_bridge_speed(gcode_path, expected_bridge_speed)
    assert ok, f"bridge_speed expected {expected_bridge_speed}, actual {actual}, details: {details}"


# ================== thick_bridges ==================
@pytest.mark.engine_params
def test_thick_bridges(slice_and_export: Path, expected_thick_bridges: bool):
    """验证外部桥接是否采用厚桥流量模型。

    C3DSlicer 在 ``LayerRegion::bridging_flow`` 中根据开关选择圆截面厚桥或普通流量；
    规划比较开关两组 Bridge 段的线宽、层高和 ``E/长度``，开启时单位长度挤出量应更大。
    3MF 使用同一双桥墩跨梁，并固定喷嘴、层高和 bridge_flow。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_thick_bridges(gcode_path, expected_thick_bridges)
    assert ok, f"thick_bridges expected {expected_thick_bridges}, actual {actual}, details: {details}"


# ================== dont_filter_internal_bridges ==================
@pytest.mark.engine_params
def test_dont_filter_internal_bridges(slice_and_export: Path, expected_dont_filter_internal_bridges: str):
    """验证短小内部桥接面的过滤策略。

    C3DSlicer 在 ``PrintObject.cpp`` 中按 disabled/limited/nofilter 筛选内部桥接候选面；
    规划统计各尺寸内腔上方的 Internal Bridge 段，三种模式应呈现逐步保留更多小桥面的关系。
    3MF 设计 3 组不同宽度的封闭空腔顶板，尺寸跨越 limited 的过滤边界。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_dont_filter_internal_bridges(gcode_path, expected_dont_filter_internal_bridges)
    assert ok, f"dont_filter_internal_bridges expected {expected_dont_filter_internal_bridges}, actual {actual}, details: {details}"


# ================== thick_internal_bridges ==================
@pytest.mark.engine_params
def test_thick_internal_bridges(slice_and_export: Path, expected_thick_internal_bridges: bool):
    """验证内部桥接是否采用厚桥流量模型。

    C3DSlicer 仅对 ``surface.is_internal_bridge()`` 读取该开关；规划在 Internal Bridge
    挤出块比较开关两组的 ``E/XY长度`` 和推导线宽，开启时应符合厚桥截面而非普通填充截面。
    3MF 使用内部封闭空腔，确保观测对象不会被识别成外部桥面。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_thick_internal_bridges(gcode_path, expected_thick_internal_bridges)
    assert ok, f"thick_internal_bridges expected {expected_thick_internal_bridges}, actual {actual}, details: {details}"


# ================== internal_bridge_speed ==================
@pytest.mark.engine_params
def test_internal_bridge_speed(slice_and_export: Path, expected_internal_bridge_speed: str):
    """验证内部桥接速度及百分比换算。

    C3DSlicer 在 ``GCode.cpp`` 中优先使用 ``internal_bridge_speed``，百分比以
    ``bridge_speed`` 为基准；规划读取 Internal Bridge 段 ``F`` 值并验证
    ``实际速度 = bridge_speed × 百分比``。3MF 使用长直的内部空腔顶板。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_internal_bridge_speed(gcode_path, expected_internal_bridge_speed)
    assert ok, f"internal_bridge_speed expected {expected_internal_bridge_speed}, actual {actual}, details: {details}"


# ================== counterbore_hole_bridging ==================
@pytest.mark.engine_params
def test_counterbore_hole_bridging(slice_and_export: Path, expected_counterbore_hole_bridging: str):
    """验证沉孔底部的桥接处理模式。

    C3DSlicer 在 ``PerimeterGenerator.cpp`` 中对 none/partiallybridge/sacrificiallayer
    生成不同的沉孔底面路径；规划比较沉孔台阶层的 Bridge 面积、桥接线和牺牲层覆盖范围。
    3MF 使用竖直圆孔加明确台阶的 counterbore，孔径和台阶宽度均大于 6 mm。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_counterbore_hole_bridging(gcode_path, expected_counterbore_hole_bridging)
    assert ok, f"counterbore_hole_bridging expected {expected_counterbore_hole_bridging}, actual {actual}, details: {details}"
