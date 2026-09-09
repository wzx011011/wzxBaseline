"""Exercise the actual snapshot cases against perturbed checked-in G-code."""

import json
import re
from pathlib import Path

import pytest

from engine_params.case.params.process.strength import test_fill as fill_cases
from engine_params.case.params.process.strength import test_advance as advance_cases
from engine_params.case.params.process.strength import test_top_or_bottom_shells as shell_cases
from engine_params.src.gcode.process.strength.fill_check import parse_internal_solid_infill_pattern
from engine_params.src.testing_utils.tolerances import GCODE_COORDINATE_TOLERANCE_MM


MODELS = Path(__file__).parent / "data/models/process/strength"
CASES = [
    (fill_cases.test_bottom_surface_pattern, "fill/bottom_surface_pattern/baseline_bottomsf_rectilinear.gcode", True),
    (fill_cases.test_internal_solid_infill_pattern, "fill/internal_solid_infill_pattern/baseline_sip_rectilinear.gcode", True),
    (fill_cases.test_sparse_infill_density, "fill/sparse_infill_density/baseline_50%_noai_concentric.gcode", True),
    (fill_cases.test_ai_infill, "fill/ai_infill/baseline_25%_ai_rectilinear.gcode", True),
    (fill_cases.test_tmps_start_infill_density, "fill/tmps_start_infill_density/baseline_tmps_start_infill_density_25.gcode", True),
    (fill_cases.test_tmps_end_infill_density, "fill/tmps_end_infill_density/baseline_tmps_end_infill_density_99.gcode", True),
    (fill_cases.test_infill_wall_overlap, "fill/infill_wall_overlap/baseline_infill_wall_overlap_100percentage.gcode", False),
    (shell_cases.test_top_bottom_infill_wall_overlap, "top_or_bottom_shells/top_bottom_infill_wall_overlap/top_bottom_infill_wall_overlap_100percentage.gcode", False),
]


def _shift_xy(baseline, target, delta):
    lines = []
    for raw in baseline.read_text(encoding="utf-8").splitlines():
        if re.match(r"^G[0123]\s", raw):
            body, separator, comment = raw.partition(";")
            body = re.sub(r"\b([XY])(-?\d+(?:\.\d*)?)",
                          lambda m: f"{m[1]}{float(m[2])+delta:.6f}", body)
            raw = body + separator + comment
        lines.append(raw)
    target.write_text("\n".join(lines), encoding="utf-8")


@pytest.mark.parametrize("case,relative,has_expected", CASES, ids=[c[0].__name__ for c in CASES])
@pytest.mark.parametrize("delta", [-.002, -.001, .001, .002])
def test_snapshot_cases_accept_only_one_coordinate_quantum(tmp_path, case, relative, has_expected, delta):
    baseline = MODELS / relative
    target = tmp_path / "shifted.gcode"
    _shift_xy(baseline, target, delta)
    args = (target, True, str(baseline)) if has_expected else (target, baseline)
    if abs(delta) <= .001:
        case(*args)
    else:
        with pytest.raises(AssertionError):
            case(*args)


def test_low_level_comparator_keeps_explicit_strict_tolerance(tmp_path):
    baseline = MODELS / "fill/internal_solid_infill_pattern/baseline_sip_rectilinear.gcode"
    target = tmp_path / "strict.gcode"
    _shift_xy(baseline, target, .001)
    assert not parse_internal_solid_infill_pattern(target, baseline, tolerance=1e-6)[0]


def test_coordinate_tolerance_does_not_allow_extra_points(tmp_path):
    baseline = MODELS / "fill/internal_solid_infill_pattern/baseline_sip_rectilinear.gcode"
    target = tmp_path / "extra-points.gcode"
    lines = baseline.read_text(encoding="utf-8").splitlines()
    changed = []
    inserted = 0
    for line in lines:
        if re.match(r"^G1 .*\bX", line) and re.search(r"\bE(?:[0-9]|\.)", line):
            # Add a distinct point inside the coordinate tolerance: rejection
            # must come from topology, not the size of the coordinate offset.
            changed.append(re.sub(r"\bX(-?\d+(?:\.\d*)?)",
                                  lambda m: f"X{float(m[1])+.0005:.6f}", line))
            inserted += 1
        changed.append(line)
    assert inserted > 0
    target.write_text("\n".join(changed), encoding="utf-8")
    ok, _, _ = parse_internal_solid_infill_pattern(
        target, baseline, tolerance=GCODE_COORDINATE_TOLERANCE_MM)
    assert not ok


SHELL_CASES = json.loads((Path(__file__).parent / "data/case_input/process/strength/advance/ensure_vertical_shell_thickness.json")
                        .read_text(encoding="utf-8"))["cases"]


@pytest.mark.parametrize("case", SHELL_CASES, ids=[case["project_name"] for case in SHELL_CASES])
@pytest.mark.parametrize("delta", [-.002, -.001, .001, .002])
def test_vertical_shell_case_tolerance_is_one_output_quantum(tmp_path, case, delta):
    baseline = MODELS / "advance/ensure_vertical_shell_thickness" / case["baseline_gcode"]
    target = tmp_path / "shell.gcode"
    _shift_xy(baseline, target, delta)
    assert case["tolerance"] == pytest.approx(GCODE_COORDINATE_TOLERANCE_MM, abs=1e-12)
    args = (target, case["expected_ensure_vertical_shell_thickness"], baseline, case["tolerance"])
    if abs(delta) <= .001:
        advance_cases.test_ensure_vertical_shell_thickness(*args)
    else:
        with pytest.raises(AssertionError):
            advance_cases.test_ensure_vertical_shell_thickness(*args)
