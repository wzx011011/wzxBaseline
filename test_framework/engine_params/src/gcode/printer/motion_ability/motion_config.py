"""Read machine limit vectors for the first physical nozzle in Normal mode."""

import math
from pathlib import Path
from typing import Any, Dict, Tuple

from engine_params.src.gcode.GCodeParser import GCodeParser


def _number(value: Any) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError("expected a non-negative finite number")
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise ValueError("expected a non-negative finite number")
    return int(number) if number.is_integer() else number


def _limit_values(value: Any) -> list[int | float]:
    if isinstance(value, str):
        items = value.split(",")
    elif isinstance(value, (list, tuple)):
        items = value
    else:
        items = [value]
    if not items:
        raise ValueError("empty machine limit vector")
    # Validate every element so a malformed tail cannot be hidden by index 0.
    return [_number(item) for item in items]


def parse_motion_limit(
    gcode_path: Path,
    expected_value: Any,
    parameter: str,
    unit: str,
) -> Tuple[bool, Any, Dict]:
    """Validate the existing single-nozzle cases without discarding decimal values.

    Machine limits may contain Normal/Silent pairs or per-nozzle values. Index
    zero is the first physical nozzle's Normal limit in either layout; these
    cases do not validate other nozzles or Silent mode.
    """
    raw_data = {"config_value": None, "raw_config_value": None,
                "expected_value": expected_value, "selected_index": 0}
    actual = None
    try:
        cfg = GCodeParser(gcode_path).load_config()
        raw_data["raw_config_value"] = cfg.get(parameter)
        if parameter not in cfg:
            raise ValueError(f"missing configuration key: {parameter}")
        values = _limit_values(cfg[parameter])
        raw_data["config_values"] = values
        actual = values[0]
        raw_data["config_value"] = actual
        expected = _number(expected_value)
        success = math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-9)
        message = (
            f"{parameter}: expected {expected} {unit}, got {actual} {unit}; "
            f"raw={raw_data['raw_config_value']!r}, selected_index=0 (first nozzle, Normal)"
        )
    except Exception as exc:
        success = False
        raw_data["error"] = str(exc)
        message = (
            f"Error parsing {parameter}: {exc}; "
            f"raw={raw_data['raw_config_value']!r}, expected={expected_value!r}"
        )
    return success, actual, {
        "detection_method": "Level 1 - Config",
        "message": message,
        "raw_data": raw_data,
    }
