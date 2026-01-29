# Process 参数 G-code 校验方案（完整版）

## 一、概述

本文档基于 **C3DSlicer 源代码** (`src/slic3r/GUI/Tab.cpp` TabPrint::build 函数，行 2462-4946) 提取的 UI 参数，共计 **390 个参数**，分布在 6 个主要页面。

### 参数体系 - UI 页面结构

| 页面 | 参数数量 | 子分组数 | 主要功能 |
|------|---------|---------|---------|
| **Quality（质量）** | ~50 | 9 | 层高、线宽、接缝、精度、熨烫、墙面、桥接、悬垂 |
| **Strength（强度）** | ~35 | 4 | 墙壁、顶底壳、填充、高级 |
| **Speed（速度）** | ~55 | 7 | 首层速度、其他层速度、悬垂速度、移动速度、加速度、抖动、高级 |
| **Support（支撑）** | ~47 | 5 | 支撑、Raft、支撑耗材、高级、树支撑 |
| **Multimaterial（多材料）** | ~34 | 5 | 擦料塔、特征耗材、渗料预防、冲刷选项、高级 |
| **Others（其他）** | ~32 | 6 | 裙边、边缘、特殊模式、G代码输出、后处理、备注 |

**附加页面**（动态/条件显示）：
- **Frequent（常用）**: 快速设置入口
- **Plate Settings（板设置）**: 温度参数
- **Setting Overrides（设置覆盖）**: 耗材覆盖参数

### 校验层次说明

| 层次 | 名称 | 适用场景 | 复杂度 | 可靠性 |
|------|------|---------|--------|--------|
| Level 1 (L1) | 配置对比 | 简单值校验，直接从 G-code 配置注释（CONFIG_BLOCK）读取并对比 | 简单 | 快速预检 |
| Level 2 (L2) | GCode 解析 | 解析 GCode 指令（TYPE 标记、坐标、E值、F值），验证指令序列和单层逻辑 | 中等 | 效果验证 |
| Level 3 (L3) | 复杂逻辑验证 | 基线对比 + 跨层分析 + 几何轮廓验证（需要 baseline_gcode 参数） | 复杂 | 精确验证 |

**详细说明：**
- **L1**: 从 `; CONFIG_BLOCK_START` 到 `; CONFIG_BLOCK_END` 之间提取参数值，直接字符串对比
- **L2**: 使用 GCodeParser 解析 G0/G1 指令，提取坐标/E值/F值，验证 TYPE 标记转换、指令序列、单层路径逻辑
- **L3**: 在 L2 基础上，需要 `baseline_gcode` 参数进行对比，使用 `get_type_contours_per_layer()` 进行跨层几何分析

---

## 二、Page 1: Quality（质量页面）- ~50 个参数

**数据来源**: `src/slic3r/GUI/Tab.cpp` L2471-2580

### 2.1 Layer height（层高）- 2 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `layer_height` | float | 0.2 | L1 | 层高 ★关键 |
| `initial_layer_print_height` | float | 0.2 | L1 | 首层打印高度 |

### 2.2 Line width（线宽）- ~10 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `line_width` | float | 0.4 | L1 | 默认线宽 ★关键 |
| `initial_layer_line_width` | float | 0.4 | L1 | 首层线宽 |
| `outer_wall_line_width` | float | 0.4 | L1 | 外墙线宽 |
| `inner_wall_line_width` | float | 0.4 | L1 | 内墙线宽 |
| `top_surface_line_width` | float | 0.4 | L1 | 顶面线宽 |
| `sparse_infill_line_width` | float | 0.4 | L1 | 稀疏填充线宽 |
| `internal_solid_infill_line_width` | float | 0.4 | L1 | 内部实心填充线宽 |
| `support_line_width` | float | 0.4 | L1 | 支撑线宽 |

### 2.3 Seam（接缝）- ~12 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `seam_position` | enum | aligned | L1 | 接缝位置 |
| `seam_gap` | float | 0 | L1 | 接缝间隙 |
| `staggered_inner_seams` | bool | false | L1 | 交错内墙接缝 |
| `seam_slope_type` | enum | - | L1 | 斜坡类型 |
| `seam_slope_conditional` | bool | false | L1 | 条件斜坡 |
| `seam_slope_entire_loop` | bool | false | L1 | 整圈斜坡 |
| `seam_slope_inner_walls` | bool | false | L1 | 内墙斜坡 |
| `seam_slope_min_length` | float | 0 | L1 | 最小斜坡长度 |
| `seam_slope_start_height` | float | 0 | L1 | 斜坡起始高度 |
| `seam_slope_steps` | int | 0 | L1 | 斜坡步数 |
| `scarf_angle_threshold` | float | 0 | L1 | 斜接角度阈值 |
| `scarf_joint_speed` | float | 0 | L1 | 斜接速度 |
| `scarf_joint_flow_ratio` | float | 1.0 | L1 | 斜接流量比 |
| `scarf_overhang_threshold` | float | 0 | L1 | 斜接悬垂阈值 |

### 2.4 Precision（精度）- ~10 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `slice_closing_radius` | float | 0.049 | L1 | 切片闭合半径 |
| `resolution` | float | 0.012 | L1 | 分辨率 |
| `xy_hole_compensation` | float | 0 | L1 | XY 孔补偿 |
| `xy_contour_compensation` | float | 0 | L1 | XY 轮廓补偿 |
| `elefant_foot_compensation` | float | 0 | L1 | 象脚补偿 |
| `elefant_foot_compensation_layers` | int | 1 | L1 | 象脚补偿层数 |
| `hole_to_polyhole` | bool | false | L1 | 孔转多边形 |
| `hole_to_polyhole_threshold` | float | 0.01 | L1 | 孔转多边形阈值 |
| `hole_to_polyhole_twisted` | bool | false | L1 | 扭曲多边形孔 |
| `precise_outer_wall` | bool | false | L1 | 精确外墙 |
| `precise_z_height` | float | 0 | L1 | 精确 Z 高度 |

### 2.5 Ironing（熨烫）- ~6 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `ironing_type` | enum | no_ironing | L1/L2 | 熨烫类型 |
| `ironing_pattern` | enum | rectilinear | L1 | 熨烫图案 |
| `ironing_flow` | float | 15% | L1 | 熨烫流量 |
| `ironing_spacing` | float | 0.1 | L1 | 熨烫间距 |
| `ironing_speed` | float | 15 | L1 | 熨烫速度 |
| `ironing_angle` | float | 45 | L1 | 熨烫角度 |

### 2.6 Wall generator（墙面生成器）- ~8 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `wall_generator` | enum | classic | L1 | 墙面生成器类型 |
| `wall_transition_angle` | float | 10 | L1 | 墙面过渡角度 |
| `wall_transition_filter_deviation` | float | 25% | L1 | 过渡过滤偏差 |
| `wall_transition_length` | float | 100% | L1 | 过渡长度 |
| `wall_distribution_count` | int | 1 | L1 | 墙面分布数 |
| `min_feature_size` | float | 25% | L1 | 最小特征尺寸 |
| `min_bead_width` | float | 85% | L1 | 最小珠宽度 |
| `initial_layer_min_bead_width` | float | 85% | L1 | 首层最小珠宽度 |

### 2.7 Walls and surfaces（墙面和表面）- ~10 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `min_width_top_surface` | float | 200% | L1 | 顶面最小宽度 |
| `only_one_wall_top` | bool | false | L1 | 顶层仅单墙 |
| `only_one_wall_first_layer` | bool | false | L1 | 首层仅单墙 |
| `detect_thin_wall` | bool | true | L1 | 检测薄墙 |
| `detect_overhang_wall` | bool | true | L1 | 检测悬垂墙 |
| `overhang_reverse` | bool | false | L1 | 悬垂反向 |
| `overhang_reverse_internal_only` | bool | false | L1 | 仅内部悬垂反向 |
| `overhang_reverse_threshold` | float | 50% | L1 | 悬垂反向阈值 |
| `wipe_on_loops` | bool | false | L1 | 环上擦拭 |
| `wipe_before_external_loop` | bool | false | L1 | 外环前擦拭 |

### 2.8 Bridging（桥接）- ~8 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `bridge_angle` | float | 0 | L1 | 桥接角度 |
| `bridge_flow` | float | 1.0 | L1 | 桥接流量 |
| `bridge_density` | float | 100% | L1 | 桥接密度 |
| `bridge_speed` | float | 25 | L1 | 桥接速度 |
| `thick_bridges` | bool | false | L1 | 厚桥接 |
| `dont_filter_internal_bridges` | bool | false | L1 | 不过滤内部桥接 |
| `thick_internal_bridges` | bool | false | L1 | 厚内部桥接 |
| `internal_bridge_flow` | float | 1.0 | L1 | 内部桥接流量 |
| `internal_bridge_speed` | float | 150% | L1 | 内部桥接速度 |
| `counterbore_hole_bridging` | enum | none | L1 | 沉孔桥接 |

### 2.9 Overhangs（悬垂）- ~6 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `extra_perimeters_on_overhangs` | bool | false | L1 | 悬垂额外周长 |
| `make_overhang_printable` | bool | false | L1 | 使悬垂可打印 |
| `make_overhang_printable_angle` | float | 55 | L1 | 可打印悬垂角度 |
| `make_overhang_printable_hole_size` | float | 0 | L1 | 可打印悬垂孔尺寸 |
| `overhang_optimization` | bool | false | L1 | 悬垂优化 |

---

## 三、Page 2: Strength（强度页面）- ~35 个参数

**数据来源**: `src/slic3r/GUI/Tab.cpp` L2581-2643

### 3.1 Walls（墙壁）- ~6 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `wall_loops` | int | 2 | L1 | 墙壁圈数 ★关键 |
| `alternate_extra_wall` | bool | false | L1 | 交替额外墙 |
| `wall_sequence` | enum | inner_outer | L1 | 墙壁顺序 |
| `wall_direction` | enum | auto | L1 | 墙壁方向 |
| `ensure_vertical_shell_thickness` | enum | none | L1 | 确保垂直壳厚度 |

### 3.2 Top/bottom shells（顶底壳）- ~10 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `top_shell_layers` | int | 4 | L1 | 顶壳层数 ★关键 |
| `top_shell_thickness` | float | 0.8 | L1 | 顶壳厚度 |
| `bottom_shell_layers` | int | 4 | L1 | 底壳层数 ★关键 |
| `bottom_shell_thickness` | float | 0.8 | L1 | 底壳厚度 |
| `top_surface_pattern` | enum | monotonic | L1 | 顶面图案 |
| `bottom_surface_pattern` | enum | monotonic | L1 | 底面图案 |
| `internal_solid_infill_pattern` | enum | monotonic | L1 | 内部实心填充图案 |
| `top_solid_infill_flow_ratio` | float | 1.0 | L1 | 顶部实心填充流量比 |
| `bottom_solid_infill_flow_ratio` | float | 1.0 | L1 | 底部实心填充流量比 |
| `rotate_solid_infill_direction` | bool | false | L1 | 旋转实心填充方向 |

### 3.3 Infill（填充）- ~20 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `sparse_infill_density` | float | 15% | L1 | 稀疏填充密度 ★关键 |
| `sparse_infill_pattern` | enum | grid | L1 | 稀疏填充图案 ★关键 |
| `infill_direction` | float | 45 | L1 | 填充方向 |
| `infill_anchor` | float | 400% | L1 | 填充锚点 |
| `infill_anchor_max` | float | 20 | L1 | 填充锚点最大值 |
| `infill_combination` | bool | false | L1 | 填充组合 |
| `infill_wall_overlap` | float | 25% | L1 | 填充墙重叠 |
| `top_bottom_infill_wall_overlap` | float | 25% | L1 | 顶底填充墙重叠 |
| `minimum_sparse_infill_area` | float | 10 | L1 | 最小稀疏填充区域 |
| `infill_rotate_step` | float | 90 | L1 | 填充旋转步进 |
| `infill_shift_step` | float | 0 | L1 | 填充偏移步进 |
| `infill_overhang_angle` | float | 0 | L1 | 填充悬垂角度 |
| `infill_lock_depth` | int | 0 | L1 | 填充锁定深度 |
| `is_infill_first` | bool | false | L1 | 先填充 |
| `symmetric_infill_y_axis` | bool | false | L1 | Y 轴对称填充 |
| `sparse_infill_rotate_template` | bool | false | L1 | 旋转稀疏填充模板 |
| `fill_multiline` | enum | none | L1 | 多线填充 |

### 3.4 Advanced（高级）- ~10 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `detect_narrow_internal_solid_infill` | bool | true | L1 | 检测窄内部实心填充 |
| `filter_out_gap_fill` | float | 0 | L1 | 过滤间隙填充 |
| `gap_fill_target` | enum | - | L1 | 间隙填充目标 |
| `solid_infill_direction` | float | 45 | L1 | 实心填充方向 |
| `ai_infill` | bool | false | L1 | AI 填充 |
| `skeleton_infill_density` | float | 0 | L1 | 骨架填充密度 |
| `skeleton_infill_line_width` | float | 0.4 | L1 | 骨架填充线宽 |
| `skin_infill_density` | float | 0 | L1 | 皮肤填充密度 |
| `skin_infill_depth` | int | 0 | L1 | 皮肤填充深度 |
| `skin_infill_line_width` | float | 0.4 | L1 | 皮肤填充线宽 |

---

## 四、Page 3: Speed（速度页面）- ~55 个参数

**数据来源**: `src/slic3r/GUI/Tab.cpp` L2644-2721

### 4.1 Initial layer speed（首层速度）- ~5 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `initial_layer_speed` | float | 30 | L1 | 首层速度 ★关键 |
| `initial_layer_infill_speed` | float | 60 | L1 | 首层填充速度 |
| `initial_layer_travel_speed` | float | 100 | L1 | 首层移动速度 |

### 4.2 Other layers speed（其他层速度）- ~15 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `outer_wall_speed` | float | 60 | L1 | 外墙速度 ★关键 |
| `inner_wall_speed` | float | 80 | L1 | 内墙速度 |
| `small_perimeter_speed` | float | 50% | L1 | 小周长速度 |
| `small_perimeter_threshold` | float | 0 | L1 | 小周长阈值 |
| `sparse_infill_speed` | float | 80 | L1 | 稀疏填充速度 |
| `internal_solid_infill_speed` | float | 100 | L1 | 内部实心填充速度 |
| `top_surface_speed` | float | 100 | L1 | 顶面速度 |
| `gap_infill_speed` | float | 30 | L1 | 间隙填充速度 |
| `support_speed` | float | 60 | L1 | 支撑速度 |
| `support_interface_speed` | float | 80 | L1 | 支撑接触面速度 |
| `wipe_speed` | float | 80% | L1 | 擦拭速度 |
| `role_based_wipe_speed` | bool | false | L1 | 基于角色的擦拭速度 |

### 4.3 Overhang speed（悬垂速度）- ~8 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `enable_overhang_speed` | bool | true | L1 | 启用悬垂速度 |
| `overhang_speed_classic` | bool | false | L1 | 经典悬垂速度 |
| `overhang_1_4_speed` | float | 0 | L1 | 悬垂 1/4 速度 |
| `overhang_2_4_speed` | float | 0 | L1 | 悬垂 2/4 速度 |
| `overhang_3_4_speed` | float | 0 | L1 | 悬垂 3/4 速度 |
| `overhang_4_4_speed` | float | 0 | L1 | 悬垂 4/4 速度 |
| `overhang_totally_speed` | float | 0 | L1 | 完全悬垂速度 |
| `slowdown_for_curled_perimeters` | bool | false | L1 | 卷曲周长减速 |

### 4.4 Travel speed（移动速度）- ~3 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `travel_speed` | float | 200 | L1 | 移动速度 ★关键 |
| `max_travel_detour_distance` | float | 0 | L1 | 最大移动绕行距离 |
| `reduce_crossing_wall` | bool | false | L1 | 减少穿墙 |

### 4.5 Acceleration（加速度）- ~12 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `default_acceleration` | float | 500 | L1 | 默认加速度 ★关键 |
| `initial_layer_acceleration` | float | 300 | L1 | 首层加速度 |
| `outer_wall_acceleration` | float | 500 | L1 | 外墙加速度 |
| `inner_wall_acceleration` | float | 500 | L1 | 内墙加速度 |
| `top_surface_acceleration` | float | 500 | L1 | 顶面加速度 |
| `sparse_infill_acceleration` | float | 500 | L1 | 稀疏填充加速度 |
| `internal_solid_infill_acceleration` | float | 500 | L1 | 内部实心填充加速度 |
| `bridge_acceleration` | float | 500 | L1 | 桥接加速度 |
| `travel_acceleration` | float | 500 | L1 | 移动加速度 |
| `travel_short_distance_acceleration` | float | 500 | L1 | 短距离移动加速度 |
| `travel_short_distance_threshold` | float | 0 | L1 | 短距离移动阈值 |
| `accel_to_decel_enable` | bool | false | L1 | 启用加减速 |
| `accel_to_decel_factor` | float | 50% | L1 | 加减速因子 |

### 4.6 Jerk (XY)（抖动）- ~6 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `default_jerk` | float | 0 | L1 | 默认抖动 |
| `initial_layer_jerk` | float | 0 | L1 | 首层抖动 |
| `outer_wall_jerk` | float | 0 | L1 | 外墙抖动 |
| `inner_wall_jerk` | float | 0 | L1 | 内墙抖动 |
| `top_surface_jerk` | float | 0 | L1 | 顶面抖动 |
| `infill_jerk` | float | 0 | L1 | 填充抖动 |
| `travel_jerk` | float | 0 | L1 | 移动抖动 |

### 4.7 Advanced（高级）- ~15 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `enable_arc_fitting` | bool | false | L1 | 启用圆弧拟合 |
| `enable_pressure_advance` | bool | false | L1 | 启用压力推进 |
| `pressure_advance` | float | 0 | L1 | 压力推进值 |
| `print_flow_ratio` | float | 1.0 | L1 | 打印流量比 |
| `speed_limit_to_height_enable` | bool | false | L1 | 启用高度速度限制 |
| `speed_limit_to_height` | float | 0 | L1 | 高度速度限制 |
| `acceleration_limit_mess_enable` | bool | false | L1 | 启用加速度限制 |
| `acceleration_limit_mess` | float | 0 | L1 | 加速度限制值 |
| `smooth_speed_discontinuity_area` | float | 0 | L1 | 速度不连续区域平滑 |
| `smooth_coefficient` | float | 0 | L1 | 平滑系数 |
| `min_length_factor` | float | 0.5 | L1 | 最小长度因子 |
| `max_volumetric_extrusion_rate_slope` | float | 0 | L1 | 最大体积挤出率斜率 |
| `max_volumetric_extrusion_rate_slope_segment_length` | float | 0 | L1 | 斜率段长度 |

---

## 五、Page 4: Support（支撑页面）- ~47 个参数

**数据来源**: `src/slic3r/GUI/Tab.cpp` L2722-2795

### 5.1 Support（支撑）- 7 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `enable_support` | bool | false | L2 | 启用支撑 ★关键 |
| `support_type` | enum | normal_auto | L1 | 支撑类型 |
| `support_style` | enum | default | L1 | 支撑风格 |
| `support_threshold_angle` | int | 30 | L1 | 支撑阈值角度 |
| `support_on_build_plate_only` | bool | false | L2 | 仅底板支撑 |
| `support_critical_regions_only` | bool | false | L2 | 仅关键区域支撑 |
| `support_remove_small_overhang` | bool | false | L1 | 移除小悬垂 |

### 5.2 Raft（筏）- 3 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `raft_layers` | int | 0 | L2 | 筏层数 |
| `raft_contact_distance` | float | 0.1 | L1 | 筏接触距离 |
| `enforce_support_layers` | int | 0 | L1 | 强制支撑层数 |

### 5.3 Support filament（支撑耗材）- 3 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `support_filament` | int | 0 | L2 | 支撑耗材 |
| `support_interface_filament` | int | 0 | L2 | 支撑接触面耗材 |
| `support_interface_not_for_body` | bool | false | L1 | 接触面材料不用于主体 |

### 5.4 Advanced（高级）- ~28 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `raft_first_layer_density` | float | 90% | L1 | 筏首层密度 |
| `raft_first_layer_expansion` | float | 2 | L1 | 筏首层扩展 |
| `support_top_z_distance` | float | 0.2 | L1 | 支撑顶部 Z 距离 |
| `support_bottom_z_distance` | float | 0.2 | L1 | 支撑底部 Z 距离 |
| `support_base_pattern` | enum | rectilinear | L1 | 支撑主体图案 |
| `support_base_pattern_spacing` | float | 2.5 | L1 | 支撑主体间距 |
| `support_angle` | float | 0 | L1 | 支撑角度 |
| `support_interface_top_layers` | int | 2 | L1 | 顶部接触面层数 |
| `support_interface_bottom_layers` | int | 2 | L1 | 底部接触面层数 |
| `support_interface_pattern` | enum | rectilinear | L1 | 接触面图案 |
| `support_interface_spacing` | float | 0.5 | L1 | 接触面间距 |
| `support_bottom_interface_spacing` | float | 0.5 | L1 | 底部接触面间距 |
| `support_interface_loop_pattern` | bool | false | L2 | 接触面环形图案 |
| `support_interface_speed` | float | 80 | L1 | 接触面速度 |
| `support_interface_min_area` | float | 0 | L1 | 最小接触面面积 |
| `support_material_interface_fan_speed` | string | -1,-1 | L1 | 接触面风扇速度 |
| `support_expansion` | float | 0 | L1 | 支撑扩展 |
| `support_object_xy_distance` | float | 0.35 | L1 | 支撑 XY 距离 |
| `support_object_first_layer_gap` | float | 0.2 | L1 | 首层间隙 |
| `support_xy_overrides_z` | enum | xy_overrides_z | L1 | XY 覆盖 Z |
| `bridge_no_support` | bool | false | L1 | 桥接无支撑 |
| `max_bridge_length` | float | 10 | L1 | 最大桥接长度 |
| `independent_support_layer_height` | bool | false | L1 | 独立支撑层高 |
| `ironing_support_layer` | bool | false | L1 | 熨烫支撑层 |
| `tree_hybrid_cross_height` | float | 0 | L1 | 树支撑混合横梁高度 |
| `support_line_width` | float | 0.4 | L1 | 支撑线宽 |
| `support_speed` | float | 60 | L1 | 支撑速度 |
| `minimum_support_area` | float | 5 | L1 | 最小支撑面积 |

### 5.5 Tree supports（树支撑）- ~15 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `tree_support_branch_diameter` | float | 2 | L1 | 分支直径 |
| `tree_support_branch_angle` | float | 45 | L1 | 分支角度 |
| `tree_support_branch_angle_organic` | float | 40 | L1 | 有机分支角度 |
| `tree_support_branch_diameter_organic` | float | 2 | L1 | 有机分支直径 |
| `tree_support_branch_diameter_angle` | float | 5 | L1 | 分支直径角度 |
| `tree_support_branch_diameter_double_wall` | float | 3 | L1 | 双壁分支直径 |
| `tree_support_branch_distance` | float | 1 | L1 | 分支距离 |
| `tree_support_branch_distance_organic` | float | 1 | L1 | 有机分支距离 |
| `tree_support_tip_diameter` | float | 0.8 | L1 | 尖端直径 |
| `tree_support_top_rate` | float | 30% | L1 | 顶部比率 |
| `tree_support_wall_count` | int | 0 | L1 | 墙壁数量 |
| `tree_support_wall_count_tree` | int | 0 | L1 | 树墙壁数量 |
| `tree_support_adaptive_layer_height` | bool | false | L1 | 自适应层高 |
| `tree_support_auto_brim` | bool | false | L1 | 自动边缘 |
| `tree_support_brim_width` | float | 3 | L1 | 边缘宽度 |
| `tree_support_angle_slow` | float | 30 | L1 | 慢速角度 |
| `support_base_pattern_tree` | enum | - | L1 | 树支撑底座图案 |

---

## 六、Page 5: Multimaterial（多材料页面）- ~34 个参数

**数据来源**: `src/slic3r/GUI/Tab.cpp` L2796-2841

### 6.1 Prime tower（擦料塔）- 15 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `enable_prime_tower` | bool | false | L2 | 启用擦料塔 ★关键 |
| `prime_tower_width` | float | 60 | L1/L3 | 擦料塔宽度 |
| `prime_volume` | float | 45 | L1 | 擦料体积 |
| `prime_tower_brim_width` | float | 3 | L1 | 擦料塔边缘宽度 |
| `wipe_tower_rotation_angle` | float | 0 | L1 | 旋转角度 |
| `wipe_tower_bridging` | float | 10 | L1 | 桥接层间距 |
| `prime_tower_enhance_type` | enum | chamfer | L3 | 底部增强类型 |
| `wipe_tower_cone_angle` | float | 0 | L1 | 锥形角度 |
| `wipe_tower_extra_spacing` | float | 150% | L1 | 额外间距 |
| `wipe_tower_extra_flow` | float | 100% | L1 | 额外流量 |
| `wipe_tower_max_purge_speed` | float | 90 | L1 | 最大冲刷速度 |
| `wipe_tower_no_sparse_layers` | bool | false | L1 | 禁用稀疏层 |
| `prime_tower_enable_framework` | bool | false | L1 | 启用框架 |
| `prime_tower_rib_wall` | bool | false | L1 | 肋墙 |
| `prime_tower_skip_points` | int | 0 | L1 | 跳过点数 |

### 6.2 Filament for Features（特征耗材）- 4 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `wall_filament` | int | 1 | L2 | 墙壁耗材 |
| `sparse_infill_filament` | int | 1 | L2 | 稀疏填充耗材 |
| `solid_infill_filament` | int | 1 | L2 | 实心填充耗材 |
| `wipe_tower_filament` | int | 1 | L2 | 擦料塔耗材 |

### 6.3 Ooze prevention（渗料预防）- 4 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `ooze_prevention` | bool | false | L1 | 渗料预防 |
| `standby_temperature_delta` | int | -5 | L1 | 待机温度差 |
| `preheat_time` | float | 0 | L1 | 预热时间 |
| `preheat_steps` | int | 0 | L1 | 预热步数 |

### 6.4 Flush options（冲刷选项）- 3 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `flush_into_infill` | bool | false | L2 | 冲刷到填充 |
| `flush_into_support` | bool | true | L2 | 冲刷到支撑 |
| `flush_into_objects` | bool | false | L1 | 冲刷到对象 |

### 6.5 Advanced（高级）- 8 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `interlocking_beam` | bool | false | L2 | 互锁梁 |
| `mmu_segmented_region_max_width` | float | 0 | L1 | 分段区域最大宽度 |
| `mmu_segmented_region_interlocking_depth` | float | 0 | L1 | 分段互锁深度 |
| `interlocking_beam_width` | float | 0 | L1 | 互锁梁宽度 |
| `interlocking_orientation` | float | 0 | L1 | 互锁方向 |
| `interlocking_beam_layer_count` | int | 0 | L1 | 互锁梁层数 |
| `interlocking_depth` | float | 0 | L1 | 互锁深度 |
| `interlocking_boundary_avoidance` | float | 0 | L1 | 边界避让 |

---

## 七、Page 6: Others（其他页面）- ~32 个参数

**数据来源**: `src/slic3r/GUI/Tab.cpp` L2842-2914

### 7.1 Skirt（裙边）- 7 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `skirt_type` | enum | - | L1 | 裙边类型 |
| `skirt_loops` | int | 1 | L1/L3 | 裙边圈数 |
| `min_skirt_length` | float | 0 | L1 | 最小裙边长度 |
| `skirt_distance` | float | 6 | L1/L3 | 裙边距离 |
| `skirt_height` | int | 1 | L1 | 裙边高度 |
| `skirt_speed` | float | 50 | L1 | 裙边速度 |
| `draft_shield` | bool | false | L2 | 防护罩 |

### 7.2 Brim（边缘）- 5 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `brim_type` | enum | auto | L1 | 边缘类型 |
| `brim_width` | float | 5 | L1/L3 | 边缘宽度 |
| `brim_object_gap` | float | 0.1 | L1 | 边缘对象间隙 |
| `brim_ears_max_angle` | float | 125 | L1 | 耳朵最大角度 |
| `brim_ears_detection_length` | float | 1 | L1 | 耳朵检测长度 |

### 7.3 Special mode（特殊模式）- 12 个参数

| 参数名 | 类型 | 枚举值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `slicing_mode` | enum | Regular/EvenOdd/CloseHoles | L1 | 切片模式 |
| `print_sequence` | enum | ByLayer/ByObject/ByDefault | L1 | 打印顺序 |
| `print_order` | enum | Default/AsObjectList | L1 | 打印顺序 |
| `spiral_mode` | bool | false | L2 | 螺旋模式 |
| `ignore_inner_color` | bool | false | L1 | 忽略内部颜色 |
| `spiral_mode_smooth` | bool | false | L1 | 平滑螺旋模式 |
| `spiral_mode_max_xy_smoothing` | float | 0 | L1 | 最大 XY 平滑 |
| `timelapse_type` | enum | Traditional/Smooth/Close | L2 | 延时摄影类型 |
| `fuzzy_skin` | enum | None/External/All/AllWalls | L2/L3 | 模糊皮肤 |
| `fuzzy_skin_point_distance` | float | 0.8 | L3 | 模糊点间距 |
| `fuzzy_skin_thickness` | float | 0.3 | L3 | 模糊厚度 |
| `fuzzy_skin_first_layer` | bool | false | L2 | 首层模糊 |

### 7.4 G-code output（G代码输出）- 6 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `reduce_infill_retraction` | bool | false | L1 | 减少填充回抽 |
| `gcode_add_line_number` | bool | false | L2 | 添加行号 |
| `gcode_comments` | bool | false | L2 | 添加注释 |
| `gcode_label_objects` | bool | false | L2 | 标记对象 |
| `exclude_object` | bool | false | L2 | 排除对象 |
| `filename_format` | string | - | N/A | 文件名格式 |

### 7.5 Post-processing Scripts（后处理脚本）- 1 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `post_process` | string | - | N/A | 后处理脚本 |

### 7.6 Notes（备注）- 1 个参数

| 参数名 | 类型 | 默认值 | 校验层次 | 说明 |
|--------|------|--------|---------|------|
| `notes` | string | - | L1 | 备注 |

---

## 八、附加页面

### 8.1 Plate Settings（板设置页面）

温度相关参数，按床面类型分组：

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `cool_plate_temp` | int | 冷板温度 |
| `cool_plate_temp_initial_layer` | int | 冷板首层温度 |
| `eng_plate_temp` | int | 工程板温度 |
| `eng_plate_temp_initial_layer` | int | 工程板首层温度 |
| `hot_plate_temp` | int | 热板温度 |
| `hot_plate_temp_initial_layer` | int | 热板首层温度 |
| `textured_plate_temp` | int | 纹理板温度 |
| `textured_plate_temp_initial_layer` | int | 纹理板首层温度 |
| `epoxy_resin_plate_temp` | int | 环氧树脂板温度 |
| `epoxy_resin_plate_temp_initial_layer` | int | 环氧树脂板首层温度 |
| `customized_plate_temp` | int | 自定义板温度 |
| `customized_plate_temp_initial_layer` | int | 自定义板首层温度 |
| `curr_bed_type` | enum | 当前床面类型 |

### 8.2 Cooling（冷却相关参数）

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `fan_min_speed` | int | 风扇最小速度 |
| `fan_max_speed` | int | 风扇最大速度 |
| `fan_cooling_layer_time` | float | 风扇冷却层时间 |
| `full_fan_speed_layer` | int | 全速风扇层 |
| `close_fan_the_first_x_layers` | int | 首 X 层关闭风扇 |
| `overhang_fan_speed` | int | 悬垂风扇速度 |
| `overhang_fan_threshold` | float | 悬垂风扇阈值 |
| `enable_overhang_bridge_fan` | bool | 启用悬垂/桥接风扇 |
| `slow_down_for_layer_cooling` | bool | 层冷却减速 |
| `slow_down_layer_time` | float | 减速层时间 |
| `slow_down_min_speed` | float | 减速最小速度 |
| `slow_down_layers` | int | 减速层数 |
| `reduce_fan_stop_start_freq` | bool | 减少风扇启停频率 |
| `additional_cooling_fan_speed` | int | 附加冷却风扇速度 |
| `enable_special_area_additional_cooling_fan` | bool | 启用特殊区域附加冷却风扇 |
| `cool_cds_fan_start_at_height` | float | CDS 风扇启动高度 |
| `cool_special_cds_fan_speed` | int | 特殊 CDS 风扇速度 |
| `cooling_slowdown_logic` | enum | 冷却减速逻辑 |
| `cooling_perimeter_transition_distance` | float | 周长过渡距离 |

### 8.3 Filament 相关参数（在 Process Tab 中）

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `nozzle_temperature` | int | 喷嘴温度 |
| `nozzle_temperature_initial_layer` | int | 首层喷嘴温度 |
| `nozzle_temperature_range_low` | int | 喷嘴温度下限 |
| `nozzle_temperature_range_high` | int | 喷嘴温度上限 |
| `chamber_temperature` | int | 腔室温度 |
| `temperature_vitrification` | int | 玻璃化温度 |
| `idle_temperature` | int | 空闲温度 |
| `filament_type` | enum | 耗材类型 |
| `filament_colour` | string | 耗材颜色 |
| `filament_diameter` | float | 耗材直径 |
| `filament_density` | float | 耗材密度 |
| `filament_cost` | float | 耗材成本 |
| `filament_flow_ratio` | float | 耗材流量比 |
| `filament_max_volumetric_speed` | float | 最大体积速度 |
| `filament_shrink` | float | 耗材收缩 |
| `filament_shrinkage_compensation_z` | float | Z 方向收缩补偿 |
| `filament_is_support` | bool | 是支撑耗材 |
| `filament_soluble` | bool | 可溶耗材 |
| `filament_vendor` | string | 耗材厂商 |
| `filament_adhesiveness_category` | enum | 粘附性类别 |
| `required_nozzle_HRC` | int | 需要的喷嘴硬度 |

---

## 九、校验覆盖统计

| 页面 | 参数数量 | L1 可校验 | L2 可校验 | L3 可校验 | 无法校验 |
|------|---------|-----------|-----------|-----------|----------|
| Quality | ~50 | 48 (96%) | 2 (4%) | 0 | 0 |
| Strength | ~35 | 35 (100%) | 0 | 0 | 0 |
| Speed | ~55 | 55 (100%) | 0 | 0 | 0 |
| Support | ~47 | 37 (79%) | 9 (19%) | 1 (2%) | 0 |
| Multimaterial | ~34 | 26 (76%) | 6 (18%) | 2 (6%) | 0 |
| Others | ~32 | 24 (75%) | 6 (19%) | 2 (6%) | 2 |
| Plate Settings | ~13 | 13 (100%) | 0 | 0 | 0 |
| Cooling | ~19 | 19 (100%) | 0 | 0 | 0 |
| Filament related | ~21 | 21 (100%) | 0 | 0 | 0 |
| **总计** | **~390** | **~350 (90%)** | **~25 (6%)** | **~5 (1%)** | **2 (<1%)** |

---

## 十、实施优先级

### 高优先级（P1）- 核心参数

| 页面 | 参数 | 理由 |
|------|------|------|
| Quality | `layer_height`, `line_width` | 影响打印质量的基础参数 |
| Strength | `wall_loops`, `top_shell_layers`, `sparse_infill_density` | 影响打印强度 |
| Speed | `outer_wall_speed`, `travel_speed`, `default_acceleration` | 影响打印时间 |
| Support | `enable_support`, `support_type`, `support_style` | 支撑核心参数 |

### 中优先级（P2）- 进阶参数

| 页面 | 参数组 | 理由 |
|------|--------|------|
| Quality | Seam, Bridging, Overhangs | 影响外观细节 |
| Speed | Overhang speed, Acceleration | 悬垂打印质量 |
| Multimaterial | Prime tower, Flush options | 多色打印必需 |
| Others | Skirt, Brim, Special mode | 首层附着和特殊功能 |

### 低优先级（P3）- 高级参数

| 页面 | 参数组 | 理由 |
|------|--------|------|
| Quality | Wall generator, Precision | 高级墙面控制 |
| Strength | AI infill, Skeleton infill | 实验性功能 |
| Support | Tree supports 高级参数 | 树支撑微调 |
| Multimaterial | Interlocking | 互锁结构 |

---

## 十一、与原文档对比

原 `process_parameters_validation.md` 文档仅涵盖：
- Multimaterial: 34 个参数
- Others: 32 个参数
- Support: 47 个参数
- **总计**: 113 个参数

**本完整版新增**：
- Quality: ~50 个参数（全新）
- Strength: ~35 个参数（全新）
- Speed: ~55 个参数（全新）
- Plate Settings: ~13 个参数（全新）
- Cooling: ~19 个参数（全新）
- Filament related: ~21 个参数（全新）
- **新增总计**: ~277 个参数

**完整版总计**: **~390 个参数**
