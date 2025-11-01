from pathlib import Path
from engine_params.src.gcode.precision_check import (
    check_elefant_foot_compensation,
    parse_xy_hole_compensation, parse_xy_contour_compensation,
    parse_enable_arc_fitting,
)
from engine_params.src.gcode.constants import ExtrusionType
import pytest

# # ================== elefant_foot_compensation ==================
# '''
#     现在象脚补偿只是使用立方体模型，用的边界框的方式校验，其他模型会失效。
# '''
#
#
# # 仅供夹具使用的切片参数
# slice_cases = [
#     {"input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\cube_01mm_efc.3mf",
#      "project_name": "efc_01mm_case"},
# ]
#
# # 与夹具无关、用于断言的期望
# expectations = [
#     (r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\baseline_cube_no_efc.gcode",
#      0.10,   # expected_comp
#      1e-6),
# ]
#
# # 一一对应（而不是笛卡尔积），用 zip 合并：
# params = [
#     pytest.param(sc, *exp, id=sc["project_name"])
#     for sc, exp in zip(slice_cases, expectations)
# ]
#
# @pytest.mark.engine_params
# @pytest.mark.parametrize(
#     "slice_and_export, baseline_gcode, expected_comp, tol",
#     params,
#     indirect=["slice_and_export"],   # 只把第一个参数（切片用的 dict）传给夹具
# )
# def test_elefant_foot_compensation(
#     slice_and_export: Path,
#     baseline_gcode: str | Path,
#     expected_comp: float,
#     tol: float,
# ):
#     """
#     验证第一层的象脚补偿：同时校验 Outer/Inner Walls，且只把带 E 的挤出行视作轮廓点。
#     其它层不能补偿。
#     """
#     baseline_gcode = Path(baseline_gcode)
#     assert baseline_gcode.exists(), f"baseline G-code 不存在：{baseline_gcode}"
#     assert slice_and_export.exists(), f"tested G-code 不存在：{slice_and_export}"
#
#     check_elefant_foot_compensation(
#         baseline=baseline_gcode,
#         tested=slice_and_export,
#         expected_comp=expected_comp,
#         tol=tol,
#         max_layers=1
#     )
#
# # ================== elefant_foot_compensation_layers ==================
# # 仅供夹具使用的切片参数
# slice_cases = [
#     {"input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\efc_cube_01mm_5layers.3mf",
#      "project_name": "efc_01mm_case"},
#     # ...更多切片 case 可继续加
# ]
#
# # 与夹具无关、用于断言的期望
# expectations = [
#     (r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\baseline_cube_no_efc.gcode",
#      0.10,   # expected_comp
#      1e-6,
#      5),
# ]
#
# # 一一对应（而不是笛卡尔积），用 zip 合并：
# params = [
#     pytest.param(sc, *exp, id=sc["project_name"])
#     for sc, exp in zip(slice_cases, expectations)
# ]
# @pytest.mark.engine_params
# @pytest.mark.parametrize(
#     "slice_and_export, baseline_gcode, expected_comp, tol, efc_layers",
#     params,
#     indirect=["slice_and_export"],  # 只把第一个参数（切片用的 dict）传给夹具
# )
# def test_elefant_foot_compensation_layers(
#     slice_and_export: Path,
#     baseline_gcode: str | Path,
#     expected_comp: float,
#     tol: float,
#     efc_layers: int
# ):
#     """
#     验证efc_layers的象脚补偿：同时校验 Outer/Inner Walls，且只把带 E 的挤出行视作轮廓点。
#     efc_layers外的层不能补偿。
#     """
#     baseline_gcode = Path(baseline_gcode)
#     assert baseline_gcode.exists(), f"baseline G-code 不存在：{baseline_gcode}"
#     assert slice_and_export.exists(), f"tested G-code 不存在：{slice_and_export}"
#
#     check_elefant_foot_compensation(
#         baseline=baseline_gcode,
#         tested=slice_and_export,
#         expected_comp=expected_comp,
#         tol=tol,
#         max_layers=efc_layers
#     )

# ================== xy_hole_compensation ==================
slice_cases_xy = [
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\xy_hole_compensation_001.3mf",
        "project_name": "xy_hole_compensation_shrink",
    },
]
expectations_xy = [
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\baselline_xy_compensation.gcode",
     -2.0,  # expected_offset (mm)
     0.001),  # tolerance
]
params_xy = [
    pytest.param(sc, *exp, id=sc["project_name"])
    for sc, exp in zip(slice_cases_xy, expectations_xy)
]


@pytest.mark.engine_params
@pytest.mark.parametrize(
    "slice_and_export, baseline_gcode, expected_offset, tol",
    params_xy,
    indirect=["slice_and_export"],
)
def test_xy_hole_compensation(
        slice_and_export: Path,
        baseline_gcode: str | Path,
        expected_offset: float,
        tol: float,
):
    """
    说明：每一层将测试 G-code 的 XY 边界框与基准 G-code 对比，
    期望所有边界均在容差内向内收缩 |expected_offset| mm（参数为负时）
    或向外扩张 expected_offset mm（参数为正时）。
    """
    baseline_path = Path(baseline_gcode)
    assert baseline_path.exists(), f"baseline G-code 不存在: {baseline_path}"
    assert slice_and_export.exists(), f"tested G-code 不存在: {slice_and_export}"

    ok, details = parse_xy_hole_compensation(
        baseline=baseline_path,
        tested=slice_and_export,
        expected_offset=expected_offset,
        tolerance=tol,
        object_id=0,
    )

    assert ok, f"xy_hole_compensation 未达到期望: {details}"


# ================== xy_contour_compensation ==================
slice_cases_xy_contour = [
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\xy_contour_compensation_001.3mf",
        "project_name": "xy_contour_compensation_shrink",
    },
]
expectations_xy_contour = [
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\baselline_xy_compensation.gcode",
     2.0,  # expected_offset (mm): 负=收缩；正=外扩
     0.001,  # tolerance
     ),
]
params_xy_contour = [
    pytest.param(sc, *exp, id=sc["project_name"])
    for sc, exp in zip(slice_cases_xy_contour, expectations_xy_contour)
]


@pytest.mark.engine_params
@pytest.mark.parametrize(
    "slice_and_export, baseline_gcode, expected_offset, tol",
    params_xy_contour,
    indirect=["slice_and_export"],
)
def test_xy_contour_compensation(
        slice_and_export: Path,
        baseline_gcode: str | Path,
        expected_offset: float,
        tol: float
):
    """
    说明：
      - 逐层对“外轮廓族”的外墙（outer）与指定圈的内墙（inner_{k}）做 bbx 边界位移校验；
      - 期望：四边位移满足统一公式（Left/Bottom=-expected_offset, Right/Top=+expected_offset），允许 ±tol。
    """
    baseline_path = Path(baseline_gcode)
    assert baseline_path.exists(), f"baseline G-code 不存在: {baseline_path}"
    assert slice_and_export.exists(), f"tested G-code 不存在: {slice_and_export}"

    ok, details = parse_xy_contour_compensation(
        baseline=baseline_path,
        tested=slice_and_export,
        expected_offset=expected_offset,
        tolerance=tol,
        object_id=0,
    )
    assert ok, f"xy_contour_compensation 未达到期望: {details}"


# ================== enable_arc_fitting ==================
slice_cases_arc = [
    {
        "input_3mf": r"D:\\C3DBaseline\test_framework\engine_params\data\models\quality\enable_arc_fitting_001.3mf",
        "project_name": "enable_arc_fitting_off",
    },
    {
        "input_3mf": r"D:\\C3DBaseline\test_framework\engine_params\data\models\quality\enable_arc_fitting_002.3mf",
        "project_name": "enable_arc_fitting_off",
    },
]
expectations_arc = [
    False,
    True
]
params_arc = [
    pytest.param(sc, exp, id=sc["project_name"])
    for sc, exp in zip(slice_cases_arc, expectations_arc)
]


@pytest.mark.engine_params
@pytest.mark.parametrize(
    ("slice_and_export", "expected_enable"),
    params_arc,
    indirect=["slice_and_export"],
)
def test_enable_arc_fitting(
        slice_and_export: Path,
        expected_enable: bool,
):
    """
    说明：enable_arc_fitting=0 时，内/外墙挤出块不应出现 G2/G3 圆弧指令。
    """
    assert slice_and_export.exists(), f"tested G-code 不存在: {slice_and_export}"

    ok, details = parse_enable_arc_fitting(
        gcode_path=slice_and_export,
        expected_enable=expected_enable,
        object_id=0,
    )
    assert ok, f"enable_arc_fitting 校验失败: {details}"
