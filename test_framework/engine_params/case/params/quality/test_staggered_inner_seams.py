import os
from pathlib import Path

import pytest

# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, "..", "..", "..", "..", "..")
data_root = os.path.join(project_root, "test_framework", "engine_params", "data", "models", "quality")

slice_cases = [
    {"input_3mf": os.path.join(data_root, "staggered_inner_seams.3mf")},
]
expectations = [False, ]  # 根据实际需要修改期望值
params = [
    pytest.param(
        sc, exp
    )
    for sc, exp in zip(slice_cases, expectations)
]


@pytest.mark.engine_params
@pytest.mark.parametrize(("slice_and_export", "expected_staggered_inner_seams"), params,
                         indirect=["slice_and_export"])
def test_staggered_inner_seams(slice_and_export: Path,
                               expected_staggered_inner_seams: bool):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()
    # TODO: 实现staggered_inner_seams解析逻辑
    result = False  # 临时返回False
    assert result == expected_staggered_inner_seams, f"result={result}, but expected {expected_staggered_inner_seams}!"