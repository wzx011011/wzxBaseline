"""Test Position group parameters for Extruder X page"""

from pathlib import Path

import pytest

from engine_params.src.gcode.printer.extruder_x.extruder_x_check import parse_extruder_offset


@pytest.mark.engine_params
def test_extruder_offset(
    slice_and_export: Path,
    expected_value: str,
):
    """Test extruder_offset (Level 1 - Config)"""
    ok, actual, details = parse_extruder_offset(slice_and_export, expected_value)

    assert ok, (
        f"extruder_offset validation failed. "
        f"Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )
