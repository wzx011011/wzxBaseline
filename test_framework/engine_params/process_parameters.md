# 工艺（Process）参数列表

本文档列出了所有工艺相关的参数，按照分级结构组织。

## 质量 (Quality)

### 层高 (Layer height)

| 参数名 |
|--------|
| `layer_height` |
| `initial_layer_print_height` |

### 线宽 (Line width)

| 参数名 |
|--------|
| `line_width` |
| `initial_layer_line_width` |
| `outer_wall_line_width` |
| `inner_wall_line_width` |
| `top_surface_line_width` |
| `sparse_infill_line_width` |
| `internal_solid_infill_line_width` |
| `support_line_width` |

### 接缝 (Seam)

| 参数名 |
|--------|
| `seam_position` |
| `staggered_inner_seams` |
| `seam_gap` |
| `seam_slope_type` |
| `seam_slope_conditional` |
| `scarf_angle_threshold` |
| `scarf_overhang_threshold` |
| `scarf_joint_speed` |
| `seam_slope_start_height` |
| `seam_slope_entire_loop` |
| `seam_slope_min_length` |
| `seam_slope_steps` |
| `scarf_joint_flow_ratio` |
| `seam_slope_inner_walls` |
| `role_based_wipe_speed` |
| `wipe_speed` |
| `wipe_on_loops` |
| `wipe_before_external_loop` |

### 精度 (Precision)

| 参数名 |
|--------|
| `slice_closing_radius` |
| `resolution` |
| `enable_arc_fitting` |
| `xy_hole_compensation` |
| `xy_contour_compensation` |
| `elefant_foot_compensation` |
| `elefant_foot_compensation_layers` |
| `precise_outer_wall` |
| `hole_to_polyhole` |
| `hole_to_polyhole_threshold` |
| `hole_to_polyhole_twisted` |
| `precise_z_height` |

### 熨烫 (Ironing)

| 参数名 |
|--------|
| `ironing_type` |
| `ironing_pattern` |
| `ironing_speed` |
| `ironing_flow` |
| `ironing_spacing` |
| `ironing_angle` |

### 墙壁生成器 (Wall generator)

| 参数名 |
|--------|
| `wall_generator` |
| `wall_transition_angle` |
| `wall_transition_filter_deviation` |
| `wall_transition_length` |
| `wall_distribution_count` |
| `initial_layer_min_bead_width` |
| `min_bead_width` |
| `min_feature_size` |
| `min_length_factor` |

### 墙壁和表面 (Walls and surfaces)

| 参数名 |
|--------|
| `wall_sequence` |
| `is_infill_first` |
| `wall_direction` |
| `print_flow_ratio` |
| `top_solid_infill_flow_ratio` |
| `bottom_solid_infill_flow_ratio` |
| `only_one_wall_top` |
| `min_width_top_surface` |
| `only_one_wall_first_layer` |
| `reduce_crossing_wall` |
| `max_travel_detour_distance` |
| `small_area_infill_flow_compensation` |
| `small_area_infill_flow_compensation_model` |
| `z_direction_outwall_speed_continuous` |

### 桥接 (Bridging)

| 参数名 |
|--------|
| `bridge_flow` |
| `internal_bridge_flow` |
| `bridge_density` |
| `thick_bridges` |
| `thick_internal_bridges` |
| `dont_filter_internal_bridges` |
| `counterbore_hole_bridging` |

### 悬垂 (Overhangs)

| 参数名 |
|--------|
| `detect_overhang_wall` |
| `make_overhang_printable` |
| `make_overhang_printable_angle` |
| `make_overhang_printable_hole_size` |
| `extra_perimeters_on_overhangs` |
| `overhang_reverse` |
| `overhang_reverse_internal_only` |
| `overhang_reverse_threshold` |
| `overhang_optimization` |

## 强度 (Strength)

### 墙壁 (Walls)

| 参数名 |
|--------|
| `wall_loops` |
| `alternate_extra_wall` |
| `detect_thin_wall` |

### 顶部/底部壳 (Top/bottom shells)

| 参数名 |
|--------|
| `top_surface_pattern` |
| `top_shell_layers` |
| `top_shell_thickness` |
| `bottom_surface_pattern` |
| `bottom_shell_layers` |
| `bottom_shell_thickness` |
| `top_bottom_infill_wall_overlap` |

### 填充 (Infill)

| 参数名 |
|--------|
| `sparse_infill_density` |
| `tpms_start_infill_density` |
| `tpms_end_infill_density` |
| `tpms_gradual_direction` |
| `ai_infill` |
| `sparse_infill_pattern` |
| `infill_anchor` |
| `infill_anchor_max` |
| `internal_solid_infill_pattern` |
| `gap_fill_target` |
| `filter_out_gap_fill` |
| `infill_wall_overlap` |
| `external_infill_margin` |
| `fill_multiline` |
| `locked_skin_infill_pattern` |
| `locked_skeleton_infill_pattern` |
| `skin_infill_density` |
| `skeleton_infill_density` |
| `infill_lock_depth` |
| `skin_infill_depth` |
| `skin_infill_line_width` |
| `skeleton_infill_line_width` |
| `infill_rotate_step` |
| `symmetric_infill_y_axis` |
| `infill_shift_step` |
| `lateral_lattice_angle_1` |
| `lateral_lattice_angle_2` |
| `infill_overhang_angle` |

### 高级 (Advanced)

| 参数名 |
|--------|
| `infill_direction` |
| `solid_infill_direction` |
| `rotate_solid_infill_direction` |
| `bridge_angle` |
| `minimum_sparse_infill_area` |
| `infill_combination` |
| `detect_narrow_internal_solid_infill` |
| `ensure_vertical_shell_thickness` |

## 速度 (Speed)

### 首层速度 (Initial layer speed)

| 参数名 |
|--------|
| `initial_layer_speed` |
| `initial_layer_infill_speed` |
| `initial_layer_travel_speed` |
| `slow_down_layers` |

### 其他层速度 (Other layers speed)

| 参数名 |
|--------|
| `outer_wall_speed` |
| `inner_wall_speed` |
| `small_perimeter_speed` |
| `small_perimeter_threshold` |
| `sparse_infill_speed` |
| `internal_solid_infill_speed` |
| `top_surface_speed` |
| `gap_infill_speed` |
| `support_speed` |
| `support_interface_speed` |

### 悬垂速度 (Overhang speed)

| 参数名 |
|--------|
| `enable_overhang_speed` |
| `overhang_speed_classic` |
| `slowdown_for_curled_perimeters` |
| `overhang_1_4_speed` |
| `overhang_2_4_speed` |
| `overhang_3_4_speed` |
| `overhang_4_4_speed` |
| `overhang_totally_speed` |
| `bridge_speed` |
| `internal_bridge_speed` |
| `smooth_speed_discontinuity_area` |
| `smooth_coefficient` |

### 空驶速度 (Travel speed)

| 参数名 |
|--------|
| `travel_speed` |

### 加速度 (Acceleration)

| 参数名 |
|--------|
| `default_acceleration` |
| `outer_wall_acceleration` |
| `inner_wall_acceleration` |
| `bridge_acceleration` |
| `sparse_infill_acceleration` |
| `internal_solid_infill_acceleration` |
| `initial_layer_acceleration` |
| `top_surface_acceleration` |
| `travel_acceleration` |
| `accel_to_decel_enable` |
| `accel_to_decel_factor` |
| `travel_short_distance_acceleration` |
| `travel_short_distance_threshold` |

### 抖动(XY) (Jerk(XY))

| 参数名 |
|--------|
| `default_jerk` |
| `outer_wall_jerk` |
| `inner_wall_jerk` |
| `infill_jerk` |
| `top_surface_jerk` |
| `initial_layer_jerk` |
| `travel_jerk` |

### 高级 (Advanced)

| 参数名 |
|--------|
| `max_volumetric_extrusion_rate_slope` |
| `max_volumetric_extrusion_rate_slope_segment_length` |
| `acceleration_limit_mess_enable` |
| `acceleration_limit_mess` |
| `speed_limit_to_height_enable` |
| `speed_limit_to_height` |

## 支撑 (Support)

### 支撑 (Support)

| 参数名 |
|--------|
| `enable_support` |
| `support_type` |
| `support_style` |
| `support_threshold_angle` |
| `support_on_build_plate_only` |
| `support_critical_regions_only` |
| `support_remove_small_overhang` |
| `minimum_support_area` |

### 底筏 (Raft)

| 参数名 |
|--------|
| `raft_layers` |
| `raft_contact_distance` |

### 支撑耗材 (Support filament)

| 参数名 |
|--------|
| `support_filament` |
| `support_interface_filament` |
| `support_interface_not_for_body` |

### 高级 (Advanced)

| 参数名 |
|--------|
| `raft_first_layer_density` |
| `raft_first_layer_expansion` |
| `support_top_z_distance` |
| `support_bottom_z_distance` |
| `support_base_pattern` |
| `tree_support_wall_count` |
| `support_base_pattern_spacing` |
| `support_angle` |
| `support_interface_top_layers` |
| `support_interface_bottom_layers` |
| `support_interface_min_area` |
| `support_interface_pattern` |
| `support_interface_spacing` |
| `support_bottom_interface_spacing` |
| `support_expansion` |
| `support_object_xy_distance` |
| `support_object_first_layer_gap` |
| `support_xy_overrides_z` |
| `bridge_no_support` |
| `max_bridge_length` |
| `independent_support_layer_height` |
| `ironing_support_layer` |
| `tree_hybrid_cross_height` |

### 树状支撑 (Tree supports)

| 参数名 |
|--------|
| `tree_support_branch_distance` |
| `tree_support_branch_diameter` |
| `tree_support_branch_angle` |
| `tree_support_branch_diameter_angle` |
| `support_base_pattern_tree` |
| `tree_support_wall_count_tree` |

## 多材料 (Multimaterial)

### 擦料塔 (Prime tower)

| 参数名 |
|--------|
| `enable_prime_tower` |
| `prime_tower_width` |
| `prime_volume` |
| `prime_tower_brim_width` |
| `wipe_tower_rotation_angle` |
| `wipe_tower_bridging` |
| `prime_tower_enhance_type` |
| `wipe_tower_cone_angle` |
| `wipe_tower_extra_spacing` |
| `wipe_tower_extra_flow` |
| `wipe_tower_max_purge_speed` |
| `wipe_tower_no_sparse_layers` |

### 特征耗材 (Filament for Features)

| 参数名 |
|--------|
| `wall_filament` |
| `sparse_infill_filament` |
| `solid_infill_filament` |
| `wipe_tower_filament` |

### 渗料预防 (Ooze prevention)

| 参数名 |
|--------|
| `ooze_prevention` |
| `standby_temperature_delta` |
| `preheat_time` |
| `preheat_steps` |

### 冲刷选项 (Flush options)

| 参数名 |
|--------|
| `flush_into_infill` |
| `flush_into_objects` |
| `flush_into_support` |

### 高级 (Advanced)

| 参数名 |
|--------|
| `interlocking_beam` |
| `mmu_segmented_region_max_width` |
| `mmu_segmented_region_interlocking_depth` |
| `interlocking_beam_width` |
| `interlocking_orientation` |
| `interlocking_beam_layer_count` |
| `interlocking_depth` |
| `interlocking_boundary_avoidance` |

## 其他 (Others)

### 裙边 (Skirt)

| 参数名 |
|--------|
| `skirt_type` |
| `skirt_loops` |
| `min_skirt_length` |
| `skirt_distance` |
| `skirt_height` |
| `skirt_speed` |
| `draft_shield` |

### 边缘 (Brim)

| 参数名 |
|--------|
| `brim_type` |
| `brim_width` |
| `brim_object_gap` |
| `brim_ears_max_angle` |
| `brim_ears_detection_length` |

### 特殊模式 (Special mode)

| 参数名 |
|--------|
| `slicing_mode` |
| `print_sequence` |
| `print_order` |
| `spiral_mode` |
| `ignore_inner_color` |
| `spiral_mode_smooth` |
| `spiral_mode_max_xy_smoothing` |
| `timelapse_type` |
| `fuzzy_skin` |
| `fuzzy_skin_point_distance` |
| `fuzzy_skin_thickness` |
| `fuzzy_skin_first_layer` |

### G代码输出 (G-code output)

| 参数名 |
|--------|
| `reduce_infill_retraction` |
| `gcode_add_line_number` |
| `gcode_comments` |
| `gcode_label_objects` |
| `exclude_object` |
| `filename_format` |

### 后处理脚本 (Post-processing Scripts)

| 参数名 |
|--------|
| `post_process` |

### 备注 (Notes)

| 参数名 |
|--------|
| `notes` |

---
**总参数数量: 289**