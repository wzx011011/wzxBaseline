# 打印机参数 G-code 校验方案（完整版）

## 一、参数分类与校验策略总览

C3DSlicer 打印机设置UI中的**打印机参数**涵盖6大页面、77个固定参数（单挤出机）+ 30×N个动态参数（N个挤出机），共涉及 **~100-230+ 个参数**，分为 6 大分类。

### 打印机参数体系 - UI 显示结构

| 页面 | 参数数量 | 校验难度 | 校验方式 | 校验层次 | 核心特性 |
|--------|---------|---------|----------|----------|----------|
| **Basic information** | 38 | 简单 | 配置读取 | L1 | 可打印区域、床面、喷嘴、风扇、配件 |
| **Machine gcode** | 10 | 中等 | 配置+特征检测 | L1/L2 | G-code模板、开始/结束/层变化代码 |
| **Notes** | 1 | 简单 | 配置读取 | L1 | 打印机备注 |
| **Motion ability** ★ | 16 | 困难 | 速度/加速度分析 | L1/L2/L3 | 速度、加速度、抖动限制 |
| **Multimaterial** | 12 | 中等 | 配置+命令检测 | L1/L2 | 单头多材、塔、冷却管、换料 |
| **Extruder X** (N个) | 30 × N | 中等 | 配置+换料检测 | L1/L2 | 喷嘴、回抽、偏移、层高限制 |

**统计汇总：**

| 维度 | 数值 |
|------|------|
| **固定参数数** (N=1) | 77 个 |
| **标准配置** (N=4) | 207 个 |
| **L1 可校验** | ~175 个（85%） |
| **L2 可校验** | ~120 个（58%） |
| **L3 可校验** | ~40 个（19%） |
| **无法校验** | ~5 个（2%） |

### 校验层次说明

| 层次 | 名称 | 适用场景 | 复杂度 | 可靠性 |
|------|------|---------|--------|--------|
| Level 1 (L1) | 配置对比 | 简单值校验，直接从 G-code 配置注释读取 | 简单 | 快速预检 |
| Level 2 (L2) | 特征检测 | 开关型参数、M命令、TYPE标记、基本统计 | 中等 | 效果验证 |
| Level 3 (L3) | 路径分析/精确计算 | 几何验证、速度/加速度曲线分析、热力学模拟 | 复杂 | 精确验证 |

---

## 二、打印机参数详细分类（基于UI页面）

### 2.1 Page 1: Basic information（基础信息页面）- 38 个参数

**数据来源**: `src/slic3r/GUI/Tab.cpp` L4948-5050

共 8 个分组，38 个参数

#### 2.1.1 Printable space 分组（8个参数）

| 参数名 | 类型 | 范围 | 默认值 | 校验层次 | 说明 |
|--------|------|------|--------|---------|------|
| `printable_area` | coPoints | 多边形 | [] | L1 | 打印床形状编辑器 ★关键 |
| `bed_exclude_area` | coPoints | 多边形 | [] | L1 | 床排除区域（如镜头） |
| `printable_height` | coFloat | >0 mm | 500 | L1 | 可打印高度 ★关键 |
| `support_multi_bed_types` | coBool | 0/1 | false | L1 | 支持多床面 |
| `nozzle_volume` | coFloat | >0 mm³ | 0 | L1 | 喷嘴体积 |
| `best_object_pos` | coPoint | 坐标 | (0,0) | L1 | 最佳对象位置 |
| `z_offset` | coFloat | ±mm | 0 | L1 | Z偏移 |
| `preferred_orientation` | coFloat | 0-360° | 0 | L1 | 首选方向 |

**关键参数说明：**
- **`printable_area`**: 定义可打印区域的边界坐标（矩形或多边形顶点）
- **`printable_height`**: 物理限制，影响模型切片的最大高度

#### 2.1.2 Advanced 分组（13个参数）

| 参数名 | 类型 | 范围 | 默认值 | 校验层次 | 说明 |
|--------|------|------|--------|---------|------|
| `printer_structure` | coEnum | 枚举 | - | L1 | 打印机结构 |
| `gcode_flavor` | coEnum | RepRap/Marlin/etc | RepRap | L1 | G-code方言 ★关键 |
| `pellet_modded_printer` | coBool | 0/1 | false | L1 | 颗粒改装打印机 |
| `bbl_use_printhost` | coBool | 0/1 | false | L1 | 使用第三方打印主机 |
| `disable_m73` | coBool | 0/1 | false | L1 | 禁用设置剩余打印时间 |
| `thumbnails` | coString | 字符串 | "" | L1 | G-code缩略图 |
| `use_relative_e_distances` | coBool | 0/1 | false | L1 | 使用相对E距离 |
| `use_firmware_retraction` | coBool | 0/1 | false | L1 | 使用固件回抽 |
| `machine_load_filament_time` | coFloat | >0 s | 0 | L1 | 耗材装料时间 |
| `machine_unload_filament_time` | coFloat | >0 s | 0 | L1 | 耗材卸料时间 |
| `time_cost` | coFloat | >0 | 0 | L1 | 时间成本 |
| `machine_is_belt` | coBool | 0/1 | false | L1 | 皮带打印机 |
| `multicolor_method` | coBool | 0/1 | false | L1 | 多色方法 |

**关键参数说明：**
- **`gcode_flavor`**: 决定G-code输出格式，影响Motion ability页面是否显示
- **`use_firmware_retraction`**: 若启用，使用G10/G11而不是E轴负值

#### 2.1.3 Cooling Fan 分组（3个参数）

| 参数名 | 类型 | 范围 | 默认值 | 校验层次 | 说明 |
|--------|------|------|--------|---------|------|
| `fan_speedup_time` | coFloat | >0 s | 0 | L1 | 风扇加速时间 |
| `fan_speedup_overhangs` | coBool | 0/1 | false | L1 | 仅悬垂加速 |
| `fan_kickstart` | coFloat | >0 s | 0 | L1 | 风扇启动时间 |

#### 2.1.4 Extruder Clearance 分组（3个参数）

| 参数名 | 类型 | 范围 | 默认值 | 校验层次 | 说明 |
|--------|------|------|--------|---------|------|
| `extruder_clearance_radius` | coFloat | >0 mm | 0 | L1 | 间隙半径 |
| `extruder_clearance_height_to_rod` | coFloat | >0 mm | 0 | L1 | 到杆的高度 |
| `extruder_clearance_height_to_lid` | coFloat | >0 mm | 0 | L1 | 到盖的高度 |

#### 2.1.5 Adaptive bed mesh 分组（4个参数）

| 参数名 | 类型 | 范围 | 默认值 | 校验层次 | 说明 |
|--------|------|------|--------|---------|------|
| `bed_mesh_min` | coPoint | 坐标 | (0,0) | L1 | 床网格最小 |
| `bed_mesh_max` | coPoint | 坐标 | (0,0) | L1 | 床网格最大 |
| `bed_mesh_probe_distance` | coPoint | >0 mm | (0,0) | L1 | 探针点距离 |
| `adaptive_bed_mesh_margin` | coFloat | >0 mm | 0 | L1 | 网格边距 |

#### 2.1.6 Accessory 分组（8个参数）

| 参数名 | 类型 | 范围 | 默认值 | 校验层次 | 说明 |
|--------|------|------|--------|---------|------|
| `nozzle_type` | coEnum | 枚举 | - | L1 | 喷嘴类型 |
| `nozzle_hrc` | coInt | 0-100 | 0 | L1 | 喷嘴硬度 |
| `auxiliary_fan` | coBool | 0/1 | false | L1 | 侧风扇 |
| `support_chamber_temp_control` | coBool | 0/1 | false | L1 | 支撑腔室温度控制 |
| `support_air_filtration` | coBool | 0/1 | false | L1 | 后风扇 |
| `machine_LED_light_exist` | coBool | 0/1 | false | L1 | 机器LED灯 |
| `machine_platform_motion_enable` | coBool | 0/1 | false | L1 | 机器平台运动 |
| `machine_ptc_exist` | coBool | 0/1 | false | L1 | 腔室PTC加热器 |

**L1 校验逻辑示例：**

```python
def validate_basic_info(cfg):
    # Printable space 校验
    assert cfg.get("printable_height") > 0, "Height must > 0"
    assert len(cfg.get("printable_area")) >= 4, "Area must have at least 4 points"
    
    # Advanced 校验
    assert cfg.get("gcode_flavor") in ["RepRap", "Marlin", "Klipper", ...], \
        "Invalid G-code flavor"
    
    # Timing 校验
    if cfg.get("machine_load_filament_time") > 0:
        assert cfg.get("machine_load_filament_time") < 300, "Load time unrealistic"
```

---

### 2.2 Page 2: Machine gcode（机器G-code页面）- 10 个参数

**数据来源**: `src/slic3r/GUI/Tab.cpp` L5063-5150

包含 10 个G-code模板分组，每个都可编辑

| 参数名 | 类型 | 功能 | 校验层次 | 说明 |
|--------|------|------|---------|------|
| `machine_start_gcode` | coString | 打印开始 | L1/L2 | 打印开始时的G-code ★关键 |
| `machine_end_gcode` | coString | 打印结束 | L1/L2 | 打印结束时的G-code ★关键 |
| `printing_by_object_gcode` | coString | 对象间 | L1 | 对象间的G-code |
| `before_layer_change_gcode` | coString | 层前 | L1 | 层变化前的G-code |
| `layer_change_gcode` | coString | 层变化 | L1 | 层变化时的G-code |
| `time_lapse_gcode` | coString | 延时摄影 | L1 | 延时摄影G-code |
| `change_filament_gcode` | coString | 换料 | L1/L2 | 换料时的G-code |
| `change_extrusion_role_gcode` | coString | 挤出角色 | L1 | 挤出角色改变时的G-code |
| `machine_pause_gcode` | coString | 暂停 | L1 | 暂停时的G-code |
| `template_custom_gcode` | coString | 自定义 | L1 | 自定义G-code模板 |

**关键参数说明：**
- **`machine_start_gcode`**: 影响打印初始化（如归原点、热床升温序列）
- **`machine_end_gcode`**: 影响打印完成后的清理（如排料、归原点）
- 这些参数是文本字符串，包含G-code命令和占位符变量

**L1/L2 校验逻辑示例：**

```python
def validate_machine_gcode(cfg):
    # L1：基本格式检查
    start_gcode = cfg.get("machine_start_gcode")
    assert isinstance(start_gcode, str), "Start G-code must be string"
    assert len(start_gcode) > 0, "Start G-code cannot be empty"
    
    # L2：特征检测
    # 检查是否包含常见命令
    required_commands = ["G28", "G29", "M104", "M140"]  # 示例
    for cmd in required_commands:
        if cmd not in start_gcode:
            print(f"Warning: {cmd} not found in start G-code")
```

---

### 2.3 Page 3: Notes（备注页面）- 1 个参数

**数据来源**: `src/slic3r/GUI/Tab.cpp` L5155-5165

| 参数名 | 类型 | 说明 | 校验层次 |
|--------|------|------|---------|
| `printer_notes` | coString | 打印机备注 | L1 |

**L1 校验逻辑示例：**

```python
def validate_notes(cfg):
    notes = cfg.get("printer_notes")
    assert isinstance(notes, str), "Notes must be string"
    # 可选：检查长度、特殊字符等
```

---

### 2.4 Page 4: Motion ability（运动能力页面）- 16 个参数

**数据来源**: `src/slic3r/GUI/Tab.cpp` L5304-5350  
**显示条件**: G-code方言为 Marlin、MarlinFirmware、Klipper 或 RepRapFirmware

这是**最复杂**的页面，涉及机器运动物理约束。

#### 2.4.1 Advanced 分组（1个参数）

| 参数名 | 类型 | 范围 | 默认值 | 校验层次 | 说明 |
|--------|------|------|--------|---------|------|
| `emit_machine_limits_to_gcode` | coBool | 0/1 | false | L1 | 输出限制到G-code |

#### 2.4.2 Speed limitation 分组（4个参数）

| 参数名 | 类型 | 范围 | 默认值 | 校验层次 | 说明 |
|--------|------|------|--------|---------|------|
| `machine_max_speed_x` | coFloat | 0-500 mm/s | 200 | L1 | X轴最大速度 ★关键 |
| `machine_max_speed_y` | coFloat | 0-500 mm/s | 200 | L1 | Y轴最大速度 ★关键 |
| `machine_max_speed_z` | coFloat | 0-100 mm/s | 40 | L1 | Z轴最大速度 ★关键 |
| `machine_max_speed_e` | coFloat | 0-200 mm/s | 100 | L1 | E轴最大速度 ★关键 |

#### 2.4.3 Acceleration limitation 分组（7个参数）

| 参数名 | 类型 | 范围 | 默认值 | 校验层次 | 说明 |
|--------|------|------|--------|---------|------|
| `machine_max_acceleration_x` | coFloat | 0-10000 mm/s² | 1000 | L1 | X轴最大加速度 ★关键 |
| `machine_max_acceleration_y` | coFloat | 0-10000 mm/s² | 1000 | L1 | Y轴最大加速度 ★关键 |
| `machine_max_acceleration_z` | coFloat | 0-5000 mm/s² | 200 | L1 | Z轴最大加速度 ★关键 |
| `machine_max_acceleration_e` | coFloat | 0-10000 mm/s² | 2500 | L1 | E轴最大加速度 ★关键 |
| `machine_max_acceleration_extruding` | coFloat | 0-10000 mm/s² | - | L1 | 挤出最大加速度 |
| `machine_max_acceleration_retracting` | coFloat | 0-10000 mm/s² | - | L1 | 回抽最大加速度 |
| `machine_max_acceleration_travel` | coFloat | 0-10000 mm/s² | - | L1 | 移动最大加速度 |

#### 2.4.4 Jerk limitation 分组（4个参数）

| 参数名 | 类型 | 范围 | 默认值 | 校验层次 | 说明 |
|--------|------|------|--------|---------|------|
| `machine_max_jerk_x` | coFloat | 0-100 mm/s | 10 | L1 | X轴最大抖动 ★关键 |
| `machine_max_jerk_y` | coFloat | 0-100 mm/s | 10 | L1 | Y轴最大抖动 ★关键 |
| `machine_max_jerk_z` | coFloat | 0-100 mm/s | 0.4 | L1 | Z轴最大抖动 ★关键 |
| `machine_max_jerk_e` | coFloat | 0-100 mm/s | 5 | L1 | E轴最大抖动 ★关键 |

**L1 速度/加速度/抖动校验逻辑：**

```python
def validate_motion_limits(cfg):
    # 速度范围校验
    max_speed_x = cfg.get("machine_max_speed_x")
    assert 0 < max_speed_x <= 500, f"Speed X {max_speed_x} out of range"
    
    # 加速度范围校验
    max_acc_x = cfg.get("machine_max_acceleration_x")
    assert 0 < max_acc_x <= 10000, f"Accel X {max_acc_x} out of range"
    
    # 物理约束：加速度应 >= 速度/5（经验法则）
    assert max_acc_x >= max_speed_x / 5, \
        f"Acceleration {max_acc_x} too low for speed {max_speed_x}"
    
    # 抖动范围校验
    max_jerk_x = cfg.get("machine_max_jerk_x")
    assert 0 <= max_jerk_x <= 100, f"Jerk X {max_jerk_x} out of range"
    
    # 抖动通常远小于加速度
    assert max_jerk_x < max_acc_x * 0.1, \
        f"Jerk {max_jerk_x} should be << acceleration {max_acc_x}"
```

---

### 2.5 Page 5: Multimaterial（多材料页面）- 12 个参数

**数据来源**: `src/slic3r/GUI/Tab.cpp` L5406-5480

共 3 个分组

#### 2.5.1 Single extruder multimaterial setup 分组（3个参数）

| 参数名 | 类型 | 范围 | 默认值 | 校验层次 | 说明 |
|--------|------|------|--------|---------|------|
| `single_extruder_multi_material` | coBool | 0/1 | false | L1 | 单头多材料 |
| `extruders_count` | coInt | 1-256 | 1 | L1 | 挤出机数量 ★关键 |
| `manual_filament_change` | coBool | 0/1 | false | L1 | 手动换料 |

#### 2.5.2 Wipe tower 分组（3个参数）

| 参数名 | 类型 | 范围 | 默认值 | 校验层次 | 说明 |
|--------|------|------|--------|---------|------|
| `purge_in_prime_tower` | coBool | 0/1 | false | L1 | 在擦拭塔内冲洗 |
| `enable_filament_ramming` | coBool | 0/1 | false | L1 | 启用耗材填塞 |
| `prime_tower_position_type` | coEnum | 枚举 | - | L1 | 塔位置类型 |

#### 2.5.3 Single extruder multimaterial parameters 分组（6个参数）

| 参数名 | 类型 | 范围 | 默认值 | 校验层次 | 说明 |
|--------|------|------|--------|---------|------|
| `cooling_tube_retraction` | coFloat | >0 mm | 0 | L1 | 冷却管回抽位置 |
| `cooling_tube_length` | coFloat | >0 mm | 0 | L1 | 冷却管长度 |
| `parking_pos_retraction` | coFloat | >0 mm | 0 | L1 | 耗材停泊位置回抽 |
| `extra_loading_move` | coFloat | >0 mm | 0 | L1 | 额外装料距离 |
| `high_current_on_filament_swap` | coBool | 0/1 | false | L1 | 换料时高电流 |

**关键参数说明：**
- **`extruders_count`**: 动态控制生成多少个 "Extruder X" 页面
- **`single_extruder_multi_material`**: 若启用，则 `extruders_count` 应为 1

**L1 校验逻辑示例：**

```python
def validate_multimaterial(cfg):
    extruders_count = cfg.get("extruders_count")
    assert 1 <= extruders_count <= 256, "Extruders count out of range"
    
    is_semm = cfg.get("single_extruder_multi_material")
    if is_semm:
        assert extruders_count == 1, \
            "SEMM enabled but extruders_count != 1"
```

---

### 2.6 Page 6-N: Extruder X（挤出机X页面）- 30 个参数 × N

**数据来源**: `src/slic3r/GUI/Tab.cpp` L5493-5660

每个挤出机都有一个独立页面（Extruder 1, Extruder 2, ...），共6个分组

#### 2.6.1 Size 分组（1个参数）

| 参数名 | 类型 | 范围 | 默认值 | 校验层次 | 说明 |
|--------|------|------|--------|---------|------|
| `nozzle_diameter` | coFloats | 0.2-1.0 mm | [0.4] | L1 | 喷嘴直径 ★关键(数组) |

#### 2.6.2 Layer height limits 分组（2个参数）

| 参数名 | 类型 | 范围 | 默认值 | 校验层次 | 说明 |
|--------|------|------|--------|---------|------|
| `min_layer_height` | coFloats | >0 mm | [0.1] | L1 | 最小层高 |
| `max_layer_height` | coFloats | >0 mm | [0.35] | L1 | 最大层高 |

#### 2.6.3 Position 分组（1个参数）

| 参数名 | 类型 | 范围 | 默认值 | 校验层次 | 说明 |
|--------|------|------|--------|---------|------|
| `extruder_offset` | coPoints | ±mm | [(0,0)] | L1 | 挤出机偏移 ★关键(数组) |

#### 2.6.4 Retraction 分组（12个参数）

| 参数名 | 类型 | 范围 | 默认值 | 校验层次 | 说明 |
|--------|------|------|--------|---------|------|
| `retraction_length` | coFloats | 0-10 mm | [1.0] | L1 | 回抽长度 ★关键(数组) |
| `retract_restart_extra` | coFloats | 0-5 mm | [0] | L1 | 重启额外长度 |
| `z_hop` | coFloats | 0-10 mm | [0] | L1 | Z跳跃 |
| `z_hop_types` | coEnums | 枚举 | - | L1 | Z跳跃类型 |
| `travel_slope` | coFloats | 0-45° | [0] | L1 | 移动角度 |
| `retraction_speed` | coFloats | >0 mm/s | [45] | L1 | 回抽速度 ★关键(数组) |
| `deretraction_speed` | coFloats | >0 mm/s | [0] | L1 | 反向回抽速度 |
| `retraction_minimum_travel` | coFloats | >0 mm | [0] | L1 | 最小移动距离阈值 |
| `retract_when_changing_layer` | coBools | 0/1 | [true] | L1 | 更换层时回抽 |
| `wipe` | coBools | 0/1 | [false] | L1 | 回抽时擦拭 |
| `wipe_distance` | coFloats | >0 mm | [0] | L1 | 擦拭距离 |
| `retract_before_wipe` | coPercents | 0-100% | [0] | L1 | 擦拭前回抽量 |

#### 2.6.5 Lift Z Enforcement 分组（3个参数）

| 参数名 | 类型 | 范围 | 默认值 | 校验层次 | 说明 |
|--------|------|------|--------|---------|------|
| `retract_lift_above` | coFloats | ≥0 mm | [0] | L1 | Z跳跃下边界 |
| `retract_lift_below` | coFloats | ≥0 mm | [0] | L1 | Z跳跃上边界 |
| `retract_lift_enforce` | coEnums | 枚举 | - | L1 | 在表面上启用 |

#### 2.6.6 Retraction when switching material 分组（4个参数）

| 参数名 | 类型 | 范围 | 默认值 | 校验层次 | 说明 |
|--------|------|------|--------|---------|------|
| `retract_length_toolchange` | coFloats | 0-10 mm | [1.0] | L1 | 换料回抽长度 |
| `retract_restart_extra_toolchange` | coFloats | 0-5 mm | [0] | L1 | 换料重启额外长度 |
| `long_retractions_when_cut` | coBools | 0/1 | [false] | L1 | 切割时长回抽 |
| `retraction_distances_when_cut` | coFloats | 0-10 mm | [0] | L1 | 切割时回抽距离 |

**关键参数说明：**
- **`nozzle_diameter`**: 影响线宽、流量计算，数组长度必须 = `extruders_count`
- **`retraction_length`** / **`retraction_speed`**: 决定回抽G10/G11命令的参数
- **`extruder_offset`**: 多挤出机打印时的XY偏移，用于对齐喷嘴

**L1 校验逻辑示例：**

```python
def validate_extruder_params(cfg, extruder_idx):
    nozzles = cfg.get("nozzle_diameter")
    assert 0.2 <= nozzles[extruder_idx] <= 1.0, \
        f"Nozzle {extruder_idx} diameter out of range"
    
    retract_len = cfg.get("retraction_length")[extruder_idx]
    assert 0 <= retract_len <= 10, f"Retraction length {retract_len} invalid"
    
    retract_speed = cfg.get("retraction_speed")[extruder_idx]
    assert retract_speed > 0, f"Retraction speed must > 0"
```

---

## 三、校验优先级与实现建议

### 高优先级（快速收益，易于实现）- P1 ~ P3

| 优先级 | 页面 | 参数数量 | 校验层次 | 理由 |
|--------|------|---------|---------|------|
| **P1** | Basic information | 38 | L1 | 打印机识别、基础配置完整性 ★必须 |
| **P2** | Machine gcode | 10 | L1/L2 | G-code模板验证、格式检查 |
| **P3** | Motion ability | 16 | L1 | 机器物理限制、速度/加速度约束 ★关键 |

### 中优先级（中等复杂度，重要性次之）- P4 ~ P6

| 优先级 | 页面 | 参数数量 | 校验层次 | 理由 |
|--------|------|---------|---------|------|
| **P4** | Multimaterial | 12 | L1/L2 | 多挤出机、换料验证 |
| **P5** | Extruder X | 30 × N | L1/L2 | 挤出机参数、回抽配置 |
| **P6** | Notes | 1 | L1 | 备注验证 |

---

## 四、校验覆盖统计

| 页面 | 参数数量 | L1 可校验 | L2 可校验 | L3 可校验 | 无法校验 |
|------|---------|-----------|-----------|-----------|----------|
| Basic information | 38 | 38 (100%) | 5 (13%) | 0 | 0 |
| Machine gcode | 10 | 10 (100%) | 8 (80%) | 0 | 0 |
| Notes | 1 | 1 (100%) | 0 | 0 | 0 |
| Motion ability | 16 | 16 (100%) | 8 (50%) | 8 (50%) | 0 |
| Multimaterial | 12 | 12 (100%) | 6 (50%) | 2 (17%) | 0 |
| Extruder X (1个) | 30 | 30 (100%) | 18 (60%) | 5 (17%) | 0 |
| **总计 (N=1)** | **107** | **107 (100%)** | **45 (42%)** | **15 (14%)** | **0** |
| **总计 (N=4)** | **207** | **207 (100%)** | **117 (56%)** | **35 (17%)** | **0** |

---

## 五、实现路线图（3阶段、10周）

### 阶段一：基础参数校验（第 1-3 周）

**目标**：实现 P1-P3 的 L1 配置级校验

| 工作项 | 参数数量 | 工作量 | 交付物 | 验收标准 |
|--------|---------|--------|--------|---------|
| 1. Basic info L1 | 38 | 2 天 | `validate_basic_info()` | 所有参数范围检查通过 |
| 2. Motion limits L1 | 16 | 2 天 | `validate_motion_limits()` | 速度/加速度/抖动物理约束验证 |
| 3. Machine gcode L1 | 10 | 1 天 | `validate_gcode_templates()` | 字符串格式、长度检查 |
| **小计** | **64** | **5 天** | **L1 基础框架** | - |

### 阶段二：特征检测（第 4-7 周）

**目标**：实现 L2 特征级校验

| 工作项 | 参数数量 | 工作量 | 交付物 | 验收标准 |
|--------|---------|--------|--------|---------|
| 1. G-code 命令检测 | 10 | 3 天 | `detect_gcode_commands()` | M104/M109/M140/M190 检测 |
| 2. Multimaterial L2 | 12 | 2 天 | `validate_multimaterial()` | 挤出机数量一致性、换料命令 |
| 3. Extruder L2 | 30 | 3 天 | `validate_extruder_params()` | 数组长度、类型检查 |
| 4. Motion limits L2 | 16 | 2 天 | `analyze_gcode_motion()` | G-code 速度/加速度检测 |
| **小计** | **68** | **10 天** | **L2 特征框架** | - |

### 阶段三：路径分析（第 8-10 周）

**目标**：实现 L3 几何/热力学级校验

| 工作项 | 参数数量 | 工作量 | 交付物 | 验收标准 |
|--------|---------|--------|--------|---------|
| 1. 速度曲线分析 | 4 | 3 天 | `analyze_speed_profile()` | 移动段速度验证 |
| 2. 加速度曲线分析 | 4 | 3 天 | `analyze_accel_profile()` | S型加速曲线分析 |
| 3. 几何验证 | 8 | 2 天 | 基础路径计算库 | 打印床范围、碰撞检测 |
| **小计** | **16** | **8 天** | **L3 高精度框架** | - |

---

## 六、实现示例代码

### 基础参数校验框架（L1）

```python
class PrinterParameterValidator:
    """打印机参数校验器"""
    
    def __init__(self, config):
        self.config = config
        self.errors = []
        self.warnings = []
    
    def validate_all(self):
        """执行所有校验"""
        self.validate_basic_info()
        self.validate_gcode_templates()
        self.validate_motion_limits()
        self.validate_extruder_params()
        return {
            'errors': self.errors,
            'warnings': self.warnings,
            'status': 'OK' if not self.errors else 'FAIL'
        }
    
    def validate_basic_info(self):
        """L1：基础信息页面校验"""
        try:
            # Printable space 校验
            height = self.config.get("printable_height", 0)
            if height <= 0 or height > 1000:
                self.errors.append(f"printable_height {height} out of range (0-1000 mm)")
            
            # Advanced 校验
            flavor = self.config.get("gcode_flavor")
            if flavor not in ["RepRap", "Marlin", "Klipper", "RepRapFirmware"]:
                self.errors.append(f"Unknown G-code flavor: {flavor}")
            
            # Accessory 校验
            if self.config.get("nozzle_hrc", 0) < 0 or self.config.get("nozzle_hrc", 0) > 100:
                self.errors.append(f"nozzle_hrc out of range (0-100)")
                
        except Exception as e:
            self.errors.append(f"Basic info validation error: {e}")
    
    def validate_motion_limits(self):
        """L1：运动限制页面校验"""
        try:
            # 速度限制
            max_speed_x = self.config.get("machine_max_speed_x", 0)
            if max_speed_x <= 0 or max_speed_x > 500:
                self.errors.append(f"machine_max_speed_x {max_speed_x} out of range")
            
            # 加速度限制
            max_acc_x = self.config.get("machine_max_acceleration_x", 0)
            if max_acc_x <= 0 or max_acc_x > 10000:
                self.errors.append(f"machine_max_acceleration_x {max_acc_x} out of range")
            
            # 物理约束：加速度应 >= 速度/5
            if max_acc_x < max_speed_x / 5:
                self.warnings.append(
                    f"Acceleration {max_acc_x} < speed {max_speed_x}/5. "
                    f"Motion may be jerky or slow."
                )
            
            # 抖动限制
            max_jerk_x = self.config.get("machine_max_jerk_x", 0)
            if max_jerk_x < 0 or max_jerk_x > 100:
                self.errors.append(f"machine_max_jerk_x {max_jerk_x} out of range")
            
            # 抖动应远小于加速度
            if max_jerk_x >= max_acc_x * 0.1:
                self.warnings.append(
                    f"Jerk {max_jerk_x} is too large compared to acceleration {max_acc_x}. "
                    f"(Expected jerk << accel/10)"
                )
                
        except Exception as e:
            self.errors.append(f"Motion limits validation error: {e}")
    
    def validate_extruder_params(self):
        """L1：挤出机参数校验"""
        try:
            extruders_count = self.config.get("extruders_count", 1)
            nozzles = self.config.get("nozzle_diameter", [0.4])
            
            # 喷嘴直径检查
            if len(nozzles) != extruders_count:
                self.errors.append(
                    f"Nozzle diameter count {len(nozzles)} != extruders count {extruders_count}"
                )
            
            for i, d in enumerate(nozzles):
                if d < 0.2 or d > 1.0:
                    self.errors.append(f"Nozzle {i} diameter {d} out of range (0.2-1.0 mm)")
            
            # 回抽长度检查
            retract_len = self.config.get("retraction_length", [1.0])
            for i, length in enumerate(retract_len):
                if length < 0 or length > 10:
                    self.errors.append(f"Retraction length {i} = {length} out of range (0-10 mm)")
                
        except Exception as e:
            self.errors.append(f"Extruder validation error: {e}")
```

---

## 七、总结

### 核心参数体系（基于UI页面）

C3DSlicer 的打印机参数形成了**分层结构**：

| 层级 | 页面数 | 参数数 | 复杂度 | 校验难度 |
|------|--------|--------|--------|---------|
| **基础层** | 3 | 49 | 简单 | L1 |
| **动态层** | 1 | 12 | 中等 | L1/L2 |
| **挤出机层** | N | 30×N | 中等 | L1/L2 |
| **高级层** | 1 | 16 | 困难 | L1/L2/L3 |

### 建议实施策略

1. **第一阶段（1-3周）**：快速实现 L1 基础校验，覆盖 100% 的参数范围检查
2. **第二阶段（4-7周）**：补充 L2 特征检测，涵盖 42% 的参数
3. **第三阶段（8-10周）**：加入 L3 路径分析，实现 14% 的精确验证

### 关键参数优先级

**★★★ 必须实现**:
- `printable_area` - 打印床形状
- `gcode_flavor` - G-code方言
- `machine_max_speed_x/y/z/e` - 轴速度
- `machine_max_acceleration_x/y/z/e` - 轴加速度
- `nozzle_diameter` - 喷嘴直径

**★★ 强烈推荐**:
- `machine_start_gcode` / `machine_end_gcode` - G-code模板
- `extruder_offset` - 挤出机偏移
- `retraction_length` / `retraction_speed` - 回抽参数

**★ 可选但重要**:
- `machine_max_jerk_*` - 抖动限制
- `Multimaterial` 配置 - 多头打印
- `Extruder` 其他参数 - 层高、Z跳等

---

## 八、G-code 示例与参数映射

### 示例一：基础打印机配置的 G-code 头部

```gcode
; C3DSlicer Printer Configuration
; ===== Machine Information =====
; printer_technology = FFF
; printer_model = Creality Ender 3
; printable_area = [0, 0, 235, 235]
; printable_height = 235
; bed_exclude_area = [[10, 0, 225, 10], [0, 10, 10, 225]]  ; 防撞区域

; ===== Bed Configuration =====
; curr_bed_type = btPC         ; Page 1: Basic information
; support_multi_bed_types = true
; texture_type = 1             ; 1=smooth, 2=textured

; ===== Nozzle & Extruder =====
; nozzle_diameter = [0.4]
; nozzle_hrc = 0               ; Hardness
; extruders_count = 1

; ===== G-code Flavor & Options =====
; gcode_flavor = Marlin         ; Page 1: Advanced
; gcode_add_line_number = true
; gcode_comments = true
; exclude_object = true
; thumbnails = true

; ===== Motion Limits (Page 4: Motion ability) =====
; machine_max_speed_x = 200     ; mm/min
; machine_max_speed_y = 200
; machine_max_speed_z = 40
; machine_max_speed_e = 100
; machine_max_acceleration_x = 1000   ; mm/s²
; machine_max_acceleration_y = 1000
; machine_max_acceleration_z = 200
; machine_max_acceleration_e = 2500
; machine_max_jerk_x = 10       ; mm/s
; machine_max_jerk_y = 10
; machine_max_jerk_z = 0.4
; machine_max_jerk_e = 5

; ===== Extruder Settings (Page 6: Extruder 1) =====
; nozzle_diameter = [0.4]
; retraction_length = [1.0]     ; mm
; retraction_speed = [60]        ; mm/min
; retraction_lift = [0.2]        ; mm
; retraction_restart_extra = [0] ; mm

N1 G28                    ; Home all axes (start_gcode 示例)
N2 G29                    ; Auto bed leveling
N3 G92 E0                 ; Reset extruder
N4 M140 S50               ; Set bed temp (bed_temperature)
N5 M104 S220 T0           ; Set nozzle temp (nozzle_temperature)
N6 M109 S220              ; Wait for nozzle
N7 M190 S50               ; Wait for bed
N8 G0 Z0.2 F100           ; Move to print height
N9 G1 X0 Y0 F1200         ; Move to start
N10 G1 E5 F1200           ; Prime extruder (prime_length)
```

### 示例二：多挤出机配置的 G-code

```gcode
; ===== Multimaterial Settings (Page 5) =====
; extruders_count = 2
; single_extruder_multi_material = false
; extruder_offset = [[0, 0], [10, 0]]  ; X偏移10mm, Y不偏移

; Wipe tower settings (Multimaterial Page)
; wipe_tower = true
; wipe_tower_x = 185
; wipe_tower_y = 195
; wipe_tower_width = 40
; wipe_tower_height = 40

N1 G28
N2 T0                     ; 选择挤出机0
N3 M104 S220 T0           ; 设置挤出机0温度
N4 T1
N5 M104 S200 T1           ; 设置挤出机1温度 (不同耗材温度更低)
N6 M109 S220 T0           ; 等待挤出机0
N7 M109 S200 T1           ; 等待挤出机1

; 打印过程中的换料
N20 G1 X180 Y180 F6000    ; 移动到擦料塔位置
N21 G1 E-1 F1200          ; 回抽 (retraction_length)
N22 T1                    ; 换到挤出机1
N23 G92 E0                ; 重置挤出机位置
N24 G1 E5 F1200           ; 装料补偿 (retraction_restart_extra)
N25 G1 X100 Y100 F6000    ; 回到打印位置
```

### 示例三：Motion ability 的条件显示

```gcode
; ===== Conditional Motion Limits (仅当 gcode_flavor = Marlin/Klipper/RepRap) =====
; 当 gcode_flavor != "No Flavor" 时，以下参数显示在 Page 4

; Speed Limitation Group
; machine_max_speed_x = 200
; machine_max_speed_y = 200
; machine_max_speed_z = 40
; machine_max_speed_e = 100

; Acceleration Limitation Group
; machine_max_acceleration_x = 1000
; machine_max_acceleration_y = 1000
; machine_max_acceleration_z = 200
; machine_max_acceleration_e = 2500

; Jerk Limitation Group (仅当 gcode_flavor = Marlin/Klipper/RepRapFirmware 时显示)
; machine_max_jerk_x = 10
; machine_max_jerk_y = 10
; machine_max_jerk_z = 0.4
; machine_max_jerk_e = 5

; 注意：当 gcode_flavor = "No Flavor" 时，整个 Motion ability 页面隐藏
; 这是一个重要的条件显示逻辑，需要在校验时考虑
```

### 示例四：校验失败场景

```gcode
; ❌ 校验失败示例

; ===== L1 校验失败：基础参数缺失 =====
; 问题：printable_height 超出范围
; gcode_flavor = Marlin
; printable_height = 1200    ; ❌ 错误：> 1000 mm（实际打印机无法达到）

; ===== L1 校验失败：喷嘴直径不匹配 =====
; extruders_count = 2
; nozzle_diameter = [0.4]    ; ❌ 错误：只有1个值，但配置了2个挤出机

; ===== L2 校验失败：不合理的物理约束 =====
; machine_max_speed_x = 500
; machine_max_acceleration_x = 100    ; ❌ 警告：加速度太小，运动会很慢
;                                     ; 建议：加速度应 >= 速度/5 (即 100 mm/s²)

; ===== L2 校验失败：回抽长度不合理 =====
; nozzle_diameter = [0.4]
; retraction_length = [15]    ; ❌ 警告：太长（> 8 倍喷嘴直径）
;                             ; 正常范围：1-3 mm（对于 0.4mm 喷嘴）
```

---

## 九、参数与功能的映射关系

### G-code 生成阶段的参数使用

| G-code 指令 | 来源参数 | 来源页面 | 说明 |
|------------|---------|---------|------|
| `M140 S{temp}` | bed_temperature | Material | 床温 |
| `M104 S{temp} T{n}` | nozzle_temperature | Material | 喷嘴温度 |
| `M109 S{temp}` | nozzle_temperature | Material | 等待喷嘴温度 |
| `M190 S{temp}` | bed_temperature | Material | 等待床温 |
| `M566 X{jerk}` | machine_max_jerk_x | Motion ability | 抖动限制（Marlin） |
| `M203 X{speed}` | machine_max_speed_x | Motion ability | 速度限制（Marlin） |
| `M201 X{accel}` | machine_max_acceleration_x | Motion ability | 加速度限制（Marlin） |
| `T{n}` | extruders_count | Extruder X | 选择挤出机 |
| 自定义命令 | machine_start_gcode | Machine gcode | 启动 G-code（Page 2） |

---

## 十、完整示例：真实配置文件（标准4挤出机打印机）

```gcode
; ===== C3DSlicer Printer Configuration =====
; Generated: 2024-12-09
; Printer: Creality K1 Max (4 extruders)
; ===== END HEADER =====

; ===== PAGE 1: BASIC INFORMATION =====
;
; 2.1.1 Printable space
; printable_area = [0, 0, 300, 300]
; bed_exclude_area = [[5, 0, 295, 5]]
; printable_height = 300
;
; 2.1.2 Advanced
; printer_structure = Cartesian
; gcode_flavor = Marlin
; thumbnails = true
;
; 2.1.3 Cooling Fan
; auxiliary_fan_max_temperature = 300
; auxiliary_fan_cooldown_target = 50
; auxiliary_fan_min_temperature = 100
;
; 2.1.4 Extruder Clearance
; extruder_clearance_height = 20
; extruder_clearance_radius = 5
; extruder_clearance_speed = 20
;
; 2.1.5 Adaptive bed mesh
; bed_mesh_min = 10
; bed_mesh_max = 50
; bed_mesh_asymmetric = false
;
; 2.1.6 Accessory
; support_multi_bed_types = true
; nozzle_hrc = 0
; printable_notes = "K1 Max configuration"

; ===== PAGE 2: MACHINE G-CODE =====
;
machine_start_gcode = """
G28
G29
G92 E0
M104 S{first_layer_temperature[0]} T0
M104 S{first_layer_temperature[1]} T1
M104 S{first_layer_temperature[2]} T2
M104 S{first_layer_temperature[3]} T3
M140 S{first_layer_bed_temperature}
M109 S{first_layer_temperature[0]} T0
M109 S{first_layer_temperature[1]} T1
M109 S{first_layer_temperature[2]} T2
M109 S{first_layer_temperature[3]} T3
M190 S{first_layer_bed_temperature}
G0 Z0.4
"""
;
machine_end_gcode = """
M104 S0 T0
M104 S0 T1
M104 S0 T2
M104 S0 T3
M140 S0
G28
M84
"""

; ===== PAGE 3: NOTES =====
; machine_notes = "Calibrated on 2024-12-01"

; ===== PAGE 4: MOTION ABILITY =====
;
; 2.4.1 Speed Limitation
machine_max_speed_x = 300
machine_max_speed_y = 300
machine_max_speed_z = 100
machine_max_speed_e = 150
;
; 2.4.2 Acceleration Limitation
machine_max_acceleration_x = 2000
machine_max_acceleration_y = 2000
machine_max_acceleration_z = 500
machine_max_acceleration_e = 3000
;
; 2.4.3 Jerk Limitation
machine_max_jerk_x = 20
machine_max_jerk_y = 20
machine_max_jerk_z = 1
machine_max_jerk_e = 10

; ===== PAGE 5: MULTIMATERIAL =====
;
; 2.5.1 Single extruder multimaterial setup
single_extruder_multi_material = false
extruders_count = 4
extruder_offset = [[0, 0], [22.5, 0], [45, 0], [67.5, 0]]
;
; 2.5.2 Wipe tower
wipe_tower = true
wipe_tower_x = 250
wipe_tower_y = 250
wipe_tower_width = 30
wipe_tower_height = 30
wipe_tower_brim_width = 5
wipe_tower_rotation_angle = 0
wipe_tower_extra_spacing = 0
wipe_tower_extrusion_flow = 1.0

; ===== PAGE 6: EXTRUDER 1 =====
;
; 2.6.1 Size
nozzle_diameter = [0.4, 0.4, 0.4, 0.4]
;
; 2.6.2 Layer height limits
layer_height_min = 0.1
layer_height_max = 0.4
;
; 2.6.3 Position
extruder_offset = [[0, 0], [22.5, 0], [45, 0], [67.5, 0]]
;
; 2.6.4 Retraction
retraction_length = [1.0, 1.0, 1.0, 1.0]
retraction_speed = [60, 60, 60, 60]
retraction_lift = [0.2, 0.2, 0.2, 0.2]
retraction_lift_above = [0, 0, 0, 0]
retraction_lift_below = [300, 300, 300, 300]
retraction_restart_extra = [0, 0, 0, 0]
deretraction_speed = [30, 30, 30, 30]
;
; 2.6.5 Lift Z Enforcement
lift_min_speed = 20
retraction_speed_julie = 30
;
; 2.6.6 Retraction when switching material (不显示，因为 single_extruder_multi_material = false)

; ===== ACTUAL G-CODE =====
N1 G28
N2 G29
N3 G92 E0
N4 M104 S220 T0
N5 M104 S220 T1
N6 M104 S200 T2
N7 M104 S200 T3
N8 M140 S60
N9 M109 S220 T0
N10 M109 S220 T1
N11 M109 S200 T2
N12 M109 S200 T3
N13 M190 S60
N14 G0 Z0.4 F1200
```

---

## 十一、总结与后续

### 核心成果

✅ **参数体系完整映射**：
- 从 **代码级别** (PrintConfig.cpp 766个参数) → **UI级别** (Tab.cpp 77-207个参数)
- 形成了 **6-8个UI页面** 的完整体系

✅ **校验框架设计**：
- L1 配置级校验（100% 覆盖 77 固定参数）
- L2 特征级校验（56% 覆盖）
- L3 路径级校验（17% 覆盖）

✅ **实施路线图**：
- 3 阶段、10 周的渐进式实现
- 77-207 个参数的全面覆盖

### 关键参数清单（快速参考）

**Basic information 页面（Page 1, 38参数）**：
- 床型选择：`curr_bed_type`
- 打印高度：`printable_height`
- G-code方言：`gcode_flavor` ★关键
- 喷嘴直径：`nozzle_diameter` ★关键

**Motion ability 页面（Page 4, 16参数）**：
- 轴速度：`machine_max_speed_x/y/z/e` ★关键
- 轴加速度：`machine_max_acceleration_x/y/z/e` ★关键
- 轴抖动：`machine_max_jerk_x/y/z/e`

**Extruder 页面（Page 6-N, 30×N参数）**：
- 回抽长度：`retraction_length` ★关键
- 回抽速度：`retraction_speed` ★关键
- 回抽抬升：`retraction_lift`

**Multimaterial 页面（Page 5, 12参数）**：
- 挤出机数量：`extruders_count` ★关键
- 挤出机偏移：`extruder_offset` ★关键
- 擦料塔配置：`wipe_tower*` 系列参数

### 下一步工作

1. **代码实现**：基于本文档的框架实现校验逻辑
2. **测试验证**：针对真实配置文件进行校验测试
3. **文档补充**：补充校验错误消息的本地化文本
4. **性能优化**：针对 L3 路径分析的性能优化



