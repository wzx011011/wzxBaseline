from __future__ import annotations

from pathlib import Path

import pytest

from engine_params.src.gcode.Quality.bridging_check import parse_internal_bridge_flow


# ================== internal_bridge_flow ==================
slice_cases = [
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\internal_bridge_flow_001.3mf",
        "project_name": "internal_bridge_flow",
    },
]
expectations = [
    (
        r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\baseline_bridging_flow_ratio.gcode",
        0.5,
        1e-3,
    ),
]
params = [
    pytest.param(sc, *exp, id=sc.get("project_name", None))
    for sc, exp in zip(slice_cases, expectations)
]


@pytest.mark.engine_params
@pytest.mark.parametrize(
    ("slice_and_export", "baseline_gcode", "expected_ratio", "tol"),
    params,
    indirect=["slice_and_export"],
)
def test_internal_bridge_flow(
    slice_and_export: Path,
    baseline_gcode: str | Path,
    expected_ratio: float,
    tol: float,
):
    gcode_path: Path = slice_and_export
    baseline_path = Path(baseline_gcode)
    assert gcode_path.exists()
    assert baseline_path.exists()

    ok, ratio, details = parse_internal_bridge_flow(
        tested_gcode=gcode_path,
        baseline_gcode=baseline_path,
        expected_ratio=expected_ratio,
        tol=tol,
    )

    assert ok, (
        f"internal_bridge_flow expected {expected_ratio}, actual {ratio}, details: {details}"
    )
