"""Contour regressions: real missing-tenon evidence and adversarial G-code controls."""

import copy
import hashlib
import json
from pathlib import Path

import pytest

from engine_params.src.gcode.process.filament import interlocking_check as checks
from engine_params.src.gcode.process.filament.interlocking_baseline import (
    BASELINE_FILE, reference_layer_indices, validate_interlocking_geometry,
)
from engine_params.src.gcode.process.filament.interlocking_geometry import (
    compare_contours, read_outer_contours,
)


REFERENCE = json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
BUG_KEY = "interlocking_beam/bug18042_four_material"
SPECIMEN = Path(__file__).parent / "data/gcode_samples/interlocking_bug18042_z10.json"


def _write_reference_gcode(path, entry, *, enabled=1, marker=";Z:"):
    geometry = entry["geometry"]
    selected = {layer["index"]: layer["tools"] for layer in geometry["layers"]}
    lines = ["; EXECUTABLE_BLOCK_START", "G90", "M83"]
    for index, z in enumerate(geometry["layer_heights"]):
        lines.extend([";LAYER_CHANGE", f"{marker}{z}"])
        for tool, segments in selected.get(index, {}).items():
            lines.extend([f"T{tool}", ";TYPE:Outer wall"])
            for x, y, end_x, end_y in segments:
                lines.extend([f"G1 X{x} Y{y}", f"G1 X{end_x} Y{end_y} E0.1"])
    values = {"interlocking_beam": enabled, entry["parameter"]: entry["expected_value"]}
    lines.extend(["; EXECUTABLE_BLOCK_END", "; CONFIG_BLOCK_START"])
    lines.extend(f"; {key} = {int(value) if isinstance(value, bool) else value}" for key, value in values.items())
    lines.append("; CONFIG_BLOCK_END")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


@pytest.mark.parametrize("key", sorted(REFERENCE["entries"]))
def test_all_reviewed_cases_have_matching_input_and_complete_references(key):
    entry = REFERENCE["entries"][key]
    repo = Path(__file__).resolve().parents[2]
    assert hashlib.sha256((repo / entry["input_3mf"]).read_bytes()).hexdigest() == entry["input_sha256"]
    geometry = entry["geometry"]
    assert [layer["index"] for layer in geometry["layers"]] == reference_layer_indices(len(geometry["layer_heights"]))
    assert all(len(layer["tools"]) >= 2 for layer in geometry["layers"])


@pytest.mark.parametrize("marker", [";Z:", ";:"])
def test_reviewed_tenons_pass_with_both_layer_comment_formats(tmp_path, marker):
    entry = REFERENCE["entries"][BUG_KEY]
    path = _write_reference_gcode(tmp_path / "normal.gcode", entry, marker=marker)
    ok, actual, details = checks.parse_interlocking_beam(path, True, BUG_KEY)
    assert ok, details
    assert actual is True
    assert details["geometry_check"]["checked_layers"] == 10


def test_real_bug18042_sawtooth_fails_even_with_enabled_config(tmp_path):
    entry = copy.deepcopy(REFERENCE["entries"][BUG_KEY])
    specimen = json.loads(SPECIMEN.read_text())
    layer = next(layer for layer in entry["geometry"]["layers"] if layer["index"] == specimen["layer_index"])
    layer["tools"] = specimen["tools"]
    path = _write_reference_gcode(tmp_path / "sawtooth.gcode", entry)
    ok, actual, details = checks.parse_interlocking_beam(path, True, BUG_KEY)
    assert not ok
    assert actual is True
    assert details["geometry_check"]["mismatches"][0]["layer_index"] == 49


def test_disabled_geometry_with_forged_enabled_config_does_not_pass(tmp_path):
    entry = copy.deepcopy(REFERENCE["entries"]["interlocking_beam/bug18042_four_material_disabled"])
    entry["expected_value"] = True
    path = _write_reference_gcode(tmp_path / "disabled_geometry.gcode", entry)
    ok, _, details = checks.parse_interlocking_beam(path, True, BUG_KEY)
    assert not ok
    assert details["geometry_check"]["mismatches"]


@pytest.mark.parametrize("parameter", [
    "interlocking_beam_width", "interlocking_orientation", "interlocking_beam_layer_count",
    "interlocking_depth", "interlocking_boundary_avoidance",
])
def test_parameter_checks_reject_disabled_interlocking(tmp_path, parameter):
    key = next(key for key in REFERENCE["entries"] if key.startswith(parameter + "/"))
    entry = REFERENCE["entries"][key]
    path = _write_reference_gcode(tmp_path / "off.gcode", entry, enabled=0)
    ok, _, details = getattr(checks, "parse_" + parameter)(path, entry["expected_value"], key)
    assert not ok
    assert "must be enabled" in details["error"]


@pytest.mark.parametrize("parameter,source_key,target_key", [
    ("interlocking_beam_width", "0.5mm", "1.2mm"),
    ("interlocking_orientation", "45deg", "90deg"),
    ("interlocking_beam_layer_count", "interlocking_beam_layer_count_1", "interlocking_beam_layer_count_3"),
    ("interlocking_depth", "1mm", "3mm"),
    ("interlocking_boundary_avoidance", "1mm", "3mm"),
])
def test_config_only_parameter_change_cannot_hide_wrong_geometry(tmp_path, parameter, source_key, target_key):
    entry = copy.deepcopy(REFERENCE["entries"][parameter + "/" + source_key])
    target = REFERENCE["entries"][parameter + "/" + target_key]
    entry["expected_value"] = target["expected_value"]
    path = _write_reference_gcode(tmp_path / "forged.gcode", entry)
    ok, _, details = getattr(checks, "parse_" + parameter)(path, target["expected_value"], parameter + "/" + target_key)
    assert not ok, details
    assert details["geometry_check"]["mismatches"]


def test_period_shift_on_one_layer_is_detected(tmp_path):
    entry = copy.deepcopy(REFERENCE["entries"][BUG_KEY])
    layers = entry["geometry"]["layers"]
    by_index = {layer["index"]: layer for layer in layers}
    by_index[49]["tools"] = copy.deepcopy(by_index[51]["tools"])
    path = _write_reference_gcode(tmp_path / "wrong_period.gcode", entry)
    ok, _, details = checks.parse_interlocking_beam(path, True, BUG_KEY)
    assert not ok
    assert details["geometry_check"]["mismatches"][0]["layer_index"] == 49


def test_comparison_is_bidirectional_and_tool_sensitive():
    normal = {"0": [[0, 0, 4, 0], [4, 0, 4, 2]], "1": [[5, 0, 5, 2]]}
    reordered = {"0": [[4, 2, 4, 0], [4, 0, 2, 0], [2, 0, 0, 0]], "1": [[5, 2, 5, 0]]}
    assert compare_contours(reordered, normal) is None
    for altered in [
        {"0": [[0, 0, 4, 0]], "1": normal["1"]},
        {"0": normal["0"] + [[2, 0, 2, 1]], "1": normal["1"]},
        {"0": normal["1"], "1": normal["0"]},
        {"0": normal["0"]},
    ]:
        assert compare_contours(altered, normal) is not None


@pytest.mark.parametrize("offset,accepted", [(0.002, True), (0.2, False)])
def test_coordinate_rounding_tolerance_is_bounded(offset, accepted):
    expected = {"0": [[0, 0, 3, 0]]}
    actual = {"0": [[0, offset, 3, offset]]}
    assert (compare_contours(actual, expected) is None) is accepted


def test_parser_uses_extrusion_modes_and_ignores_infill_travel_and_tower(tmp_path):
    path = tmp_path / "modes.gcode"
    path.write_text("\n".join([
        "M82", "G90", ";LAYER_CHANGE", ";:0.2", "T1", ";TYPE:Outer wall",
        "G92 E10", "G1 X2 E11", "G1 X3 E10", "G1 X4", "M83", "G91",
        "G1 X1 E.1", ";TYPE:Prime tower", "G1 X1 E.1", ";TYPE:Sparse infill", "G1 X1 E.1",
        ";TYPE:Outer wall", "G90", "G92 X0 Y0", "G1 Y2 E.1",
        "; CONFIG_BLOCK_START", "G1 Y4 E.1",
    ]))
    layers = read_outer_contours(path)
    assert layers == [{"z": 0.2, "tools": {"1": [[0, 0, 2, 0], [4, 0, 5, 0], [0, 0, 0, 2]]}}]


def test_arc_is_not_replaced_with_a_straight_chord(tmp_path):
    path = tmp_path / "arc.gcode"
    path.write_text("M83\n;LAYER_CHANGE\n;Z:0.2\nG1 X1 Y0\n;TYPE:Outer wall\nG3 X0 Y1 I-1 J0 E1\n")
    segments = read_outer_contours(path)[0]["tools"]["0"]
    assert len(segments) > 20
    assert max(min(segment[2], segment[3]) for segment in segments) > 0.68


def test_missing_reference_and_missing_geometry_fail_closed(tmp_path):
    path = tmp_path / "empty.gcode"
    path.write_text("; CONFIG_BLOCK_START\n; interlocking_beam = 1\n; CONFIG_BLOCK_END\n")
    assert not checks.parse_interlocking_beam(path, True, BUG_KEY)[0]
    ok, details = validate_interlocking_geometry(path, "interlocking_beam", True, "unknown")
    assert not ok
    assert "Missing or ambiguous" in details["error"]
