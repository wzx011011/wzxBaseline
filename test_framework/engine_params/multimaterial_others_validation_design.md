# 多材料与其他参数 G-code 校验方案

## 一、参数分类与校验策略总览

### 多材料 (Multimaterial) - 共 34 个参数

| 子分类 | 参数数量 | 校验难度 | 校验方式 | 校验层次 |
|--------|---------|---------|----------|----------|
| 擦料塔 (Prime tower) | 15 | 简单-中等 | 配置读取 + G-code 特征检测 | L1/L2/L3 |
| 特征耗材 (Filament for Features) | 4 | 简单 | 配置注释 + 换料命令 | L1/L2 |
| 渗料预防 (Ooze prevention) | 4 | 中等 | 温度命令分析 | L1/L2 |
| 冲刷选项 (Flush options) | 3 | 简单-中等 | 配置读取 + 特征检测 | L1/L2 |
| 高级 (Advanced) | 8 | 困难 | 路径分析 | L3 |

### 其他 (Others) - 共 32 个参数

| 子分类 | 参数数量 | 校验难度 | 校验方式 | 校验层次 |
|--------|---------|---------|---------|----------|
| 裙边 (Skirt) | 7 | 简单-中等 | G-code 首层分析 | L1/L2/L3 |
| 边缘 (Brim) | 5 | 简单 | G-code 首层分析 | L1/L2/L3 |
| 特殊模式 (Special mode) | 12 | 中等-困难 | 多种方式 | L1/L2/L3 |
| G代码输出 (G-code output) | 6 | 简单-中等 | G-code 格式检测 | L1/L2 |
| 后处理脚本 | 1 | 特殊 | 无法通过 G-code 校验 | N/A |
| 备注 | 1 | 特殊 | 注释检测 | L1 |

### 校验层次说明

| 层次 | 名称 | 适用场景 | 复杂度 | 可靠性 |
|------|------|---------|--------|--------|
| Level 1 (L1) | 配置对比 | 简单值校验，直接从 G-code 配置注释读取 | 简单 | 快速预检 |
| Level 2 (L2) | 特征检测 | 开关型参数，检测 TYPE 标记是否存在 | 中等 | 效果验证 |
| Level 3 (L3) | 路径分析/基线对比 | 几何验证，需要分析实际打印路径 | 复杂 | 精确验证 |

### 校验覆盖统计

| 分类 | 参数数量 | L1 可校验 | L2 可校验 | L3 可校验 | 无法校验 |
|------|---------|-----------|-----------|-----------|----------|
| 多材料 | 34 | 28 | 4 | 2 | 0 |
| 其他 | 32 | 24 | 5 | 2 | 1 |
| **总计** | **66** | **52** | **9** | **4** | **1** |

---

## 二、详细校验逻辑设计

### 2.1 擦料塔 (Prime Tower) 参数

> **参考资料**: [Bambu Lab Wiki - 擦料塔介绍](https://wiki.bambulab.com/zh/software/bambu-studio/parameter/prime-tower)

擦料塔用于多色打印或平滑模式延时摄影时清理喷嘴残留料，使喷嘴内部腔压达到稳定状态。

| 参数名 | 类型 | 默认值 | 校验层次 | 校验方法 | 参数说明 |
|--------|------|--------|---------|----------|----------|
| `enable_prime_tower` | bool | false | Level 2 | 检测 `;TYPE:Prime tower` 或 `WIPE_TOWER_START` 标记 | 启用/禁用擦料塔 |
| `prime_tower_width` | float | 60mm | Level 1 / Level 3 | 配置读取 / 边界框宽度计算 | 料塔宽度，所有层采用统一宽度 |
| `prime_volume` | float | 45mm³ | Level 1 | 配置读取: `cfg.get("prime_volume")` | 每次换料在料塔上打印的体积（清理量） |
| `prime_tower_brim_width` | float | 3mm | Level 1 | 配置读取: `cfg.get("prime_tower_brim_width")` | 料塔底部 Brim 宽度，增加稳固性 |
| `wipe_tower_rotation_angle` | float | 0° | Level 1 | 配置读取: `cfg.get("wipe_tower_rotation_angle")` | 料塔旋转角度 |
| `wipe_tower_bridging` | float | 10 | Level 1 | 配置读取: `cfg.get("wipe_tower_bridging")` | 桥接层间距 |
| `prime_tower_enhance_type` | enum | chamfer | Level 3 | 底部边界框趋势分析 | 底部增强类型：cone（锥形）/chamfer（倒角） |
| `wipe_tower_cone_angle` | float | 0° | Level 1 | 配置读取: `cfg.get("wipe_tower_cone_angle")` | 锥形角度 |
| `wipe_tower_extra_spacing` | percent | 150% | Level 1 | 配置读取: `cfg.get("wipe_tower_extra_spacing")` | 走线填充间隙（150%=1.5倍线宽间距） |
| `wipe_tower_extra_flow` | percent | 100% | Level 1 | 配置读取: `cfg.get("wipe_tower_extra_flow")` | 额外流量百分比 |
| `wipe_tower_max_purge_speed` | float | 90 | Level 1 | 配置读取: `cfg.get("wipe_tower_max_purge_speed")` | 料塔填充最大打印速度 (mm/s) |
| `wipe_tower_no_sparse_layers` | bool | false | Level 1 | 配置读取: `cfg.get("wipe_tower_no_sparse_layers")` | 禁用稀疏层 |
| `prime_tower_position_type` | enum | - | Level 1 | 配置读取: `cfg.get("prime_tower_position_type")` | 位置类型 |
| `wipe_tower_x` | float | 130 | Level 1 / Level 3 | 配置读取 / 边界框中心计算 | 料塔 X 坐标 |
| `wipe_tower_y` | float | 265 | Level 1 / Level 3 | 配置读取 / 边界框中心计算 | 料塔 Y 坐标 |

**校验层次说明：**

| 层次 | 名称 | 适用场景 | 复杂度 |
|------|------|---------|--------|
| Level 1 | 配置对比 | 简单值校验，直接从 G-code 配置注释读取 | 简单 |
| Level 2 | 特征检测 | 开关型参数，检测 TYPE 标记是否存在 | 中等 |
| Level 3 | 路径分析/基线对比 | 几何验证，需要分析实际打印路径或对比基线 G-code | 复杂 |

**擦料塔几何计算公式（来自 Wiki）：**

```
折返次数 = 每次换料打印长度 / 料塔宽度
每次换料深度 = 折返次数 × 走线线宽
单层总深度 = (折返次数 × 线宽) × 该层换料次数
```

**校验逻辑：**

```python
# Level 1: 配置对比（推荐，简单快速）
parser = GCodeParser(gcode_path)
cfg = parser.load_config()
actual_value = cfg.get("prime_tower_width")  # 直接读取配置值
prime_volume = cfg.get("prime_volume")  # 清理量可直接读取

# Level 2: 特征检测（开关型参数）
# 检测 ";TYPE:Prime tower" 或 "; WIPE_TOWER_START" 标记
prime_tower_blocks = parser.get_extrusion_blocks_per_layer(ExtrusionType.PRIME_TOWER.value)
tower_present = any(blocks for blocks in prime_tower_blocks if blocks)

# Level 3: 路径分析（几何验证，可选升级）
# 
# prime_tower_width 边界框验证:
#   验证思路：计算 Prime Tower 区域的实际宽度
#   1. 提取 Prime Tower 区域的所有 G1 命令坐标
#   2. 计算边界框：width = max_x - min_x
#   3. 验证实际宽度与参数值的偏差在容差范围内（如 ±2mm）
#
# wipe_tower_x / wipe_tower_y 位置验证:
#   验证思路：验证 Prime Tower 中心位置
#   1. 计算 Prime Tower 边界框的中心点
#   2. 中心 X = (min_x + max_x) / 2
#   3. 中心 Y = (min_y + max_y) / 2
#   4. 验证中心位置与参数值的偏差在容差范围内（如 ±5mm）

# Level 3: 边界框趋势分析（用于验证 prime_tower_enhance_type）
# 验证思路：比较底部几层 Prime Tower 区域的边界框变化趋势
# - cone（锥形）特征：底部几层的边界框逐层缩小，呈现收缩趋势
# - chamfer（倒角）特征：底部几层的边界框基本一致，只在边角有轻微变化
# 具体步骤：
# 1. 提取底部 5-10 层的 Prime Tower 路径
# 2. 计算每层的边界框面积
# 3. 分析面积变化趋势：锥形时面积递减明显，倒角时面积基本稳定
```

---

### 2.2 特征耗材 (Filament for Features)

| 参数名 | 类型 | 校验方法 |
|--------|------|---------|
| `wall_filament` | int | 检测外墙前的 T<n> 换料命令 |
| `sparse_infill_filament` | int | 检测填充前的 T<n> 换料命令 |
| `solid_infill_filament` | int | 检测实心填充前的 T<n> 换料命令 |
| `wipe_tower_filament` | int | 检测擦料塔使用的挤出机 |

**校验逻辑：**

```
1. 解析 ;TYPE: 注释确定当前打印类型
2. 记录每种类型前最近的 T<n> 命令
3. 验证 T<n> 中的 n 与参数值匹配
```

---

### 2.3 渗料预防 (Ooze prevention)

| 参数名 | 类型 | 校验方法 |
|--------|------|---------|
| `ooze_prevention` | bool | 检测是否有待机温度变化 |
| `standby_temperature_delta` | int | 计算待机与工作温度差值 |
| `preheat_time` | float | 分析预热命令时序 |
| `preheat_steps` | int | 统计预热温度阶梯数 |

**校验逻辑：**

```
1. 提取所有 M104/M109 温度命令
2. 分析换料前后温度变化模式
3. standby_temp = work_temp - standby_temperature_delta
4. 验证预热序列符合 preheat_steps
```

---

### 2.4 冲刷选项 (Flush options)

> **参考资料**: [Bambu Lab Wiki - 减少多色打印时的材料浪费](https://wiki.bambulab.com/zh/software/bambu-studio/reduce-wasting-during-filament-change)

冲刷选项用于将换料时的冲刷耗材利用起来，减少浪费。冲刷功能**必须启用擦料塔才能生效**。

| 参数名 | 类型 | 默认值 | 校验层次 | 校验方法 | 参数说明 |
|--------|------|--------|---------|----------|----------|
| `flush_into_infill` | bool | false | Level 2 | 检测换料后首个挤出是否在填充区域 | 冲刷到对象的填充，将冲刷耗材用于打印填充部分 |
| `flush_into_support` | bool | **true** | Level 1 | 配置读取: `cfg.get("flush_into_support")` | 冲刷到对象的支撑（**默认启用**），将冲刷耗材用于支撑区域 |
| `flush_into_objects` | bool | false | Level 1 | 配置读取: `cfg.get("flush_into_objects")` | 冲刷到指定模型，需要同时打印多个模型才可用 |

**参数特性说明（来自 Wiki）：**

| 参数 | 优点 | 缺点/注意事项 |
|------|------|--------------|
| `flush_into_infill` | 减少擦料塔耗材浪费 | 浅色/透明材料可能透色，外壁层数少时更明显 |
| `flush_into_support` | 无明显副作用，默认启用 | 支撑面积通常不足以显著降低浪费 |
| `flush_into_objects` | 可大幅减少浪费（如 70g→1g） | 仅多模型可用，指定模型会有渐变/杂色效果 |

**校验逻辑：**

```python
# Level 1: 配置对比（用于 flush_into_support, flush_into_objects）
parser = GCodeParser(gcode_path)
cfg = parser.load_config()
flush_into_support = cfg.get("flush_into_support")    # 默认 true（注意！）
flush_into_objects = cfg.get("flush_into_objects")    # 默认 false

# Level 2: 特征检测（用于 flush_into_infill）
# 验证思路：检测换料后首个挤出块是否在填充区域
# 
# flush_into_infill 启用时的特征：
#   1. 换料命令（T0/T1/T2...）之后
#   2. 在 Prime tower 挤出完成后
#   3. 首个模型挤出出现在填充区域（;TYPE:Sparse infill 或 ;TYPE:Internal solid infill）
#   4. 该填充区域的挤出量明显大于正常填充（包含冲刷量）
#
# 具体检测步骤：
#   1. 定位所有换料命令（T0, T1, T2...）
#   2. 在换料后，跳过 Prime tower 区域
#   3. 记录进入模型打印后的首个 TYPE 标记
#   4. 统计换料后首个 TYPE 为填充类型的比例
#   5. 如果比例 > 80%，判定为 flush_into_infill 启用
#
# flush_into_infill 禁用时的特征：
#   - 换料后首个挤出通常在外墙或其他区域
#   - 填充区域的挤出量正常

def check_flush_into_infill(gcode_path: Path) -> Tuple[bool, Dict]:
    """
    检测 flush_into_infill 是否启用
    
    返回:
        (is_enabled, details)
    """
    parser = GCodeParser(gcode_path)
    
    # 定位换料命令
    tool_changes = []  # [(line_no, tool_id), ...]
    
    # 统计换料后首个挤出类型
    first_type_after_change = []
    
    # 填充类型标记
    infill_types = ["Sparse infill", "Internal solid infill"]
    
    # 遍历 G-code，分析换料后的挤出模式
    # ...
    
    # 判断：如果换料后首个挤出大部分是填充类型，则启用
    infill_ratio = sum(1 for t in first_type_after_change if t in infill_types) / len(first_type_after_change)
    is_enabled = infill_ratio > 0.8
    
    return is_enabled, {
        "infill_ratio": infill_ratio,
        "first_types": first_type_after_change,
        "tool_changes": len(tool_changes),
    }

# 注意事项：
# 1. flush_into_support 默认启用，测试时需注意
# 2. 冲刷功能需要 enable_prime_tower = true 才能生效
# 3. flush_into_objects 需要多模型场景才能测试
# 4. flush_into_infill 的 Level 2 检测需要有换料操作才能验证
```

**测试建议：**

| 参数 | 推荐测试模型 | 测试要点 |
|------|-------------|---------|
| `flush_into_infill` | 多色模型 + 较多填充 | 对比启用/禁用时的擦料塔耗材量 |
| `flush_into_support` | 多色模型 + 需要支撑 | 默认启用，测试禁用场景 |
| `flush_into_objects` | 多个模型同时打印 | 需要至少 2 个模型，其中一个设为冲刷对象 |

---

### 2.5 高级-互锁结构 (Interlocking)

| 参数名 | 类型 | 校验方法 |
|--------|------|---------|
| `interlocking_beam` | bool | 检测多材料边界的互锁特征 |
| `mmu_segmented_region_max_width` | float | 分析分段区域宽度 |
| `mmu_segmented_region_interlocking_depth` | float | 分析互锁深度 |
| `interlocking_beam_width` | float | 测量互锁梁宽度 |
| `interlocking_orientation` | float | 分析互锁方向角度 |
| `interlocking_beam_layer_count` | int | 统计互锁梁层数 |
| `interlocking_depth` | float | 分析互锁深度 |
| `interlocking_boundary_avoidance` | float | 分析边界避让距离 |

**校验逻辑：**

```
1. 定位材料切换边界
2. 分析边界区域的路径交错模式
3. 测量交错深度和宽度
4. 与参数值进行对比
```

---

### 2.6 裙边 (Skirt)

| 参数名 | 类型 | 默认值 | 校验方法 |
|--------|------|--------|---------|
| `skirt_type` | enum | - | 分析裙边形状（普通/防护罩） |
| `skirt_loops` | int | 1 | 统计首层裙边圈数 |
| `min_skirt_length` | float | - | 计算裙边总长度 |
| `skirt_distance` | float | 6mm | 计算裙边与物体距离 |
| `skirt_height` | int | 1 | 统计裙边层数 |
| `skirt_speed` | float | - | 检测裙边打印速度 |
| `draft_shield` | bool | false | Level 2: 检测裙边是否贯穿全部层高 |

**校验逻辑：**

```
基础校验（Level 1 - 配置读取）：
1. 从配置注释读取 skirt_loops, skirt_distance, skirt_height 等值

增强校验（Level 2/3 - 按需升级）：

skirt_loops（Level 3 - 路径计数）:
  验证思路：统计首层裙边的闭合路径数量
  1. 提取首层 Skirt 区域的路径
  2. 识别闭合路径（起点和终点重合，或形成封闭环）
  3. 闭合路径数量应等于 skirt_loops

skirt_distance（Level 3 - 距离计算）:
  验证思路：计算裙边到物体轮廓的最小距离
  1. 提取首层 Skirt 路径的最内侧点
  2. 提取首层物体轮廓的最外侧点
  3. 计算两者之间的最小距离，应接近 skirt_distance

draft_shield（Level 2 - 高度检测）:
  验证思路：检测裙边是否贯穿全部层高
  - 启用特征：Skirt 标记出现在所有层（从首层到顶层）
  - 禁用特征：Skirt 标记只出现在首层或前几层
  具体步骤：
  1. 统计 ;TYPE:Skirt 出现的层数
  2. 如果层数等于模型总层数，则为全高防护罩（draft_shield 启用）
  3. 如果只有 1-2 层，则为普通裙边
```

---

### 2.7 边缘 (Brim)

| 参数名 | 类型 | 默认值 | 校验层次 | 校验方法 |
|--------|------|--------|---------|----------|
| `brim_type` | enum | auto_brim | Level 1 | 配置读取: `cfg.get("brim_type")` |
| `brim_width` | float | 5mm | Level 1 | 配置读取: `cfg.get("brim_width")` |
| `brim_object_gap` | float | 0.1mm | Level 1 | 配置读取: `cfg.get("brim_object_gap")` |
| `brim_ears_max_angle` | float | 125° | Level 1 | 配置读取: `cfg.get("brim_ears_max_angle")` |
| `brim_ears_detection_length` | float | 1mm | Level 1 | 配置读取: `cfg.get("brim_ears_detection_length")` |

**校验逻辑：**

```python
# Level 1: 配置对比（推荐）
cfg = parser.load_config()
brim_type = cfg.get("brim_type")  # 直接读取
brim_width = cfg.get("brim_width")

# Level 2: 特征检测（验证实际生成）
# 识别 ;TYPE:Brim 标记（注意：Skirt 和 Brim 是分开的标记）
brim_blocks = parser.get_extrusion_blocks_per_layer(ExtrusionType.BRIM.value)

# Level 3: 路径分析（几何验证）
# 1. 计算边缘向外延伸的最大距离验证 brim_width
# 2. 测量边缘内边界到物体外边界的距离验证 brim_object_gap
```

---

### 2.8 特殊模式 (Special mode)

| 参数名 | 类型 | 校验方法 |
|--------|------|---------|
| `slicing_mode` | enum | 检测配置注释 |
| `print_sequence` | enum | 分析多物体打印顺序 |
| `print_order` | enum | 分析打印优先级 |
| `spiral_mode` | bool | **检测 Z 轴是否连续变化** |
| `ignore_inner_color` | bool | 检测内部是否忽略颜色 |
| `spiral_mode_smooth` | bool | 分析 Z 轴变化平滑度 |
| `spiral_mode_max_xy_smoothing` | float | 分析 XY 平滑程度 |
| `timelapse_type` | enum | 检测延时摄影命令 |
| `fuzzy_skin` | enum | **检测外墙路径是否有随机偏移** |
| `fuzzy_skin_point_distance` | float | 分析模糊点间距 |
| `fuzzy_skin_thickness` | float | 分析模糊偏移幅度 |
| `fuzzy_skin_first_layer` | bool | 检测首层是否有模糊效果 |

**spiral_mode 校验逻辑（Level 2 - Z轴连续性检测）：**

```
验证思路：检测 Z 轴是否连续递增，不存在层间跳跃
- 螺旋模式特征：每条 G1 挤出命令的 Z 值都比上一条略高，形成连续螺旋
- 普通模式特征：同一层内 Z 值相同，层间有明显跳跃

具体步骤：
1. 提取所有带 E 参数的 G1 命令（挤出移动）
2. 计算相邻命令的 Z 差值
3. 螺旋模式判定：
   - Z 差值应该都为正（单调递增）
   - Z 差值接近均匀（标准差小）
   - 不存在大于 layer_height 的跳跃
4. 普通模式判定：
   - 大部分 Z 差值为 0（同层移动）
   - 仅在换层时有等于 layer_height 的跳跃
```

**fuzzy_skin 校验逻辑（Level 3 - 路径偏差分析）：**

```
验证思路：检测外墙路径是否存在随机偏移
- 模糊皮肤特征：外墙路径点相对于理想轮廓有随机抖动
- 正常外墙特征：路径点平滑连续，贴合理想轮廓

简化方案（推荐用于圆柱体等简单几何）：
1. 提取外墙（Outer wall）路径坐标
2. 计算各点到几何中心的距离
3. 统计距离分布的标准差
4. 判定标准：
   - 正常外墙：距离分布集中，标准差很小（< 0.1mm）
   - 模糊皮肤：距离分布分散，标准差明显增大（接近 fuzzy_skin_thickness）

完整方案（适用于任意几何）：
1. 定位外墙路径 (;TYPE:Outer wall)
2. 拟合理想轮廓曲线（如最小二乘拟合）
3. 计算实际路径点到理想曲线的偏差
4. 统计偏差分布:
   - 偏差范围应在 [-fuzzy_skin_thickness, +fuzzy_skin_thickness]
   - 相邻偏差点距离应接近 fuzzy_skin_point_distance
```

---

### 2.9 G代码输出 (G-code output)

| 参数名 | 类型 | 校验方法 |
|--------|------|---------|
| `reduce_infill_retraction` | bool | 统计填充区域的回抽次数 |
| `gcode_add_line_number` | bool | 检测是否有 N<num> 行号前缀 |
| `gcode_comments` | bool | 检测是否有丰富的注释 |
| `gcode_label_objects` | bool | 检测是否有 EXCLUDE_OBJECT 标签 |
| `exclude_object` | bool | 检测是否支持对象排除 |
| `filename_format` | string | 验证输出文件名格式 |

**校验逻辑（全部升级为 Level 2 特征检测）：**

```
gcode_add_line_number（Level 2 - 格式检测）:
  验证思路：检测 G-code 行是否有 N 开头的行号
  - 启用特征：每行以 N1, N2, N3 ... 开头，行号连续递增
  - 禁用特征：行首直接是 G/M 命令或注释
  具体步骤：
  1. 正则匹配: ^N\d+
  2. 统计匹配成功的行数比例
  3. 如果超过 90% 的非空非注释行都有行号，则判定为启用

gcode_comments（Level 2 - 比例检测）:
  验证思路：统计注释行占比
  - 启用特征：注释行（以 ; 开头）占比较高（如 > 5%）
  - 禁用特征：注释行很少，仅有必要的配置注释
  具体步骤：
  1. 统计以 ; 开头的行数
  2. 计算：注释率 = 注释行数 / 总行数
  3. 根据阈值判定是否启用详细注释

gcode_label_objects（Level 2 - 关键字检测）:
  验证思路：搜索对象标签相关的关键字
  - 启用特征：存在 EXCLUDE_OBJECT_DEFINE、EXCLUDE_OBJECT_START、EXCLUDE_OBJECT_END 标记
  - 禁用特征：不存在上述标记
  具体步骤：
  1. 在 G-code 中搜索 EXCLUDE_OBJECT
  2. 找到任意一个匹配即可判定为启用
```

---

### 2.10 后处理脚本与备注

| 参数名 | 类型 | 校验方法 |
|--------|------|---------|
| `post_process` | string | **无法直接校验**（脚本执行后效果） |
| `notes` | string | 检测 G-code 头部是否包含备注内容 |

---

## 三、校验优先级与实现建议

### 校验策略总结

```
1. 优先使用配置对比（Level 1）- 简单、快速、准确
   parser.load_config().get("参数名")

2. 开关型参数使用特征检测（Level 2）
   - enable_prime_tower: 检测 ";TYPE:Prime tower" 或 WIPE_TOWER_START
   - spiral_mode: 检测 Z 轴连续递增
   - fuzzy_skin: 检测外墙路径偏差

3. 需要几何验证时才使用路径分析（Level 3）
   - 验证 prime_tower_width 实际生成的宽度
   - 验证 skirt_distance 与物体的实际距离
```

### 高优先级（配置读取即可，价值高）

| 优先级 | 参数 | 校验层次 | 原因 |
|--------|------|---------|------|
| 1 | `prime_tower_width` | Level 1 | 配置直接读取 |
| 2 | `skirt_loops`, `skirt_distance` | Level 1 | 配置直接读取 |
| 3 | `brim_type`, `brim_width` | Level 1 | 配置直接读取 |
| 4 | `enable_prime_tower` | Level 2 | TYPE 标记检测 |
| 5 | `gcode_add_line_number` | Level 2 | 正则匹配即可 |
| 6 | `gcode_label_objects` | Level 2 | 关键字搜索即可 |

### 中优先级（需要复杂分析）

| 优先级 | 参数 | 原因 |
|--------|------|------|
| 7 | `fuzzy_skin` | 需要路径偏差分析 |
| 8 | `prime_tower_width` | 需要边界计算 |
| 9 | `wall_filament` 等 | 需要换料命令分析 |
| 10 | `ooze_prevention` | 需要温度序列分析 |

### 低优先级（实现复杂或价值有限）

| 优先级 | 参数 | 原因 |
|--------|------|------|
| 11 | `interlocking_*` | 路径分析复杂 |
| 12 | `post_process` | 无法直接校验 |
| 13 | `filename_format` | 与G-code内容无关 |

---

## 四、测试模型建议

| 参数类别 | 推荐测试模型 | 原因 |
|---------|-------------|------|
| 裙边/边缘 | `20mmbox-LF.stl` | 简单立方体，首层特征清晰 |
| 擦料塔 | 多色模型 | 需要换料才会生成擦料塔 |
| 螺旋模式 | 花瓶模型 | 单壁结构最适合螺旋模式 |
| 模糊皮肤 | 圆柱体 | 外墙曲线便于分析偏差 |
| 互锁结构 | 多材料拼接模型 | 需要材料边界 |

---

## 五、校验结果判定标准

| 参数类型 | 判定方法 | 容差 |
|---------|---------|------|
| 布尔型 | 特征存在/不存在 | 无 |
| 整数型 | 计数精确匹配 | 0 |
| 浮点型 | 测量值对比 | ±5% 或 ±0.1mm |
| 枚举型 | 特征模式匹配 | 无 |

---

## 七、参数完整列表

### 多材料 (Multimaterial) - 31 个参数

#### 擦料塔 (Prime tower) - 15 个参数
- `enable_prime_tower`
- `prime_tower_width`
- `prime_volume`
- `prime_tower_brim_width`
- `prime_tower_position_type` *(新增)*
- `wipe_tower_x` *(新增)*
- `wipe_tower_y` *(新增)*
- `wipe_tower_rotation_angle`
- `wipe_tower_bridging`
- `prime_tower_enhance_type`
- `wipe_tower_cone_angle`
- `wipe_tower_extra_spacing`
- `wipe_tower_extra_flow`
- `wipe_tower_max_purge_speed`
- `wipe_tower_no_sparse_layers`

#### 特征耗材 (Filament for Features)
- `wall_filament`
- `sparse_infill_filament`
- `solid_infill_filament`
- `wipe_tower_filament`

#### 渗料预防 (Ooze prevention)
- `ooze_prevention`
- `standby_temperature_delta`
- `preheat_time`
- `preheat_steps`

#### 冲刷选项 (Flush options)
- `flush_into_infill`
- `flush_into_objects`
- `flush_into_support`

#### 高级 (Advanced)
- `interlocking_beam`
- `mmu_segmented_region_max_width`
- `mmu_segmented_region_interlocking_depth`
- `interlocking_beam_width`
- `interlocking_orientation`
- `interlocking_beam_layer_count`
- `interlocking_depth`
- `interlocking_boundary_avoidance`

### 其他 (Others) - 32 个参数

#### 裙边 (Skirt)
- `skirt_type`
- `skirt_loops`
- `min_skirt_length`
- `skirt_distance`
- `skirt_height`
- `skirt_speed`
- `draft_shield`

#### 边缘 (Brim)
- `brim_type`
- `brim_width`
- `brim_object_gap`
- `brim_ears_max_angle`
- `brim_ears_detection_length`

#### 特殊模式 (Special mode)
- `slicing_mode`
- `print_sequence`
- `print_order`
- `spiral_mode`
- `ignore_inner_color`
- `spiral_mode_smooth`
- `spiral_mode_max_xy_smoothing`
- `timelapse_type`
- `fuzzy_skin`
- `fuzzy_skin_point_distance`
- `fuzzy_skin_thickness`
- `fuzzy_skin_first_layer`

#### G代码输出 (G-code output)
- `reduce_infill_retraction`
- `gcode_add_line_number`
- `gcode_comments`
- `gcode_label_objects`
- `exclude_object`
- `filename_format`

#### 后处理脚本 (Post-processing Scripts)
- `post_process`

#### 备注 (Notes)
- `notes`

---

## 八、G-code TYPE 标记参考

实际 G-code 中使用的 TYPE 标记（与 `ExtrusionType` 枚举对应）：

| 标记 | 说明 |
|------|------|
| `;TYPE:Inner wall` | 内墙 |
| `;TYPE:Outer wall` | 外墙 |
| `;TYPE:Sparse infill` | 稀疏填充 |
| `;TYPE:Internal solid infill` | 内部实心填充 |
| `;TYPE:Top surface` | 顶面 |
| `;TYPE:Bottom surface` | 底面 |
| `;TYPE:Bridge` | 桥接 |
| `;TYPE:Support` | 支撑 |
| `;TYPE:Skirt` | 裙边 |
| `;TYPE:Brim` | 边缘 |
| `;TYPE:Prime tower` | 擦料塔 |
| `;TYPE:Custom` | 自定义 |

**注意**：
- 裙边和边缘是**分开的标记**，不存在 `;TYPE:Skirt/Brim`
- 擦料塔使用 `;TYPE:Prime tower`，不是 `;TYPE:Wipe tower`
- 外墙使用 `;TYPE:Outer wall`，不是 `;TYPE:External perimeter`
- 擦料塔还有额外标记：`; WIPE_TOWER_START` 和 `; WIPE_TOWER_END`

---

## 九、总结

| 分类 | 参数数量 | Level 1 可校验 | Level 2 可校验 | Level 3 可校验 | 无法校验 |
|------|---------|---------------|---------------|---------------|----------|
| 多材料 | 34 | 28 | 4 | 0 | 2 |
| 其他 | 32 | 24 | 4 | 2 | 2 |
| **总计** | **66** | **52** | **8** | **2** | **4** |

- **Level 1 可校验 (52个)**：直接从 G-code 配置注释读取（快速预检）
- **Level 2 可校验 (8个)**：需要 TYPE 标记或特征检测
- **Level 3 可校验 (2个)**：需要路径分析/几何验证
- **无法校验参数 (4个)**：`post_process`, `filename_format`, `notes`, `ignore_inner_color`

**建议升级的效果型参数（Level 1 不可靠，需升级到 Level 2/3）：**

| 批次 | 参数 | 原层次 | 目标层次 | 验证方法 |
|------|------|--------|----------|----------|
| 一 | prime_tower_enhance_type | L1 | L3 | 底部边界框趋势分析 |
| 一 | spiral_mode | L2 | L2 细化 | Z轴连续性检测 |
| 一 | fuzzy_skin | L3 | L3 细化 | 路径偏差分析 |
| 二 | gcode_add_line_number | L1 | L2 | 行号格式检测 |
| 二 | gcode_label_objects | L1 | L2 | EXCLUDE_OBJECT关键字检测 |
| 二 | gcode_comments | L1 | L2 | 注释行比例检测 |
| 二 | draft_shield | L1 | L2 | 裙边层高检测 |
| 三 | prime_tower_width | L1 | L3 | 边界框宽度计算 |
| 三 | wipe_tower_x/y | L1 | L3 | 边界框中心计算 |
| 三 | skirt_loops | L1 | L3 | 闭合路径计数 |
| 三 | skirt_distance | L1 | L3 | 最小距离计算 |
