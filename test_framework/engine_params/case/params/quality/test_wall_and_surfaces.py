import pytest
from engine_params.src.gcode.Quality.wall_and_surfaces_check import *

# # ================== wall_sequence ==================
# slice_cases = [
#     {
#         "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\strength\cube_inner_outer_inner_wallSeq.3mf"},
# ]
# expectations = ['inner-outer-inner wall', ]
# params = [
#     pytest.param(
#         sc, exp
#     )
#     for sc, exp in zip(slice_cases, expectations)
# ]
#
#
# @pytest.mark.engine_params
# @pytest.mark.parametrize(("slice_and_export", "expected_sequence"), params,
#                          indirect=["slice_and_export"])
# def test_wall_sequence(slice_and_export: Path,
#                        expected_sequence: WallStyle):
#     gcode_path: Path = slice_and_export
#     assert gcode_path.exists()
#
#     ret: tuple[bool, WallStyle, list[tuple[int, WallStyle, list[str]]]] = parse_wall_sequence(
#         gcode_path, expected_style=expected_sequence
#     )
#
#     assert ret[0], f"gcode中的墙顺序不是期望的{expected_sequence}顺序，而是{ret[2]}。"
#
#
# # ================== is_infill_first ==================
#
# slice_cases = [
#     {"input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\is_infill_first_001.3mf"},
#     {}
#
# ]
# expectations = [True, ]
# params = [
#     pytest.param(
#         sc, exp
#     )
#     for sc, exp in zip(slice_cases, expectations)
# ]
#
#
# @pytest.mark.engine_params
# @pytest.mark.parametrize(("slice_and_export", "expected_first"), params,
#                          indirect=["slice_and_export"])
# def test_is_infill_first(slice_and_export: Path,
#                         expected_first: bool):
#     gcode_path: Path = slice_and_export
#     assert gcode_path.exists()
#
#     ret = parse_is_infill_first(gcode_path, expected_first=expected_first)
#
#     assert ret[0], f"输入期望is_infill_first =={ret[1]}，然而gcode的解析情况是{ret[2]}。"
#
#
# # ================== wall_direction ==================
# slice_cases = [
#     {"input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\cw_wall_direction_01.3mf"},
# ]
# expectations = ['cw', ]
# params = [
#     pytest.param(
#         sc, exp
#     )
#     for sc, exp in zip(slice_cases, expectations)
# ]
#
#
# @pytest.mark.engine_params
# @pytest.mark.parametrize(("slice_and_export", "expected_direction"), params,
#                          indirect=["slice_and_export"])
# def test_wall_direction(slice_and_export: Path,
#                         expected_direction: WallDirection):
#     gcode_path: Path = slice_and_export
#     assert gcode_path.exists()
#
#     ret = parse_wall_directions(gcode_path, expected_dir=expected_direction)
#
#     assert ret[0], f"gcode中的墙打印顺序不是期望的{ret[1]}顺序，而是{ret[2]}。"
#
# # ================== only_one_wall_top ==================

slice_cases = [
    {"input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\only_one_wall_top_001.3mf"},
    {"input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\only_one_wall_top_002.3mf"},
]
expectations = [True,False]
params = [
    pytest.param(
        sc, exp
    )
    for sc, exp in zip(slice_cases, expectations)
]
@pytest.mark.engine_params
@pytest.mark.parametrize(("slice_and_export", "expected_only_one_wall_top"), params,
                         indirect=["slice_and_export"])
def test_only_one_wall_top(slice_and_export: Path,
                        expected_only_one_wall_top: bool):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ret = parse_only_one_wall_top(gcode_path, expected_only_one_wall_top=expected_only_one_wall_top)

    assert ret[0], f"gcode中的墙打印顺序不是期望的{ret[1]}顺序，而是{ret[2]}。"
