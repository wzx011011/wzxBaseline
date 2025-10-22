from pathlib import Path
from engine_params.src.gcode.precision_check import check_elefant_foot_compensation
import pytest


# ================== elefant_foot_compensation ==================
'''
    现在象脚补偿只是使用立方体模型，用的边界框的方式校验，其他模型会失效。
'''


# 仅供夹具使用的切片参数
slice_cases = [
    {"input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\cube_01mm_efc.3mf",
     "project_name": "efc_01mm_case"},
]

# 与夹具无关、用于断言的期望
expectations = [
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\baseline_cube_no_efc.gcode",
     0.10,   # expected_comp
     1e-6),
]

# 一一对应（而不是笛卡尔积），用 zip 合并：
params = [
    pytest.param(sc, *exp, id=sc["project_name"])
    for sc, exp in zip(slice_cases, expectations)
]

@pytest.mark.engine_params
@pytest.mark.parametrize(
    "slice_and_export, baseline_gcode, expected_comp, tol",
    params,
    indirect=["slice_and_export"],   # 只把第一个参数（切片用的 dict）传给夹具
)
def test_elefant_foot_compensation(
    slice_and_export: Path,
    baseline_gcode: str | Path,
    expected_comp: float,
    tol: float,
):
    """
    验证第一层的象脚补偿：同时校验 Outer/Inner Walls，且只把带 E 的挤出行视作轮廓点。
    其它层不能补偿。
    """
    baseline_gcode = Path(baseline_gcode)
    assert baseline_gcode.exists(), f"baseline G-code 不存在：{baseline_gcode}"
    assert slice_and_export.exists(), f"tested G-code 不存在：{slice_and_export}"

    check_elefant_foot_compensation(
        baseline=baseline_gcode,
        tested=slice_and_export,
        expected_comp=expected_comp,
        tol=tol,
        max_layers=1
    )

# ================== elefant_foot_compensation_layers ==================
# 仅供夹具使用的切片参数
slice_cases = [
    {"input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\efc_cube_01mm_5layers.3mf",
     "project_name": "efc_01mm_case"},
    # ...更多切片 case 可继续加
]

# 与夹具无关、用于断言的期望
expectations = [
    (r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\baseline_cube_no_efc.gcode",
     0.10,   # expected_comp
     1e-6,
     5),
]

# 一一对应（而不是笛卡尔积），用 zip 合并：
params = [
    pytest.param(sc, *exp, id=sc["project_name"])
    for sc, exp in zip(slice_cases, expectations)
]
@pytest.mark.engine_params
@pytest.mark.parametrize(
    "slice_and_export, baseline_gcode, expected_comp, tol, efc_layers",
    params,
    indirect=["slice_and_export"],  # 只把第一个参数（切片用的 dict）传给夹具
)
def test_elefant_foot_compensation_layers(
    slice_and_export: Path,
    baseline_gcode: str | Path,
    expected_comp: float,
    tol: float,
    efc_layers: int
):
    """
    验证efc_layers的象脚补偿：同时校验 Outer/Inner Walls，且只把带 E 的挤出行视作轮廓点。
    efc_layers外的层不能补偿。
    """
    baseline_gcode = Path(baseline_gcode)
    assert baseline_gcode.exists(), f"baseline G-code 不存在：{baseline_gcode}"
    assert slice_and_export.exists(), f"tested G-code 不存在：{slice_and_export}"

    check_elefant_foot_compensation(
        baseline=baseline_gcode,
        tested=slice_and_export,
        expected_comp=expected_comp,
        tol=tol,
        max_layers=efc_layers
    )
