from __future__ import annotations

from pathlib import Path

import pytest

from engine_params.src.gcode.others.special_mode_check import parse_print_sequence

# ================== print_sequence ==================

@pytest.mark.engine_params
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
