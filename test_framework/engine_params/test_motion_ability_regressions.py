"""Regression coverage for scalar and Normal/Silent machine limit configs."""

from pathlib import Path

import pytest

from engine_params.src.gcode.printer.motion_ability import (
    acceleration_check,
    jerk_check,
    motion_config,
    speed_check,
)


CASES = [
    (acceleration_check, "machine_max_acceleration_x", 20000),
    (acceleration_check, "machine_max_acceleration_y", 20000),
    (acceleration_check, "machine_max_acceleration_z", 300),
    (acceleration_check, "machine_max_acceleration_e", 5000),
    (acceleration_check, "machine_max_acceleration_extruding", 20000),
    (acceleration_check, "machine_max_acceleration_retracting", 5000),
    (acceleration_check, "machine_max_acceleration_travel", 20000),
    (jerk_check, "machine_max_jerk_x", 20),
    (jerk_check, "machine_max_jerk_y", 20),
    (jerk_check, "machine_max_jerk_z", 5),
    (jerk_check, "machine_max_jerk_e", 10),
    (speed_check, "machine_max_speed_x", 600),
    (speed_check, "machine_max_speed_y", 600),
    (speed_check, "machine_max_speed_z", 10),
    (speed_check, "machine_max_speed_e", 100),
]


def _gcode(tmp_path: Path, key: str, value: str | None) -> Path:
    path = tmp_path / "motion.gcode"
    option = "" if value is None else f"; {key} = {value}\n"
    path.write_text(
        "; CONFIG_BLOCK_START\n" + option + "; CONFIG_BLOCK_END\n",
        encoding="utf-8",
    )
    return path


@pytest.mark.parametrize("module,key,expected", CASES, ids=[case[1] for case in CASES])
@pytest.mark.parametrize("layout", ["integer", "decimal", "pair"])
def test_all_machine_limits_accept_legacy_and_vector_configs(tmp_path, module, key, expected, layout):
    raw = str(expected)
    if layout == "decimal":
        raw += ".0"
    elif layout == "pair":
        raw = f" {expected}.0, {expected}.0 "
    path = _gcode(tmp_path, key, raw)

    ok, actual, details = getattr(module, "parse_" + key)(path, expected)

    assert ok, details
    assert actual == expected
    assert isinstance(actual, int)
    assert details["raw_data"]["config_value"] == expected
    assert details["raw_data"]["selected_index"] == 0
    assert "message" in details and details["detection_method"] == "Level 1 - Config"
    if layout == "pair":
        assert details["raw_data"]["raw_config_value"] == raw.strip()
        assert details["raw_data"]["config_values"] == [expected, expected]


@pytest.mark.parametrize("raw,expected,actual,passed", [
    ("600,200", 600, 600, True),
    ("600,200", 200, 600, False),
    ("200,600", 600, 200, False),
    ("600,200,800,300", 600, 600, True),
    ("0.25", 0.25, 0.25, True),
    ("0.25,0.4", "0.25", 0.25, True),
    ("0.25,0.4", 0, 0.25, False),
    ("600.125,600", 600, 600.125, False),
    ("6e2,2e2", 600.0, 600, True),
    ("0,0", 0, 0, True),
])
def test_selection_and_decimal_values_are_not_truncated(tmp_path, raw, expected, actual, passed):
    path = _gcode(tmp_path, "machine_max_speed_x", raw)

    ok, value, details = speed_check.parse_machine_max_speed_x(path, expected)

    assert ok is passed
    assert value == actual
    assert "selected_index=0" in details["message"]
    if "," in raw:
        assert details["raw_data"]["raw_config_value"] == raw
        assert repr(raw) in details["message"]


@pytest.mark.parametrize("raw", [
    None, "", "bad", "600,", ",600", "600,,600", "600,bad", "600,nil",
    "nan", "inf", "-1", "600,nan", "600,inf", "600,-1", "1e999", "true",
])
def test_invalid_config_cannot_pass_even_with_invalid_expected(tmp_path, raw):
    path = _gcode(tmp_path, "machine_max_speed_x", raw)
    for expected in (600, None):
        ok, actual, details = speed_check.parse_machine_max_speed_x(path, expected)
        assert not ok
        assert actual is None
        assert "error" in details["raw_data"]
        assert "raw=" in details["message"]
        if raw is None:
            assert "missing configuration key" in details["message"]


@pytest.mark.parametrize("expected", [None, "", "bad", "600,600", [], True, -1, float("nan"), float("inf")])
def test_invalid_expected_value_is_reported(tmp_path, expected):
    path = _gcode(tmp_path, "machine_max_speed_x", "600,600")

    ok, actual, details = speed_check.parse_machine_max_speed_x(path, expected)

    assert not ok
    assert actual == 600
    assert details["raw_data"]["raw_config_value"] == "600,600"
    assert "error" in details["raw_data"]


@pytest.mark.parametrize("values", [[600, 200], (600.0, 200.0), ["600", "200"]])
def test_sequence_config_values_are_supported(monkeypatch, values):
    monkeypatch.setattr(motion_config.GCodeParser, "load_config", lambda _: {"machine_max_speed_x": values})

    ok, actual, details = speed_check.parse_machine_max_speed_x(Path("unused.gcode"), 600)

    assert ok
    assert actual == 600
    assert details["raw_data"]["raw_config_value"] == values


def test_unreadable_gcode_keeps_the_result_contract(tmp_path):
    ok, actual, details = speed_check.parse_machine_max_speed_x(tmp_path / "missing.gcode", 600)

    assert not ok
    assert actual is None
    assert details["raw_data"]["error"]
    assert "machine_max_speed_x" in details["message"]
