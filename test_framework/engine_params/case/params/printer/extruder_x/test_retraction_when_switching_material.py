"""Test Retraction when switching material group parameters for Extruder X page"""

from pathlib import Path

import pytest

from engine_params.src.gcode.printer.extruder_x.extruder_x_check import (
    parse_long_retractions_when_cut,
    parse_retract_length_toolchange,
    parse_retract_restart_extra_toolchange,
    parse_retraction_distances_when_cut,
)


@pytest.mark.engine_params
def test_retract_length_toolchange(slice_and_export: Path, expected_value):
    ok, actual, details = parse_retract_length_toolchange(slice_and_export, expected_value)
    assert ok, (
        f"retract_length_toolchange validation failed. Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )


@pytest.mark.engine_params
def test_retract_restart_extra_toolchange(slice_and_export: Path, expected_value):
    ok, actual, details = parse_retract_restart_extra_toolchange(slice_and_export, expected_value)
    assert ok, (
        f"retract_restart_extra_toolchange validation failed. Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )


@pytest.mark.engine_params
def test_long_retractions_when_cut(slice_and_export: Path, expected_value: int):
    ok, actual, details = parse_long_retractions_when_cut(slice_and_export, expected_value)
    assert ok, (
        f"long_retractions_when_cut validation failed. Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )


@pytest.mark.engine_params
def test_retraction_distances_when_cut(slice_and_export: Path, expected_value):
    ok, actual, details = parse_retraction_distances_when_cut(slice_and_export, expected_value)
    assert ok, (
        f"retraction_distances_when_cut validation failed. Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )
