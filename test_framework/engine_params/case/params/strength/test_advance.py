from pathlib import Path

import pytest

from engine_params.src.gcode.strength.advance_check import (
    parse_detect_narrow_internal_solid_infill,
    parse_bridge_angle,
    parse_minimum_sparse_infill_area,
    parse_infill_combination,
    parse_ensure_vertical_shell_thickness,
)


# ================== detect_narrow_internal_solid_infill ==================
@pytest.mark.engine_params
def test_detect_narrow_internal_solid_infill(
        slice_and_export: Path,
        expected_enabled: bool,
) -> None:
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, details = parse_detect_narrow_internal_solid_infill(
        gcode_path,
        expected_enabled=expected_enabled,
    )

    expected_polyline_count = 3 if expected_enabled else 1
    assert details["expected_polyline_count"] == expected_polyline_count

    assert details["config_enabled"] == expected_enabled, (
        f"CONFIG detect_narrow_internal_solid_infill 应为 {expected_enabled}, "
        f"实际 {details['config_enabled']}"
    )

    assert ok, (
        "detect_narrow_internal_solid_infill 校验未通过: "
        f"solid_layers={details['solid_layers']}, violations={details['violations']}"
    )


# ================== bridge_angle ==================
@pytest.mark.engine_params
def test_bridge_angle(
        slice_and_export: Path,
        expected_bridge_angle: float,
        baseline_gcode: str | Path | None,
) -> None:
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual_angle, details = parse_bridge_angle(
        gcode_path,
        expected_bridge_angle=expected_bridge_angle,
        baseline_gcode=Path(baseline_gcode) if baseline_gcode else None,
    )

    if abs(expected_bridge_angle) < 1e-6:
        assert ok, (
            "bridge_angle(0°) 快照对比失败: "
            f"baseline={details.get('baseline_gcode')}, "
            f"compare_details={details.get('compare_details')}"
        )
    else:
        assert actual_angle is not None
        assert ok, (
            f"bridge_angle 角度校验失败: expected={expected_bridge_angle}, "
            f"actual={actual_angle}, details={details}"
        )


# ================== minimum_sparse_infill_area ==================
@pytest.mark.engine_params
def test_minimum_sparse_infill_area(
        slice_and_export: Path,
        expected_has_sp_infill: bool,
) -> None:
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, details = parse_minimum_sparse_infill_area(gcode_path)

    assert ok == expected_has_sp_infill, (
        f"minimum_sparse_infill_area 结果不匹配: "
        f"expected_has_sp_infill={expected_has_sp_infill}, actual_ok={ok}, "
        f"violations={details['violations']}, reports={details['layer_reports']}"
    )


# ================== infill_combination ==================
@pytest.mark.engine_params
def test_infill_combination(
        slice_and_export: Path,
        expected_infill_combination: bool,
        expected_interval: int,
) -> None:
    """
    稀疏填充合并：检测稀疏填充层间隔是否满足 N=int(nozzle_diameter/layer_height) ⇒ diff=N-1。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_infill_combination(
        gcode_path,
        expected_enabled=expected_infill_combination,
        expected_interval=expected_interval,
    )

    assert ok, (
        f"infill_combination 校验失败: expected={expected_infill_combination}, "
        f"details={details}"
    )

# ================== ensure_vertical_shell_thickness ==================
@pytest.mark.engine_params
def test_ensure_vertical_shell_thickness(
        slice_and_export: Path,
        expected_ensure_vertical_shell_thickness: str,
        baseline_gcode: str | Path,
        tolerance: float,
) -> None:
    """
    ensure_vertical_shell_thickness：与基线 G-code 逐层比对外/内墙轮廓，忽略轮廓顺序差异。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_ensure_vertical_shell_thickness(
        gcode_path,
        expected_value=expected_ensure_vertical_shell_thickness,
        baseline_gcode=baseline_gcode,
        tolerance=tolerance,
    )
    assert ok, f"details={details}"
