import pytest
from pathlib import Path
from engine_params.src.gcode.filament.multimaterial.wipe_tower_check import (
    parse_filament_minimal_purge_on_wipe_tower,
)

def test_filament_minimal_purge_on_wipe_tower(slice_and_export: Path, expected_value: str):
    """Test filament_minimal_purge_on_wipe_tower parameter (Level 1 - Config)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_filament_minimal_purge_on_wipe_tower(gcode_path, expected_value)
    assert ok, f"filament_minimal_purge_on_wipe_tower expected {expected_value}, got {actual}: {details}"



