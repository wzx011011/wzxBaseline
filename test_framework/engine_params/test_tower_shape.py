"""Regression tests for deposited tower geometry and effective shape settings."""

import json
from pathlib import Path
from zipfile import ZipFile

import pytest

from engine_params.src.gcode.process.filament.tower_shape import (
    extract_tower_paths, compare_tower_paths,
)
from engine_params.src.gcode.process.filament.filament_check import parse_prime_tower_enhance_type


def _gcode(tmp_path, code):
    path = tmp_path / "tower.gcode"
    path.write_text(code, encoding="utf-8")
    return path


def test_travel_retraction_and_non_tower_moves_do_not_change_shape(tmp_path):
    path = _gcode(tmp_path, """G90
M83
G0 X10 Y20 Z0.2
;TYPE:Prime tower
G1 X12 E1
G1 X1000 Y1000
G1 E-1
G0 X12 Y20
G1 E1
G1 Y22 E1
; WIPE_TOWER_END
G1 X999 E5
;TYPE:Internal infill
G1 X500 E5
""")
    segments = extract_tower_paths(path)
    assert len(segments) == 2
    assert segments[0]["min_x"] == 10
    assert segments[0]["max_x"] == 12
    assert segments[1]["max_y"] == 22
    assert {s["z"] for s in segments} == {0.2}


def test_absolute_extrusion_g92_and_relative_coordinates(tmp_path):
    path = _gcode(tmp_path, """G90
M82
G0 X10 Y20 Z0.2
G92 E100
; WIPE_TOWER_START
G1 X12 E101
G1 E100
G1 E101
G92 E0
G91
G1 Y2 E1
G90
M83
G1 X10 E0.5
""")
    segments = extract_tower_paths(path)
    assert [s["e"] for s in segments] == [1, 1, 0.5]
    assert [(s["x"], s["y"]) for s in segments] == [(12, 20), (12, 22), (10, 22)]


@pytest.mark.parametrize("command,ymin,ymax", [("G2", 0, 1), ("G3", -1, 0)])
def test_arc_extrema_and_direction(tmp_path, command, ymin, ymax):
    path = _gcode(tmp_path, f"M83\nG0 X-1 Y0 Z0.2\n;TYPE:Prime tower\n{command} X1 Y0 I1 J0 E1\n")
    segment, = extract_tower_paths(path)
    assert segment["min_y"] == pytest.approx(ymin, abs=1e-9)
    assert segment["max_y"] == pytest.approx(ymax, abs=1e-9)
    assert segment["min_x"] == -1 and segment["max_x"] == 1


@pytest.mark.parametrize("center_mode,center", [("G91.1", "I-1 J0"), ("G90.1", "I10 J20")])
def test_full_circle_and_center_modes(tmp_path, center_mode, center):
    path = _gcode(tmp_path, f"M83\nG0 X11 Y20 Z0.2\n{center_mode}\n;TYPE:Prime tower\nG3 {center} E1\n")
    segment, = extract_tower_paths(path)
    assert (segment["min_x"], segment["max_x"]) == (9, 11)
    assert (segment["min_y"], segment["max_y"]) == (19, 21)


@pytest.mark.parametrize("arc", ["G2 X2 R1 E1", "G3 X2 I0 J0 E1", "G3 X2 I1 P2 E1"])
def test_unsupported_or_invalid_arc_is_not_silently_dropped(tmp_path, arc):
    path = _gcode(tmp_path, f"M83\nG0 X0 Y0 Z0.2\n;TYPE:Prime tower\n{arc}\n")
    with pytest.raises(ValueError):
        extract_tower_paths(path)


def test_per_layer_profile_detects_same_global_box_with_wrong_taper():
    base = [{"x": 0, "y": 0, "z": 0.2}, {"x": 20, "y": 20, "z": 0.2},
            {"x": 0, "y": 0, "z": 1}, {"x": 10, "y": 10, "z": 1}]
    wrong = [dict(point) for point in base]
    wrong[-1]["x"] = 20
    ok, details = compare_tower_paths(base, wrong)
    assert not ok
    assert details["width_diff"] == 0
    assert details["layer_mismatch_count"] == 1
    assert not compare_tower_paths([], [])[0]


def test_effective_cone_angle_is_required_when_requested(tmp_path):
    path = _gcode(tmp_path, "; CONFIG_BLOCK_START\n; prime_tower_enhance_type = cone\n; wipe_tower_cone_angle = 0\n; CONFIG_BLOCK_END\n")
    assert parse_prime_tower_enhance_type(path, "cone")[0]
    ok, _, details = parse_prime_tower_enhance_type(path, "cone", expected_cone_angle=60)
    assert not ok and details["actual_cone_angle"] == 0


def test_arc_parse_failure_preserves_public_result_contract(tmp_path):
    path = _gcode(tmp_path, "; CONFIG_BLOCK_START\n; prime_tower_enhance_type = cone\n; CONFIG_BLOCK_END\n"
                 "M83\nG0 X0 Y0 Z0.2\n;TYPE:Prime tower\nG2 X2 R1 E1\n")
    ok, actual, details = parse_prime_tower_enhance_type(path, "cone", path)
    assert not ok and actual == "cone"
    assert details["level1_passed"] and details["level3_passed"] is False
    assert "I/J" in details["message"]


@pytest.mark.parametrize("shape,other", [("cone", "chamfer"), ("chamfer", "cone")])
def test_refreshed_baselines_accept_correct_shape_and_reject_swapped_geometry(shape, other):
    root = Path(__file__).parent / "data/models/process/filament/prime_tower/prime_tower_enhance_type"
    baseline = root / f"prime_tower_enhance_type_{shape}_baseline.gcode"
    wrong = root / f"prime_tower_enhance_type_{other}_baseline.gcode"
    assert parse_prime_tower_enhance_type(baseline, shape, baseline, expected_cone_angle=60)[0]
    # Bypass the enum check to prove actual geometry, not just the config string, distinguishes them.
    ok, details = compare_tower_paths(extract_tower_paths(baseline), extract_tower_paths(wrong))
    assert not ok and details["layer_mismatch_count"] > 0


@pytest.mark.parametrize("shape", ["cone", "chamfer"])
def test_shape_projects_explicitly_preserve_effective_angle(shape):
    root = Path(__file__).parent / "data"
    project = root / f"models/process/filament/prime_tower/prime_tower_enhance_type/prime_tower_enhance_type_{shape}.3mf"
    with ZipFile(project) as archive:
        cfg = json.loads(archive.read("Metadata/project_settings.config"))
    assert cfg["prime_tower_enhance_type"] == shape
    assert float(cfg["wipe_tower_cone_angle"]) == 60
    assert {"prime_tower_enhance_type", "wipe_tower_cone_angle"} <= set(cfg["different_settings_to_system"][0].split(";"))
