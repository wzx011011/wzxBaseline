from __future__ import annotations

from pathlib import Path

import pytest

from engine_params.src.gcode.wipe_speed_check import check_wipe_speed_by_layer
from engine_params.src.gcode.process.quality.seam_check import (
    parse_seam_position,
    parse_seam_gap,
    parse_staggered_inner_seams,
    parse_seam_slope_type,
    parse_scarf_joint_flow_ratio,
    parse_seam_slope_conditional,
    parse_seam_slope_entire_loop,
    parse_seam_slope_inner_walls,
    parse_seam_slope_min_length,
    parse_seam_slope_start_height,
    parse_seam_slope_steps,
    parse_scarf_angle_threshold,
    parse_scarf_joint_speed,
    parse_scarf_overhang_threshold,
    parse_seam_position_aligned_L3,
    parse_seam_position_back_L3,
    parse_seam_position_nearest_L3,
    parse_seam_position_assemble_zgap_L3,
    parse_seam_position_random_L3,)


# ================== seam_position ==================
@pytest.mark.engine_params
def test_seam_position(slice_and_export: Path, expected_seam_position: str):
    """验证外墙接缝的空间分布。

    C3DSlicer ``SeamPlacer.cpp`` 按 aligned/nearest/random 选择闭环起点；规划提取每层
    Outer Wall 首挤出点，aligned 应沿 Z 聚集、nearest 应靠近上一段终点、random 应分散。
    3MF 使用无尖角圆柱并打印足够层数，避免几何角点替算法强制选点。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_seam_position(gcode_path, expected_seam_position)
    assert ok, f"seam_position expected {expected_seam_position}, actual {actual}, details: {details}"


# ================== seam_gap ==================
@pytest.mark.engine_params
def test_seam_gap(slice_and_export: Path, expected_seam_gap: float):
    """验证闭环末端被裁掉的接缝间隙长度。

    C3DSlicer 在 ``ExtrusionEntity.cpp`` 从闭环最后一段移除 ``seam_gap``；规划计算
    外墙闭环首尾点沿轮廓的缺口长度，扣除 G-code 分辨率后应等于绝对值或喷嘴百分比换算值。
    3MF 使用大直径圆柱，使接缝所在末段长度始终大于最大测试间隙。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_seam_gap(gcode_path, expected_seam_gap, tolerance=0.001)
    assert ok, f"seam_gap expected {expected_seam_gap}, actual {actual}, details: {details}"


# ================== staggered_inner_seams ==================
@pytest.mark.engine_params
def test_staggered_inner_seams(slice_and_export: Path, expected_staggered: bool):
    """验证内墙接缝相对外墙接缝的交错。

    C3DSlicer 在 ``SeamPlacer.cpp`` 对 inner loop 按环长偏移起点；规划逐层比较同一岛
    外墙和各内墙首点的弧长位置，开启时不应重合且各圈有规律错位，关闭时应基本对齐。
    3MF 使用至少四圈墙的大圆筒，保证每个闭环都有清晰接缝。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_staggered_inner_seams(gcode_path, expected_staggered)
    assert ok, f"staggered_inner_seams expected {expected_staggered}, actual {actual}, details: {details}"


# ================== seam_slope_type ==================
@pytest.mark.engine_params
@pytest.mark.xfail(reason="seam_slope_type parameter may not be supported by current slicer version")
def test_seam_slope_type(slice_and_export: Path, expected_slope_type: str):
    """验证普通接缝与 scarf 接缝斜坡模式。

    C3DSlicer 在 ``GCode.cpp`` 仅当类型非 none 时创建 ``ExtrusionLoopSloped``；规划检查
    接缝邻域 Z/E 是否沿路径渐变，none 不应有渐变，scarf 模式应有连续升降坡。
    3MF 使用光滑大圆柱，关闭 conditional 并固定接缝位置以稳定触发斜坡。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_seam_slope_type(gcode_path, expected_slope_type)
    assert ok, f"seam_slope_type expected {expected_slope_type}, actual {actual}, details: {details}"


# ================== scarf_joint_flow_ratio ==================
@pytest.mark.engine_params
def test_scarf_joint_flow_ratio(slice_and_export: Path, expected_flow_ratio: float):
    """验证 scarf 接缝重叠段的流量倍率。

    C3DSlicer 在斜坡段将 ``mm3_per_mm`` 乘以该倍率；规划对同速同线宽的 scarf 段统计
    ``E/XY长度``，相对普通外墙或 1.0 基准的比率应等于期望值。
    3MF 使用大圆柱并强制启用整圈 scarf，提供足够长的稳定采样段。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_scarf_joint_flow_ratio(
        gcode_path, expected_flow_ratio, tolerance=0.01
    )
    assert ok, f"scarf_joint_flow_ratio expected {expected_flow_ratio}, actual {actual}, details: {details}"


# ================== wipe_speed ==================
@pytest.mark.engine_params
def test_wipe_speed(slice_and_export: Path, expected_has_wipe: bool) -> None:
    """
    slice_and_export fixture 已完成导出，并返回导出的 gcode Path。
    这里只做解析与断言（占位解析器逻辑）。
    """
    gcode_path: Path = slice_and_export  # fixture 返回的文件路径
    assert gcode_path.exists(), "导出的 gcode 文件不存在（fixture 逻辑异常）"

    wipe_cfg: dict[str, object] = check_wipe_speed_by_layer(gcode_path, 500)
    # 通过配置结果判断是否检测到了 wipe 指令，必须与预期保持一致
    assert bool(wipe_cfg) is expected_has_wipe, (
        f"wipe 检测结果应为 {expected_has_wipe}，实际为 {bool(wipe_cfg)}，详情: {wipe_cfg}"
    )
    assert wipe_cfg is not None, "未在 G-code 中检测到 wipe"
    # TODO: 完成 wipe 相关的具体断言逻辑


# ================== seam_slope_conditional ==================
@pytest.mark.engine_params
def test_seam_slope_conditional(slice_and_export: Path, expected_seam_slope_conditional: bool):
    """验证 scarf 是否受轮廓平滑度和悬垂条件限制。

    C3DSlicer 开启 conditional 后调用 ``loop.is_smooth``，并可叠加 overhang threshold；
    规划比较圆形光滑岛和尖角星形岛的斜坡段，开启时只在满足条件的岛出现。
    3MF 同盘放置圆柱、方柱和带悬垂圆柱，形成正反样本。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_seam_slope_conditional(gcode_path, expected_seam_slope_conditional)
    assert ok, f"seam_slope_conditional expected {expected_seam_slope_conditional}, actual {actual}, details: {details}"


# ================== seam_slope_entire_loop ==================
@pytest.mark.engine_params
def test_seam_slope_entire_loop(slice_and_export: Path, expected_seam_slope_entire_loop: bool):
    """验证 scarf 斜坡覆盖整圈还是最小长度。

    C3DSlicer 开启时令 slope_min_length 等于完整 loop_length；规划统计发生 Z/E 渐变的
    外墙累计弧长，开启时接近整圈，关闭时接近 seam_slope_min_length。
    3MF 使用周长远大于最小斜坡长度的圆柱以放大差异。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_seam_slope_entire_loop(gcode_path, expected_seam_slope_entire_loop)
    assert ok, f"seam_slope_entire_loop expected {expected_seam_slope_entire_loop}, actual {actual}, details: {details}"


# ================== seam_slope_inner_walls ==================
@pytest.mark.engine_params
def test_seam_slope_inner_walls(slice_and_export: Path, expected_seam_slope_inner_walls: bool):
    """验证 scarf 是否扩展到内墙。

    C3DSlicer 的 enable 条件默认只含 External Perimeter，开关开启后加入 Perimeter；
    规划分别扫描 Outer/Inner Wall 的 Z/E 渐变，外墙始终有 scarf，内墙仅开启时出现。
    3MF 使用四墙厚圆筒并启用稳定的非条件 scarf。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_seam_slope_inner_walls(gcode_path, expected_seam_slope_inner_walls)
    assert ok, f"seam_slope_inner_walls expected {expected_seam_slope_inner_walls}, actual {actual}, details: {details}"


# ================== seam_slope_min_length ==================
@pytest.mark.engine_params
def test_seam_slope_min_length(slice_and_export: Path, expected_seam_slope_min_length: float):
    """验证局部 scarf 斜坡的目标弧长。

    C3DSlicer 取 ``min(configured_length, loop_length)``；规划沿外墙累计斜坡段 XY 长度，
    应等于期望值，超过周长时应钳制为整圈。3MF 使用周长已知的大圆柱并关闭 entire_loop。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_seam_slope_min_length(gcode_path, expected_seam_slope_min_length)
    assert ok, f"seam_slope_min_length expected {expected_seam_slope_min_length}, actual {actual}, details: {details}"


# ================== seam_slope_start_height ==================
@pytest.mark.engine_params
def test_seam_slope_start_height(slice_and_export: Path, expected_seam_slope_start_height: float):
    """验证 scarf 起点相对本层的 Z 高度。

    C3DSlicer 对绝对值用 ``value/layer_height``、百分比用 ``value/100`` 计算起始比例；
    规划读取斜坡第一挤出点 Z，与上一层 Z 的差应等于期望起始高度并在斜坡内渐升。
    3MF 使用固定层高圆柱，确保 0/0.5/1.0 的设置均能产生可区分轨迹。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_seam_slope_start_height(gcode_path, expected_seam_slope_start_height)
    assert ok, f"seam_slope_start_height expected {expected_seam_slope_start_height}, actual {actual}, details: {details}"


# ================== seam_slope_steps ==================
@pytest.mark.engine_params
def test_seam_slope_steps(slice_and_export: Path, expected_seam_slope_steps: float):
    """验证 scarf 斜坡离散分段数。

    C3DSlicer 使用 ``seam_slope_steps`` 设定最少细分数并据此限制最大段长；规划在
    固定斜坡弧长内统计不同 Z 级数，验证 16 边形原始分段经最少步数约束后的结果。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_seam_slope_steps(gcode_path, expected_seam_slope_steps)
    assert ok, f"seam_slope_steps expected {expected_seam_slope_steps}, actual {actual}, details: {details}"


# ================== scarf_angle_threshold ==================
@pytest.mark.engine_params
def test_scarf_angle_threshold(slice_and_export: Path, expected_scarf_angle_threshold: float):
    """验证 conditional scarf 的轮廓转角阈值。

    C3DSlicer 将角度转为弧度传给 ``loop.is_smooth``；规划在多个已知转角的闭环上检测
    scarf 是否生成，低于平滑阈值的轮廓通过、尖锐轮廓被拒绝。
    3MF 同盘放置圆形、30°转折和60°转折轮廓，并开启 conditional。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_scarf_angle_threshold(gcode_path, expected_scarf_angle_threshold)
    assert ok, f"scarf_angle_threshold expected {expected_scarf_angle_threshold}, actual {actual}, details: {details}"


# ================== scarf_joint_speed ==================
@pytest.mark.engine_params
def test_scarf_joint_speed(slice_and_export: Path, expected_scarf_joint_speed: float):
    """验证 scarf 段速度上限。

    C3DSlicer 对内外墙取 ``min(原墙速, scarf_joint_speed)``；规划解析 scarf 渐变段 F 值，
    设置低于墙速时应被限速，0 或高于墙速时按实现回退/钳制为原墙速。
    3MF 使用长圆周和固定墙速，保证存在恒速 scarf 段。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_scarf_joint_speed(gcode_path, expected_scarf_joint_speed)
    assert ok, f"scarf_joint_speed expected {expected_scarf_joint_speed}, actual {actual}, details: {details}"


# ================== scarf_overhang_threshold ==================
@pytest.mark.engine_params
def test_scarf_overhang_threshold(slice_and_export: Path, expected_scarf_overhang_threshold: float):
    """验证悬垂接缝启用 scarf 的支撑宽度阈值。

    C3DSlicer 将该百分比乘线宽，并要求 seam_overhang 小于结果；规划在不同悬空宽度的
    外墙接缝处判断是否产生斜坡，跨越阈值时结果应翻转。
    3MF 使用三组逐级横向错层圆柱，固定接缝落在悬垂方向并开启 conditional。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_scarf_overhang_threshold(gcode_path, expected_scarf_overhang_threshold)
    assert ok, f"scarf_overhang_threshold expected {expected_scarf_overhang_threshold}, actual {actual}, details: {details}"


# ================== seam_position_aligned_L3 ==================
@pytest.mark.engine_params
def test_seam_position_aligned_L3(slice_and_export: Path):
    """保留 L3 用例名兼容现有选择器，按 L2 接缝位置分布验证 aligned。"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual_match, details = parse_seam_position_aligned_L3(gcode_path, expected_match=True)
    assert ok, f"seam_position_aligned_L3 expected match True, actual match {actual_match}, details: {details}"


# ================== seam_position_back_L3 ==================
@pytest.mark.engine_params
def test_seam_position_back_L3(slice_and_export: Path):
    """保留 L3 用例名兼容现有选择器，按 L2 接缝位置分布验证 back。"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual_match, details = parse_seam_position_back_L3(gcode_path, expected_match=True)
    assert ok, f"seam_position_back_L3 expected match True, actual match {actual_match}, details: {details}"


# ================== seam_position_nearest_L3 ==================
@pytest.mark.engine_params
def test_seam_position_nearest_L3(slice_and_export: Path):
    """保留 L3 用例名兼容现有选择器，按 L2 接缝位置分布验证 nearest。"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual_match, details = parse_seam_position_nearest_L3(gcode_path, expected_match=True)
    assert ok, f"seam_position_nearest_L3 expected match True, actual match {actual_match}, details: {details}"


# ================== seam_position_assemble_zgap_L3 ==================
@pytest.mark.engine_params
def test_seam_position_assemble_zgap_L3(slice_and_export: Path):
    """保留 L3 用例名兼容现有选择器，按 L2 接缝位置分布验证 assemble_zgap。"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual_match, details = parse_seam_position_assemble_zgap_L3(gcode_path, expected_match=True)
    assert ok, f"seam_position_assemble_zgap_L3 expected match True, actual match {actual_match}, details: {details}"


# ================== seam_position_random_L3 ==================
@pytest.mark.engine_params
def test_seam_position_random_L3(slice_and_export: Path):
    """保留 L3 用例名兼容现有选择器，按 L2 接缝位置分布验证 random。"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual_match, details = parse_seam_position_random_L3(gcode_path, expected_match=True)
    assert ok, f"seam_position_random_L3 expected match True, actual match {actual_match}, details: {details}"
