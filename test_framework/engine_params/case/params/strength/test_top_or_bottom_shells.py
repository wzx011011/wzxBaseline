from pathlib import Path

import pytest

from engine_params.src.gcode.Strength.top_or_bottom_shells_check import (
    parse_bottom_shell_layers,
    parse_top_shell_layers,
)

# ================== top_shell_layers ==================
slice_cases = [
    {"input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\top_shell_layers_001.3mf"},
    {"input_3mf":r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\top_shell_layers_002.3mf"},
]
expectations = [10, 4]
params = [
    pytest.param(
        sc, exp
    )
    for sc, exp in zip(slice_cases, expectations)
]
@pytest.mark.engine_params
@pytest.mark.parametrize(("slice_and_export", "expected_layers"), params,
                         indirect=["slice_and_export"])
def test_top_shell_layers(slice_and_export: Path, expected_layers: int):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ret = parse_top_shell_layers(gcode_path, expected_layers=expected_layers)

    assert ret[0], (
        f"top shell layers expected {expected_layers}, got violations: {ret[2]}"
    )

# ================== bottom_shell_layers ==================
slice_cases = [
    {"input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\bottom_shell_layers_001.3mf"},
]
expectations = [6]
params = [
    pytest.param(
        sc, exp
    )
    for sc, exp in zip(slice_cases, expectations)
]
@pytest.mark.engine_params
@pytest.mark.parametrize(("slice_and_export", "expected_layers"), params,
                         indirect=["slice_and_export"])
def test_bottom_shell_layers(slice_and_export: Path, expected_layers: int):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ret = parse_bottom_shell_layers(gcode_path, expected_layers=expected_layers)

    assert ret[0], (
        f"bottom shell layers expected {expected_layers}, got violations: {ret[2]}"
    )
