from pathlib import Path

import pytest

from engine_params.src.gcode.process.quality.wall_generator_check import (
    parse_wall_distribution_count,
)


def _write_variable_wall_gcode(path: Path, component_count: int) -> None:
    lines = ["M83", ";LAYER_CHANGE", ";Z:0.2", ";HEIGHT:0.2"]
    for index in range(component_count):
        x = float(index * 10)
        lines.extend(
            [
                f"G0 X{x - 1:.1f} Y0",
                ";TYPE:Inner wall",
                ";WIDTH:0.40",
                f"G1 X{x:.1f} Y0 E1",
                ";WIDTH:0.44",
                f"G1 X{x + 2:.1f} Y0 E1",
                ";WIDTH:0.48",
                f"G1 X{x + 4:.1f} Y0 E1",
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


@pytest.mark.parametrize("configured", [1.0, 2.0])
def test_wall_distribution_baseline_requires_four_components(
    tmp_path: Path, configured: float
) -> None:
    gcode = tmp_path / "baseline.gcode"
    _write_variable_wall_gcode(gcode, component_count=4)

    ok, actual, details = parse_wall_distribution_count(gcode, configured)

    assert ok
    assert actual == 4
    assert details["expectation"]["mode"] == "approximately"


@pytest.mark.parametrize("component_count", [7, 8])
def test_wall_distribution_radius_three_accepts_seam_split_variants(
    tmp_path: Path, component_count: int
) -> None:
    gcode = tmp_path / "expanded.gcode"
    _write_variable_wall_gcode(gcode, component_count=component_count)

    ok, actual, details = parse_wall_distribution_count(gcode, 3.0)

    assert ok
    assert actual == component_count
    assert details["expectation"]["mode"] == "at_least"


def test_wall_distribution_radius_three_rejects_unexpanded_behavior(
    tmp_path: Path,
) -> None:
    gcode = tmp_path / "not-expanded.gcode"
    _write_variable_wall_gcode(gcode, component_count=4)

    ok, actual, _ = parse_wall_distribution_count(gcode, 3.0)

    assert not ok
    assert actual == 4
