from types import SimpleNamespace

from engine_params.src.gcode.constants import ACCEL_KEY, ExtrusionType
from engine_params.src.gcode.process.speed import advance_check, overhang_speed_check
from engine_params.src.gcode.process.speed.travel_speed_check import parse_travel_speed


def _cfg(value, raw=None):
    return SimpleNamespace(value=value, raw=str(value) if raw is None else raw)


def test_parse_travel_speed_accepts_motion_dict_and_point_objects():
    parser = SimpleNamespace(
        load_config=lambda: {"travel_speed": _cfg(120.0)},
        get_motion_paths=lambda **_: {
        1: [SimpleNamespace(kind="travel", f=80.0)],
        2: [SimpleNamespace(kind="extrude", f=60.0)],
    })

    result = parse_travel_speed(parser, 120.0)

    assert result["passed"]
    assert result["details"]["checked_points"] == 1


def test_parse_travel_speed_rejects_empty_travel_data():
    parser = SimpleNamespace(
        load_config=lambda: {"travel_speed": _cfg(120.0)},
        get_motion_paths=lambda **_: {1: []},
    )

    result = parse_travel_speed(parser, 120.0)

    assert not result["passed"]
    assert result["details"]["note"]


def test_parse_travel_speed_rejects_config_mismatch():
    parser = SimpleNamespace(
        load_config=lambda: {"travel_speed": _cfg(100.0)},
        get_motion_paths=lambda **_: {
            1: [SimpleNamespace(kind="travel", f=120.0)],
        },
    )

    result = parse_travel_speed(parser, 120.0)

    assert not result["passed"]
    assert not result["details"]["config_match"]


def test_height_limit_uses_point_z_speed_and_acceleration(monkeypatch, tmp_path):
    gcode = tmp_path / "height.gcode"
    gcode.touch()
    points = {
        500: [SimpleNamespace(
            kind="extrude", extrusion_type=ExtrusionType.OUTER_WALL.value,
            z=110.0, f=100.0, velocity_limits={ACCEL_KEY: 3000.0},
        )],
        750: [SimpleNamespace(
            kind="extrude", extrusion_type=ExtrusionType.OUTER_WALL.value,
            z=160.0, f=80.0, velocity_limits={ACCEL_KEY: 2000.0},
        )],
    }

    class Parser:
        def __init__(self, _):
            pass

        def load_config(self):
            curve = "[[100,150,100,3000],[150,200,80,2000],[200,250,60,500]]"
            return {
                "speed_limit_to_height_enable": _cfg(True),
                "speed_limit_to_height": _cfg(curve, curve),
            }

        def get_motion_paths(self, **_):
            return points

    monkeypatch.setattr(advance_check, "GCodeParserEx", Parser)
    curve = "[[100,150,100,3000],[150,200,80,2000],[200,250,60,500]]"

    ok, _, details = advance_check.parse_speed_limit_to_height_enable(gcode, True, curve)

    assert ok, details
    assert details["sample_count"] == 2


def test_height_limit_reports_empty_behavior_sample(monkeypatch, tmp_path):
    gcode = tmp_path / "empty-height.gcode"
    gcode.touch()
    curve = "[[100,150,100,3000],[150,200,80,2000]]"

    class Parser:
        def __init__(self, _):
            pass

        def load_config(self):
            return {
                "speed_limit_to_height_enable": _cfg(True),
                "speed_limit_to_height": _cfg(curve, curve),
            }

        def get_motion_paths(self, **_):
            return {1: []}

    monkeypatch.setattr(advance_check, "GCodeParserEx", Parser)

    ok, _, details = advance_check.parse_speed_limit_to_height_enable(gcode, True, curve)

    assert not ok
    assert details["sample_count"] == 0
    assert details["note"].startswith("No eligible")


def test_curled_perimeter_uses_config_and_overhang_diagnostics(monkeypatch, tmp_path):
    gcode = tmp_path / "curled.gcode"
    gcode.touch()
    point = SimpleNamespace(f=17.5)
    region = SimpleNamespace(paths=[SimpleNamespace(points=[point])])
    layer = SimpleNamespace(
        index=50,
        regions={0: {ExtrusionType.OVERHANG_WALL.value: region}},
    )

    class Parser:
        def __init__(self, _):
            pass

        def load_config(self):
            return {"slowdown_for_curled_perimeters": _cfg(True)}

        def get_type_contours_per_layer(self, **_):
            return [layer]

    monkeypatch.setattr(overhang_speed_check, "GCodeParserEx", Parser)

    ok, _, details = overhang_speed_check.parse_slowdown_for_curled_perimeters(
        gcode, True,
    )

    assert ok, details
    assert details["actual_values_set"] == [17.5]


def test_curled_perimeter_disabled_does_not_require_magic_bridge_speed(
        monkeypatch, tmp_path,
):
    gcode = tmp_path / "curled-disabled.gcode"
    gcode.touch()

    class Parser:
        def __init__(self, _):
            pass

        def load_config(self):
            return {"slowdown_for_curled_perimeters": _cfg("0")}

        def get_type_contours_per_layer(self, **_):
            return []

    monkeypatch.setattr(overhang_speed_check, "GCodeParserEx", Parser)

    ok, _, details = overhang_speed_check.parse_slowdown_for_curled_perimeters(
        gcode, False,
    )

    assert ok, details
    assert details["config_match"]
