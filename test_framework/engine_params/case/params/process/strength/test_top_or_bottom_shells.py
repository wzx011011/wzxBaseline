import math
from pathlib import Path

import pytest

from engine_params.src.gcode.process.strength.top_or_bottom_shells_check import (
    parse_bottom_shell_layers,
    parse_bottom_shell_thickness,
    parse_top_bottom_infill_wall_overlap,
    parse_top_shell_layers,
    parse_top_shell_thickness,
)


# ================== top_shell_layers ==================
@pytest.mark.engine_params
def test_top_shell_layers(slice_and_export: Path, expected_layers: int):
    # 验证方法：使用实体、薄壁、桥接或填充专用 3MF切片，解析Top/Bottom surface 连续层数、厚度和路径形态；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ret = parse_top_shell_layers(gcode_path, expected_layers=expected_layers)

    assert ret[0], (
        f"top shell layers expected {expected_layers}, got violations: {ret[2]}"
    )


# ================== top_shell_thickness ==================
def _layers_from_thickness(
        expected_thickness: float,
        base_thickness: float,
        base_layers: int,
        layer_height: float,
        tol: float = 1e-6,
) -> int:
    if base_thickness + tol >= expected_thickness:
        return base_layers
    deficit = expected_thickness - base_thickness
    extra_layers = int(math.ceil((max(0.0, deficit) - tol) / layer_height))
    extra_layers = max(extra_layers, 1)
    return base_layers + extra_layers


@pytest.mark.engine_params
def test_top_shell_thickness(
        slice_and_export: Path,
        expected_top_shell_thickness: float,
):
    # 验证方法：使用实体、薄壁、桥接或填充专用 3MF切片，解析Top/Bottom surface 连续层数、厚度和路径形态；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, matched_layers, details = parse_top_shell_thickness(
        gcode_path,
        expected_top_shell_thickness=expected_top_shell_thickness,
    )

    layer_height = details["layer_height"]
    base_thickness = details["base_thickness"]
    base_layers = details["config_top_shell_layers"]
    calculated_layers = _layers_from_thickness(
        expected_top_shell_thickness,
        base_thickness,
        base_layers,
        layer_height,
    )

    assert calculated_layers == details["layers_from_thickness"], (
        f"layers_from_thickness mismatch: expected {calculated_layers}, "
        f"got {details['layers_from_thickness']}"
    )

    target_layers = details["target_layers"]
    assert ok, (
        f"top shell thickness check failed: target_layers={target_layers}, "
        f"violations={details['violations']}"
    )
    assert matched_layers == target_layers, (
        f"matched_layers={matched_layers} must equal target_layers={target_layers}"
    )


# ================== top_bottom_infill_wall_overlap ==================
@pytest.mark.engine_params
def test_top_bottom_infill_wall_overlap(
        slice_and_export: Path,
        baseline_gcode: str | Path,
) -> None:
    # 验证方法：使用实体、薄壁、桥接或填充专用 3MF切片，解析各层填充类型、路径方向、间距及正向挤出量；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    baseline_path = Path(baseline_gcode)
    assert baseline_path.exists()

    ok, details = parse_top_bottom_infill_wall_overlap(
        gcode_path,
        baseline_gcode=baseline_path,
    )

    assert ok, (
        "top_bottom_infill_wall_overlap snapshot mismatch: "
        f"baseline={details.get('baseline_gcode')}, "
        f"mismatches={details.get('mismatch_layers')}, errors={details.get('errors')}"
    )


# ================== bottom_shell_layers ==================
@pytest.mark.engine_params
def test_bottom_shell_layers(slice_and_export: Path, expected_layers: int):
    # 验证方法：使用实体、薄壁、桥接或填充专用 3MF切片，解析Top/Bottom surface 连续层数、厚度和路径形态；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ret = parse_bottom_shell_layers(gcode_path, expected_layers=expected_layers)

    assert ret[0], (
        f"bottom shell layers expected {expected_layers}, got violations: {ret[2]}"
    )


# ================== bottom_shell_thickness ==================
@pytest.mark.engine_params
def test_bottom_shell_thickness(
        slice_and_export: Path,
        expected_bottom_shell_thickness: float,
):
    # 验证方法：使用实体、薄壁、桥接或填充专用 3MF切片，解析Top/Bottom surface 连续层数、厚度和路径形态；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, matched_layers, details = parse_bottom_shell_thickness(
        gcode_path,
        expected_bottom_shell_thickness=expected_bottom_shell_thickness,
    )

    layer_height = details["layer_height"]
    base_thickness = details["base_thickness"]
    base_layers = details["config_bottom_shell_layers"]
    calculated_layers = _layers_from_thickness(
        expected_bottom_shell_thickness,
        base_thickness,
        base_layers,
        layer_height,
    )

    assert calculated_layers == details["layers_from_thickness"], (
        f"layers_from_thickness mismatch: expected {calculated_layers}, "
        f"got {details['layers_from_thickness']}"
    )

    target_layers = details["target_layers"]
    assert ok, (
        f"bottom shell thickness check failed: target_layers={target_layers}, "
        f"violations={details['violations']}"
    )
    assert matched_layers == target_layers, (
        f"matched_layers={matched_layers} must equal target_layers={target_layers}"
    )
