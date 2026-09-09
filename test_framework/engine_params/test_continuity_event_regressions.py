import pytest

from engine_params.src.gcode.process.strength.fill_check import parse_rectilinear_path_continuity


def _fixture(path, events=8, segments=4, absolute=False, reset=False, partial=False):
    lines = ["M82" if absolute else "M83", "G92 E100", ";LAYER_CHANGE", "G0 X0 Y0 Z.2",
             ";TYPE:Sparse infill"]
    position = 100.0

    def move(delta, axes=""):
        nonlocal position
        position += delta
        lines.append(f"G1 {axes} E{position if absolute else delta:.6f}")

    for event in range(events):
        move(1, f"X{event+1} Y0")
        move(-.9)
        lines.append(";WIPE_START")
        for index in range(segments):
            move(-.095 / segments, f"X{event+1} Y{(index+1)*.01}")
        lines.append(";WIPE_END")
        if partial:
            move(.2)  # A partial restore does not start a second retract event.
            move(-.2)
        move(-.005)
        if reset:
            lines.append("G92 E0")
            position = 0.0
        lines.append(f"G0 X{event+1} Y1 Z.6")
        move(1)
    lines.extend([";TYPE:Inner wall", "; fill_multiline = 1"])
    path.write_text("\n".join(lines), encoding="utf-8")


def _check(path, **limits):
    options = dict(max_block_lines=800, max_retractions=24, max_wipe_sections=12, max_z_hop_travels=20)
    options.update(limits)
    return parse_rectilinear_path_continuity(path, **options)


@pytest.mark.parametrize("absolute", [False, True])
@pytest.mark.parametrize("segments", [1, 4, 12])
@pytest.mark.parametrize("reset,partial", [(False, False), (True, False), (False, True)])
def test_retraction_events_ignore_wipe_segmentation(tmp_path, absolute, segments, reset, partial):
    path = tmp_path / "continuity.gcode"
    _fixture(path, segments=segments, absolute=absolute, reset=reset, partial=partial)
    ok, details = _check(path)
    assert ok, details
    assert details["metrics"]["retractions"] == 8
    assert details["metrics"]["retraction_commands"] == 8 * (segments + 2 + int(partial))
    assert len(details["retraction_event_lines"]) == 8


@pytest.mark.parametrize("absolute", [False, True])
def test_real_fragmentation_still_fails_retraction_limit(tmp_path, absolute):
    path = tmp_path / "fragmented.gcode"
    _fixture(path, events=25, segments=1, absolute=absolute)
    ok, details = _check(path, max_block_lines=5000, max_wipe_sections=100, max_z_hop_travels=100)
    assert not ok
    assert details["metrics"]["retractions"] == 25
    assert not details["checks"]["retractions"]


@pytest.mark.parametrize("limit", ["max_block_lines", "max_wipe_sections", "max_z_hop_travels"])
def test_other_limits_are_still_enforced(tmp_path, limit):
    path = tmp_path / "limits.gcode"
    _fixture(path)
    assert not _check(path, **{limit: 1})[0]


@pytest.mark.parametrize("body", ["G1 E1", ";WIPE_START\nG1 X1 Y1 E.1\n;WIPE_END"])
def test_reprime_or_wipe_alone_is_not_printing(tmp_path, body):
    path = tmp_path / "empty.gcode"
    path.write_text(f"M83\n;TYPE:Sparse infill\n{body}\n; fill_multiline = 1", encoding="utf-8")
    assert not _check(path)[0]


def test_missing_sparse_block_fails(tmp_path):
    path = tmp_path / "missing.gcode"
    path.write_text("M83\n; fill_multiline = 1", encoding="utf-8")
    assert not _check(path)[0]


def test_wrong_multiline_fails(tmp_path):
    path = tmp_path / "wrong.gcode"
    _fixture(path)
    path.write_text(path.read_text(encoding="utf-8").replace("fill_multiline = 1", "fill_multiline = 2"), encoding="utf-8")
    assert not _check(path)[0]
