from pathlib import Path

import pytest

from engine_params.src.gcode.Strength.walls_check import parse_wall_loops

# ================== wall_loops ==================
slice_cases = [
    {"input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\wall_loops_001.3mf"},
]
expectations = [3]
params = [
    pytest.param(
        sc, exp
    )
    for sc, exp in zip(slice_cases, expectations)
]
@pytest.mark.engine_params
@pytest.mark.parametrize(("slice_and_export", "expected_wall_loops"), params,
                         indirect=["slice_and_export"])
def test_wall_loops(slice_and_export: Path,
                     expected_wall_loops: int):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ret = parse_wall_loops(gcode_path, expected_wall_loops=expected_wall_loops)

    assert ret[0], (
        f"期望的墙数：{expected_wall_loops}, 但是找到不匹配的: {ret[2]}"
    )
