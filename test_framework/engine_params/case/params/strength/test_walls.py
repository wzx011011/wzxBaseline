from pathlib import Path

import pytest

from engine_params.src.gcode.strength.walls_check import parse_wall_loops

# ================== wall_loops ==================

@pytest.mark.engine_params
def test_wall_loops(slice_and_export: Path,
                     expected_wall_loops: int):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ret = parse_wall_loops(gcode_path, expected_wall_loops=expected_wall_loops)

    assert ret[0], (
        f"期望的墙数：{expected_wall_loops}, 但是找到不匹配的: {ret[2]}"
    )
