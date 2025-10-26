import os
from pathlib import Path

import pytest
from engine_params.src.gcode.Quality.ironing_type_check import parse_ironing_type

# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, "..", "..", "..", "..", "..")
data_root = os.path.join(project_root, "test_framework", "engine_params", "data", "models", "quality")

slice_cases = [
    {"input_3mf": os.path.join(data_root, "ironing_type_cube.3mf")},
]
expectations = [True, ]  # 期望类型TODO，因为现在只能检查存在性
params = [
    pytest.param(
        sc, exp
    )
    for sc, exp in zip(slice_cases, expectations)
]


@pytest.mark.engine_params
@pytest.mark.parametrize(("slice_and_export", "expected_ironing_type"), params,
                         indirect=["slice_and_export"])
def test_ironing_type(slice_and_export: Path,
                      expected_ironing_type: bool):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()
    result:list[dict[int, list[bytes | str]]] = parse_ironing_type(gcode_path)
    has_ironing_type = False
    for layer in result:
        for obj_id,blocks in layer.items():
            has_ironing_type = any(blocks)
        if has_ironing_type:
            break
    assert has_ironing_type

    # return any(bool(layer_blocks) for layer_blocks in blocks_per_layer)
    # assert result == expected_ironing_type,f"result={result},but expected {expected_ironing_type}!"