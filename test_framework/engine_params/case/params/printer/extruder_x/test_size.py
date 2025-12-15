"""Test Size group parameters for Extruder X page"""

from pathlib import Path

import pytest

from engine_params.src.gcode.printer.extruder_x.extruder_x_check import parse_nozzle_diameter


@pytest.mark.engine_params
def test_nozzle_diameter(
    slice_and_export: Path,
    expected_value: float,
):
    """Test nozzle_diameter (Level 1 - Config)"""
    ok, actual, details = parse_nozzle_diameter(slice_and_export, expected_value)

    assert ok, (
        f"nozzle_diameter validation failed. "
        f"Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )
