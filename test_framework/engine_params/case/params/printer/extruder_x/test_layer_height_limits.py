"""Test Layer height limits group parameters for Extruder X page"""

from pathlib import Path

import pytest

from engine_params.src.gcode.printer.extruder_x.extruder_x_check import (
    parse_max_layer_height,
    parse_min_layer_height,
)


@pytest.mark.engine_params
def test_min_layer_height(
    slice_and_export: Path,
    expected_value: float,
):
    """Test min_layer_height (Level 1 - Config)"""
    ok, actual, details = parse_min_layer_height(slice_and_export, expected_value)

    assert ok, (
        f"min_layer_height validation failed. "
        f"Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )


@pytest.mark.engine_params
def test_max_layer_height(
    slice_and_export: Path,
    expected_value: float,
):
    """Test max_layer_height (Level 1 - Config)"""
    ok, actual, details = parse_max_layer_height(slice_and_export, expected_value)

    assert ok, (
        f"max_layer_height validation failed. "
        f"Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )
