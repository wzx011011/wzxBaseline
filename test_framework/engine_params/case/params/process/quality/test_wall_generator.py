from __future__ import annotations

from pathlib import Path

import pytest

from engine_params.src.gcode.process.quality.wall_generator_check import (
    WallGenerator,
    parse_wall_generator,
    parse_wall_transition_angle,
    parse_wall_transition_filter_deviation,
    parse_wall_transition_length,
    parse_wall_distribution_count,
    parse_min_feature_size,
    parse_min_bead_width,
    parse_initial_layer_min_bead_width,
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


# ================== wall_transition_angle ==================
@pytest.mark.engine_params
def test_wall_transition_angle(slice_and_export: Path, expected_wall_transition_angle: float):
    """验证 Arachne 墙线数量切换允许的转角。

    C3DSlicer ``WallToolPaths.cpp`` 将该值转为弧度筛选 transitioning angle；规划在渐宽
    楔形轮廓上定位单墙变双墙的过渡点，并比较不同角度设置下保留/拆分的过渡段。
    3MF 使用包含 5/10/15° 三段渐宽楔形的薄壁板，固定 wall_generator=arachne。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_wall_transition_angle(gcode_path, expected_wall_transition_angle)
    assert ok, f"wall_transition_angle expected {expected_wall_transition_angle}, actual {actual}, details: {details}"


# ================== wall_transition_filter_deviation ==================
@pytest.mark.engine_params
def test_wall_transition_filter_deviation(slice_and_export: Path, expected_wall_transition_filter_deviation: str):
    """验证过滤短墙宽过渡时允许的线宽偏差。

    C3DSlicer 以喷嘴直径百分比换算 ``allowed_filter_deviation``；规划统计楔形薄壁上的
    短过渡及线宽峰谷，偏差容限增大时更多短过渡被合并且剩余线宽偏差不超阈值。
    3MF 使用周期性微小宽度起伏的薄壁波纹板。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_wall_transition_filter_deviation(gcode_path, expected_wall_transition_filter_deviation)
    assert ok, f"wall_transition_filter_deviation expected {expected_wall_transition_filter_deviation}, actual {actual}, details: {details}"


# ================== wall_transition_length ==================
@pytest.mark.engine_params
def test_wall_transition_length(slice_and_export: Path, expected_wall_transition_length: str):
    """验证 Arachne 墙宽过渡的最小展开长度。

    C3DSlicer 按喷嘴百分比换算 transition length 并用于墙数切换；规划测量从线宽开始变化
    到新墙数稳定的路径长度，应随设置值增加而变长并接近期望换算值。
    3MF 使用长直渐宽楔形薄壁，确保两端均有稳定单墙/双墙区域。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_wall_transition_length(gcode_path, expected_wall_transition_length)
    assert ok, f"wall_transition_length expected {expected_wall_transition_length}, actual {actual}, details: {details}"


# ================== wall_distribution_count ==================
@pytest.mark.engine_params
def test_wall_distribution_count(slice_and_export: Path, expected_wall_distribution_count: float):
    """验证宽度变化分摊到多少圈内墙。

    C3DSlicer 将该整数作为 DistributedBeadingStrategy 的分布半径；规划在渐变壁厚截面
    逐圈读取线宽，统计共同承担余量的墙圈数量。源码中半径 1 与 2 的权重系数同为 1，
    因而两者路径一致；半径 3 应把宽度变化扩散到更多相邻墙圈。
    3MF 使用可容纳六圈墙、壁厚由 3 mm 缓慢增至 5 mm 的椭圆内孔环壁。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_wall_distribution_count(gcode_path, expected_wall_distribution_count)
    assert ok, (
        "wall_distribution_count behavior mismatch: "
        f"configured={expected_wall_distribution_count}, "
        f"variable_path_components={actual}, details={details}"
    )


# ================== min_feature_size ==================
@pytest.mark.engine_params
def test_min_feature_size(slice_and_export: Path, expected_min_feature_size: str):
    """验证 Arachne 可加宽并保留的最小模型特征。

    C3DSlicer 的 WideningBeadingStrategy 对小于该尺寸的特征不生成墙；规划检查不同宽度
    独立薄肋是否有挤出路径，跨越阈值时结果由消失变为保留。
    3MF 使用喷嘴直径 15%~35% 的多根薄肋，彼此间距足够避免合并。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_min_feature_size(gcode_path, expected_min_feature_size)
    assert ok, f"min_feature_size expected {expected_min_feature_size}, actual {actual}, details: {details}"


# ================== min_bead_width ==================
@pytest.mark.engine_params
def test_min_bead_width(slice_and_export: Path, expected_min_bead_width: str):
    """验证非首层 Arachne 加宽薄特征采用的最小挤出线宽。

    C3DSlicer 以喷嘴百分比设置 WideningBeadingStrategy 的最小输出 bead；规划在第二层以后
    提取刚超过 min_feature_size 的薄肋线宽；该参数是最小输出下限，因此实际最窄线宽
    应不低于期望换算值，并在窄肋模型上保持接近该下限。
    3MF 使用由窄到宽的竖直薄肋阵列并打印至少五层。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_min_bead_width(gcode_path, expected_min_bead_width)
    assert ok, f"min_bead_width expected {expected_min_bead_width}, actual {actual}, details: {details}"


# ================== initial_layer_min_bead_width ==================
@pytest.mark.engine_params
def test_initial_layer_min_bead_width(slice_and_export: Path, expected_initial_layer_min_bead_width: str):
    """验证首层专用的 Arachne 最小 bead 宽度。

    C3DSlicer ``make_paths_params`` 仅在 layer_id=0 用该值覆盖 min_bead_width；规划分别统计
    首层和第二层薄肋线宽；首层最小值应不低于该专用下限，后续层回到
    min_bead_width 的下限约束。
    3MF 使用贯穿多层的窄肋阵列，使同一几何可进行逐层对照。
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual, details = parse_initial_layer_min_bead_width(gcode_path, expected_initial_layer_min_bead_width)
    assert ok, f"initial_layer_min_bead_width expected {expected_initial_layer_min_bead_width}, actual {actual}, details: {details}"
