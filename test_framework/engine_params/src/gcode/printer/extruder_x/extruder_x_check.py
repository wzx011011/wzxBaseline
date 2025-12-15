from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple

from engine_params.src.gcode.GCodeParser import GCodeParser


def _parse_config_value(
    gcode_path: Path,
    key: str,
    expected_value: Any,
) -> Tuple[bool, Any, Dict[str, Any]]:
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()

    actual = cfg.get(key)
    if actual is None and key not in cfg:
        return (
            False,
            None,
            {
                "detection_method": "Level 1 - Config",
                "message": f"Config key '{key}' not found.",
                "raw_data": {"available_keys_sample": list(cfg.keys())[:50]},
            },
        )

    ok = actual == expected_value
    return (
        ok,
        actual,
        {
            "detection_method": "Level 1 - Config",
            "message": f"Config '{key}' expected {expected_value}, got {actual}.",
            "raw_data": {"key": key, "expected": expected_value, "actual": actual},
        },
    )


def parse_nozzle_diameter(gcode_path: Path, expected_value: float):
    return _parse_config_value(gcode_path, "nozzle_diameter", expected_value)


def parse_min_layer_height(gcode_path: Path, expected_value: float):
    return _parse_config_value(gcode_path, "min_layer_height", expected_value)


def parse_max_layer_height(gcode_path: Path, expected_value: float):
    return _parse_config_value(gcode_path, "max_layer_height", expected_value)


def parse_extruder_offset(gcode_path: Path, expected_value: str):
    return _parse_config_value(gcode_path, "extruder_offset", expected_value)


def parse_retraction_length(gcode_path: Path, expected_value: float):
    return _parse_config_value(gcode_path, "retraction_length", expected_value)


def parse_retract_restart_extra(gcode_path: Path, expected_value: float | int):
    return _parse_config_value(gcode_path, "retract_restart_extra", expected_value)


def parse_z_hop(gcode_path: Path, expected_value: float):
    return _parse_config_value(gcode_path, "z_hop", expected_value)


def parse_z_hop_types(gcode_path: Path, expected_value: str):
    return _parse_config_value(gcode_path, "z_hop_types", expected_value)


def parse_travel_slope(gcode_path: Path, expected_value: float | int):
    return _parse_config_value(gcode_path, "travel_slope", expected_value)


def parse_retraction_speed(gcode_path: Path, expected_value: float | int):
    return _parse_config_value(gcode_path, "retraction_speed", expected_value)


def parse_deretraction_speed(gcode_path: Path, expected_value: float | int):
    return _parse_config_value(gcode_path, "deretraction_speed", expected_value)


def parse_retraction_minimum_travel(gcode_path: Path, expected_value: float | int):
    return _parse_config_value(gcode_path, "retraction_minimum_travel", expected_value)


def parse_retract_when_changing_layer(gcode_path: Path, expected_value: int):
    return _parse_config_value(gcode_path, "retract_when_changing_layer", expected_value)


def parse_wipe(gcode_path: Path, expected_value: int):
    return _parse_config_value(gcode_path, "wipe", expected_value)


def parse_wipe_distance(gcode_path: Path, expected_value: float | int):
    return _parse_config_value(gcode_path, "wipe_distance", expected_value)


def parse_retract_before_wipe(gcode_path: Path, expected_value: str):
    return _parse_config_value(gcode_path, "retract_before_wipe", expected_value)


def parse_retract_lift_above(gcode_path: Path, expected_value: float | int):
    return _parse_config_value(gcode_path, "retract_lift_above", expected_value)


def parse_retract_lift_below(gcode_path: Path, expected_value: float | int):
    return _parse_config_value(gcode_path, "retract_lift_below", expected_value)


def parse_retract_lift_enforce(gcode_path: Path, expected_value: str):
    return _parse_config_value(gcode_path, "retract_lift_enforce", expected_value)


def parse_retract_length_toolchange(gcode_path: Path, expected_value: float | int):
    return _parse_config_value(gcode_path, "retract_length_toolchange", expected_value)


def parse_retract_restart_extra_toolchange(gcode_path: Path, expected_value: float | int):
    return _parse_config_value(gcode_path, "retract_restart_extra_toolchange", expected_value)


def parse_long_retractions_when_cut(gcode_path: Path, expected_value: int):
    return _parse_config_value(gcode_path, "long_retractions_when_cut", expected_value)


def parse_retraction_distances_when_cut(gcode_path: Path, expected_value: float | int):
    return _parse_config_value(gcode_path, "retraction_distances_when_cut", expected_value)
