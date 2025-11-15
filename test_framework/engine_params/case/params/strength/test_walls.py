from pathlib import Path

import pytest
from engine_params.src.gcode.strength.walls_check import parse_wall_loops, parse_alternate_extra_wall, parse_detect_thin_wall

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

# ================== alternate_extra_wall ==================

@pytest.mark.engine_params
def test_alternate_extra_wall(slice_and_export: Path, expected_on: bool):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ret = parse_alternate_extra_wall(gcode_path, expected_on)

    assert ret[0], (
        f"期望是否打开交替添加额外内墙功能：{expected_on}, 但是检测到的结果不符合预期：{ret[1]}, 详情: {ret[2]}"
    )


# ================== detect_thin_wall ==================
@pytest.mark.engine_params
def test_detect_thin_wall(slice_and_export: Path, expected_detect_thin_wall: bool, tolerance: float):
    """检测 detect_thin_wall：非首层 OUTER_WALL 分成双孤岛，一条线宽多变，一条线宽恒定。"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_detect_thin_wall(
        gcode_path,
        expected_detect_thin_wall,
        tolerance,
    )

    assert ok, f"expected={expected_detect_thin_wall}, details={details}"
