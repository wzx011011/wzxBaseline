from pathlib import Path

import pytest

from engine_params.src.gcode.layer_comments import read_layer_heights
from engine_params.src.gcode.process.others.special_mode_check import parse_print_sequence


def _write_gcode(path: Path, comments: list[str], sequence: str) -> Path:
    lines = ["; EXECUTABLE_BLOCK_START"]
    for comment in comments:
        lines.extend([";LAYER_CHANGE", comment, ";HEIGHT:0.2", "G1 X10 E1"])
    lines.extend([
        "; EXECUTABLE_BLOCK_END",
        "; CONFIG_BLOCK_START",
        f"; print_sequence = {sequence}",
        "; CONFIG_BLOCK_END",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


@pytest.mark.parametrize("marker", [";Z:", ";:"])
@pytest.mark.parametrize("heights,expected", [
    ([0.2, 0.4, 0.6], "by layer"),
    ([0.2, 0.4, 0.2, 0.4], "by object"),
])
def test_print_sequence_uses_layer_order(tmp_path: Path, marker, heights, expected):
    path = _write_gcode(tmp_path / "sequence.gcode", [f"{marker}{z}" for z in heights], expected)

    ok, actual, details = parse_print_sequence(path, expected)

    assert ok
    assert actual == expected
    assert details["layer_count"] == len(heights)
    assert details["missing_layer_count"] == 0


@pytest.mark.parametrize("expected", ["by layer", "by object", None])
@pytest.mark.parametrize("comments", [
    [], [";Z:0.2"], [";Z:bad", ";:bad"], [";Z:0.2", ";HEIGHT:0.2", ";Z:0.4"],
])
def test_missing_or_insufficient_heights_cannot_pass(tmp_path: Path, comments, expected):
    path = _write_gcode(tmp_path / "unknown.gcode", comments, expected or "by layer")

    ok, actual, details = parse_print_sequence(path, expected)

    assert not ok
    assert actual is None
    assert details["is_monotonic_z"] is None
    assert "无法判定" in details["message"]


def test_print_sequence_does_not_fall_back_to_config(tmp_path: Path):
    path = _write_gcode(tmp_path / "mismatch.gcode", [";Z:0.2", ";Z:0.4"], "by object")

    ok, actual, _ = parse_print_sequence(path, "by object")

    assert not ok
    assert actual == "by layer"


def test_layer_reader_bounds_records_and_ignores_height_comments():
    assert read_layer_heights([
        ";Z:99", ";LAYER_CHANGE", ";HEIGHT:0.1", "; : +.2 ", ";Z:99",
        ";LAYER_CHANGE", "G1 X0", ";Z:99",
        ";LAYER_CHANGE", ";Z:0.4", "; EXECUTABLE_BLOCK_END",
        ";LAYER_CHANGE", ";Z:99",
    ]) == [0.2, None, 0.4]
