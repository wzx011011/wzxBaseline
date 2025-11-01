from __future__ import annotations

from pathlib import Path

import pytest

from engine_params.src.gcode.Others.special_mode_check import parse_print_sequence

# ================== print_sequence ==================
print_sequence_cases = [
    {"input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\others\print_sequence_byOrder_001.3mf"},
    {"input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\others\print_sequence_byOrder_002.3mf"},
]
print_sequence_expectations = ["逐件打印","逐层打印"]
print_sequence_params = [
    pytest.param(
        case, exp
    )
    for case, exp in zip(print_sequence_cases, print_sequence_expectations)
]


@pytest.mark.engine_params
@pytest.mark.parametrize(("slice_and_export", "expected_sequence"), print_sequence_params,
                         indirect=["slice_and_export"])
def test_print_sequence(slice_and_export: Path,
                        expected_sequence: str):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual_mode, details = parse_print_sequence(
        gcode_path,
        expected_sequence,
    )

    assert ok, (
        f"print_sequence expected {expected_sequence}, actual {actual_mode}, details: {details}"
    )
