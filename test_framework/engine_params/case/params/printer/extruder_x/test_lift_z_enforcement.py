"""Test Lift Z Enforcement group parameters for Extruder X page"""

from pathlib import Path

import pytest

from engine_params.src.gcode.printer.extruder_x.extruder_x_check import (
    parse_retract_lift_above,
    parse_retract_lift_below,
    parse_retract_lift_enforce,
)


@pytest.mark.engine_params
def test_retract_lift_above(slice_and_export: Path, expected_value):
    ok, actual, details = parse_retract_lift_above(slice_and_export, expected_value)
    assert ok, (
        f"retract_lift_above validation failed. Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )


@pytest.mark.engine_params
def test_retract_lift_below(slice_and_export: Path, expected_value):
    ok, actual, details = parse_retract_lift_below(slice_and_export, expected_value)
    assert ok, (
        f"retract_lift_below validation failed. Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )


@pytest.mark.engine_params
def test_retract_lift_enforce(slice_and_export: Path, expected_value: str):
    ok, actual, details = parse_retract_lift_enforce(slice_and_export, expected_value)
    assert ok, (
        f"retract_lift_enforce validation failed. Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )
