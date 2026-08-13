from __future__ import annotations
from pathlib import Path
import pytest
from engine_params.src.gcode.process.strength.fill_check import (
    GapFillTarget,
    parse_gap_fill_target,
    parse_filter_out_gap_fill,
    parse_anchor_line,
    parse_sparse_infill_pattern,
    parse_rectilinear_path_continuity,
    parse_ai_infill,
    parse_sparse_infill_density,
    parse_internal_solid_infill_pattern,
    parse_infill_direction,
    parse_top_surface_pattern,
    parse_bottom_surface_pattern,
    parse_solid_infill_direction,
    parse_rotate_solid_infill_direction,
    parse_infill_wall_overlap,
    parse_tmps_start_infill_density,
    parse_tmps_end_infill_density,
    parse_tpms_gradual_direction
)

# ================== gap_fill_target ==================
@pytest.mark.engine_params
def test_gap_fill_target(
        slice_and_export: Path,
        expected_target: str,
):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()
    ok, actual_target, details, warnings = parse_gap_fill_target(
        gcode_path,
        expected_target= GapFillTarget.from_str(expected_target),
    )
    assert ok, (
        f"gap_fill_target expected {expected_target}, actual {actual_target}, details: {details}"
    )
    if expected_target != GapFillTarget.EVERYWHERE:
        assert not warnings, f"unexpected warnings for target {expected_target}: {warnings}"


# ================== filter_out_gap_fill ==================
@pytest.mark.engine_params
def test_filter_out_gap_fill(
        slice_and_export: Path,
        expected_value: float,
):
    # 验证方法：使用实体、薄壁、桥接或填充专用 3MF切片，解析各层填充类型、路径方向、间距及正向挤出量；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual_value, details = parse_filter_out_gap_fill(
        gcode_path,
        expected_value=expected_value,
    )

    assert ok, (
        f"filter_out_gap_fill expected {expected_value}, actual {actual_value}, details: {details}"
    )


# ================== infill_anchor && infill_anchor_max ==================
@pytest.mark.engine_params
def test_anchor_line(
        slice_and_export: Path,
        expected_point_line: float,
        expected_anchor_line: float,
        threshold: float,
) -> None:
    # 验证方法：使用实体、薄壁、桥接或填充专用 3MF切片，解析目标特征的 G-code 类型块、运动指令和尾部配置；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual_value, details = parse_anchor_line(
        gcode_path,
        threshold,
        point_line=expected_point_line,
        anchor_line=expected_anchor_line,
    )

    assert ok, (
        f"infill_anchor/anchor_line check failed: "
        f"threshold={threshold}, point_line_expect={expected_point_line}, "
        f"anchor_line_expect={expected_anchor_line}, "
        f"actual_op_anchor_line={actual_value}, details={details}"
    )


# ================== sparse_infill_pattern ==================
@pytest.mark.engine_params
def test_sparse_infill_pattern(
        slice_and_export: Path,
        expected_match: bool,
        baseline_gcode: str,
) -> None:
    """验证 Sparse infill 图案确实形成对应的 G-code 行为。

    先核对图案配置身份和实际稀疏填充挤出，再与基线比较填充层覆盖、总路径
    长度、包围盒及 15° 方向直方图。允许算法改变折线分段和起点顺序。
    Lightning 不使用随机坐标快照，改查树枝路径随高度分叉增长。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual_match, details = parse_sparse_infill_pattern(
        gcode_path,
        baseline_gcode,
        tolerance=1e-6,
        object_id=0,
    )

    assert ok, (
        f"sparse_infill_pattern expected {expected_match}, actual {actual_match}, details: {details}"
    )
    assert actual_match == expected_match, (
        f"Pattern match result mismatch: expected {expected_match}, got {actual_match}"
    )


# ================== rectilinear_path_continuity ==================
@pytest.mark.engine_params
def test_rectilinear_path_continuity(
        slice_and_export: Path,
        expected_max_block_lines: int,
        expected_max_retractions: int,
        expected_max_wipe_sections: int,
        expected_max_z_hop_travels: int,
) -> None:
    """防止 fill_multiline=1 的复杂岛被多线连接器拆成大量短路径。"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, details = parse_rectilinear_path_continuity(
        gcode_path,
        max_block_lines=expected_max_block_lines,
        max_retractions=expected_max_retractions,
        max_wipe_sections=expected_max_wipe_sections,
        max_z_hop_travels=expected_max_z_hop_travels,
    )

    assert ok, f"rectilinear path continuity regression: {details}"


# ================== bottom_surface_pattern ==================


@pytest.mark.engine_params
def test_bottom_surface_pattern(
        slice_and_export: Path,
        expected_match: bool,
        baseline_gcode: str,
) -> None:
    # 验证方法：使用实体、薄壁、桥接或填充专用 3MF切片，解析Top/Bottom surface 连续层数、厚度和路径形态；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual_match, details = parse_bottom_surface_pattern(
        gcode_path,
        baseline_gcode,
        tolerance=1e-6,
        object_id=0,
    )

    assert ok, (
        f"bottom_surface_pattern expected {expected_match}, actual {actual_match}, details: {details}"
    )
    assert actual_match == expected_match, (
        f"Pattern match result mismatch: expected {expected_match}, got {actual_match}"
    )


# ================== ai_infill ==================


@pytest.mark.engine_params
def test_ai_infill(
        slice_and_export: Path,
        expected_match: bool,
        baseline_gcode: str,
) -> None:
    """
    测试ai_infill参数是否有效，采用快照对比的方式。
    """
    # 验证方法：使用实体、薄壁、桥接或填充专用 3MF切片，解析各层填充类型、路径方向、间距及正向挤出量；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual_match, details = parse_ai_infill(
        gcode_path,
        baseline_gcode,
        tolerance=1e-6,
        object_id=0,
    )

    assert ok, (
        f"ai_infill expected {expected_match}, actual {actual_match}, details: {details}"
    )
    assert actual_match == expected_match, (
        f"Pattern match result mismatch: expected {expected_match}, got {actual_match}"
    )


# ================== infill_direction ==================


@pytest.mark.engine_params
def test_infill_direction(
        slice_and_export: Path,
        expected_angle: float,
):
    # 验证方法：使用实体、薄壁、桥接或填充专用 3MF切片，解析各层填充类型、路径方向、间距及正向挤出量；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual_angle, details = parse_infill_direction(
        gcode_path,
        expected_angle,
        tolerance=0.2,
        object_id=0,
    )

    assert ok, (
        f"infill_direction expected {expected_angle}°, actual {actual_angle:.2f}°, details: {details}"
    )


# ================== internal_solid_infill_pattern ==================


@pytest.mark.engine_params
def test_internal_solid_infill_pattern(
        slice_and_export: Path,
        expected_match: bool,
        baseline_gcode: str,
) -> None:
    # 验证方法：使用实体、薄壁、桥接或填充专用 3MF切片，解析各层填充类型、路径方向、间距及正向挤出量；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual_match, details = parse_internal_solid_infill_pattern(
        gcode_path,
        baseline_gcode,
        tolerance=1e-6,
        object_id=0,
    )

    assert ok, (
        f"internal_solid_infill_pattern expected {expected_match}, actual {actual_match}, details: {details}"
    )
    assert actual_match == expected_match, (
        f"Pattern match result mismatch: expected {expected_match}, got {actual_match}"
    )


# ================== solid_infill_direction ==================


@pytest.mark.engine_params
def test_solid_infill_direction(
        slice_and_export: Path,
        expected_angle: float,
):
    # 验证方法：使用实体、薄壁、桥接或填充专用 3MF切片，解析各层填充类型、路径方向、间距及正向挤出量；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual_angle, details = parse_solid_infill_direction(
        gcode_path,
        expected_angle,
        tolerance=0.2,
        object_id=0,
    )

    assert ok, (
        f"solid_infill_direction expected {expected_angle}°, actual average angle:{actual_angle:.2f}°, details: {details}"
    )


# ================== sparse_infill_density ==================


@pytest.mark.engine_params
def test_sparse_infill_density(
        slice_and_export: Path,
        expected_match: bool,
        baseline_gcode: str,
) -> None:
    # 验证方法：使用实体、薄壁、桥接或填充专用 3MF切片，解析各层填充类型、路径方向、间距及正向挤出量；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual_match, details = parse_sparse_infill_density(
        gcode_path,
        baseline_gcode,
        tolerance=1e-6,
        object_id=0,
    )

    assert ok, (
        f"sparse_infill_density expected {expected_match}, actual {actual_match}, details: {details}"
    )
    assert actual_match == expected_match, (
        f"Pattern match result mismatch: expected {expected_match}, got {actual_match}"
    )


# ================== rotate_solid_infill_direction ==================


@pytest.mark.engine_params
def test_rotate_solid_infill_direction(
        slice_and_export: Path,
        expected_value: bool,
):
    # 验证方法：使用实体、薄壁、桥接或填充专用 3MF切片，解析各层填充类型、路径方向、间距及正向挤出量；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual_value, details = parse_rotate_solid_infill_direction(
        gcode_path,
        expected_value,
        tolerance=0.2,
        object_id=0,
    )

    assert ok, (
        f"rotate_solid_infill_direction expected {expected_value}, actual {actual_value}, details: {details}"
    )
    assert actual_value == expected_value, (
        f"Rotation state mismatch: expected {expected_value}, got {actual_value}"
    )

# ================== top_surface_pattern ==================

@pytest.mark.engine_params
def test_top_surface_pattern(
        slice_and_export: Path,
        expected_match: bool,
        baseline_gcode: str,
) -> None:
    """核对顶面图案配置和真实 Top surface 路径行为。

    与基线比较顶面层覆盖、路径总长、打印边界和方向分布，不比较折线点数及
    坐标顺序；因此 Octagram spiral 的合法重新分段不会造成误报。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual_match, details = parse_top_surface_pattern(
        gcode_path,
        baseline_gcode,
        tolerance=1e-6,
        object_id=0,
    )

    assert ok, (
        f"top_surface_pattern expected {expected_match}, actual {actual_match}, details: {details}"
    )
    assert actual_match == expected_match, (
        f"Pattern match result mismatch: expected {expected_match}, got {actual_match}"
    )
# ================== infill_wall_overlap ==================
@pytest.mark.engine_params
def test_infill_wall_overlap(
        slice_and_export: Path,
        baseline_gcode: str | Path,
) -> None:
    # 验证方法：使用实体、薄壁、桥接或填充专用 3MF切片，解析各层填充类型、路径方向、间距及正向挤出量；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    baseline_path = Path(baseline_gcode)
    assert baseline_path.exists()

    ok, details = parse_infill_wall_overlap(
        gcode_path,
        baseline_gcode_path=baseline_path,
    )

    assert ok, (
        "infill_wall_overlap snapshot mismatch: "
        f"baseline={details.get('baseline_gcode')}, "
        f"mismatches={details.get('mismatch_layers')}, errors={details.get('errors')}"
    )

# ================== tmps_start_infill_density ==================
@pytest.mark.engine_params
def test_tmps_start_infill_density(
        slice_and_export: Path,
        expected_match: bool,
        baseline_gcode: str,
) -> None:
    # 验证方法：使用实体、薄壁、桥接或填充专用 3MF切片，解析各层填充类型、路径方向、间距及正向挤出量；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual_match, details = parse_tmps_start_infill_density(
        gcode_path,
        baseline_gcode,
        tolerance=1e-6,
        object_id=0,
    )

    assert ok, (
        f"tmps_start_infill_density expected {expected_match}, actual {actual_match}, details: {details}"
    )
    assert actual_match == expected_match, (
        f"Pattern match result mismatch: expected {expected_match}, got {actual_match}"
    )

# ================== tmps_end_infill_density ==================
@pytest.mark.engine_params
def test_tmps_end_infill_density(
        slice_and_export: Path,
        expected_match: bool,
        baseline_gcode: str,
) -> None:
    # 验证方法：使用实体、薄壁、桥接或填充专用 3MF切片，解析各层填充类型、路径方向、间距及正向挤出量；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual_match, details = parse_tmps_end_infill_density(
        gcode_path,
        baseline_gcode,
        tolerance=1e-6,
        object_id=0,
    )

    assert ok, (
        f"tmps_end_infill_density expected {expected_match}, actual {actual_match}, details: {details}"
    )
    assert actual_match == expected_match, (
        f"Pattern match result mismatch: expected {expected_match}, got {actual_match}"
    )

# ================== tpms_gradual_direction ==================
@pytest.mark.engine_params
def test_tpms_gradual_direction(
        slice_and_export: Path,
        expected_match: bool,
        baseline_gcode: str,
) -> None:
    """验证 TPMS 渐变方向对稀疏填充路径的实际作用。

    核对 ``tpms_gradual_direction`` 配置，并与对应方向基线比较稀疏填充的
    有效层、路径长度、边界和逐段方向分布；允许新版 TPMS 将曲线重新分段。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual_match, details = parse_tpms_gradual_direction(
        gcode_path,
        baseline_gcode,
        tolerance=1e-6,
        object_id=0,
    )

    assert ok, (
        f"tpms_gradual_direction expected {expected_match}, actual {actual_match}, details: {details}"
    )
    assert actual_match == expected_match, (
        f"Pattern match result mismatch: expected {expected_match}, got {actual_match}"
    )
