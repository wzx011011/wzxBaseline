"""Test Retraction group parameters for Extruder X page"""

from pathlib import Path

import pytest

from engine_params.src.gcode.printer.extruder_x.extruder_x_check import (
    parse_deretraction_speed,
    parse_retract_before_wipe,
    parse_retract_restart_extra,
    parse_retract_when_changing_layer,
    parse_retraction_length,
    parse_retraction_minimum_travel,
    parse_retraction_speed,
    parse_travel_slope,
    parse_wipe,
    parse_wipe_distance,
    parse_z_hop,
    parse_z_hop_types,
)


@pytest.mark.engine_params
def test_retraction_length(slice_and_export: Path, expected_value: float):
    ok, actual, details = parse_retraction_length(slice_and_export, expected_value)
    assert ok, (
        f"retraction_length validation failed. Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )


@pytest.mark.engine_params
def test_retract_restart_extra(slice_and_export: Path, expected_value):
    ok, actual, details = parse_retract_restart_extra(slice_and_export, expected_value)
    assert ok, (
        f"retract_restart_extra validation failed. Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )


@pytest.mark.engine_params
def test_z_hop(slice_and_export: Path, expected_value: float):
    ok, actual, details = parse_z_hop(slice_and_export, expected_value)
    assert ok, (
        f"z_hop validation failed. Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )


@pytest.mark.engine_params
def test_z_hop_types(slice_and_export: Path, expected_value: str):
    ok, actual, details = parse_z_hop_types(slice_and_export, expected_value)
    assert ok, (
        f"z_hop_types validation failed. Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )


@pytest.mark.engine_params
def test_travel_slope(slice_and_export: Path, expected_value):
    ok, actual, details = parse_travel_slope(slice_and_export, expected_value)
    assert ok, (
        f"travel_slope validation failed. Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )


@pytest.mark.engine_params
def test_retraction_speed(slice_and_export: Path, expected_value):
    ok, actual, details = parse_retraction_speed(slice_and_export, expected_value)
    assert ok, (
        f"retraction_speed validation failed. Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )


@pytest.mark.engine_params
def test_deretraction_speed(slice_and_export: Path, expected_value):
    ok, actual, details = parse_deretraction_speed(slice_and_export, expected_value)
    assert ok, (
        f"deretraction_speed validation failed. Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )


@pytest.mark.engine_params
def test_retraction_minimum_travel(slice_and_export: Path, expected_value):
    ok, actual, details = parse_retraction_minimum_travel(slice_and_export, expected_value)
    assert ok, (
        f"retraction_minimum_travel validation failed. Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )


@pytest.mark.engine_params
def test_retract_when_changing_layer(slice_and_export: Path, expected_value: int):
    ok, actual, details = parse_retract_when_changing_layer(slice_and_export, expected_value)
    assert ok, (
        f"retract_when_changing_layer validation failed. Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )


@pytest.mark.engine_params
def test_wipe(slice_and_export: Path, expected_value: int):
    ok, actual, details = parse_wipe(slice_and_export, expected_value)
    assert ok, (
        f"wipe validation failed. Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )


@pytest.mark.engine_params
def test_wipe_distance(slice_and_export: Path, expected_value):
    ok, actual, details = parse_wipe_distance(slice_and_export, expected_value)
    assert ok, (
        f"wipe_distance validation failed. Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )


@pytest.mark.engine_params
def test_retract_before_wipe(slice_and_export: Path, expected_value: str):
    ok, actual, details = parse_retract_before_wipe(slice_and_export, expected_value)
    assert ok, (
        f"retract_before_wipe validation failed. Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )
