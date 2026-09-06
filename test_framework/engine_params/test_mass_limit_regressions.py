import math

import pytest

from engine_params.src.gcode.process.speed.advance_check import parse_acceleration_limit_mess_enable
from engine_params.src.gcode.process.speed.mass_limit_check import _endpoint


CURVE = "[[0,0.1,30,600]]"


def _fixture(path, *, speed=80, accel=2910, enabled=True, samples=True,
             material=100, curve=CURVE, absolute=False, custom_prime=False):
    # Non-wall first-layer extrusion provides 80 g of weight. Wall validation
    # begins after layer 10, so truncated scans or target-only mass fail.
    e = 80 / (math.pi * 1.75 ** 2 / 4 * .1)
    lines = ["; EXECUTABLE_BLOCK_START", "M82" if absolute else "M83", ";LAYER_CHANGE",
             ";:0.2", "G0 X0 Y0 Z0.2", ";TYPE:Bottom surface", f"G1 X10 Y0 E{e} F1200"]
    if custom_prime:
        lines[2:2] = [";TYPE:Custom", "G0 X0 Y0", "G1 X100 Y0 E1000", "G92 E0"]
    for i in range(1, 13):
        lines.extend([";LAYER_CHANGE", f";:{.2*(i+1)}", f"G0 Z{.2*(i+1)}"])
    if samples:
        lines.extend(["G0 X0 Y0 F18000", "G92 E0", ";TYPE:Outer wall"])
        if accel is not None:
            lines.append(f"SET_VELOCITY_LIMIT ACCEL={accel}")
        lines.append(f"G1 X10 Y0 E1 F{speed*60}")
    lines.extend(["; EXECUTABLE_BLOCK_END", "; CONFIG_BLOCK_START",
                  f"; acceleration_limit_mess_enable = {int(enabled)}",
                  f"; acceleration_limit_mess = {curve}", "; filament_diameter = 1.75",
                  f"; filament_density = {material}", "; speed_limit_to_height_enable = 0",
                  "; outer_wall_speed = 300", "; inner_wall_speed = 300",
                  "; outer_wall_acceleration = 5000", "; inner_wall_acceleration = 5000",
                  "; default_acceleration = 12000", "; CONFIG_BLOCK_END"])
    path.write_text("\n".join(lines), encoding="utf-8")


def _check(path):
    return parse_acceleration_limit_mess_enable(path, True, CURVE, 1.75, 100, 1, 10)


@pytest.mark.parametrize("absolute", [False, True])
def test_mass_uses_all_roles_all_layers_and_ignores_fast_travel(tmp_path, absolute):
    path = tmp_path / "mass.gcode"
    _fixture(path, absolute=absolute)
    ok, _, details = _check(path)
    assert ok, details
    assert details["checked_layers"] == [12]
    assert details["sample_count"] == 1
    assert details["final_total_weight"] > 80


@pytest.mark.parametrize("options", [{"speed": 300}, {"accel": 5000}, {"accel": 100},
                                     {"accel": None}, {"samples": False}, {"enabled": False},
                                     {"material": 1.24}, {"curve": "[[0,0.2,30,600]]"}])
def test_mass_rejects_unlimited_missing_or_wrong_input(tmp_path, options):
    path = tmp_path / "bad-mass.gcode"
    _fixture(path, **options)
    assert not _check(path)[0]


def test_mass_endpoint_keeps_cpp_double_precision():
    assert _endpoint(.1) == 100.5


def test_mass_excludes_custom_purge_from_slicer_weight(tmp_path):
    path = tmp_path / "custom-purge.gcode"
    _fixture(path, custom_prime=True)
    ok, _, details = _check(path)
    assert ok, details
    assert 80 < details["final_total_weight"] < 81
