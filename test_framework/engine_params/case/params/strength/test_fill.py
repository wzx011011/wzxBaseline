from __future__ import annotations
from pathlib import Path
import pytest
from engine_params.src.gcode.Strength.fill_check import (
    GapFillTarget,
    parse_gap_fill_target,
    parse_filter_out_gap_fill,
    parse_anchor_line,
    parse_sparse_infill_pattern,
    parse_ai_infill,
    parse_sparse_infill_density,
    parse_internal_solid_infill_pattern,
    parse_infill_direction,
    parse_top_surface_pattern,
    parse_bottom_surface_pattern,
    parse_solid_infill_direction,
    parse_rotate_solid_infill_direction
)

# ================== gap_fill_target ==================
slice_cases = [
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\gap_fill_target_001.3mf",
        "project_name": "gap_fill_target_nowhere",
    },
]
expectations = [
    GapFillTarget.NOWHERE,
]
params = [
    pytest.param(sc, exp, id=sc.get("project_name"))
    for sc, exp in zip(slice_cases, expectations)
]


@pytest.mark.engine_params
@pytest.mark.parametrize(
    ("slice_and_export", "expected_target"),
    params,
    indirect=["slice_and_export"],
)
def test_gap_fill_target(
        slice_and_export: Path,
        expected_target: GapFillTarget,
):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()
    ok, actual_target, details, warnings = parse_gap_fill_target(
        gcode_path,
        expected_target=expected_target,
    )
    assert ok, (
        f"gap_fill_target expected {expected_target}, actual {actual_target}, details: {details}"
    )
    if expected_target != GapFillTarget.EVERYWHERE:
        assert not warnings, f"unexpected warnings for target {expected_target}: {warnings}"


# ================== filter_out_gap_fill ==================
slice_cases_filter = [
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\filter_out_gap_fill_001.3mf",
        "project_name": "filter_out_gap_fill",
    },
]
expectations_filter = [
    5.0,
]
params_filter = [
    pytest.param(sc, exp, id=sc.get("project_name"))
    for sc, exp in zip(slice_cases_filter, expectations_filter)
]


@pytest.mark.engine_params
@pytest.mark.parametrize(
    ("slice_and_export", "expected_value"),
    params_filter,
    indirect=["slice_and_export"],
)
def test_filter_out_gap_fill(
        slice_and_export: Path,
        expected_value: float,
):
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
slice_cases_anchor = [
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\infill_anchor_001.3mf",
        "project_name": "test infill_anchor and infill_anchor_max",
    },
]
expectations_anchor = [
    (
        18.216,  # 阈值长度 threshold
        0,  # point line 的期望长度
        2,  # anchor line 的期望长度
    ),
]
params_anchor = [
    pytest.param(sc, *exp, id=sc.get("project_name"))
    for sc, exp in zip(slice_cases_anchor, expectations_anchor)
]


@pytest.mark.engine_params
@pytest.mark.parametrize(
    ("slice_and_export", "threshold", "point_line", "anchor_line"),
    params_anchor,
    indirect=["slice_and_export"],
)
def test_anchor_line(
        slice_and_export: Path,
        threshold: float,
        point_line: float,
        anchor_line: float,
):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual_value, details = parse_anchor_line(
        gcode_path,
        threshold,
        point_line=point_line,
        anchor_line=anchor_line,
    )

    assert ok, (
        f"infill_anchor/anchor_line check failed: "
        f"threshold={threshold}, point_line_expect={point_line}, anchor_line_expect={anchor_line}, "
        f"actual_op_anchor_line={actual_value}, details={details}"
    )


# ================== sparse_infill_pattern ==================
sparse_infill_pattern_cases = [
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\25%_noai_3dhoneycomp.3mf",
        "project_name": "sparse_infill_pattern_3dhoneycomp",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\25%_noai_adapativecubic.3mf",
        "project_name": "sparse_infill_pattern_adapativecubic",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\25%_noai_aligned_rectilinear.3mf",
        "project_name": "sparse_infill_pattern_aligned_rectilinear",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\25%_noai_archimedean_chords.3mf",
        "project_name": "sparse_infill_pattern_archimedean_chords",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\25%_noai_concentric.3mf",
        "project_name": "sparse_infill_pattern_concentric",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\25%_noai_cross.3mf",
        "project_name": "sparse_infill_pattern_cross",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\25%_noai_cross3d.3mf",
        "project_name": "sparse_infill_pattern_cross3d",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\25%_noai_crosshatch.3mf",
        "project_name": "sparse_infill_pattern_crosshatch",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\25%_noai_cubic.3mf",
        "project_name": "sparse_infill_pattern_cubic",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\25%_noai_grid.3mf",
        "project_name": "sparse_infill_pattern_grid",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\25%_noai_gtpmsd.3mf",
        "project_name": "sparse_infill_pattern_gtpmsd",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\25%_noai_gtpmsfks.3mf",
        "project_name": "sparse_infill_pattern_gtpmsfks",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\25%_noai_gtpmsg.3mf",
        "project_name": "sparse_infill_pattern_gtpmsg",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\25%_noai_gyroid.3mf",
        "project_name": "sparse_infill_pattern_gyroid",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\25%_noai_hilbert_curve.3mf",
        "project_name": "sparse_infill_pattern_hilbert_curve",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\25%_noai_honeycomp.3mf",
        "project_name": "sparse_infill_pattern_honeycomp",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\25%_noai_lightning.3mf",
        "project_name": "sparse_infill_pattern_lightning",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\25%_noai_line.3mf",
        "project_name": "sparse_infill_pattern_line",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\25%_noai_octagram_spiral.3mf",
        "project_name": "sparse_infill_pattern_octagram_spiral",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\25%_noai_quarter_cubic.3mf",
        "project_name": "sparse_infill_pattern_quarter_cubic",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\25%_noai_rectilinear.3mf",
        "project_name": "sparse_infill_pattern_rectilinear",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\25%_noai_support_cubic.3mf",
        "project_name": "sparse_infill_pattern_support_cubic",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\25%_noai_tetrahedral.3mf",
        "project_name": "sparse_infill_pattern_tetrahedral",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\25%_noai_tpmsd.3mf",
        "project_name": "sparse_infill_pattern_tpmsd",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\25%_noai_triangles.3mf",
        "project_name": "sparse_infill_pattern_triangles",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\25%_noai_trihexagon.3mf",
        "project_name": "sparse_infill_pattern_trihexagon",
    },
]
sparse_infill_pattern_expectations = [
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_25%_noai_3dhoneycomp.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_25%_noai_adapativecubic.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_25%_noai_aligned_rectilinear.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_25%_noai_archimedean_chords.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_25%_noai_concentric.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_25%_noai_cross.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_25%_noai_cross3d.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_25%_noai_crosshatch.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_25%_noai_cubic.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_25%_noai_grid.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_25%_noai_gtpmsd.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_25%_noai_gtpmsfks.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_25%_noai_gtpmsg.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_25%_noai_gyroid.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_25%_noai_hilbert_curve.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_25%_noai_honeycomp.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_25%_noai_lightning.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_25%_noai_line.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_25%_noai_octagram_spiral.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_25%_noai_quarter_cubic.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_25%_noai_rectilinear.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_25%_noai_support_cubic.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_25%_noai_tetrahedral.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_25%_noai_tpmsd.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_25%_noai_triangles.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_25%_noai_trihexagon.gcode",
     True),
]
sparse_infill_pattern_params = [
    pytest.param(sc, *exp, id=sc.get("project_name"))
    for sc, exp in zip(
        sparse_infill_pattern_cases,
        sparse_infill_pattern_expectations
    )
]

@pytest.mark.engine_params
@pytest.mark.parametrize(
    ("slice_and_export", "baseline_gcode", "expected_match"),
    sparse_infill_pattern_params,
    indirect=["slice_and_export"],
)
def test_sparse_infill_pattern(
        slice_and_export: Path,
        baseline_gcode: str,
        expected_match: bool,
):
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


# ================== bottom_surface_pattern ==================
bottom_surface_pattern_cases = [
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\bottomsf_aligned_rectilinear.3mf",
        "project_name": "bottom_surface_aligned_rectilinear"
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\bottomsf_concentric.3mf",
        "project_name": "bottom_surface_concentric"
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\bottomsf_hilbert_curve.3mf",
        "project_name": "bottom_surface_hilbert_curve"
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\bottomsf_monotonic.3mf",
        "project_name": "bottom_surface_monotonic"
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\bottomsf_rectilinear.3mf",
        "project_name": "bottom_surface_rectilinear"
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\bottomsf_archimedean_chords.3mf",
        "project_name": "bottom_surface_archimedean_chords"
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\bottomsf_monotonic_line.3mf",
        "project_name": "bottom_surface_monotonic_line"
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\bottomsf_octagram_spiral.3mf",
        "project_name": "bottom_surface_octagram_spiral"
    },
]
bottom_surface_pattern_expectations = [
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_bottomsf_aligned_rectilinear.gcode", True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_bottomsf_concentric.gcode", True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_bottomsf_hilbert_curve.gcode", True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_bottomsf_monotonic.gcode", True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_bottomsf_rectilinear.gcode", True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_bottomsf_archimedean_chords.gcode", True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_bottomsf_monotonic_line.gcode", True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_bottomsf_octagram_spiral.gcode", True),
]
bottom_surface_pattern_params = [
    pytest.param(sc, *exp, id=sc.get("project_name"))
    for sc, exp in zip(
        bottom_surface_pattern_cases,
        bottom_surface_pattern_expectations
    )
]


@pytest.mark.engine_params
@pytest.mark.parametrize(
    ("slice_and_export", "baseline_gcode", "expected_match"),
    bottom_surface_pattern_params,
    indirect=["slice_and_export"],
)
def test_bottom_surface_pattern(
        slice_and_export: Path,
        baseline_gcode: str,
        expected_match: bool,
):
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
ai_infill_cases = [
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\25%_ai_cubic.3mf",
        "project_name": "AI infill cubic @25%"
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\25%_ai_rectilinear.3mf",
        "project_name": "AI infill rectilinear @25%"
    },
]
ai_infill_expectations = [
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_25%_ai_cubic.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_25%_ai_rectilinear.gcode",
     True),
]
ai_infill_params = [
    pytest.param(sc, *exp, id=sc.get("project_name"))
    for sc, exp in zip(
        ai_infill_cases,
        ai_infill_expectations
    )
]


@pytest.mark.engine_params
@pytest.mark.parametrize(
    ("slice_and_export", "baseline_gcode", "expected_match"),
    ai_infill_params,
    indirect=["slice_and_export"],
)
def test_ai_infill(
        slice_and_export: Path,
        baseline_gcode: str,
        expected_match: bool,
):
    """
    测试ai_infill参数是否有效，采用快照对比的方式。
    """
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
infill_direction_cases = [
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\infill_direction_60degree.3mf",
        "project_name": "infill_direction_60_degree",
    },
]
infill_direction_expectations = [
    60.0,
]
infill_direction_params = [
    pytest.param(sc, exp, id=sc.get("project_name"))
    for sc, exp in zip(
        infill_direction_cases,
        infill_direction_expectations
    )
]


@pytest.mark.engine_params
@pytest.mark.parametrize(
    ("slice_and_export", "expected_angle"),
    infill_direction_params,
    indirect=["slice_and_export"],
)
def test_infill_direction(
        slice_and_export: Path,
        expected_angle: float,
):
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
internal_solid_infill_pattern_cases = [
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\sip_aligned_rectilinear.3mf",
        "project_name": "internal_solid_infill_pattern_aligned_rectilinear",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\sip_archimedean_chords.3mf",
        "project_name": "internal_solid_infill_pattern_archimedean_chords",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\sip_concentric.3mf",
        "project_name": "internal_solid_infill_pattern_concentric",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\sip_hilbert_curve.3mf",
        "project_name": "internal_solid_infill_pattern_hilbert_curve",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\sip_monotonic.3mf",
        "project_name": "internal_solid_infill_pattern_monotonic",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\sip_monotonic_line.3mf",
        "project_name": "internal_solid_infill_pattern_monotonic_line",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\sip_octagram_spiral.3mf",
        "project_name": "internal_solid_infill_pattern_octagram_spiral",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\sip_rectilinear.3mf",
        "project_name": "internal_solid_infill_pattern_rectilinear",
    },
]
internal_solid_infill_pattern_expectations = [
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_sip_aligned_rectilinear.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_sip_archimedean_chords.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_sip_concentric.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_sip_hilbert_curve.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_sip_monotonic.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_sip_monotonic_line.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_sip_octagram_spiral.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_sip_rectilinear.gcode",
     True),
]
internal_solid_infill_pattern_params = [
    pytest.param(sc, *exp, id=sc.get("project_name"))
    for sc, exp in zip(
        internal_solid_infill_pattern_cases,
        internal_solid_infill_pattern_expectations
    )
]


@pytest.mark.engine_params
@pytest.mark.parametrize(
    ("slice_and_export", "baseline_gcode", "expected_match"),
    internal_solid_infill_pattern_params,
    indirect=["slice_and_export"],
)
def test_internal_solid_infill_pattern(
        slice_and_export: Path,
        baseline_gcode: str,
        expected_match: bool,
):
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
solid_infill_direction_cases = [
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\solid_infill_direction_0degree.3mf",
        "project_name": "solid_infill_direction_0_degree",
    },
]
solid_infill_direction_expectations = [
    0.0,
]
solid_infill_direction_params = [
    pytest.param(sc, exp, id=sc.get("project_name"))
    for sc, exp in zip(
        solid_infill_direction_cases,
        solid_infill_direction_expectations
    )
]


@pytest.mark.engine_params
@pytest.mark.parametrize(
    ("slice_and_export", "expected_angle"),
    solid_infill_direction_params,
    indirect=["slice_and_export"],
)
def test_solid_infill_direction(
        slice_and_export: Path,
        expected_angle: float,
):
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
sparse_infill_density_cases = [
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\50%_noai_concentric.3mf",
        "project_name": "Sparse infill density concentric @50%"
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\50%_noai_grid.3mf",
        "project_name": "Sparse infill density grid @50%"
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\50%_noai_hilbert_curve.3mf",
        "project_name": "Sparse infill density hilbert_curve @50%"
    },
]
sparse_infill_density_expectations = [
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_50%_noai_concentric.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_50%_noai_grid.gcode",
     True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_50%_noai_hilbert_curve.gcode",
     True),
]
sparse_infill_density_params = [
    pytest.param(sc, *exp, id=sc.get("project_name"))
    for sc, exp in zip(
        sparse_infill_density_cases,
        sparse_infill_density_expectations
    )
]


@pytest.mark.engine_params
@pytest.mark.parametrize(
    ("slice_and_export", "baseline_gcode", "expected_match"),
    sparse_infill_density_params,
    indirect=["slice_and_export"],
)
def test_sparse_infill_density(
        slice_and_export: Path,
        baseline_gcode: str,
        expected_match: bool,
):
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
rotate_solid_infill_direction_cases = [
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\rotate_solid_infill_direction_true.3mf",
        "project_name": "rotate_solid_infill_direction_true",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\rotate_solid_infill_direction_false.3mf",
        "project_name": "rotate_solid_infill_direction_false",
    },
]
rotate_solid_infill_direction_expectations = [
    True,
    False,
]
rotate_solid_infill_direction_params = [
    pytest.param(sc, exp, id=sc.get("project_name"))
    for sc, exp in zip(
        rotate_solid_infill_direction_cases,
        rotate_solid_infill_direction_expectations
    )
]


@pytest.mark.engine_params
@pytest.mark.parametrize(
    ("slice_and_export", "expected_value"),
    rotate_solid_infill_direction_params,
    indirect=["slice_and_export"],
)
def test_rotate_solid_infill_direction(
        slice_and_export: Path,
        expected_value: bool,
):
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
top_surface_pattern_cases = [
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\bottomsf_aligned_rectilinear.3mf",
        "project_name": "top_surface_aligned_rectilinear"
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\bottomsf_concentric.3mf",
        "project_name": "top_surface_concentric"
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\bottomsf_hilbert_curve.3mf",
        "project_name": "top_surface_hilbert_curve"
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\bottomsf_monotonic.3mf",
        "project_name": "top_surface_monotonic"
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\bottomsf_rectilinear.3mf",
        "project_name": "top_surface_rectilinear"
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\bottomsf_archimedean_chords.3mf",
        "project_name": "top_surface_archimedean_chords"
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\bottomsf_monotonic_line.3mf",
        "project_name": "top_surface_monotonic_line"
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\bottomsf_octagram_spiral.3mf",
        "project_name": "top_surface_octagram_spiral"
    },
]
top_surface_pattern_expectations = [
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_bottomsf_aligned_rectilinear.gcode", True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_bottomsf_concentric.gcode", True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_bottomsf_hilbert_curve.gcode", True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_bottomsf_monotonic.gcode", True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_bottomsf_rectilinear.gcode", True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_bottomsf_archimedean_chords.gcode", True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_bottomsf_monotonic_line.gcode", True),
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\baseline_bottomsf_octagram_spiral.gcode", True),
]
top_surface_pattern_params = [
    pytest.param(sc, *exp, id=sc.get("project_name"))
    for sc, exp in zip(
        top_surface_pattern_cases,
        top_surface_pattern_expectations
    )
]


@pytest.mark.engine_params
@pytest.mark.parametrize(
    ("slice_and_export", "baseline_gcode", "expected_match"),
    top_surface_pattern_params,
    indirect=["slice_and_export"],
)
def test_top_surface_pattern(
        slice_and_export: Path,
        baseline_gcode: str,
        expected_match: bool,
):
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
