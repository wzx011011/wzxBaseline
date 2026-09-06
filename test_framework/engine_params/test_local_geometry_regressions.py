from pathlib import Path

import pytest

from engine_params.src.gcode.process.quality.wall_and_surfaces_check import parse_min_width_top_surface
from engine_params.src.gcode.process.support_check import parse_support_bottom_z_distance


def _top_fixture(path, percent, removed=(), missing_top=(), split=False, shift=0):
    lines = ["M83", ";LAYER_CHANGE", ";Z:5", ";HEIGHT:0.2", "G0 Z5",
             ";TYPE:Outer wall", ";WIDTH:0.42", f"G0 X{shift+.21} Y0.21"]
    for x, y in ((39.79, .21), (39.79, 23.79), (.21, 23.79), (.21, .21)):
        lines.append(f"G1 X{x+shift} Y{y} E1")
    cursor = shift
    for index, gap in enumerate((.36, .48, .60, .78)):
        left, right = cursor + 7, cursor + 7 + gap
        if index not in removed:
            for x in (left-.5, right+.5):
                lines.extend([";TYPE:Inner wall", ";WIDTH:0.45", f"G0 X{x} Y1"])
                if split:
                    lines.append(f"G1 X{x} Y12 E1")
                lines.append(f"G1 X{x} Y23 E1")
        if index not in missing_top:
            lines.extend([";TYPE:Top surface", f"G0 X{(left+right)/2} Y1",
                          f"G1 X{(left+right)/2} Y23 E1"])
        cursor = right
    lines.extend([";LAYER_CHANGE", ";Z:10", "G0 Z10", ";TYPE:Top surface",
                  f"G0 X{shift} Y0", f"G1 X{shift+1} Y0 E1",
                  "; CONFIG_BLOCK_START", f"; min_width_top_surface = {percent}%", "; CONFIG_BLOCK_END"])
    path.write_text("\n".join(lines), encoding="utf-8")


@pytest.mark.parametrize("percent,removed", [(150, ()), (200, (0,)), (250, (0, 1))])
@pytest.mark.parametrize("split,shift", [(False, 0), (True, 90)])
def test_top_width_checks_local_walls_not_segment_count(tmp_path, percent, removed, split, shift):
    path = tmp_path / "top.gcode"
    _top_fixture(path, percent, removed, split=split, shift=shift)
    ok, actual, details = parse_min_width_top_surface(path, f"{percent}%")
    assert ok, details
    assert actual == str(len(removed))


@pytest.mark.parametrize("removed,missing", [((), ()), ((1,), ()), ((0,), (0,)), ((0, 1, 2, 3), ())])
def test_top_width_rejects_wrong_channel_or_missing_extrusion(tmp_path, removed, missing):
    path = tmp_path / "bad-top.gcode"
    _top_fixture(path, 200, removed, missing)
    assert not parse_min_width_top_surface(path, "200%")[0]


def test_top_width_rejects_configuration_mismatch(tmp_path):
    path = tmp_path / "config.gcode"
    _top_fixture(path, 200, (0,))
    assert not parse_min_width_top_surface(path, "150%")[0]


def _support_fixture(path, gap, *, expected=.2, x=0, height=True, absolute=False):
    lines = ["M82" if absolute else "M83", ";LAYER_CHANGE", ";:10", ";HEIGHT:0.2",
             "G0 X0 Y0 Z10", ";TYPE:Top surface", "G1 X10 Y0 E1",
             ";LAYER_CHANGE", f";:{10.2+gap}", f"G0 X{x} Y0 Z{10.2+gap}",
             ";TYPE:Support interface"]
    if height:
        lines.append(";HEIGHT:0.2")
    lines.extend([f"G1 X{x+10} Y0 E{2 if absolute else 1}", "; CONFIG_BLOCK_START",
                  f"; support_bottom_z_distance = {expected}", "; CONFIG_BLOCK_END"])
    path.write_text("\n".join(lines), encoding="utf-8")


@pytest.mark.parametrize("gap", [.1, .2, .3])
@pytest.mark.parametrize("absolute", [False, True])
def test_bottom_gap_uses_physical_z_and_thickness(tmp_path, gap, absolute):
    path = tmp_path / "support.gcode"
    _support_fixture(path, gap, expected=gap, absolute=absolute)
    ok, _, details = parse_support_bottom_z_distance(path, str(gap))
    assert ok, details
    assert details["behavior_check"]["measured_gaps_mm"] == [gap]


@pytest.mark.parametrize("options", [{"gap": .3}, {"gap": -.1}, {"gap": .2, "x": 100},
                                     {"gap": .2, "height": False}, {"gap": .2, "expected": .3}])
def test_bottom_gap_rejects_false_evidence(tmp_path, options):
    path = tmp_path / "bad-support.gcode"
    _support_fixture(path, **options)
    assert not parse_support_bottom_z_distance(path, ".2")[0]
