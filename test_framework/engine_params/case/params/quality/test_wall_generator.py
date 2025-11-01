from __future__ import annotations

from pathlib import Path

import pytest

from engine_params.src.gcode.Quality.wall_generator_check import (
    WallGenerator,
    parse_wall_generator,
)

# ================== wall_generator ==================
slice_cases = [
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\wall_generator_001.3mf",
        "project_name": "wall_generator_arachne",
    },
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\wall_generator_002.3mf",
        "project_name": "wall_generator_classic",
    },
]
expectations = [
    (WallGenerator.ARACHNE, 0.9),
    (WallGenerator.CLASSIC, 0.9),
]
params = [
    pytest.param(sc, exp, thr, id=sc.get("project_name"))
    for (sc, (exp, thr)) in zip(slice_cases, expectations)
]


@pytest.mark.engine_params
@pytest.mark.parametrize(
    ("slice_and_export", "expected_generator", "consistency_threshold"),
    params,
    indirect=["slice_and_export"],
)
def test_wall_generator(
        slice_and_export: Path,
        expected_generator: WallGenerator,
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

    assert actual_generator == expected_generator, (
        f"wall_generator expected {expected_generator}, actual {actual_generator}, details: {details}"
    )
