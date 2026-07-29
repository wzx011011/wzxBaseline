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
    """验证顶面识别的最小暴露宽度。

    C3DSlicer ``PerimeterGenerator.cpp`` 先按该宽度腐蚀上层投影，再确定 top surface；
    规划统计不同宽度台阶上 Top Surface 与外墙路径，窄于阈值的条带不应按顶面处理。
    3MF 使用宽度渐变的阶梯顶面，条带宽度跨越线宽百分比换算后的阈值。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_min_width_top_surface(gcode_path, expected_min_width_top_surface)
    assert ok, f"min_width_top_surface expected {expected_min_width_top_surface}, actual {actual}, details: {details}"


# ================== only_one_wall_first_layer ==================
@pytest.mark.engine_params
def test_only_one_wall_first_layer(slice_and_export: Path, expected_only_one_wall_first_layer: bool):
    """验证首层强制单墙且不影响后续层。

    C3DSlicer 在 classic 与 Arachne 分支都只对 layer_id=0 将额外 loop 数归零；规划按层
    统计同一岛的墙圈数，开启时首层为 1、第二层恢复 wall_loops，关闭时两层均为配置圈数。
    3MF 使用壁厚足够容纳四圈墙的直方柱，避免薄壁自动减墙。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_only_one_wall_first_layer(gcode_path, expected_only_one_wall_first_layer)
    assert ok, f"only_one_wall_first_layer expected {expected_only_one_wall_first_layer}, actual {actual}, details: {details}"


# ================== detect_thin_wall ==================
@pytest.mark.engine_params
def test_detect_thin_wall(slice_and_export: Path, expected_detect_thin_wall: bool):
    """验证 classic 墙生成器对窄特征的保留。

    C3DSlicer 在剩余区域仅当 detect_thin_wall 开启时生成 thin wall；规划检查多条不同宽度
    薄肋的 Outer Wall 挤出，开启时可打印宽度的肋应保留，关闭时相应路径消失。
    3MF 使用 0.25/0.35/0.45 mm 独立薄肋并固定 classic wall generator。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_detect_thin_wall(gcode_path, expected_detect_thin_wall)
    assert ok, f"detect_thin_wall expected {expected_detect_thin_wall}, actual {actual}, details: {details}"


# ================== detect_overhang_wall ==================
@pytest.mark.engine_params
def test_detect_overhang_wall(slice_and_export: Path, expected_detect_overhang_wall: bool):
    """验证悬垂墙角色识别。

    C3DSlicer 将下层轮廓外扩半喷嘴后与当前墙求差来标记 overhang perimeter；规划统计
    悬挑层 Overhang Wall 段长度，开启时应出现且使用悬垂属性，关闭时归为普通墙。
    3MF 使用下窄上宽的半边悬挑台阶，另一半保持有支撑作为同层对照。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_detect_overhang_wall(gcode_path, expected_detect_overhang_wall)
    assert ok, f"detect_overhang_wall expected {expected_detect_overhang_wall}, actual {actual}, details: {details}"


# ================== overhang_reverse ==================
@pytest.mark.engine_params
def test_overhang_reverse(slice_and_export: Path, expected_overhang_reverse: bool):
    """验证悬垂墙的打印方向反转。

    C3DSlicer 在 PerimeterGenerator 中按悬垂长度占比决定反转闭环方向；规划由 Outer Wall
    路径有向面积判断 CW/CCW，开启且超过阈值时方向相对关闭组翻转。
    3MF 使用大部分周长悬空的偏心上层，确保触发反转条件。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_overhang_reverse(gcode_path, expected_overhang_reverse)
    assert ok, f"overhang_reverse expected {expected_overhang_reverse}, actual {actual}, details: {details}"


# ================== overhang_reverse_internal_only ==================
@pytest.mark.engine_params
def test_overhang_reverse_internal_only(slice_and_export: Path, expected_overhang_reverse_internal_only: bool):
    """验证悬垂反转是否只作用于内墙。

    C3DSlicer 在 wall_direction=Auto 时用该开关限制反转对象；规划分别计算外墙和内墙
    CW/CCW，开启时只内墙翻转，关闭时符合 overhang_reverse 的全墙策略。
    3MF 使用至少三圈墙的偏心悬挑圆筒，并开启 detect_overhang_wall 与 overhang_reverse。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_overhang_reverse_internal_only(gcode_path, expected_overhang_reverse_internal_only)
    assert ok, f"overhang_reverse_internal_only expected {expected_overhang_reverse_internal_only}, actual {actual}, details: {details}"


# ================== overhang_reverse_threshold ==================
@pytest.mark.engine_params
def test_overhang_reverse_threshold(slice_and_export: Path, expected_overhang_reverse_threshold: str):
    """验证触发墙方向反转的悬垂占比阈值。

    C3DSlicer 将百分比按 extrusion width 换算并参与悬垂判定；规划对多种悬空占比的闭环
    判断路径方向，只有超过阈值的环发生反转。
    3MF 同盘放置 35%/50%/65% 周长悬空的三个偏心台阶体。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_overhang_reverse_threshold(gcode_path, expected_overhang_reverse_threshold)
    assert ok, f"overhang_reverse_threshold expected {expected_overhang_reverse_threshold}, actual {actual}, details: {details}"


# ================== wipe_on_loops ==================
@pytest.mark.engine_params
def test_wipe_on_loops(slice_and_export: Path, expected_wipe_on_loops: bool):
    """验证外墙闭环结束后的沿环擦拭。

    C3DSlicer 仅在外墙、墙数大于 1 且路径点充分时追加 wipe；规划在 Outer Wall 结束后
    检查无 E 的沿轮廓移动，开启时存在且方向/位置连续，关闭时不存在。
    3MF 使用三墙大圆柱，避免短折线不满足实现前置条件。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_wipe_on_loops(gcode_path, expected_wipe_on_loops)
    assert ok, f"wipe_on_loops expected {expected_wipe_on_loops}, actual {actual}, details: {details}"


# ================== wipe_before_external_loop ==================
@pytest.mark.engine_params
def test_wipe_before_external_loop(slice_and_export: Path, expected_wipe_before_external_loop: bool):
    """验证外墙开始前从相邻内墙执行擦拭过渡。

    C3DSlicer 要求外墙路径前后均有效且 region 有多圈墙；规划检查进入 Outer Wall 前的
    无 E 路径是否沿上一内墙延伸，开启时出现、关闭时直接 travel 到外墙起点。
    3MF 使用四墙厚圆筒并固定 inner-to-outer 墙序。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_wipe_before_external_loop(gcode_path, expected_wipe_before_external_loop)
    assert ok, f"wipe_before_external_loop expected {expected_wipe_before_external_loop}, actual {actual}, details: {details}"


# ================== small_area_infill_flow_compensation ==================
@pytest.mark.engine_params
def test_small_area_infill_flow_compensation(slice_and_export: Path, expected_small_area_infill_flow_compensation: bool):
    """验证小面积填充的流量补偿开关。

    C3DSlicer 在 ``GCode.cpp`` 对小面积 infill 调用补偿器修改 ``mm3_per_mm``；规划按岛
    统计 Internal Solid Infill 的 ``E/长度``，开启时小岛按曲线降流，大面积对照岛接近 1。
    3MF 同盘放置 0.2/0.8/2/10 mm² 的封闭实心填充小岛。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_small_area_infill_flow_compensation(gcode_path, expected_small_area_infill_flow_compensation)
    assert ok, f"small_area_infill_flow_compensation expected {expected_small_area_infill_flow_compensation}, actual {actual}, details: {details}"


# ================== small_area_infill_flow_compensation_model ==================
@pytest.mark.engine_params
def test_small_area_infill_flow_compensation_model(slice_and_export: Path, expected_small_area_infill_flow_compensation_model: list):
    """验证面积—流量补偿曲线的插值结果。

    C3DSlicer ``SmallAreaInfillFlowCompensator`` 读取每个 ``面积,倍率`` 节点并插值；
    规划为每个面积小岛测量 ``E/长度`` 相对大面积基准的比例，节点处命中配置值，节点间
    命中插值值。3MF 使用覆盖全部曲线关键点的多岛阵列，并开启补偿开关。

    当前 3MF 数组参数写入限制需先修复；在此之前该用例只能验证系统默认曲线。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_small_area_infill_flow_compensation_model(gcode_path, expected_small_area_infill_flow_compensation_model)
    assert ok, f"small_area_infill_flow_compensation_model expected {expected_small_area_infill_flow_compensation_model}, actual {actual}, details: {details}"
