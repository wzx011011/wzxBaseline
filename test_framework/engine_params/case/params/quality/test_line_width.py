import os
from pathlib import Path

import pytest

# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, "..", "..", "..", "..", "..")
data_root = os.path.join(project_root, "test_framework", "engine_params", "data", "models", "quality")

# 默认线宽测试
slice_cases_default = [
    {"input_3mf": os.path.join(data_root, "line_width_default.3mf")},
]
expectations_default = [False, ]  # 根据实际需要修改期望值
params_default = [
    pytest.param(
        sc, exp
    )
    for sc, exp in zip(slice_cases_default, expectations_default)
]


@pytest.mark.engine_params
@pytest.mark.parametrize(("slice_and_export", "expected_line_width_default"), params_default,
                         indirect=["slice_and_export"])
def test_line_width_default(slice_and_export: Path,
                            expected_line_width_default: bool):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()
    # TODO: 实现默认线宽解析逻辑
    result = False  # 临时返回False
    assert result == expected_line_width_default, f"result={result}, but expected {expected_line_width_default}!"


# 初始层线宽测试
slice_cases_initial = [
    {"input_3mf": os.path.join(data_root, "line_width_default.3mf")},
]
expectations_initial = [False, ]  # 根据实际需要修改期望值
params_initial = [
    pytest.param(
        sc, exp
    )
    for sc, exp in zip(slice_cases_initial, expectations_initial)
]


@pytest.mark.engine_params
@pytest.mark.parametrize(("slice_and_export", "expected_line_width_initial"), params_initial,
                         indirect=["slice_and_export"])
def test_line_width_initial_layer(slice_and_export: Path,
                                  expected_line_width_initial: bool):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()
    # TODO: 实现初始层线宽解析逻辑
    result = False  # 临时返回False
    assert result == expected_line_width_initial, f"result={result}, but expected {expected_line_width_initial}!"


# 外墙线宽测试
slice_cases_outer = [
    {"input_3mf": os.path.join(data_root, "line_width_default.3mf")},
]
expectations_outer = [False, ]  # 根据实际需要修改期望值
params_outer = [
    pytest.param(
        sc, exp
    )
    for sc, exp in zip(slice_cases_outer, expectations_outer)
]


@pytest.mark.engine_params
@pytest.mark.parametrize(("slice_and_export", "expected_line_width_outer"), params_outer,
                         indirect=["slice_and_export"])
def test_line_width_outer_wall(slice_and_export: Path,
                               expected_line_width_outer: bool):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()
    # TODO: 实现外墙线宽解析逻辑
    result = False  # 临时返回False
    assert result == expected_line_width_outer, f"result={result}, but expected {expected_line_width_outer}!"


# 内墙线宽测试
slice_cases_inner = [
    {"input_3mf": os.path.join(data_root, "line_width_default.3mf")},
]
expectations_inner = [False, ]  # 根据实际需要修改期望值
params_inner = [
    pytest.param(
        sc, exp
    )
    for sc, exp in zip(slice_cases_inner, expectations_inner)
]


@pytest.mark.engine_params
@pytest.mark.parametrize(("slice_and_export", "expected_line_width_inner"), params_inner,
                         indirect=["slice_and_export"])
def test_line_width_inner_wall(slice_and_export: Path,
                               expected_line_width_inner: bool):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()
    # TODO: 实现内墙线宽解析逻辑
    result = False  # 临时返回False
    assert result == expected_line_width_inner, f"result={result}, but expected {expected_line_width_inner}!"


# 顶面线宽测试
slice_cases_top = [
    {"input_3mf": os.path.join(data_root, "line_width_default.3mf")},
]
expectations_top = [False, ]  # 根据实际需要修改期望值
params_top = [
    pytest.param(
        sc, exp
    )
    for sc, exp in zip(slice_cases_top, expectations_top)
]


@pytest.mark.engine_params
@pytest.mark.parametrize(("slice_and_export", "expected_line_width_top"), params_top,
                         indirect=["slice_and_export"])
def test_line_width_top_surface(slice_and_export: Path,
                                expected_line_width_top: bool):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()
    # TODO: 实现顶面线宽解析逻辑
    result = False  # 临时返回False
    assert result == expected_line_width_top, f"result={result}, but expected {expected_line_width_top}!"


# 稀疏填充线宽测试
slice_cases_sparse = [
    {"input_3mf": os.path.join(data_root, "line_width_default.3mf")},
]
expectations_sparse = [False, ]  # 根据实际需要修改期望值
params_sparse = [
    pytest.param(
        sc, exp
    )
    for sc, exp in zip(slice_cases_sparse, expectations_sparse)
]


@pytest.mark.engine_params
@pytest.mark.parametrize(("slice_and_export", "expected_line_width_sparse"), params_sparse,
                         indirect=["slice_and_export"])
def test_line_width_sparse_infill(slice_and_export: Path,
                                  expected_line_width_sparse: bool):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()
    # TODO: 实现稀疏填充线宽解析逻辑
    result = False  # 临时返回False
    assert result == expected_line_width_sparse, f"result={result}, but expected {expected_line_width_sparse}!"


# 内部实心填充线宽测试
slice_cases_internal_solid = [
    {"input_3mf": os.path.join(data_root, "line_width_default.3mf")},
]
expectations_internal_solid = [False, ]  # 根据实际需要修改期望值
params_internal_solid = [
    pytest.param(
        sc, exp
    )
    for sc, exp in zip(slice_cases_internal_solid, expectations_internal_solid)
]


@pytest.mark.engine_params
@pytest.mark.parametrize(("slice_and_export", "expected_line_width_internal_solid"), params_internal_solid,
                         indirect=["slice_and_export"])
def test_line_width_internal_solid_infill(slice_and_export: Path,
                                          expected_line_width_internal_solid: bool):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()
    # TODO: 实现内部实心填充线宽解析逻辑
    result = False  # 临时返回False
    assert result == expected_line_width_internal_solid, f"result={result}, but expected {expected_line_width_internal_solid}!"


# 支撑线宽测试
slice_cases_support = [
    {"input_3mf": os.path.join(data_root, "line_width_default.3mf")},
]
expectations_support = [False, ]  # 根据实际需要修改期望值
params_support = [
    pytest.param(
        sc, exp
    )
    for sc, exp in zip(slice_cases_support, expectations_support)
]


@pytest.mark.engine_params
@pytest.mark.parametrize(("slice_and_export", "expected_line_width_support"), params_support,
                         indirect=["slice_and_export"])
def test_line_width_support(slice_and_export: Path,
                            expected_line_width_support: bool):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()
    # TODO: 实现支撑线宽解析逻辑
    result = False  # 临时返回False
    assert result == expected_line_width_support, f"result={result}, but expected {expected_line_width_support}!"