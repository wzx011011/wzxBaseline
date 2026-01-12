from pathlib import Path

import pytest

from engine_params.src.gcode.process.quality.wall_and_surfaces_check import *

# ================== wall_sequence ==================

@pytest.mark.engine_params
def test_wall_sequence(slice_and_export: Path,
                       expected_sequence: WallStyle):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ret: tuple[bool, WallStyle, list[tuple[int, WallStyle, list[str]]]] = parse_wall_sequence(
        gcode_path, expected_style=expected_sequence
    )

    assert ret[0], f"gcode中的墙顺序不是期望的{expected_sequence}顺序，而是{ret[2]}。"

# ================== is_infill_first ==================


@pytest.mark.engine_params
def test_is_infill_first(slice_and_export: Path,
                        expected_first: bool):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ret = parse_is_infill_first(gcode_path, expected_first=expected_first)

    assert ret[0], f"输入期望is_infill_first =={ret[1]}，然而gcode的解析情况是{ret[2]}。"


# ================== wall_direction ==================

@pytest.mark.engine_params
def test_wall_direction(slice_and_export: Path,
                        expected_direction: WallDirection):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ret = parse_wall_directions(gcode_path, expected_dir=expected_direction)

    assert ret[0], f"gcode中的墙打印顺序不是期望的{ret[1]}顺序，而是{ret[2]}。"

# ================== only_one_wall_top ==================

@pytest.mark.engine_params
def test_only_one_wall_top(slice_and_export: Path,
                        expected_only_one_wall_top: bool):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ret = parse_only_one_wall_top(gcode_path, expected_only_one_wall_top=expected_only_one_wall_top)

    assert ret[0], f"期望顶面单层墙，而{ret[2]}。" if {ret[1]} else f"期望顶面不是单层墙，而{ret[2]}。"

# ================== one_wall_first_layer ==================

@pytest.mark.engine_params
def test_one_wall_first_layer(slice_and_export: Path,
                              expected_only_one_wall_first_layer: bool):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ret = parse_one_wall_first_layer(
        gcode_path, expected_one_wall_first_layer=expected_only_one_wall_first_layer
    )

    assert ret[0], (
        f"one_wall_first_layer expected {expected_only_one_wall_first_layer}, details {ret[2]}"
    )


# ================== top_solid_infill_flow_ratio ==================

@pytest.mark.engine_params
def test_top_solid_infill_flow_ratio(
    slice_and_export: Path,
    expected_ratio: float,
    baseline_gcode: str | Path,
    tol: float,
):
    gcode_path: Path = slice_and_export
    baseline_path = Path(baseline_gcode)
    assert gcode_path.exists()
    assert baseline_path.exists()

    ok, ratio, details = parse_top_solid_infill_flow_ratio(
        tested_gcode=gcode_path,
        baseline_gcode=baseline_path,
        expected_ratio=expected_ratio,
        tol=tol,
    )

    assert ok, (
        f"top_solid_infill_flow_ratio expected {expected_ratio}, actual {ratio}, details: {details}"
    )


# ================== bottom_solid_infill_flow_ratio ==================

@pytest.mark.engine_params
def test_bottom_solid_infill_flow_ratio(
    slice_and_export: Path,
    expected_ratio: float,
    baseline_gcode: str | Path,
    tol: float,
):
    gcode_path: Path = slice_and_export
    baseline_path = Path(baseline_gcode)
    assert gcode_path.exists()
    assert baseline_path.exists()

    ok, ratio, details = parse_bottom_solid_infill_flow_ratio(
        tested_gcode=gcode_path,
        baseline_gcode=baseline_path,
        expected_ratio=expected_ratio,
        tol=tol,
    )

    assert ok, (
        f"bottom_infill_flow_ratio expected {expected_ratio}, actual {ratio}, details: {details}"
    )


# ================== min_width_top_surface ==================
@pytest.mark.engine_params
def test_min_width_top_surface(slice_and_export: Path, expected_min_width_top_surface: str):
    """测试 min_width_top_surface 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_min_width_top_surface(gcode_path, expected_min_width_top_surface)
    assert ok, f"min_width_top_surface expected {expected_min_width_top_surface}, actual {actual}, details: {details}"


# ================== only_one_wall_first_layer ==================
@pytest.mark.engine_params
def test_only_one_wall_first_layer(slice_and_export: Path, expected_only_one_wall_first_layer: bool):
    """测试 only_one_wall_first_layer 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_only_one_wall_first_layer(gcode_path, expected_only_one_wall_first_layer)
    assert ok, f"only_one_wall_first_layer expected {expected_only_one_wall_first_layer}, actual {actual}, details: {details}"


# ================== detect_thin_wall ==================
@pytest.mark.engine_params
def test_detect_thin_wall(slice_and_export: Path, expected_detect_thin_wall: bool):
    """测试 detect_thin_wall 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_detect_thin_wall(gcode_path, expected_detect_thin_wall)
    assert ok, f"detect_thin_wall expected {expected_detect_thin_wall}, actual {actual}, details: {details}"


# ================== detect_overhang_wall ==================
@pytest.mark.engine_params
def test_detect_overhang_wall(slice_and_export: Path, expected_detect_overhang_wall: bool):
    """测试 detect_overhang_wall 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_detect_overhang_wall(gcode_path, expected_detect_overhang_wall)
    assert ok, f"detect_overhang_wall expected {expected_detect_overhang_wall}, actual {actual}, details: {details}"


# ================== overhang_reverse ==================
@pytest.mark.engine_params
def test_overhang_reverse(slice_and_export: Path, expected_overhang_reverse: bool):
    """测试 overhang_reverse 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_overhang_reverse(gcode_path, expected_overhang_reverse)
    assert ok, f"overhang_reverse expected {expected_overhang_reverse}, actual {actual}, details: {details}"


# ================== overhang_reverse_internal_only ==================
@pytest.mark.engine_params
def test_overhang_reverse_internal_only(slice_and_export: Path, expected_overhang_reverse_internal_only: bool):
    """测试 overhang_reverse_internal_only 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_overhang_reverse_internal_only(gcode_path, expected_overhang_reverse_internal_only)
    assert ok, f"overhang_reverse_internal_only expected {expected_overhang_reverse_internal_only}, actual {actual}, details: {details}"


# ================== overhang_reverse_threshold ==================
@pytest.mark.engine_params
def test_overhang_reverse_threshold(slice_and_export: Path, expected_overhang_reverse_threshold: str):
    """测试 overhang_reverse_threshold 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_overhang_reverse_threshold(gcode_path, expected_overhang_reverse_threshold)
    assert ok, f"overhang_reverse_threshold expected {expected_overhang_reverse_threshold}, actual {actual}, details: {details}"


# ================== wipe_on_loops ==================
@pytest.mark.engine_params
def test_wipe_on_loops(slice_and_export: Path, expected_wipe_on_loops: bool):
    """测试 wipe_on_loops 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_wipe_on_loops(gcode_path, expected_wipe_on_loops)
    assert ok, f"wipe_on_loops expected {expected_wipe_on_loops}, actual {actual}, details: {details}"


# ================== wipe_before_external_loop ==================
@pytest.mark.engine_params
def test_wipe_before_external_loop(slice_and_export: Path, expected_wipe_before_external_loop: bool):
    """测试 wipe_before_external_loop 参数"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_wipe_before_external_loop(gcode_path, expected_wipe_before_external_loop)
    assert ok, f"wipe_before_external_loop expected {expected_wipe_before_external_loop}, actual {actual}, details: {details}"


# ================== small_area_infill_flow_compensation ==================
@pytest.mark.engine_params
def test_small_area_infill_flow_compensation(slice_and_export: Path, expected_small_area_infill_flow_compensation: bool):
    """测试 small_area_infill_flow_compensation 参数
    
    该参数控制是否对小面积填充区域进行流量补偿。
    - 启用时：切片器会自动调整小面积区域的挤出流量，改善打印质量
    - 禁用时：使用标准流量，不进行额外补偿
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_small_area_infill_flow_compensation(gcode_path, expected_small_area_infill_flow_compensation)
    assert ok, f"small_area_infill_flow_compensation expected {expected_small_area_infill_flow_compensation}, actual {actual}, details: {details}"


# ================== small_area_infill_flow_compensation_model ==================
@pytest.mark.engine_params
def test_small_area_infill_flow_compensation_model(slice_and_export: Path, expected_small_area_infill_flow_compensation_model: list):
    """测试 small_area_infill_flow_compensation_model 参数
    
    该参数定义小面积流量补偿的曲线模型，是一个数组参数，存储面积与流量比例的映射关系。
    格式: ["0,0", "\n0.2,0.4444", "\n0.4,0.6145", ...]
    - 数组中每个元素表示 "面积,流量比例" 的对应关系
    - 切片器根据此曲线动态调整不同面积区域的流量补偿
    
    注意：当前切片器版本存在已知限制 - 数组类型参数无法通过 3MF 文件自定义，
    即使在 different_settings_to_system 中标记也不会生效。因此测试用例暂时只
    验证 template_model.3mf 中的默认值。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_small_area_infill_flow_compensation_model(gcode_path, expected_small_area_infill_flow_compensation_model)
    assert ok, f"small_area_infill_flow_compensation_model expected {expected_small_area_infill_flow_compensation_model}, actual {actual}, details: {details}"
