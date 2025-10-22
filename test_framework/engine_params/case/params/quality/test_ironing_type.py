from pathlib import Path

import pytest
from engine_params.src.gcode.Quality.ironing_type_check import parse_ironing_type

slice_cases = [
    {"input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\ironing_type_cube.3mf"},
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
    result: bool = parse_ironing_type(gcode_path)
    assert result == expected_ironing_type,f"result={result},but expected {expected_ironing_type}!"
