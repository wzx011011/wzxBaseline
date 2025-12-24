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
| 支撑 | 47 | 37 | 9 | 1 | 0 |
| **总计** | **113** | **89** | **18** | **5** | **1** |

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
| `flush_into_support` | bool | **true** | Level 2 | 检测换料后首个挤出是否在支撑区域 | 冲刷到对象的支撑（**默认启用**），将冲刷耗材用于支撑区域 |
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

# Level 2: 特征检测（用于 flush_into_support）
# 验证思路：检测换料后首个挤出块是否在支撑区域
# 
# flush_into_support 启用时的特征：
#   1. 换料命令（T0/T1/T2...）之后
#   2. 在 Prime tower 挤出完成后
#   3. 首个模型挤出出现在支撑区域（;TYPE:Support 或 ;TYPE:Support interface）
#
# 具体检测步骤：
#   1. 定位所有换料命令（T0, T1, T2...）
#   2. 在换料后，跳过 Prime tower 区域
#   3. 记录进入模型打印后的首个 TYPE 标记
#   4. 统计换料后首个 TYPE 为支撑类型的比例
#   5. 如果比例 > 阈值，判定为 flush_into_support 启用
#
# flush_into_support 禁用时的特征：
#   - 换料后首个挤出不会优先进入支撑区域
#
# 注意：flush_into_support 默认启用，测试时需验证禁用场景

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

| 参数名 | 类型 | 枚举值/范围 | 校验方法 |
|--------|------|------------|---------|
| `slicing_mode` | enum | `Regular`, `EvenOdd`, `CloseHoles` | 检测配置注释 (Level 1) |
| `print_sequence` | enum | `ByLayer`, `ByObject`, `ByDefault` | 分析多物体打印顺序 (Level 1) |
| `print_order` | enum | `Default`, `AsObjectList` | 分析打印优先级 (Level 1) |
| `spiral_mode` | bool | `true`/`false` | **检测 Z 轴是否连续变化** (Level 2) |
| `ignore_inner_color` | bool | `true`/`false` | 检测内部是否忽略颜色 (Level 1) |
| `spiral_mode_smooth` | bool | `true`/`false` | 分析 Z 轴变化平滑度 (Level 1) |
| `spiral_mode_max_xy_smoothing` | float | 0-200% | 分析 XY 平滑程度 (Level 1) |
| `timelapse_type` | enum | `tlTraditional`, `tlSmooth`, `tlClose` | 检测延时摄影命令 (Level 2) |
| `fuzzy_skin` | enum | `None`, `External`, `All`, `AllWalls` | **检测外墙路径是否有随机偏移** (Level 2/3) |
| `fuzzy_skin_point_distance` | float | 0.1-1.5mm | 分析模糊点间距 (Level 3) |
| `fuzzy_skin_thickness` | float | 0.1-0.5mm | 分析模糊偏移幅度 (Level 3) |
| `fuzzy_skin_first_layer` | bool | `true`/`false` | 检测首层是否有模糊效果 (Level 2) |

**枚举值说明（来自 PrintConfig.hpp）：**

- **slicing_mode**:
  - `Regular`: 普通裁剪规则（默认）
  - `EvenOdd`: 与 3DLabPrint 模型兼容，使用奇偶规则
  - `CloseHoles`: 强制所有轮廓逆时针，闭合孔洞

- **print_sequence**:
  - `ByLayer`: 按层打印（默认）
  - `ByObject`: 按对象顺序打印（逐件打印）
  - `ByDefault`: 默认行为，由用户或全局设置决定

- **print_order**:
  - `Default`: 层内顺序（默认）
  - `AsObjectList`: 按照对象列表的顺序

- **timelapse_type**:
  - `tlTraditional`: 传统延时摄影
  - `tlSmooth`: 平滑模式，打印后移动到分流槽拍照
  - `tlClose`: 关闭延时摄影

- **fuzzy_skin**:
  - `None`: 关闭模糊
  - `External`: 仅外墙（推荐）
  - `All`: 全部墙面
  - `AllWalls`: 所有墙面且间隔更密

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

## 六、支撑 (Support) 参数校验

> **说明**：支撑参数分为普通支撑和树支撑两大类，部分参数在不同类型下行为不同。UI界面组织为5个参数组：Support(支撑)、Raft、Support filament(支撑耗材)、Advanced(高级)、Tree supports(树形支撑)。

### 6.1 支撑 (Support)

| 参数名 | 类型 | 默认值 | 校验层次 | 校验方法 | 参数说明 |
|--------|------|--------|---------|----------|----------|
| `enable_support` | bool | false | Level 2 | 检测 `;TYPE:Support` 标记是否存在 | 启用/禁用支撑生成 |
| `support_type` | enum | stNormalAuto | Level 1 | 配置读取: `cfg.get("support_type")` | 支撑类型：normal/tree/normalAuto/treeAuto/normal(manual)/tree(manual) |
| `support_style` | enum | smsDefault | Level 1 | 配置读取: `cfg.get("support_style")` | 支撑风格：Default/Grid/Snug/TreeSlim/TreeStrong/TreeHybrid/TreeOrganic |
| `support_threshold_angle` | int | 30° | Level 1 | 配置读取: `cfg.get("support_threshold_angle")` | 支撑阈值角度，小于此角度的悬空需要支撑 |
| `support_on_build_plate_only` | bool | false | Level 2 | 检测支撑是否仅在底板上生成 | 仅在打印平台生成支撑，不在模型表面 |
| `support_critical_regions_only` | bool | false | Level 2 | 检测是否只有关键区域有支撑 | 仅为尖锐尾部、悬臂等关键区域生成支撑 |
| `support_remove_small_overhang` | bool | false | Level 1 | 配置读取: `cfg.get("support_remove_small_overhang")` | 移除可能不需要支撑的小悬空 |

**枚举值说明：**

- **support_type**:
  - `stNormal` / `stNormalAuto`: 普通支撑（自动）
  - `stTree` / `stTreeAuto`: 树支撑（自动）
  - `stNormalManual`: 普通支撑（手动，仅支撑添加器）
  - `stTreeManual`: 树支撑（手动，仅支撑添加器）

- **support_style**:
  - `smsDefault`: 默认
  - `smsGrid`: 网格支撑（更稳定）
  - `smsSnug`: 贴合支撑塔（节省材料）
  - `smsTreeSlim`: 树支撑-纤细
  - `smsTreeStrong`: 树支撑-强壮
  - `smsTreeHybrid`: 树支撑-混合（大平面悬空下类似普通支撑）
  - `smsTreeOrganic`: 树支撑-有机（默认，更激进合并分支）

**校验逻辑：**

```python
# Level 1: 配置对比
parser = GCodeParser(gcode_path)
cfg = parser.load_config()
support_type = cfg.get("support_type")      # 读取支撑类型
support_style = cfg.get("support_style")    # 读取支撑风格
threshold_angle = cfg.get("support_threshold_angle")  # 阈值角度

# Level 2: 特征检测（enable_support）
# 检测 ;TYPE:Support 或 ;TYPE:Support interface 标记
support_blocks = parser.get_extrusion_blocks_per_layer(ExtrusionType.SUPPORT.value)
support_present = any(blocks for blocks in support_blocks if blocks)

# Level 2: 特征检测（support_on_build_plate_only）
# 验证思路：检测支撑是否只在首层或靠近底板的层
# - 仅底板支撑：Support 标记只出现在靠近底板的层（如前 10 层）
# - 支撑在模型上：Support 标记出现在较高的层
def check_support_on_build_plate_only(gcode_path):
    parser = GCodeParser(gcode_path)
    support_layers = []
    for layer_idx, blocks in enumerate(parser.get_extrusion_blocks_per_layer(ExtrusionType.SUPPORT.value)):
        if blocks:
            support_layers.append(layer_idx)
    
    if not support_layers:
        return None  # 无支撑
    
    # 如果支撑层都集中在底部（如 < 20% 总层高），判定为仅底板支撑
    total_layers = parser.get_layer_count()
    max_support_layer = max(support_layers)
    on_build_plate_only = max_support_layer < total_layers * 0.2
    
    return on_build_plate_only
```

---

### 6.2 Raft

| 参数名 | 类型 | 默认值 | 校验层次 | 校验方法 | 参数说明 |
|--------|------|--------|---------|----------|----------|
| `raft_layers` | int | 0 | Level 2 | 统计首层以下的支撑层数 | 筏层数（在模型下方打印的额外层） |
| `raft_contact_distance` | float | 0.1mm | Level 1 | 配置读取: `cfg.get("raft_contact_distance")` | 筏与模型的接触距离（Z间隙） |

**校验逻辑：**

```python
# Level 1: 配置对比
cfg = parser.load_config()
raft_contact = cfg.get("raft_contact_distance")

# Level 2: 筏层数检测
# 验证思路：统计模型首层（Z=layer_height）之前的支撑层数
def check_raft_layers(gcode_path):
    parser = GCodeParser(gcode_path)
    layer_height = float(cfg.get("layer_height"))
    
    raft_layer_count = 0
    for layer_idx, z in enumerate(parser.get_layer_z_values()):
        if z < layer_height:
            # 检查该层是否有支撑
            blocks = parser.get_extrusion_blocks_at_layer(layer_idx, ExtrusionType.SUPPORT.value)
            if blocks:
                raft_layer_count += 1
    
    return raft_layer_count
```

---

### 6.3 支撑耗材 (Support filament)

| 参数名 | 类型 | 默认值 | 校验层次 | 校验方法 | 参数说明 |
|--------|------|--------|---------|----------|----------|
| `support_filament` | int | 0 (默认) | Level 2 | 检测支撑前的换料命令 | 支撑/筏基础使用的耗材 |
| `support_interface_filament` | int | 0 (默认) | Level 2 | 检测接触面前的换料命令 | 支撑接触面使用的耗材 |
| `support_interface_not_for_body` | bool | false | Level 2 | 检测支撑基础是否避免使用接触面材料 | 避免用接触面材料打印支撑基础 |

**校验逻辑：**

```python
# Level 2: 换料命令检测
# 验证思路：检测 ;TYPE:Support 前的 T<n> 命令
def check_support_filament(gcode_path):
    parser = GCodeParser(gcode_path)
    support_tools = []
    interface_tools = []
    current_tool = 0
    
    for line in parser.lines:
        if line.startswith("T"):
            # 提取换料命令
            tool_match = re.match(r'T(\d+)', line)
            if tool_match:
                current_tool = int(tool_match.group(1))
        elif ";TYPE:Support" in line and ";TYPE:Support interface" not in line:
            support_tools.append(current_tool)
        elif ";TYPE:Support interface" in line:
            interface_tools.append(current_tool)
    
    # 统计最常用的工具
    most_common_support = max(set(support_tools), key=support_tools.count) if support_tools else None
    most_common_interface = max(set(interface_tools), key=interface_tools.count) if interface_tools else None
    
    return most_common_support, most_common_interface
```

---

### 6.4 高级 (Advanced)

| 参数名 | 类型 | 默认值 | 校验层次 | 校验方法 | 参数说明 |
|--------|------|--------|---------|----------|----------|
| `raft_first_layer_density` | percent | 90% | Level 1 | 配置读取: `cfg.get("raft_first_layer_density")` | Raft 首层密度 |
| `raft_first_layer_expansion` | float | 2 | Level 1 | 配置读取: `cfg.get("raft_first_layer_expansion")` | Raft 首层外扩 |
| `support_top_z_distance` | float | 0.2 | Level 1 | 配置读取: `cfg.get("support_top_z_distance")` | 支撑与模型顶部接触面的 Z 间隙 |
| `support_bottom_z_distance` | float | 0.2 | Level 1 | 配置读取: `cfg.get("support_bottom_z_distance")` | 支撑与模型底部接触面的 Z 间隙 |
| `support_base_pattern` | enum | rectilinear | Level 1 | 配置读取: `cfg.get("support_base_pattern")` | 支撑主体图案 |
| `support_base_pattern_spacing` | float | 2.5 | Level 1 | 配置读取: `cfg.get("support_base_pattern_spacing")` | 支撑主体线间距 |
| `support_angle` | float | 0 | Level 1 | 配置读取: `cfg.get("support_angle")` | 支撑角度/方向参数（具体含义与实现有关） |
| `support_interface_top_layers` | int | 2 | Level 1 / Level 2 | 配置读取 / 统计接触面层数 | 顶部接触面层数 |
| `support_interface_bottom_layers` | int | 2 | Level 1 / Level 2 | 配置读取 / 统计接触面层数 | 底部接触面层数 |
| `support_interface_pattern` | enum | smipRectilinear | Level 1 | 配置读取: `cfg.get("support_interface_pattern")` | 接触面图案：rectilinear/concentric/grid等 |
| `support_interface_spacing` | float | 0.5mm | Level 1 | 配置读取: `cfg.get("support_interface_spacing")` | 接触面线间距（0表示实心） |
| `support_bottom_interface_spacing` | float | 0.5mm | Level 1 | 配置读取: `cfg.get("support_bottom_interface_spacing")` | 底部接触面线间距 |
| `support_interface_loop_pattern` | bool | false | Level 2 | 检测接触面是否有环形路径 | 用环形覆盖接触层 |
| `support_interface_speed` | float | 80mm/s | Level 2 | 检测接触面区域的打印速度 | 接触面打印速度 |
| `support_interface_min_area` | float | 0.25mm² | Level 1 | 配置读取: `cfg.get("support_interface_min_area")` | 最小接触面积（小于此值不生成接触面） |
| `support_expansion` | float | 0 | Level 1 | 配置读取: `cfg.get("support_expansion")` | 支撑外扩 |
| `support_object_xy_distance` | float | 0.35 | Level 1 | 配置读取: `cfg.get("support_object_xy_distance")` | 支撑与模型 XY 距离 |
| `support_object_first_layer_gap` | float | 0.2 | Level 1 | 配置读取: `cfg.get("support_object_first_layer_gap")` | 支撑首层与模型的间隙 |
| `support_xy_overrides_z` | enum | xy_overrides_z | Level 1 | 配置读取: `cfg.get("support_xy_overrides_z")` | XY/Z 间隙覆盖规则（G-code 里通常序列化为字符串） |
| `bridge_no_support` | bool | 0 | Level 1 | 配置读取: `cfg.get("bridge_no_support")` | 桥接区域是否禁止生成支撑 |
| `max_bridge_length` | float | 10 | Level 1 | 配置读取: `cfg.get("max_bridge_length")` | 最大桥接长度阈值 |
| `independent_support_layer_height` | bool | 0 | Level 1 | 配置读取: `cfg.get("independent_support_layer_height")` | 支撑是否使用独立层高 |
| `ironing_support_layer` | bool | 0 | Level 1 | 配置读取: `cfg.get("ironing_support_layer")` | 支撑层是否熨烫 |
| `tree_hybrid_cross_height` | float | 0 | Level 1 | 配置读取: `cfg.get("tree_hybrid_cross_height")` | 树支撑混合横梁高度 |
| `support_line_width` | float | 0.42 | Level 1 | 配置读取: `cfg.get("support_line_width")` | 支撑线宽 |
| `support_speed` | float | 150 | Level 1 | 配置读取: `cfg.get("support_speed")` | 支撑打印速度 |
| `minimum_support_area` | float | 5 | Level 1 | 配置读取: `cfg.get("minimum_support_area")` | 最小支撑面积 |
| `support_material_interface_fan_speed` | string | -1,-1 | Level 1 | 配置读取: `cfg.get("support_material_interface_fan_speed")` | 接触面风扇速度（按耗材序列，-1 表示跟随默认） |
| `tree_support_wall_count` | int | 0 | Level 1 | 配置读取: `cfg.get("tree_support_wall_count")` | 树支撑外壳圈数 |

**枚举值说明：**

- **support_interface_pattern**:
  - `smipRectilinear`: 直线（默认，非可溶材料）
  - `smipConcentric`: 同心圆（默认，可溶材料）
  - `smipGrid`: 网格
  - `smipRectilinearInterlaced`: 交错直线
  - `smipMonotonicLine`: 单调线
  - `smipAuto`: 自动（根据材料类型选择）

**校验逻辑：**

```python
# Level 1: 配置对比
cfg = parser.load_config()
interface_top_layers = cfg.get("support_interface_top_layers")
interface_bottom_layers = cfg.get("support_interface_bottom_layers")
interface_pattern = cfg.get("support_interface_pattern")
interface_spacing = cfg.get("support_interface_spacing")

# Level 2: 层数统计（验证实际生成）
# 验证思路：统计 ;TYPE:Support interface 出现的连续层数
def check_support_interface_layers(gcode_path):
    parser = GCodeParser(gcode_path)
    interface_layer_groups = []  # [(start_layer, end_layer), ...]
    
    in_interface = False
    start_layer = None
    
    for layer_idx, blocks in enumerate(parser.get_extrusion_blocks_per_layer(ExtrusionType.SUPPORT_INTERFACE.value)):
        if blocks and not in_interface:
            # 开始一个新的接触面区域
            start_layer = layer_idx
            in_interface = True
        elif not blocks and in_interface:
            # 结束当前接触面区域
            interface_layer_groups.append((start_layer, layer_idx - 1))
            in_interface = False
    
    # 计算每组的层数
    layer_counts = [end - start + 1 for start, end in interface_layer_groups]
    return layer_counts
```

---

### 6.5 树形支撑 (Tree supports)

| 参数名 | 类型 | 默认值 | 校验层次 | 校验方法 | 参数说明 |
|--------|------|--------|---------|----------|----------|
| `tree_support_branch_diameter` | float | 2mm | Level 1 | 配置读取: `cfg.get("tree_support_branch_diameter")` | 树支撑分支直径 |
| `tree_support_branch_angle` | float | 45° | Level 1 | 配置读取: `cfg.get("tree_support_branch_angle")` | 树支撑分支角度（控制分支倾斜程度） |
| `tree_support_wall_count` | int | 1 | Level 1 / Level 2 | 配置读取 / 检测树支撑是否有外壳 | 树支撑外壳圈数（至少1圈） |
| `tree_support_branch_distance` | float | 1mm | Level 1 | 配置读取: `cfg.get("tree_support_branch_distance")` | 树支撑分支间距 |
| `tree_support_tip_diameter` | float | 0.8mm | Level 1 | 配置读取: `cfg.get("tree_support_tip_diameter")` | 树支撑尖端直径 |

**校验逻辑：**

```python
# Level 1: 配置对比
cfg = parser.load_config()
branch_diameter = cfg.get("tree_support_branch_diameter")
branch_angle = cfg.get("tree_support_branch_angle")
wall_count = cfg.get("tree_support_wall_count")

# Level 2: 外壳检测
# 验证思路：检测树支撑区域是否有多层外壳
# - wall_count > 0: 支撑区域有明显的外壳轮廓
# - wall_count = 0: 支撑区域无外壳，直接填充
def check_tree_support_wall(gcode_path):
    parser = GCodeParser(gcode_path)
    # 提取树支撑区域的路径
    # 分析是否有外壳特征（路径首先沿边界走一圈）
    # ...
```

---

## 七、参数完整列表

### 支撑 (Support) - 47 个参数

#### 6.1 支撑 (Support) - 7 个参数
- `enable_support`
- `support_type`
- `support_style`
- `support_threshold_angle`
- `support_on_build_plate_only`
- `support_critical_regions_only`
- `support_remove_small_overhang`

#### 6.2 Raft - 2 个参数
- `raft_layers`
- `raft_contact_distance`

#### 6.3 支撑耗材 (Support filament) - 3 个参数
- `support_filament`
- `support_interface_filament`
- `support_interface_not_for_body`

#### 6.4 高级 (Advanced) - 29 个参数
- `raft_first_layer_density`
- `raft_first_layer_expansion`
- `support_top_z_distance`
- `support_base_pattern`
- `tree_support_wall_count`
- `support_base_pattern_spacing`
- `support_angle`
- `support_interface_top_layers`
- `support_interface_bottom_layers`
- `support_interface_min_area`
- `support_interface_pattern`
- `support_interface_spacing`
- `support_bottom_interface_spacing`
- `support_expansion`
- `support_object_xy_distance`
- `support_object_first_layer_gap`
- `support_xy_overrides_z`
- `bridge_no_support`
- `max_bridge_length`
- `independent_support_layer_height`
- `ironing_support_layer`
- `tree_hybrid_cross_height`
- `support_bottom_z_distance`
- `support_line_width`
- `support_speed`
- `support_interface_loop_pattern`
- `support_interface_speed`
- `minimum_support_area`
- `support_material_interface_fan_speed`

#### 6.5 树形支撑 (Tree supports) - 6 个参数
- `tree_support_branch_distance`
- `tree_support_branch_diameter`
- `tree_support_branch_angle`
- `tree_support_branch_diameter_angle`
- `support_base_pattern_tree`
- `tree_support_wall_count_tree`

### 多材料 (Multimaterial) - 34 个参数

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

### 6.4 高级 (Advanced)

> 说明：本章节参数以 G-code 配置块（`; CONFIG_BLOCK_START`）输出的 **实际 key** 为准；布尔通常为 `0/1`，部分枚举为字符串。

| 参数 (config key) | 默认值 | 校验层级 | 校验方式/说明 |
|------|--------|----------|--------------|
| support_interface_top_layers | 3 | L1 | 配置块对比 |
| support_interface_bottom_layers | 3 | L1 | 配置块对比 |
| support_interface_pattern | rectilinear | L1 | 配置块对比 |
| support_interface_spacing | 0.2 | L1 | 配置块对比 |
| support_interface_speed | 80 | L1 | 配置块对比 |
| support_interface_loop_pattern | 0 | L1 | 配置块对比 |
| support_interface_min_area | 0 | L1 | 配置块对比 |
| support_material_interface_fan_speed | -1,-1 | L1 | 配置块对比（文档旧名 `support_interface_fan_speed` 以此为准） |
| support_bottom_interface_spacing | 0.5 | L1 | 配置块对比 |
| support_top_z_distance | 0.2 | L1 | 配置块对比 |
| support_bottom_z_distance | 0.2 | L1 | 配置块对比 |
| support_base_pattern | rectilinear | L1 | 配置块对比 |
| support_base_pattern_tree | 0 | L1 | 配置块对比 |
| support_base_pattern_spacing | 2.5 | L1 | 配置块对比 |
| support_angle | 0 | L1 | 配置块对比 |
| support_expansion | 0 | L1 | 配置块对比 |
| support_object_xy_distance | 0.35 | L1 | 配置块对比 |
| support_object_first_layer_gap | 0.2 | L1 | 配置块对比 |
| support_xy_overrides_z | xy_overrides_z | L1 | 配置块对比 |
| bridge_no_support | 0 | L1 | 配置块对比 |
| max_bridge_length | 10 | L1 | 配置块对比 |
| independent_support_layer_height | 1 | L1 | 配置块对比 |
| ironing_support_layer | 0 | L1 | 配置块对比 |
| tree_hybrid_cross_height | 0 | L1 | 配置块对比 |
| support_line_width | 0 | L1 | 配置块对比 |
| support_speed | 60 | L1 | 配置块对比 |
| minimum_support_area | 5 | L1 | 配置块对比 |
| raft_layers | 0 | L1 | 配置块对比 |
| raft_first_layer_density | 90% | L1 | 配置块对比 |
| raft_first_layer_expansion | 2 | L1 | 配置块对比 |
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
| 多材料 | 34 | 28 | 4 | 2 | 0 |
| 其他 | 32 | 24 | 5 | 2 | 1 |
| 支撑 | 47 | 37 | 9 | 1 | 0 |
| **总计** | **113** | **89** | **18** | **5** | **1** |

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
