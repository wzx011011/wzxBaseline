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
    gcode_path = slice_and_export
    ok, actual, details = parse_enable_support(gcode_path, expected_value)
    
    assert ok, f"enable_support expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_type(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_type parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_support_type(gcode_path, expected_value)
    
    assert ok, f"support_type expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_style(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_style parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_support_style(gcode_path, expected_value)
    
    assert ok, f"support_style expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_threshold_angle(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_threshold_angle parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_support_threshold_angle(gcode_path, expected_value)
    
    assert ok, f"support_threshold_angle expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_on_build_plate_only(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_on_build_plate_only parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_support_on_build_plate_only(gcode_path, expected_value)
    
    assert ok, f"support_on_build_plate_only expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_critical_regions_only(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_critical_regions_only parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_support_critical_regions_only(gcode_path, expected_value)
    
    assert ok, f"support_critical_regions_only expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_remove_small_overhang(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_remove_small_overhang parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_support_remove_small_overhang(gcode_path, expected_value)
    
    assert ok, f"support_remove_small_overhang expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_raft_layers(
    slice_and_export: Path,
    expected_value: str,
):
    """Test raft_layers parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_raft_layers(gcode_path, expected_value)
    
    assert ok, f"raft_layers expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_raft_contact_distance(
    slice_and_export: Path,
    expected_value: str,
):
    """Test raft_contact_distance parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_raft_contact_distance(gcode_path, expected_value)
    
    assert ok, f"raft_contact_distance expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_raft_first_layer_density(
    slice_and_export: Path,
    expected_value: str,
):
    """Test raft_first_layer_density parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_raft_first_layer_density(gcode_path, expected_value)

    assert ok, f"raft_first_layer_density expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_raft_first_layer_expansion(
    slice_and_export: Path,
    expected_value: str,
):
    """Test raft_first_layer_expansion parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_raft_first_layer_expansion(gcode_path, expected_value)

    assert ok, f"raft_first_layer_expansion expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_top_z_distance(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_top_z_distance parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_support_top_z_distance(gcode_path, expected_value)

    assert ok, f"support_top_z_distance expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_bottom_z_distance(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_bottom_z_distance parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_support_bottom_z_distance(gcode_path, expected_value)

    assert ok, f"support_bottom_z_distance expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_base_pattern(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_base_pattern parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_support_base_pattern(gcode_path, expected_value)

    assert ok, f"support_base_pattern expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_base_pattern_tree(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_base_pattern_tree parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_support_base_pattern_tree(gcode_path, expected_value)

    assert ok, f"support_base_pattern_tree expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_base_pattern_spacing(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_base_pattern_spacing parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_support_base_pattern_spacing(gcode_path, expected_value)

    assert ok, f"support_base_pattern_spacing expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_angle(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_angle parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_support_angle(gcode_path, expected_value)

    assert ok, f"support_angle expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_expansion(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_expansion parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_support_expansion(gcode_path, expected_value)

    assert ok, f"support_expansion expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_object_xy_distance(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_object_xy_distance parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_support_object_xy_distance(gcode_path, expected_value)

    assert ok, f"support_object_xy_distance expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_object_first_layer_gap(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_object_first_layer_gap parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_support_object_first_layer_gap(gcode_path, expected_value)

    assert ok, f"support_object_first_layer_gap expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_xy_overrides_z(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_xy_overrides_z parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_support_xy_overrides_z(gcode_path, expected_value)

    assert ok, f"support_xy_overrides_z expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_bridge_no_support(
    slice_and_export: Path,
    expected_value: str,
):
    """Test bridge_no_support parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_bridge_no_support(gcode_path, expected_value)

    assert ok, f"bridge_no_support expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_max_bridge_length(
    slice_and_export: Path,
    expected_value: str,
):
    """Test max_bridge_length parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_max_bridge_length(gcode_path, expected_value)

    assert ok, f"max_bridge_length expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_independent_support_layer_height(
    slice_and_export: Path,
    expected_value: str,
):
    """Test independent_support_layer_height parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_independent_support_layer_height(gcode_path, expected_value)

    assert ok, f"independent_support_layer_height expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_ironing_support_layer(
    slice_and_export: Path,
    expected_value: str,
):
    """Test ironing_support_layer parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_ironing_support_layer(gcode_path, expected_value)

    assert ok, f"ironing_support_layer expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_tree_hybrid_cross_height(
    slice_and_export: Path,
    expected_value: str,
):
    """Test tree_hybrid_cross_height parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_tree_hybrid_cross_height(gcode_path, expected_value)

    assert ok, f"tree_hybrid_cross_height expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_filament(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_filament parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_support_filament(gcode_path, expected_value)
    
    assert ok, f"support_filament expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_interface_filament(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_interface_filament parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_support_interface_filament(gcode_path, expected_value)
    
    assert ok, f"support_interface_filament expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_interface_not_for_body(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_interface_not_for_body parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_support_interface_not_for_body(gcode_path, expected_value)
    
    assert ok, f"support_interface_not_for_body expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_interface_top_layers(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_interface_top_layers parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_support_interface_top_layers(gcode_path, expected_value)
    
    assert ok, f"support_interface_top_layers expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_interface_bottom_layers(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_interface_bottom_layers parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_support_interface_bottom_layers(gcode_path, expected_value)
    
    assert ok, f"support_interface_bottom_layers expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_interface_pattern(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_interface_pattern parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_support_interface_pattern(gcode_path, expected_value)
    
    assert ok, f"support_interface_pattern expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_interface_spacing(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_interface_spacing parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_support_interface_spacing(gcode_path, expected_value)
    
    assert ok, f"support_interface_spacing expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_bottom_interface_spacing(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_bottom_interface_spacing parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_support_bottom_interface_spacing(gcode_path, expected_value)
    
    assert ok, f"support_bottom_interface_spacing expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_interface_loop_pattern(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_interface_loop_pattern parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_support_interface_loop_pattern(gcode_path, expected_value)
    
    assert ok, f"support_interface_loop_pattern expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_interface_speed(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_interface_speed parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_support_interface_speed(gcode_path, expected_value)
    
    assert ok, f"support_interface_speed expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_support_interface_min_area(
    slice_and_export: Path,
    expected_value: str,
):
    """Test support_interface_min_area parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_support_interface_min_area(gcode_path, expected_value)
    
    assert ok, f"support_interface_min_area expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_tree_support_branch_diameter(
    slice_and_export: Path,
    expected_value: str,
):
    """Test tree_support_branch_diameter parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_tree_support_branch_diameter(gcode_path, expected_value)
    
    assert ok, f"tree_support_branch_diameter expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_tree_support_branch_angle(
    slice_and_export: Path,
    expected_value: str,
):
    """Test tree_support_branch_angle parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_tree_support_branch_angle(gcode_path, expected_value)
    
    assert ok, f"tree_support_branch_angle expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_tree_support_wall_count(
    slice_and_export: Path,
    expected_value: str,
):
    """Test tree_support_wall_count parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_tree_support_wall_count(gcode_path, expected_value)
    
    assert ok, f"tree_support_wall_count expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_tree_support_wall_count_tree(
    slice_and_export: Path,
    expected_value: int,
):
    """Test tree_support_wall_count_tree parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_tree_support_wall_count_tree(gcode_path, expected_value)
    
    assert ok, f"tree_support_wall_count_tree expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_tree_support_branch_distance(
    slice_and_export: Path,
    expected_value: str,
):
    """Test tree_support_branch_distance parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_tree_support_branch_distance(gcode_path, expected_value)
    
    assert ok, f"tree_support_branch_distance expected {expected_value}, got {actual}: {details}"


@pytest.mark.engine_params
def test_tree_support_tip_diameter(
    slice_and_export: Path,
    expected_value: str,
):
    """Test tree_support_tip_diameter parameter (Level 2 - semantic G-code baseline)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_tree_support_tip_diameter(gcode_path, expected_value)
    
    assert ok, f"tree_support_tip_diameter expected {expected_value}, got {actual}: {details}"
