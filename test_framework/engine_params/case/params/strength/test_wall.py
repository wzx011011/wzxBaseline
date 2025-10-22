from pathlib import Path
import pytest
from engine_params.src.gcode.GCodeParser import WallStyle
from engine_params.src.gcode.Strength.walls_check import parse_wall_sequence

slice_cases = [
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\cube_inner_outer_inner_wallSeq.3mf"},
]
expectations = ['inner-outer-inner wall', ]
params = [
    pytest.param(
        sc, exp
    )
    for sc, exp in zip(slice_cases, expectations)
]


@pytest.mark.engine_params
@pytest.mark.parametrize(("slice_and_export", "expected_sequence"), params,
                         indirect=["slice_and_export"])
def test_wall_sequence(slice_and_export: Path,
                       expected_sequence: WallStyle):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ret: tuple[bool, WallStyle, list[tuple[int, WallStyle, list[str]]]] = parse_wall_sequence(
        gcode_path, expected_sequence=expected_sequence
    )

    assert ret[0], f"gcode中的墙顺序不是期望的{expected_sequence}顺序，而是{ret[2]}。"
