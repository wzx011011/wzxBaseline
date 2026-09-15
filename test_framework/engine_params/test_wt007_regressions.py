"""TC-WT-007 regressions; pure Python, no slicer or build required."""

import json
from pathlib import Path
from zipfile import ZipFile

import pytest

from engine_params.src.gcode.process.filament.prime_tower_gcode_check_wt007 import (
    _restart_extra,
    _within_tolerance,
    parse_tc_wt_007,
)


def test_legacy_extra_alias_and_explicit_key_precedence():
    assert _restart_extra({"extra": 0.2}) == 0.2
    assert _restart_extra({"extra": 0.3, "retract_restart_extra": 0.5}) == 0.5
    assert _restart_extra({}) == 0.0


def _check(tmp_path, loading="6.2", tail=None, params=None):
    code = "M83\nT0\nG1 E-6\nT1\n"
    if loading is not None:
        code += f"G1 E{loading} F1800\n"
    if tail is not None:
        code += "G1 X10 E1\n" + tail + "\n; WIPE_TOWER_END\n"
    path = tmp_path / "wt007.gcode"
    path.write_text(code, encoding="utf-8")
    expected = {
        "tool_params": {
            "T0": {"retraction_length": 6, "retract_restart_extra": 0.2},
            "T1": params or {"retraction_length": 8, "retract_restart_extra": 0.5},
        },
        "check_points": ["after_change"],
    }
    if tail is not None:
        expected["check_points"].append("after_infill_retract")
    return parse_tc_wt_007(path, json.dumps(expected))


@pytest.mark.parametrize("loading,passed", [
    ("6.2", True), ("6.21", True), ("6.19", True),
    ("6.2101", False), ("6.1899", False),
    ("6", False), ("8.5", False), (None, False),
])
def test_loading_includes_previous_tool_extra_and_rejects_missing_data(tmp_path, loading, passed):
    ok, _, details = _check(tmp_path, loading)
    assert ok is passed, details


@pytest.mark.parametrize("actual,expected,tolerance,passed", [
    (6.2, 6, 0.2, True), (6.4, 6.2, 0.2, True),
    (6.4001, 6.2, 0.2, False), (6.21, 6.2, 0.01, True),
    (6, 6.2, 0.01, False), (float("nan"), 6.2, 0.01, False),
    (float("inf"), 6.2, 0.01, False),
])
def test_inclusive_tolerance(actual, expected, tolerance, passed):
    assert _within_tolerance(actual, expected, tolerance) is passed


@pytest.mark.parametrize("extra", [0.0, 0.2, 0.5])
def test_restart_extra_does_not_change_wipe_ratio(tmp_path, extra):
    params = {
        "retraction_length": 8, "retract_restart_extra": extra,
        "retract_before_wipe": 0.7,
        "after_infill_retract": {"first": 5.6, "second": 2.28, "third": 0.12},
    }
    ok, _, details = _check(tmp_path, tail="G1 E-5.6\nG1 X12 E-2.28\nG1 E-.12", params=params)
    assert ok, details


def test_wrong_wipe_ratio_fails_even_when_total_is_correct(tmp_path):
    params = {"retraction_length": 8, "retract_before_wipe": 0.7}
    ok, _, details = _check(tmp_path, tail="G1 E-6.4\nG1 X12 E-1.52\nG1 E-.08", params=params)
    assert not ok
    assert any("擦拭回抽比例不符" in failure for failure in details["failures"])


@pytest.mark.parametrize("tail,passed", [
    ("G1 E-6", True), ("G1 E-5.8", False), ("G1 X12", False),
    ("G1 E-3\nG1 E-3", False),
    ("T0\nG1 E-6", False),
])
def test_single_infill_retraction_is_checked(tmp_path, tail, passed):
    params = {
        "retraction_length": 6, "retract_before_wipe": 1.0,
        "after_infill_retract": {"single": 6},
    }
    ok, _, details = _check(tmp_path, tail=tail, params=params)
    assert ok is passed, details


def test_ratio_is_checked_at_later_tool_changes(tmp_path):
    params = {"retraction_length": 8, "retract_before_wipe": 0.7}
    _check(tmp_path, tail="G1 E-5.6\nG1 X12 E-2.28\nG1 E-.12", params=params)
    path = tmp_path / "wt007.gcode"
    path.write_text(path.read_text(encoding="utf-8") +
                    "T0\nG1 E-6\nT1\nG1 E6.2\nG1 X10 E1\n"
                    "G1 E-6.4\nG1 X12 E-1.52\nG1 E-.08\n; WIPE_TOWER_END\n",
                    encoding="utf-8")
    expected = {"tool_params": {"T1": params}, "check_points": ["after_infill_retract"]}
    ok, _, details = parse_tc_wt_007(path, json.dumps(expected))
    assert not ok
    assert details["tool_change_count"] == 2
    assert len(details["failures"]) == 1
    assert "换料点1" in details["failures"][0]


def test_case_parameters_match_project_settings():
    root = Path(__file__).parent / "data"
    cases = json.loads((root / "case_input/process/filament/prime_tower/tc_wt_007.json").read_text(encoding="utf-8"))["cases"]
    for case in cases:
        project = root / "models/process/filament/prime_tower/tc_wt_007" / case["input_3mf"]
        with ZipFile(project) as archive:
            config = json.loads(archive.read("Metadata/project_settings.config"))
        expected = json.loads(case["expected_value"])
        for i, tool in enumerate(("T0", "T1")):
            params = expected["tool_params"][tool]
            assert params["retraction_length"] == float(config["filament_retraction_length"][i])
            assert params["retract_restart_extra"] == float(config["filament_retract_restart_extra"][i])
            assert params["retract_before_wipe"] == float(config["filament_retract_before_wipe"][i].rstrip("%")) / 100
