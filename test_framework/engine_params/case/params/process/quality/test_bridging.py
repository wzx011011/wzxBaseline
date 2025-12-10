from __future__ import annotations

from pathlib import Path

import pytest

from engine_params.src.gcode.process.quality.bridging_check import parse_internal_bridge_flow


# ================== internal_bridge_flow ==================
@pytest.mark.engine_params
def test_internal_bridge_flow(
    slice_and_export: Path,
    expected_ratio: float,
    baseline_gcode: str | Path,
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
