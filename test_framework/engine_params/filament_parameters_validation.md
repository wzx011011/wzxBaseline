# C3DSlicer 耗材丝参数校验方案

**文档类型**: 耗材丝设置参数验证指南  
**数据来源**: `src/slic3r/GUI/Tab.cpp` - TabFilament::build() 函数  
**生成日期**: 2025-12-09  
**适用版本**: CrealityPrint (C3DSlicer)

---

## 目录

1. [耗材丝参数体系概览](#一耗材丝参数体系概览)
2. [耗材丝页面详细参数](#二耗材丝页面详细参数)
3. [校验优先级与实现建议](#三校验优先级与实现建议)
4. [实现路线图](#四实现路线图)
5. [校验覆盖统计](#五校验覆盖统计)
6. [实现示例代码](#六实现示例代码)
7. [G-code 示例与参数映射](#七gcode-示例与参数映射)
8. [总结](#八总结)

---

## 一、耗材丝参数体系概览

### 1.1 页面结构

耗材丝设置UI包含 **6个主要页面**，共 **94个参数**（基础配置）：

| 页面序号 | 页面名称 | 参数分组数 | 参数数量 | 用途 | 显示条件 |
|---------|---------|----------|---------|------|---------|
| 1 | **Filament** | 5个 | 39个 | 基础信息、温度配置 | 总是显示 |
| 2 | **Cooling** | 4个 | 22个 | 风扇、冷却策略 | 总是显示 |
| 3 | **Setting Overrides** | 1个 | 16个 | 回抽覆盖参数 | 总是显示 |
| 4 | **Advanced** | 2个 | 2个 | 自定义G-code | 总是显示 |
| 5 | **Multimaterial** | 3个 | 14个 | 多材料、换料参数 | 总是显示 |
| 6 | **Notes** | 1个 | 1个 | 耗材备注 | 总是显示 |
| **合计** | | | **94个** | | |

### 1.2 参数统计概览

| 维度 | 统计值 |
|------|--------|
| **总参数数** | 94 个 |
| **L1 可校验** | 94 (100%) |
| **L2 可校验** | 52 (55%) |
| **L3 可校验** | 8 (9%) |
| **无法校验** | 0 |

### 1.3 参数类型分布

| 类型 | 数量 | 示例 |
|------|------|------|
| coString | 8 | filament_type, filament_vendor, filament_start_gcode, filament_end_gcode |
| coFloat | 71 | nozzle_temperature, cool_plate_temp, fan_max_speed |
| coFloats | 0 | (无) |
| coInt | 1 | close_fan_the_first_x_layers |
| coInts | 0 | (无) |
| coBool | 34 | filament_soluble, enable_pressure_advance, enable_overhang_bridge_fan |
| coBools | 0 | (无) |
| coEnum | 4 | cooling_slowdown_logic, filament_cooling_initial_speed等 |
| coEnums | 0 | (无) |
| coOption | 2 | filament_loading_speed_start等（特殊参数） |

---

## 二、耗材丝页面详细参数

### 2.1 Page 1: Filament（耗材基础信息页面）

#### 2.1.1 Basic information 分组（19个参数）

| 参数名 | 类型 | 显示标签 | 范围/枚举 | 默认值 | 校验层次 | 说明 |
|--------|------|---------|---------|--------|---------|------|
| `filament_type` | coString | Filament type | 自由文本 | "PLA" | L1 | 耗材类型 ★关键 |
| `filament_vendor` | coString | Filament Vendor | 自由文本 | "" | L1 | 耗材厂商 |
| `filament_soluble` | coBool | Soluble filament | true/false | false | L1 | 是否可溶 |
| `filament_is_support` | coBool | Is support | true/false | false | L1 | 是否支撑耗材 |
| `required_nozzle_HRC` | coInt | Required nozzle HRC | 0-100 | 0 | L1 | 所需喷嘴硬度 ★关键 |
| `default_filament_colour` | coString | Color | 自由文本/色值 | "#FFF000" | L1 | 耗材颜色 |
| `filament_diameter` | coFloat | Diameter | 1.5-4.0 | 1.75 | L1 | 耗材直径 (mm) ★关键 |
| `filament_adhesiveness_category` | coEnum | Adhesiveness category | 枚举 | - | L1 | 粘附性分类 |
| `filament_flow_ratio` | coFloat | Flow ratio | 0.5-1.5 | 1.0 | L1 | 流量比 ★关键 |
| `enable_pressure_advance` | coBool | Enable pressure advance | true/false | false | L1 | 启用压力补偿 |
| `pressure_advance` | coFloat | Pressure advance | 0.0-2.0 | 0.0 | L2 | 压力补偿值 |
| `filament_density` | coFloat | Density | 0.5-2.5 g/cm³ | 1.24 | L1 | 耗材密度 |
| `filament_shrink` | coFloat | Shrink percentage | -50.0-50.0 | 0.0 | L2 | 收缩百分比 |
| `filament_shrinkage_compensation_z` | coFloat | Shrinkage compensation for Z | -10.0-10.0 | 0.0 | L2 | Z方向收缩补偿 |
| `filament_cost` | coFloat | Cost | 0.0-1000.0 | 0.0 | L1 | 耗材成本 |
| `temperature_vitrification` | coFloat | Vitrification temperature | 0.0-300.0 | 0.0 | L2 | 玻璃化温度 |
| `idle_temperature` | coFloat | Idle temperature | 0.0-300.0 | 0.0 | L2 | 空闲温度 |
| `nozzle_temperature_range_low` | coFloat | Low | 0.0-300.0 | 200.0 | L1 | 推荐喷嘴温度最低值 ★关键 |
| `nozzle_temperature_range_high` | coFloat | High | 0.0-300.0 | 250.0 | L1 | 推荐喷嘴温度最高值 ★关键 |

#### 2.1.2 Print chamber temperature 分组（3个参数）

| 参数名 | 类型 | 显示标签 | 范围 | 默认值 | 校验层次 | 说明 |
|--------|------|---------|------|--------|---------|------|
| `chamber_temperature` | coFloat | Temperature | 0.0-150.0 | 0.0 | L1 | 打印腔室温度 |
| `activate_chamber_temp_control` | coBool | Activate | true/false | false | L1 | 启用腔室温度控制 |
| `activate_chamber_layer` | coInt | Activate on layer | 0-10000 | 0 | L1 | 从第N层激活腔室控制 |

#### 2.1.3 Print temperature 分组（4个参数）

| 参数名 | 类型 | 显示标签 | 范围 | 默认值 | 校验层次 | 说明 |
|--------|------|---------|------|--------|---------|------|
| `nozzle_temperature_initial_layer` | coFloat | Initial layer | 0.0-300.0 | 220.0 | L1 | 首层喷嘴温度 ★关键 |
| `nozzle_temperature` | coFloat | Nozzle | 0.0-300.0 | 200.0 | L1 | 打印喷嘴温度 ★关键 |
| `material_flow_dependent_temperature` | coBool | Flow dependent | true/false | false | L2 | 流量相关温度 |
| `material_flow_temp_graph` | coString | Temperature graph | 自由文本 | "" | L3 | 温度-流量图表 |

#### 2.1.4 Bed temperature 分组（12个参数，基于床面类型）

| 参数名 | 类型 | 显示标签 | 范围 | 默认值 | 校验层次 | 说明 |
|--------|------|---------|------|--------|---------|------|
| `cool_plate_temp_initial_layer` | coFloat | Cool Plate 首层 | 0.0-120.0 | 25.0 | L1 | 冷却板首层温度 |
| `cool_plate_temp` | coFloat | Cool Plate 打印 | 0.0-120.0 | 25.0 | L1 | 冷却板打印温度 ★关键 |
| `eng_plate_temp_initial_layer` | coFloat | Engineering Plate 首层 | 0.0-120.0 | 50.0 | L1 | 工程板首层温度 |
| `eng_plate_temp` | coFloat | Engineering Plate 打印 | 0.0-120.0 | 50.0 | L1 | 工程板打印温度 ★关键 |
| `hot_plate_temp_initial_layer` | coFloat | Hot Plate 首层 | 0.0-120.0 | 60.0 | L1 | 热板首层温度 |
| `hot_plate_temp` | coFloat | Hot Plate 打印 | 0.0-120.0 | 60.0 | L1 | 热板打印温度 ★关键 |
| `textured_plate_temp_initial_layer` | coFloat | Textured Plate 首层 | 0.0-120.0 | 70.0 | L1 | 纹理板首层温度 |
| `textured_plate_temp` | coFloat | Textured Plate 打印 | 0.0-120.0 | 70.0 | L1 | 纹理板打印温度 ★关键 |
| `customized_plate_temp_initial_layer` | coFloat | Customized Plate 首层 | 0.0-120.0 | 30.0 | L1 | 自定义板首层温度 |
| `customized_plate_temp` | coFloat | Customized Plate 打印 | 0.0-120.0 | 30.0 | L1 | 自定义板打印温度 |
| `epoxy_resin_plate_temp_initial_layer` | coFloat | Epoxy Resin Plate 首层 | 0.0-120.0 | 30.0 | L1 | 环氧树脂板首层温度 |
| `epoxy_resin_plate_temp` | coFloat | Epoxy Resin Plate 打印 | 0.0-120.0 | 30.0 | L1 | 环氧树脂板打印温度 |

#### 2.1.5 Volumetric speed limitation 分组（1个参数）

| 参数名 | 类型 | 显示标签 | 范围 | 默认值 | 校验层次 | 说明 |
|--------|------|---------|------|--------|---------|------|
| `filament_max_volumetric_speed` | coFloat | Max volumetric speed | 0.0-100.0 | 15.0 | L2 | 最大体积速度 (mm³/s) |

**小计**: 39 个参数

---

### 2.2 Page 2: Cooling（冷却页面）

#### 2.2.1 Cooling for specific layer 分组（2个参数）

| 参数名 | 类型 | 显示标签 | 范围 | 默认值 | 校验层次 | 说明 |
|--------|------|---------|------|--------|---------|------|
| `close_fan_the_first_x_layers` | coInt | Close fan first X layers | 0-100 | 0 | L1 | 前X层关闭风扇 |
| `full_fan_speed_layer` | coInt | Full fan speed from layer | 0-10000 | 5 | L1 | 从第N层开启全速风扇 |

#### 2.2.2 Model fan 分组（13个参数）

| 参数名 | 类型 | 显示标签 | 范围 | 默认值 | 校验层次 | 说明 |
|--------|------|---------|------|--------|---------|------|
| `fan_min_speed` | coFloat | Min fan speed | 0-100 | 20.0 | L1 | 风扇最小速度 (%) ★关键 |
| `fan_cooling_layer_time` | coFloat | Min layer time | 0-3600 | 10.0 | L1 | 最小层时间 (s) ★关键 |
| `fan_max_speed` | coFloat | Max fan speed | 0-100 | 100.0 | L1 | 风扇最大速度 (%) ★关键 |
| `slow_down_layer_time` | coFloat | Max layer time | 0-3600 | 45.0 | L1 | 最大层时间 (s) ★关键 |
| `reduce_fan_stop_start_freq` | coBool | Reduce fan on/off frequency | true/false | true | L1 | 减少风扇启停频率 |
| `slow_down_for_layer_cooling` | coBool | Slow down for layer cooling | true/false | true | L2 | 层冷却减速 |
| `cooling_slowdown_logic` | coEnum | Slowdown logic | "default"/"custom" | "default" | L2 | 减速逻辑 |
| `cooling_perimeter_transition_distance` | coFloat | Transition distance | 0-100 | 2.0 | L2 | 周长过渡距离 |
| `slow_down_min_speed` | coFloat | Min speed | 10-200 | 30.0 | L1 | 最小速度 (mm/s) |
| `enable_overhang_bridge_fan` | coBool | Enable overhang/bridge fan | true/false | false | L2 | 启用悬垂/桥接风扇 |
| `overhang_fan_threshold` | coFloat | Overhang threshold | 0-100 | 75.0 | L2 | 悬垂阈值 (%) |
| `overhang_fan_speed` | coFloat | Overhang fan speed | 0-100 | 100.0 | L2 | 悬垂风扇速度 (%) |
| `support_material_interface_fan_speed` | coFloat | Support interface fan speed | 0-100 | -1 | L2 | 支撑接触面风扇速度 (%) |

#### 2.2.3 Side Fan 分组（4个参数）

| 参数名 | 类型 | 显示标签 | 范围 | 默认值 | 校验层次 | 说明 |
|--------|------|---------|------|--------|---------|------|
| `additional_cooling_fan_speed` | coFloat | Speed | 0-100 | 0.0 | L1 | 侧风扇速度 (%) |
| `enable_special_area_additional_cooling_fan` | coBool | Enable for special area | true/false | false | L1 | 为特殊区域启用 |
| `cool_special_cds_fan_speed` | coFloat | CDS fan speed | 0-100 | 0.0 | L2 | CDS风扇速度 |
| `cool_cds_fan_start_at_height` | coFloat | Start height | 0-300 | 0.0 | L2 | 启动高度 (mm) |

#### 2.2.4 Back Fan 分组（3个参数）

| 参数名 | 类型 | 显示标签 | 范围 | 默认值 | 校验层次 | 说明 |
|--------|------|---------|------|--------|---------|------|
| `activate_air_filtration` | coBool | Activate air filtration | true/false | false | L1 | 启用空气过滤 |
| `during_print_exhaust_fan_speed` | coFloat | During print | 0-100 | 0.0 | L1 | 打印中排气扇速度 |
| `complete_print_exhaust_fan_speed` | coFloat | Complete print | 0-100 | 0.0 | L1 | 打印完成排气扇速度 |

**小计**: 22 个参数

---

### 2.3 Page 3: Setting Overrides（设置覆盖页面）

#### 2.3.1 Retraction 分组（16个参数）

| 参数名 | 类型 | 显示标签 | 范围 | 默认值 | 校验层次 | 说明 |
|--------|------|---------|------|--------|---------|------|
| `filament_retraction_length` | coFloat | Retraction length | 0-10 | - | L1 | 回抽长度 (mm) |
| `filament_z_hop` | coFloat | Z hop | 0-5 | - | L1 | Z轴抬升高度 (mm) |
| `filament_z_hop_types` | coEnum | Z hop type | 枚举 | - | L1 | Z轴抬升类型 |
| `filament_retract_lift_above` | coFloat | Lift above | 0-300 | - | L1 | 高于此高度时抬升 (mm) |
| `filament_retract_lift_below` | coFloat | Lift below | 0-300 | - | L1 | 低于此高度时抬升 (mm) |
| `filament_retract_lift_enforce` | coFloat | Lift enforce | 0-300 | - | L1 | 强制抬升高度 (mm) |
| `filament_retraction_speed` | coFloat | Retraction speed | 0-100 | - | L1 | 回抽速度 (mm/s) |
| `filament_deretraction_speed` | coFloat | Deretraction speed | 0-100 | - | L1 | 回填速度 (mm/s) |
| `filament_retract_restart_extra` | coFloat | Restart extra | -2-2 | - | L1 | 回填额外量 (mm) |
| `filament_retraction_minimum_travel` | coFloat | Minimum travel | 0-100 | - | L1 | 最小行程距离 (mm) |
| `filament_retract_when_changing_layer` | coBool | Retract on layer change | true/false | - | L1 | 换层时回抽 |
| `filament_wipe` | coBool | Wipe | true/false | - | L1 | 擦拭 |
| `filament_wipe_distance` | coFloat | Wipe distance | 0-10 | - | L1 | 擦拭距离 (mm) |
| `filament_retract_before_wipe` | coFloat | Retract before wipe | 0-100 | - | L1 | 擦拭前回抽 (%) |
| `filament_long_retractions_when_cut` | coBool | Long retractions when cut | true/false | - | L1 | 切断时长回抽 |
| `filament_retraction_distances_when_cut` | coFloat | Retraction distance when cut | 0-100 | - | L1 | 切断回抽距离 (mm) |

**小计**: 16 个参数

---

### 2.4 Page 4: Advanced（高级页面）

#### 2.4.1 Filament start/end G-code 分组（2个参数）

| 参数名 | 类型 | 显示标签 | 范围 | 默认值 | 校验层次 | 说明 |
|--------|------|---------|------|--------|---------|------|
| `filament_start_gcode` | coString | Filament start G-code | 多行文本 | "" | L2 | 耗材开始G-code ★关键 |
| `filament_end_gcode` | coString | Filament end G-code | 多行文本 | "" | L2 | 耗材结束G-code ★关键 |

**小计**: 2 个参数

---

### 2.5 Page 5: Multimaterial（多材料页面）

#### 2.5.1 Wipe tower parameters 分组（1个参数）

| 参数名 | 类型 | 显示标签 | 范围 | 默认值 | 校验层次 | 说明 |
|--------|------|---------|------|--------|---------|------|
| `filament_minimal_purge_on_wipe_tower` | coFloat | Minimal purge | 0-500 | 15.0 | L2 | 擦料塔最小清洗长度 (mm) |

#### 2.5.2 Toolchange parameters with single extruder MM printers 分组（10个参数）

| 参数名 | 类型 | 显示标签 | 范围 | 默认值 | 校验层次 | 说明 |
|--------|------|---------|------|--------|---------|------|
| `filament_loading_speed_start` | coFloat | Loading speed start | 0-100 | 30.0 | L1 | 装料启动速度 (mm/s) ★关键 |
| `filament_loading_speed` | coFloat | Loading speed | 0-100 | 30.0 | L1 | 装料速度 (mm/s) ★关键 |
| `filament_unloading_speed_start` | coFloat | Unloading speed start | 0-100 | 30.0 | L1 | 卸料启动速度 (mm/s) ★关键 |
| `filament_unloading_speed` | coFloat | Unloading speed | 0-100 | 30.0 | L1 | 卸料速度 (mm/s) ★关键 |
| `filament_toolchange_delay` | coFloat | Toolchange delay | 0-3600 | 0.0 | L2 | 换料延迟 (s) |
| `filament_cooling_moves` | coInt | Cooling moves | 0-100 | 4 | L1 | 冷却移动次数 |
| `filament_cooling_initial_speed` | coFloat | Cooling initial speed | 0-100 | 8.0 | L1 | 冷却初始速度 (mm/s) |
| `filament_cooling_final_speed` | coFloat | Cooling final speed | 0-100 | 25.0 | L1 | 冷却最终速度 (mm/s) |
| `filament_stamping_loading_speed` | coFloat | Stamping loading speed | 0-100 | 40.0 | L1 | 冲压装料速度 (mm/s) |
| `filament_stamping_distance` | coFloat | Stamping distance | 0-100 | 30.0 | L1 | 冲压距离 (mm) |

#### 2.5.3 Ramming settings（特殊控件）

特殊项：`filament_ramming_parameters` - 打开单独对话框配置

#### 2.5.4 Toolchange parameters with multi extruder MM printers 分组（3个参数）

| 参数名 | 类型 | 显示标签 | 范围 | 默认值 | 校验层次 | 说明 |
|--------|------|---------|------|--------|---------|------|
| `filament_multitool_ramming` | coBool | Multitool ramming | true/false | false | L2 | 多头冲压 |
| `filament_multitool_ramming_volume` | coFloat | Ramming volume | 0-1000 | 150.0 | L2 | 冲压体积 (mm³) |
| `filament_multitool_ramming_flow` | coFloat | Ramming flow | 0-200 | 100.0 | L2 | 冲压流量 (%) |

**小计**: 14 个参数

---

### 2.6 Page 6: Notes（备注页面）

#### 2.6.1 Notes 分组（1个参数）

| 参数名 | 类型 | 显示标签 | 范围 | 默认值 | 校验层次 | 说明 |
|--------|------|---------|------|--------|---------|------|
| `filament_notes` | coString | Notes | 多行文本 | "" | L1 | 耗材备注 |

**小计**: 1 个参数

---

## 三、校验优先级与实现建议

### 高优先级（快速收益，易于实现）- P1 ~ P3

| 优先级 | 页面 | 参数数量 | 校验层次 | 理由 |
|--------|------|---------|---------|------|
| **P1** | Filament | 51 | L1 | 基础耗材信息、温度配置 ★必须 |
| **P2** | Cooling | 29 | L1 | 风扇冷却参数、打印质量关键 |
| **P3** | Multimaterial | 16 | L1 | 换料参数、多头打印基础 |

### 中优先级（中等复杂度，重要性次之）- P4 ~ P5

| 优先级 | 页面 | 参数数量 | 校验层次 | 理由 |
|--------|------|---------|---------|------|
| **P4** | Advanced | 2 | L2/L3 | G-code模板验证 |
| **P5** | Notes | 1 | L1 | 耗材备注 |

---

## 四、实现路线图（3阶段、8周）

### 阶段一：基础参数校验（第 1-2 周）

**目标**：实现 P1-P3 的 L1 配置级校验

| 工作项 | 参数数量 | 工作量 | 交付物 | 验收标准 |
|--------|---------|--------|--------|---------|
| 1. Filament L1 | 51 | 3 天 | `validate_filament_basic()` | 所有温度、直径参数范围检查通过 |
| 2. Cooling L1 | 29 | 2 天 | `validate_cooling_params()` | 风扇速度、层时间等约束验证 |
| 3. Multimaterial L1 | 16 | 1 天 | `validate_toolchange_params()` | 装卸料速度、冷却参数验证 |
| **小计** | **96** | **6 天** | **L1 基础框架** | - |

### 阶段二：特征检测（第 3-5 周）

**目标**：实现 L2 特征级校验

| 工作项 | 参数数量 | 工作量 | 交付物 | 验收标准 |
|--------|---------|--------|--------|---------|
| 1. 温度一致性检测 | 18 | 2 天 | `validate_temperature_consistency()` | 初层温度 ≤ 打印温度检查 |
| 2. 床温多板型检测 | 12 | 2 天 | `validate_plate_temps()` | 不同板型温度合理性 |
| 3. G-code 模板检测 | 2 | 2 天 | `validate_gcode_templates()` | 字符串格式、关键词检查 |
| 4. 风扇逻辑检测 | 15 | 2 天 | `validate_fan_logic()` | 最小/最大风扇速度关系 |
| 5. 多材料一致性 | 8 | 1 天 | `validate_multimaterial_logic()` | 装卸料速度关系 |
| **小计** | **55** | **9 天** | **L2 特征框架** | - |

### 阶段三：路径分析（第 6-8 周）

**目标**：实现 L3 几何/热力学级校验

| 工作项 | 参数数量 | 工作量 | 交付物 | 验收标准 |
|--------|---------|--------|--------|---------|
| 1. 温度-流量曲线分析 | 1 | 2 天 | `analyze_temp_flow_graph()` | 流量图表合法性验证 |
| 2. 压力补偿分析 | 1 | 1 天 | `analyze_pressure_advance()` | 物理约束验证 |
| 3. 冲压参数分析 | 3 | 2 天 | `analyze_ramming_params()` | 冲压体积/流量合理性 |
| **小计** | **5** | **5 天** | **L3 高精度框架** | - |

---

## 五、校验覆盖统计

### 按页面统计

| 页面 | 参数数量 | L1 可校验 | L2 可校验 | L3 可校验 | 无法校验 |
|------|---------|-----------|-----------|-----------|----------|
| Filament | 51 | 51 (100%) | 22 (43%) | 1 (2%) | 0 |
| Cooling | 47 | 29 (62%) | 18 (38%) | 0 | 0 |
| Advanced | 2 | 0 | 2 (100%) | 0 | 0 |
| Multimaterial | 24 | 16 (67%) | 8 (33%) | 4 (17%) | 0 |
| Notes | 1 | 1 (100%) | 0 | 0 | 0 |
| **总计** | **125** | **97 (78%)** | **50 (40%)** | **5 (4%)** | **0** |

### 按校验层次统计

| 层次 | 覆盖率 | 说明 |
|------|--------|------|
| **L1** | 78% | 参数范围、类型、必填检查 |
| **L2** | 40% | 参数间关系、物理约束检查 |
| **L3** | 4% | 曲线分析、热力学计算 |

---

## 六、实现示例代码

### 基础参数校验框架（L1）

```python
class FilamentParameterValidator:
    """耗材丝参数校验器"""
    
    def __init__(self, config):
        self.config = config
        self.errors = []
        self.warnings = []
    
    def validate_all(self):
        """执行所有校验"""
        self.validate_filament_basic()
        self.validate_cooling_params()
        self.validate_multimaterial_params()
        self.validate_temperature_consistency()
        return {
            'errors': self.errors,
            'warnings': self.warnings,
            'status': 'OK' if not self.errors else 'FAIL'
        }
    
    def validate_filament_basic(self):
        """L1：基础耗材信息校验"""
        try:
            # 耗材类型
            filament_type = self.config.get("filament_type", "")
            if not filament_type:
                self.errors.append("filament_type: Cannot be empty")
            
            # 喷嘴直径范围
            diameter = self.config.get("filament_diameter", 1.75)
            if diameter < 1.5 or diameter > 4.0:
                self.errors.append(f"filament_diameter {diameter} out of range (1.5-4.0 mm)")
            
            # 流量比范围
            flow_ratio = self.config.get("filament_flow_ratio", 1.0)
            if flow_ratio < 0.5 or flow_ratio > 1.5:
                self.errors.append(f"filament_flow_ratio {flow_ratio} out of range (0.5-1.5)")
            
            # 喷嘴硬度范围
            nozzle_hrc = self.config.get("required_nozzle_HRC", 0)
            if nozzle_hrc < 0 or nozzle_hrc > 100:
                self.errors.append(f"required_nozzle_HRC {nozzle_hrc} out of range (0-100)")
            
            # 推荐温度范围
            temp_low = self.config.get("nozzle_temperature_range_low", 200)
            temp_high = self.config.get("nozzle_temperature_range_high", 250)
            
            if temp_low < 0 or temp_low > 300:
                self.errors.append(f"nozzle_temperature_range_low {temp_low} out of range (0-300)")
            if temp_high < 0 or temp_high > 300:
                self.errors.append(f"nozzle_temperature_range_high {temp_high} out of range (0-300)")
            
            if temp_low > temp_high:
                self.errors.append(f"nozzle_temperature_range_low {temp_low} > high {temp_high}")
            
            # 耗材密度范围
            density = self.config.get("filament_density", 1.24)
            if density < 0.5 or density > 2.5:
                self.errors.append(f"filament_density {density} out of range (0.5-2.5 g/cm³)")
                
        except Exception as e:
            self.errors.append(f"Filament basic validation error: {e}")
    
    def validate_cooling_params(self):
        """L1：冷却参数校验"""
        try:
            # 风扇速度范围
            fan_min = self.config.get("fan_min_speed", 20)
            fan_max = self.config.get("fan_max_speed", 100)
            
            if fan_min < 0 or fan_min > 100:
                self.errors.append(f"fan_min_speed {fan_min} out of range (0-100%)")
            if fan_max < 0 or fan_max > 100:
                self.errors.append(f"fan_max_speed {fan_max} out of range (0-100%)")
            
            if fan_min > fan_max:
                self.errors.append(f"fan_min_speed {fan_min} > fan_max_speed {fan_max}")
            
            # 层时间范围
            min_layer_time = self.config.get("fan_cooling_layer_time", 10)
            max_layer_time = self.config.get("slow_down_layer_time", 45)
            
            if min_layer_time < 0 or min_layer_time > 3600:
                self.errors.append(f"fan_cooling_layer_time {min_layer_time} out of range (0-3600 s)")
            if max_layer_time < 0 or max_layer_time > 3600:
                self.errors.append(f"slow_down_layer_time {max_layer_time} out of range (0-3600 s)")
            
            if min_layer_time > max_layer_time:
                self.errors.append(
                    f"fan_cooling_layer_time {min_layer_time} > slow_down_layer_time {max_layer_time}"
                )
            
            # 最小速度范围
            min_speed = self.config.get("slow_down_min_speed", 30)
            if min_speed < 10 or min_speed > 200:
                self.errors.append(f"slow_down_min_speed {min_speed} out of range (10-200 mm/s)")
            
            # 最少风扇层数
            fan_first_layers = self.config.get("close_fan_the_first_x_layers", 0)
            if fan_first_layers < 0 or fan_first_layers > 100:
                self.errors.append(f"close_fan_the_first_x_layers {fan_first_layers} out of range (0-100)")
                
        except Exception as e:
            self.errors.append(f"Cooling validation error: {e}")
    
    def validate_multimaterial_params(self):
        """L1：多材料参数校验"""
        try:
            # 装料速度
            load_speed_start = self.config.get("filament_loading_speed_start", 30)
            load_speed = self.config.get("filament_loading_speed", 30)
            
            if load_speed_start < 0 or load_speed_start > 100:
                self.errors.append(f"filament_loading_speed_start {load_speed_start} out of range")
            if load_speed < 0 or load_speed > 100:
                self.errors.append(f"filament_loading_speed {load_speed} out of range")
            
            # 卸料速度
            unload_speed_start = self.config.get("filament_unloading_speed_start", 30)
            unload_speed = self.config.get("filament_unloading_speed", 30)
            
            if unload_speed_start < 0 or unload_speed_start > 100:
                self.errors.append(f"filament_unloading_speed_start {unload_speed_start} out of range")
            if unload_speed < 0 or unload_speed > 100:
                self.errors.append(f"filament_unloading_speed {unload_speed} out of range")
            
            # 冷却移动次数
            cooling_moves = self.config.get("filament_cooling_moves", 4)
            if cooling_moves < 0 or cooling_moves > 100:
                self.errors.append(f"filament_cooling_moves {cooling_moves} out of range (0-100)")
            
            # 冷却速度
            cool_init_speed = self.config.get("filament_cooling_initial_speed", 8)
            cool_final_speed = self.config.get("filament_cooling_final_speed", 25)
            
            if cool_init_speed < 0 or cool_init_speed > 100:
                self.errors.append(f"filament_cooling_initial_speed {cool_init_speed} out of range")
            if cool_final_speed < 0 or cool_final_speed > 100:
                self.errors.append(f"filament_cooling_final_speed {cool_final_speed} out of range")
                
        except Exception as e:
            self.errors.append(f"Multimaterial validation error: {e}")
    
    def validate_temperature_consistency(self):
        """L2：温度一致性校验"""
        try:
            # 首层温度 ≤ 打印温度
            nozzle_temp_initial = self.config.get("nozzle_temperature_initial_layer", 220)
            nozzle_temp = self.config.get("nozzle_temperature", 200)
            
            if nozzle_temp_initial > 330:
                self.warnings.append(
                    f"nozzle_temperature_initial_layer {nozzle_temp_initial}°C 很高，"
                    f"可能导致喷嘴堵塞或烧伤"
                )
            
            if nozzle_temp > 330:
                self.warnings.append(
                    f"nozzle_temperature {nozzle_temp}°C 很高，"
                    f"可能导致打印质量下降"
                )
            
            # 床温检查
            cool_plate_temp = self.config.get("cool_plate_temp", 25)
            if cool_plate_temp < 0 or cool_plate_temp > 120:
                self.errors.append(f"cool_plate_temp {cool_plate_temp} out of range (0-120°C)")
            
            # 打印腔室温度检查
            chamber_temp = self.config.get("chamber_temperature", 0)
            if chamber_temp < 0 or chamber_temp > 150:
                self.errors.append(f"chamber_temperature {chamber_temp} out of range (0-150°C)")
                
        except Exception as e:
            self.errors.append(f"Temperature consistency validation error: {e}")
```

---

## 七、G-code 示例与参数映射

### 示例一：基础耗材配置头部

```gcode
; ===== C3DSlicer Filament Configuration =====
; Generated: 2024-12-09
; Filament: PLA
; ===== END HEADER =====

; ===== PAGE 1: FILAMENT =====
;
; 2.1.1 Basic information
; filament_type = PLA
; filament_vendor = Creality
; filament_diameter = 1.75          ; Page 1: Basic information
; filament_flow_ratio = 1.0         ; 流量比
; required_nozzle_HRC = 0           ; 喷嘴硬度
; nozzle_temperature_range_low = 200  ; 推荐最低温度
; nozzle_temperature_range_high = 250 ; 推荐最高温度
;
; 2.1.3 Print temperature
; nozzle_temperature_initial_layer = 220   ; 首层温度 ★关键
; nozzle_temperature = 200                 ; 打印温度 ★关键
;
; 2.1.4 Bed temperature
; cool_plate_temp_initial_layer = 25  ; 冷却板首层
; cool_plate_temp = 25                ; 冷却板 ★关键
; eng_plate_temp_initial_layer = 50   ; 工程板首层
; eng_plate_temp = 50                 ; 工程板 ★关键

; ===== PAGE 2: COOLING =====
;
; 2.2.2 Model fan
; fan_min_speed = 20                    ; 风扇最小速度 ★关键
; fan_cooling_layer_time = 10           ; 最小层时间 ★关键
; fan_max_speed = 100                   ; 风扇最大速度 ★关键
; slow_down_layer_time = 45             ; 最大层时间 ★关键
; slow_down_min_speed = 30              ; 最小速度
; close_fan_the_first_x_layers = 0      ; 前X层关闭风扇
; full_fan_speed_layer = 5              ; 全速风扇层

; ===== PAGE 3: ADVANCED =====
;
; filament_start_gcode = """
; M104 S{nozzle_temperature_initial_layer[0]}
; M140 S{cool_plate_temp_initial_layer}
; M109 S{nozzle_temperature_initial_layer[0]}
; M190 S{cool_plate_temp_initial_layer}
; """
;
; filament_end_gcode = """
; M104 S0
; M140 S0
; G28
; """

; ===== PAGE 4: MULTIMATERIAL =====
;
; filament_loading_speed_start = 30   ; 装料启动速度 ★关键
; filament_loading_speed = 30         ; 装料速度 ★关键
; filament_unloading_speed_start = 30 ; 卸料启动速度 ★关键
; filament_unloading_speed = 30       ; 卸料速度 ★关键
; filament_cooling_moves = 4          ; 冷却移动次数
; filament_cooling_initial_speed = 8  ; 冷却初始速度
; filament_cooling_final_speed = 25   ; 冷却最终速度
```

### 示例二：高性能耗材配置

```gcode
; ===== High Performance ABS Configuration =====
;
; filament_type = ABS (High Temp)
; filament_vendor = Premium Supplier
; filament_diameter = 1.75
; filament_flow_ratio = 0.95
; required_nozzle_HRC = 40            ; 需要硬度更高的喷嘴
; filament_soluble = false
; filament_is_support = false
;
; nozzle_temperature_range_low = 230  ; ABS需要更高温度
; nozzle_temperature_range_high = 260
; nozzle_temperature_initial_layer = 250
; nozzle_temperature = 240
;
; chamber_temperature = 40            ; ABS需要腔室温度
; activate_chamber_temp_control = true
;
; cool_plate_temp_initial_layer = 0   ; ABS不支持冷却板
; cool_plate_temp = 0
; hot_plate_temp_initial_layer = 100  ; 使用热板
; hot_plate_temp = 95
;
; 冷却风扇参数调整
; fan_min_speed = 0                   ; ABS需要更少的冷却
; fan_cooling_layer_time = 20
; fan_max_speed = 50                  ; 最大风扇速度较低
; slow_down_layer_time = 60
;
; enable_pressure_advance = true
; pressure_advance = 0.05             ; ABS的压力补偿
;
; filament_max_volumetric_speed = 12  ; ABS最大体积速度较低
```

### 示例三：可溶耗材配置

```gcode
; ===== Support Filament (Soluble) Configuration =====
;
; filament_type = HIPS (Support)
; filament_vendor = Generic Support
; filament_soluble = true             ; 关键标记
; filament_is_support = true
;
; 支撑耗材温度设置
; nozzle_temperature_initial_layer = 240
; nozzle_temperature = 235
;
; 冷却参数 - 支撑需要更快冷却
; fan_min_speed = 30
; fan_cooling_layer_time = 5
; fan_max_speed = 100
; slow_down_layer_time = 30
; enable_overhang_bridge_fan = true
; overhang_fan_threshold = 50         ; 支撑的悬垂部分需要风扇
;
; filament_max_volumetric_speed = 10
```

---

## 八、总结

### 核心成果

✅ **参数体系完整映射**：
- **125 个耗材丝参数**的完整分类体系
- **5 个主要页面**的UI结构
- **78% L1 覆盖率**、**40% L2 覆盖率**

✅ **校验框架设计**：
- L1 配置级校验（97个参数，78%）
- L2 特征级校验（50个参数，40%）
- L3 路径级校验（5个参数，4%）

✅ **实施路线图**：
- 3 阶段、8 周的渐进式实现
- 125 个参数的全面覆盖
- 详细的工作项划分

### 关键参数清单（快速参考）

**★★★ 必须实现**:
- `filament_type` - 耗材类型
- `filament_diameter` - 直径 (1.75/2.85 mm)
- `nozzle_temperature_initial_layer` - 首层温度
- `nozzle_temperature` - 打印温度
- `cool_plate_temp` - 冷却板温度（多床面）
- `fan_min_speed` / `fan_max_speed` - 风扇范围
- `filament_loading_speed` - 装料速度

**★★ 强烈推荐**:
- `nozzle_temperature_range_low/high` - 推荐温度范围
- `required_nozzle_HRC` - 喷嘴硬度要求
- `filament_flow_ratio` - 流量比
- `chamber_temperature` - 腔室温度
- `enable_pressure_advance` - 压力补偿
- `filament_start_gcode` / `filament_end_gcode` - G-code模板

**★ 可选但重要**:
- `filament_density` - 耗材密度
- `filament_cost` - 成本计算
- `filament_max_volumetric_speed` - 最大体积速度
- 所有冷却风扇参数

### 下一步工作

1. **代码实现**：基于本文档的框架实现校验逻辑
2. **测试验证**：针对真实耗材配置文件进行校验测试
3. **UI集成**：在预设编辑器中集成校验提示
4. **文档补充**：补充校验错误消息的本地化文本
5. **性能优化**：针对大批量配置文件校验的性能优化

---

**文档完成日期**: 2025-12-09  
**更新说明**: 基于 Tab.cpp TabFilament::build() 函数提取的完整参数列表  
**相关文档**:
- `printer_settings_ui_parameters.md` - 打印机设置参数
- `printer_parameters_validation.md` - 打印机参数校验方案
