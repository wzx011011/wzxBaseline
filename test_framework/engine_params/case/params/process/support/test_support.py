"""Test cases for the independent Process/Support category."""

import pytest
from pathlib import Path
from engine_params.src.gcode.process.support_check import (
    parse_enable_support,
    parse_support_type,
    parse_support_style,
    parse_support_threshold_angle,
    parse_support_on_build_plate_only,
    parse_support_critical_regions_only,
    parse_support_remove_small_overhang,
    parse_raft_layers,
    parse_raft_contact_distance,
    parse_raft_first_layer_density,
    parse_raft_first_layer_expansion,
    parse_support_filament,
    parse_support_interface_filament,
    parse_support_interface_not_for_body,
    parse_support_top_z_distance,
    parse_support_bottom_z_distance,
    parse_support_base_pattern,
    parse_support_base_pattern_tree,
    parse_support_base_pattern_spacing,
    parse_support_angle,
    parse_support_interface_top_layers,
    parse_support_interface_bottom_layers,
    parse_support_interface_pattern,
    parse_support_interface_spacing,
    parse_support_bottom_interface_spacing,
    parse_support_interface_loop_pattern,
    parse_support_interface_speed,
    parse_support_interface_min_area,
    parse_support_expansion,
    parse_support_object_xy_distance,
    parse_support_object_first_layer_gap,
    parse_support_xy_overrides_z,
    parse_bridge_no_support,
    parse_max_bridge_length,
    parse_independent_support_layer_height,
    parse_ironing_support_layer,
    parse_tree_hybrid_cross_height,
    parse_tree_support_branch_diameter,
    parse_tree_support_branch_angle,
    parse_tree_support_wall_count,
    parse_tree_support_wall_count_tree,
    parse_tree_support_branch_distance,
    parse_tree_support_tip_diameter,
)


@pytest.mark.engine_params
def test_enable_support(
    slice_and_export: Path,
    expected_value: str,
):
    """Test enable_support parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：读取 Support/Support interface 挤出块判断支撑是否存在；再比较 Support total 的层数、块数、包围盒、挤出量、风扇和单层最大路径长度。
    gcode_path = slice_and_export
    ok, actual, details = parse_enable_support(gcode_path, expected_value)
    
    assert ok, f"enable_support expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_type(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_type parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对 support_type 枚举值；再比较 Support interface 的覆盖范围、块数、层数、挤出量、单层路径长度和路径数，确认普通/树状及自动/手动类型确实改变支撑。
    gcode_path = slice_and_export
    ok, actual, details = parse_support_type(gcode_path, expected_value)
    
    assert ok, f"support_type expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_style(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_style parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对 support_style 枚举值；再比较 Support 与 Support total 的包围盒、块数、层数、挤出量和单层最大路径长度，确认各支撑风格生成对应几何。
    gcode_path = slice_and_export
    ok, actual, details = parse_support_style(gcode_path, expected_value)
    
    assert ok, f"support_style expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_threshold_angle(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_threshold_angle parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对阈值角度；再比较 Support interface 的覆盖宽度/面积、块数、层数、挤出量、路径数和单层路径长度，确认悬垂阈值改变支撑范围。
    gcode_path = slice_and_export
    ok, actual, details = parse_support_threshold_angle(gcode_path, expected_value)
    
    assert ok, f"support_threshold_angle expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_on_build_plate_only(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_on_build_plate_only parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对仅热床支撑开关；再比较 Support total 的实际挤出块数量，确认非热床可达支撑是否被移除。
    gcode_path = slice_and_export
    ok, actual, details = parse_support_on_build_plate_only(gcode_path, expected_value)
    
    assert ok, f"support_on_build_plate_only expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_critical_regions_only(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_critical_regions_only parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对仅关键区域开关；再比较 Support interface 的包围盒、挤出量、总路径长度及每层/总移动数，确认支撑被收缩到关键区域。
    gcode_path = slice_and_export
    ok, actual, details = parse_support_critical_regions_only(gcode_path, expected_value)
    
    assert ok, f"support_critical_regions_only expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_remove_small_overhang(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_remove_small_overhang parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对移除小悬垂开关；再比较 Support interface 的覆盖范围、块数、层数、挤出量、移动数和总路径长度，确认小支撑区域是否消失。
    gcode_path = slice_and_export
    ok, actual, details = parse_support_remove_small_overhang(gcode_path, expected_value)
    
    assert ok, f"support_remove_small_overhang expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_raft_layers(
    slice_and_export: Path,
    expected_value: str,
):
    """Test raft_layers parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：读取 raft_layers（缺失时按模型首层前的支撑层计数）；再比较 Support interface 的层数、块数、包围盒、挤出量和单层路径长度。
    gcode_path = slice_and_export
    ok, actual, details = parse_raft_layers(gcode_path, expected_value)
    
    assert ok, f"raft_layers expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_raft_contact_distance(
    slice_and_export: Path,
    expected_value: str,
):
    """Test raft_contact_distance parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对筏层接触距离；再比较 Support total 的首末 Z、层数、块数、移动数和总路径长度，确认筏层与模型的垂直布局发生对应变化。
    gcode_path = slice_and_export
    ok, actual, details = parse_raft_contact_distance(gcode_path, expected_value)
    
    assert ok, f"raft_contact_distance expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_raft_first_layer_density(
    slice_and_export: Path,
    expected_value: str,
):
    """Test raft_first_layer_density parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对筏层首层密度；再比较 Support total 的挤出量、移动数、总/单层路径长度以及 T0 路径和挤出量。
    gcode_path = slice_and_export
    ok, actual, details = parse_raft_first_layer_density(gcode_path, expected_value)

    assert ok, f"raft_first_layer_density expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_raft_first_layer_expansion(
    slice_and_export: Path,
    expected_value: str,
):
    """Test raft_first_layer_expansion parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对筏层首层扩展量；再比较 Support total 的包围盒、挤出量、总/单层路径长度、每层移动数和最大线段长度。
    gcode_path = slice_and_export
    ok, actual, details = parse_raft_first_layer_expansion(gcode_path, expected_value)

    assert ok, f"raft_first_layer_expansion expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_top_z_distance(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_top_z_distance parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对顶部 Z 间距配置；并将 Support interface 与上方模型路径按 XY 栅格配对，实测两者的众数 Z 间隙后与语义基线比较。
    gcode_path = slice_and_export
    ok, actual, details = parse_support_top_z_distance(gcode_path, expected_value)

    assert ok, f"support_top_z_distance expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_bottom_z_distance(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_bottom_z_distance parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对底部 Z 间距配置；再比较内外墙、稀疏填充和内部实心填充路径的实际速度档位数，验证底部接触区的切片行为。
    gcode_path = slice_and_export
    ok, actual, details = parse_support_bottom_z_distance(gcode_path, expected_value)

    assert ok, f"support_bottom_z_distance expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_base_pattern(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_base_pattern parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对普通支撑底层图案枚举；再统计 Support total 路径方向分布，比较主方向占比以区分图案。
    gcode_path = slice_and_export
    ok, actual, details = parse_support_base_pattern(gcode_path, expected_value)

    assert ok, f"support_base_pattern expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_base_pattern_tree(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_base_pattern_tree parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对树状支撑底层图案枚举；再比较 Support/Support total 的路径方向占比和最大线段长度，区分默认与网格图案。
    gcode_path = slice_and_export
    ok, actual, details = parse_support_base_pattern_tree(gcode_path, expected_value)

    assert ok, f"support_base_pattern_tree expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_base_pattern_spacing(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_base_pattern_spacing parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对支撑底层间距；再比较 Support interface 的包围盒、块数、层数、挤出量以及单层路径长度，验证疏密变化。
    gcode_path = slice_and_export
    ok, actual, details = parse_support_base_pattern_spacing(gcode_path, expected_value)

    assert ok, f"support_base_pattern_spacing expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_angle(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_angle parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对支撑走线角度；再比较 Support interface 的包围盒、块数、层数、挤出量和单层路径长度，确认旋转后的支撑几何。
    gcode_path = slice_and_export
    ok, actual, details = parse_support_angle(gcode_path, expected_value)

    assert ok, f"support_angle expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_expansion(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_expansion parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对支撑扩展量；再比较 Support interface 的覆盖宽度/面积、块数、层数、挤出量以及单层路径长度和移动数。
    gcode_path = slice_and_export
    ok, actual, details = parse_support_expansion(gcode_path, expected_value)

    assert ok, f"support_expansion expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_object_xy_distance(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_object_xy_distance parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对支撑与模型 XY 距离；再比较 Support interface 挤出线段长度中位数，验证避让距离对路径分段的影响。
    gcode_path = slice_and_export
    ok, actual, details = parse_support_object_xy_distance(gcode_path, expected_value)

    assert ok, f"support_object_xy_distance expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_object_first_layer_gap(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_object_first_layer_gap parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对支撑与模型首层间隙；再比较 Support/Support total 的单层最大路径长度和最大移动数。
    gcode_path = slice_and_export
    ok, actual, details = parse_support_object_first_layer_gap(gcode_path, expected_value)

    assert ok, f"support_object_first_layer_gap expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_xy_overrides_z(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_xy_overrides_z parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对 XY/Z 间距优先级枚举；再比较 Support interface 的块数、层数、挤出量、总/单层路径长度、每层移动数和最低速度。
    gcode_path = slice_and_export
    ok, actual, details = parse_support_xy_overrides_z(gcode_path, expected_value)

    assert ok, f"support_xy_overrides_z expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_bridge_no_support(
    slice_and_export: Path,
    expected_value: str,
):
    """Test bridge_no_support parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对桥接不生成支撑开关；再比较 Support interface 的挤出量、总/单层移动数、单层路径长度及路径方向占比。
    gcode_path = slice_and_export
    ok, actual, details = parse_bridge_no_support(gcode_path, expected_value)

    assert ok, f"bridge_no_support expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_max_bridge_length(
    slice_and_export: Path,
    expected_value: str,
):
    """Test max_bridge_length parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对最大桥接长度；再比较 Support 与 Support total 每层最大支撑移动数，确认超过阈值的桥接区域才生成支撑。
    gcode_path = slice_and_export
    ok, actual, details = parse_max_bridge_length(gcode_path, expected_value)

    assert ok, f"max_bridge_length expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_independent_support_layer_height(
    slice_and_export: Path,
    expected_value: str,
):
    """Test independent_support_layer_height parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对独立支撑层高开关；再比较 Support total 的层数、块数、移动数、路径/挤出量、速度档位以及 T0 挤出量。
    gcode_path = slice_and_export
    ok, actual, details = parse_independent_support_layer_height(gcode_path, expected_value)

    assert ok, f"independent_support_layer_height expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_ironing_support_layer(
    slice_and_export: Path,
    expected_value: str,
):
    """Test ironing_support_layer parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对支撑层熨平开关；再比较 Support/Support total 的块数、移动数、路径/挤出量及 T1 的移动、路径和挤出量。
    gcode_path = slice_and_export
    ok, actual, details = parse_ironing_support_layer(gcode_path, expected_value)

    assert ok, f"ironing_support_layer expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_tree_hybrid_cross_height(
    slice_and_export: Path,
    expected_value: str,
):
    """Test tree_hybrid_cross_height parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对树状混合交叉高度；再比较 Support total 的首末 Z、层数、块数、移动数和总路径长度。
    gcode_path = slice_and_export
    ok, actual, details = parse_tree_hybrid_cross_height(gcode_path, expected_value)

    assert ok, f"tree_hybrid_cross_height expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_filament(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_filament parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对支撑主体耗材编号；再比较 Support interface 的块数、层数、移动数、挤出量及总/单层路径长度，确认多材料支撑行为与基线一致。
    gcode_path = slice_and_export
    ok, actual, details = parse_support_filament(gcode_path, expected_value)
    
    assert ok, f"support_filament expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_interface_filament(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_interface_filament parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对支撑界面耗材编号；再比较 Support interface 的块数、层数、移动数、挤出量及总/单层路径长度，确认界面生成行为。
    gcode_path = slice_and_export
    ok, actual, details = parse_support_interface_filament(gcode_path, expected_value)
    
    assert ok, f"support_interface_filament expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_interface_not_for_body(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_interface_not_for_body parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对界面耗材不用于主体开关；再分别统计 Support 与 Support total 中 T0/T1 的移动数、路径长度和挤出量，验证工具分配。
    gcode_path = slice_and_export
    ok, actual, details = parse_support_interface_not_for_body(gcode_path, expected_value)
    
    assert ok, f"support_interface_not_for_body expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_interface_top_layers(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_interface_top_layers parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对顶部界面层数；再比较 Support interface 的层数、块数、移动数、挤出量以及总/单层路径长度。
    gcode_path = slice_and_export
    ok, actual, details = parse_support_interface_top_layers(gcode_path, expected_value)
    
    assert ok, f"support_interface_top_layers expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_interface_bottom_layers(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_interface_bottom_layers parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对底部界面层数；再比较 Support interface 的层数、块数、移动数、路径/挤出量以及 T0 的移动、路径和挤出量。
    gcode_path = slice_and_export
    ok, actual, details = parse_support_interface_bottom_layers(gcode_path, expected_value)
    
    assert ok, f"support_interface_bottom_layers expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_interface_pattern(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_interface_pattern parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对支撑界面图案枚举；再比较 Support interface 的包围盒、块数、层数、挤出量以及单层路径长度和移动数。
    gcode_path = slice_and_export
    ok, actual, details = parse_support_interface_pattern(gcode_path, expected_value)
    
    assert ok, f"support_interface_pattern expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_interface_spacing(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_interface_spacing parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对顶部界面线距；再比较 Support interface 的块数、层数、移动数、挤出量和单层路径长度/移动数，验证疏密变化。
    gcode_path = slice_and_export
    ok, actual, details = parse_support_interface_spacing(gcode_path, expected_value)
    
    assert ok, f"support_interface_spacing expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_bottom_interface_spacing(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_bottom_interface_spacing parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对底部界面线距；再比较 Support total 的首末 Z、层数、块数、移动数和总路径长度。
    gcode_path = slice_and_export
    ok, actual, details = parse_support_bottom_interface_spacing(gcode_path, expected_value)
    
    assert ok, f"support_bottom_interface_spacing expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_interface_loop_pattern(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_interface_loop_pattern parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对界面环形图案开关；再比较 Support interface 的单层路径长度/移动数、总移动数、方向占比、线段分位数和最低速度。
    gcode_path = slice_and_export
    ok, actual, details = parse_support_interface_loop_pattern(gcode_path, expected_value)
    
    assert ok, f"support_interface_loop_pattern expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_interface_speed(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_interface_speed parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对支撑界面速度；再解析 Support interface 与 Support total 的实际 F 值，比较中位/最大速度及速度档位数。
    gcode_path = slice_and_export
    ok, actual, details = parse_support_interface_speed(gcode_path, expected_value)
    
    assert ok, f"support_interface_speed expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_interface_min_area(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_interface_min_area parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对生成支撑界面的最小面积；再比较 Support interface/Support total 的块数、层数、单层路径/移动数、方向分布和最大线段。
    gcode_path = slice_and_export
    ok, actual, details = parse_support_interface_min_area(gcode_path, expected_value)
    
    assert ok, f"support_interface_min_area expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_tree_support_branch_diameter(
    slice_and_export: Path,
    expected_value: str,
):
    """Test tree_support_branch_diameter parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对树枝直径；再比较 Support interface 的挤出量、总/单层路径长度、方向占比、线段 P90 以及 T0 挤出量。
    gcode_path = slice_and_export
    ok, actual, details = parse_tree_support_branch_diameter(gcode_path, expected_value)
    
    assert ok, f"tree_support_branch_diameter expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_tree_support_branch_angle(
    slice_and_export: Path,
    expected_value: str,
):
    """Test tree_support_branch_angle parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对树枝角度；再比较 Support total 的块数、挤出量、总/单层移动数、单层路径长度和路径方向占比。
    gcode_path = slice_and_export
    ok, actual, details = parse_tree_support_branch_angle(gcode_path, expected_value)
    
    assert ok, f"tree_support_branch_angle expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_tree_support_wall_count(
    slice_and_export: Path,
    expected_value: str,
):
    """Test tree_support_wall_count parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对树状支撑壁数；再比较 Support total 的首末 Z、层数、块数、移动数和总路径长度。
    gcode_path = slice_and_export
    ok, actual, details = parse_tree_support_wall_count(gcode_path, expected_value)
    
    assert ok, f"tree_support_wall_count expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_tree_support_wall_count_tree(
    slice_and_export: Path,
    expected_value: int,
):
    """Test tree_support_wall_count_tree parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对树状模式专用壁数；再比较 Support total 的首末 Z、层数、块数、移动数和总路径长度。
    gcode_path = slice_and_export
    ok, actual, details = parse_tree_support_wall_count_tree(gcode_path, expected_value)
    
    assert ok, f"tree_support_wall_count_tree expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_tree_support_branch_distance(
    slice_and_export: Path,
    expected_value: str,
):
    """Test tree_support_branch_distance parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对树枝间距；再比较 Support total 的首末 Z、层数、块数、移动数和总路径长度。
    gcode_path = slice_and_export
    ok, actual, details = parse_tree_support_branch_distance(gcode_path, expected_value)
    
    assert ok, f"tree_support_branch_distance expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_tree_support_tip_diameter(
    slice_and_export: Path,
    expected_value: str,
):
    """Test tree_support_tip_diameter parameter (Level 2 - semantic G-code baseline)"""
    # 验证方法：核对树枝尖端直径；再比较 Support total 的首末 Z、层数、块数、移动数和总路径长度。
    gcode_path = slice_and_export
    ok, actual, details = parse_tree_support_tip_diameter(gcode_path, expected_value)
    
    assert ok, f"tree_support_tip_diameter expected {expected_value}, got {actual}: {details}"
