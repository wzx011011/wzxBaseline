"""Test advanced group parameters for motion_ability page"""

import pytest
from pathlib import Path
from engine_params.src.gcode.printer.motion_ability.advanced_check import (
    parse_emit_machine_limits_to_gcode,
)


@pytest.mark.engine_params
def test_emit_machine_limits_to_gcode(
    slice_and_export: Path,
    expected_value: int,
):
    """Test emit_machine_limits_to_gcode (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_emit_machine_limits_to_gcode(gcode_path, expected_value)
    
    assert ok, (
        f"emit_machine_limits_to_gcode validation failed. "
        f"Expected {expected_value}, got {actual}. "
        f"Details: {details['message']}"
    )
