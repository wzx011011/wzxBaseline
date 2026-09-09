import math

import pytest

from engine_params.src.gcode.process.quality.overhangs_check import parse_make_overhang_printable_hole_size


def _fixture(path, value, holes, style="G3", bodies=3):
    lines = ["M83"]
    for layer in range(3):
        lines.extend([";LAYER_CHANGE", ";HEIGHT:0.2", f"G0 Z{.2 * (layer + 1)}"])
        for index in range(bodies):
            cx = index * 18
            lines.extend([f"G0 X{cx+7} Y0", ";TYPE:Outer wall", ";WIDTH:0.42",
                          f"G3 X{cx+7} Y0 I-7 J0 E2"])
        for index in range(holes):
            cx, radius = index * 18, 1.21 + index * .5
            lines.extend([f"G0 X{cx+radius} Y0", ";TYPE:Outer wall", ";WIDTH:0.42"])
            if style == "linear":
                for step in range(1, 65):
                    angle = math.tau * step / 64
                    lines.append(f"G1 X{cx+radius*math.cos(angle):.6f} Y{radius*math.sin(angle):.6f} E.01")
            else:
                # An almost-full arc has a tiny endpoint box and chord length.
                command = "G2" if style == "G2" else "G3"
                angle = .02 if command == "G2" else -.02
                if style == "full":
                    angle = 0
                elif style == "open":
                    angle = math.pi
                lines.append(f"{command} X{cx+radius*math.cos(angle):.6f} "
                             f"Y{radius*math.sin(angle):.6f} I{-radius} J0 E1")
    lines.extend(["; CONFIG_BLOCK_START", f"; make_overhang_printable_hole_size = {value}",
                  "; CONFIG_BLOCK_END"])
    path.write_text("\n".join(lines), encoding="utf-8")


@pytest.mark.parametrize("style", ["G2", "G3", "full", "linear"])
@pytest.mark.parametrize("value,holes", [(0, 0), (5, 1), (10, 2)])
def test_counts_true_arc_extent_and_length(tmp_path, value, holes, style):
    path = tmp_path / "holes.gcode"
    _fixture(path, value, holes, style)
    ok, actual, details = parse_make_overhang_printable_hole_size(path, value)
    assert ok, details
    assert actual == holes
    assert sorted(details["observed_diameters"]) == pytest.approx([2.42 + i for i in range(holes)], abs=.002)


@pytest.mark.parametrize("value,holes", [(0, 1), (5, 0), (5, 2), (10, 1), (10, 3)])
def test_missing_or_extra_holes_still_fail(tmp_path, value, holes):
    path = tmp_path / "bad.gcode"
    _fixture(path, value, holes)
    assert not parse_make_overhang_printable_hole_size(path, value)[0]


def test_open_arc_is_not_a_hole_loop(tmp_path):
    path = tmp_path / "open.gcode"
    _fixture(path, 5, 1, "open")
    assert not parse_make_overhang_printable_hole_size(path, 5)[0]


@pytest.mark.parametrize("contents", ["", "; CONFIG_BLOCK_START\n; make_overhang_printable_hole_size = 0\n; CONFIG_BLOCK_END"])
def test_empty_geometry_does_not_pass_zero_threshold(tmp_path, contents):
    path = tmp_path / "empty.gcode"
    path.write_text(contents, encoding="utf-8")
    assert not parse_make_overhang_printable_hole_size(path, 0)[0]


def test_configuration_mismatch_fails(tmp_path):
    path = tmp_path / "wrong-config.gcode"
    _fixture(path, 10, 1)
    assert not parse_make_overhang_printable_hole_size(path, 5)[0]


@pytest.mark.parametrize("replacement", ["R1.21", "I0 J0", "I-9 J0"])
def test_unsupported_or_invalid_arc_fails_closed(tmp_path, replacement):
    path = tmp_path / "bad-arc.gcode"
    _fixture(path, 5, 1)
    path.write_text(path.read_text(encoding="utf-8").replace("I-1.21 J0", replacement), encoding="utf-8")
    assert not parse_make_overhang_printable_hole_size(path, 5)[0]
