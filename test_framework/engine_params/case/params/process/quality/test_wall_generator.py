from __future__ import annotations

from pathlib import Path

import pytest

from engine_params.src.gcode.process.quality.wall_generator_check import (
    WallGenerator,
    parse_wall_generator,
)

# ================== wall_generator ==================

@pytest.mark.engine_params
def test_wall_generator(
        slice_and_export: Path,
        expected_generator: str,
        consistency_threshold: float
):
    """
    consistency_threshold 表示在线宽检测中，单层内“线宽落在容差范围内”的挤出段所占比例。
    当单层合格比例低于该阈值，就视为该层存在明显的可变线宽（倾向于判定为 arachne 墙）。
    """

    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    actual_generator, details = parse_wall_generator(
        gcode_path,
        tolerance=0.01,
        consistency_threshold=consistency_threshold,
    )

    assert actual_generator == WallGenerator.from_str(expected_generator), (
        f"wall_generator expected {expected_generator}, actual {actual_generator}, details: {details}"
    )
