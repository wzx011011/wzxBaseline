"""Thin-wall checks must reject centerlines, not rescued perimeter loops."""

import math

import pytest

from engine_params.src.gcode.process.quality.wall_and_surfaces_check import parse_detect_thin_wall


def _fixture(path, *, enabled=False, centerline=False, control=True, narrow=True,
             retrace=False, rotation=0, width_hints=True, role="Outer wall"):
    lines = ["M83", ";LAYER_CHANGE", ";Z:0.4", ";HEIGHT:0.2", "G0 Z0.4"]
    angle = math.radians(rotation)

    def add(points, width, extrusion_role="Outer wall"):
        lines.append(f";TYPE:{extrusion_role}")
        if width_hints:
            lines.append(f";WIDTH:{width}")
        for i, (x, y) in enumerate(points):
            rx = 100 + x * math.cos(angle) - y * math.sin(angle)
            ry = 100 + x * math.sin(angle) + y * math.cos(angle)
            lines.append(f"{'G0' if i == 0 else 'G1'} X{rx:.3f} Y{ry:.3f}" + (" E1" if i else ""))

    if control:
        add([(0, 0), (2.58, 0), (2.58, 19.6), (0, 19.6), (0, .04)], .42)
    if narrow:
        add([(10, 19.6), (10, 0), (10.102, 0), (10.102, 19.56)], .378512)
    if centerline:
        points = [(20, 0), (20, 10), (20, 20)]
        if retrace:
            points.extend([(20, 10), (20, 0)])
        add(points, .28, role)
    lines.extend(["; CONFIG_BLOCK_START", f"; detect_thin_wall = {int(enabled)}", "; CONFIG_BLOCK_END"])
    path.write_text("\n".join(lines), encoding="utf-8")


@pytest.mark.parametrize("rotation", [0, 45, 90])
def test_disabled_accepts_narrow_closed_loop_with_seam(tmp_path, rotation):
    path = tmp_path / "closed.gcode"
    _fixture(path, rotation=rotation)
    ok, actual, details = parse_detect_thin_wall(path, False)
    assert ok, details
    assert actual is False
    assert details["closed_narrow_paths"] == 1
    assert details["control_paths"] == 1


@pytest.mark.parametrize("rotation", [0, 45, 90])
@pytest.mark.parametrize("retrace", [False, True])
@pytest.mark.parametrize("role", ["Outer wall", "Gap infill"])
def test_disabled_rejects_real_centerline_even_when_retraced(tmp_path, rotation, retrace, role):
    path = tmp_path / "centerline.gcode"
    _fixture(path, centerline=True, rotation=rotation, retrace=retrace, role=role)
    ok, actual, details = parse_detect_thin_wall(path, False)
    assert not ok, details
    assert actual is True
    assert details["thin_centerline_paths"] == 1


@pytest.mark.parametrize("centerline", [False, True])
def test_enabled_requires_actual_centerline(tmp_path, centerline):
    path = tmp_path / "enabled.gcode"
    _fixture(path, enabled=True, centerline=centerline)
    ok, actual, details = parse_detect_thin_wall(path, True)
    assert ok == centerline, details
    assert actual == centerline


@pytest.mark.parametrize("options", [
    {"control": False},
    {"control": False, "narrow": False},
    {"width_hints": False},
    {"enabled": True},
])
def test_disabled_rejects_missing_evidence_or_wrong_config(tmp_path, options):
    path = tmp_path / "invalid.gcode"
    _fixture(path, **options)
    assert not parse_detect_thin_wall(path, False)[0]


def test_first_layer_may_omit_width_but_body_layers_must_have_it(tmp_path):
    path = tmp_path / "first-layer.gcode"
    _fixture(path)
    body = path.read_text(encoding="utf-8")
    prefix = "M83\n;LAYER_CHANGE\n;Z:0.2\nG0 Z0.2\n;TYPE:Outer wall\nG0 X0 Y0\nG1 X20 Y0 E1\n"
    path.write_text(prefix + body, encoding="utf-8")
    assert parse_detect_thin_wall(path, False)[0]
    path.write_text(prefix + "\n".join(line for line in body.splitlines() if not line.startswith(";WIDTH:")),
                    encoding="utf-8")
    assert not parse_detect_thin_wall(path, False)[0]
