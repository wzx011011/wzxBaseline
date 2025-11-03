from pathlib import Path

import pytest

from engine_params.src.gcode.strength.top_or_bottom_shells_check import (
    parse_bottom_shell_layers,
    parse_top_shell_layers,
)

# ================== top_shell_layers ==================
@pytest.mark.engine_params
def test_top_shell_layers(slice_and_export: Path, expected_layers: int):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ret = parse_top_shell_layers(gcode_path, expected_layers=expected_layers)

    assert ret[0], (
        f"top shell layers expected {expected_layers}, got violations: {ret[2]}"
    )

# ================== bottom_shell_layers ==================

@pytest.mark.engine_params
def test_bottom_shell_layers(slice_and_export: Path, expected_layers: int):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ret = parse_bottom_shell_layers(gcode_path, expected_layers=expected_layers)

    assert ret[0], (
        f"bottom shell layers expected {expected_layers}, got violations: {ret[2]}"
    )
