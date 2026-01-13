"""
Test extruder assignment parameters
"""

from pathlib import Path
import pytest

from engine_params.src.gcode.process.extruder_assignment_check import (
    parse_wall_filament,
)


@pytest.mark.engine_params
def test_wall_filament(
    slice_and_export: Path,
    expected_value: str,
):
    """Test wall_filament parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_wall_filament(gcode_path, expected_value)
    
    assert ok, f"wall_filament expected {expected_value}, got {actual}: {details}"
