# 测试用例计划

*注意：此测试用例计划基于 docs/ai-reference 目录中的 jobs-todo.csv 文件。*

本文档概述了引擎参数验证框架的测试用例。测试按参数类别组织，基于 jobs-todo.csv 文件，该文件包含需要验证的参数的完整列表。

## 1. 质量参数

### 1.1 层高测试
- 测试从 G-code 解析层高
- 验证层高值是否与预期参数匹配（例如，0.24mm）
- 检查所有层的层高一致性
- 验证方法：基于 `;LAYER_CHANGE` 注释分析 G-code

### 1.2 初始层打印高度测试
- 测试从 G-code 解析初始层打印高度
- 验证第一层高度是否与预期值匹配（例如，0.28mm）
- 验证方法：分析 G-code 中的第一个 `;LAYER_CHANGE` 注释

### 1.3 线宽测试
- 测试默认线宽（line_width）验证
  - 注意：当其他线宽设置为 0 时，这是默认的走线线宽
- 测试初始层线宽验证
  - 验证方法：通过 `;LAYER_CHANGE` 找到第一层，根据 "E X" 挤出值计算线宽（圆角矩形模型）
  - 所需参数：耗材直径、当前层高、挤出长度
- 测试外墙线宽验证
  - 验证方法：找到 ";TYPE:OUTER WALL"，根据 "E X" 挤出值计算线宽
  - 所需参数：耗材直径、当前层高、挤出长度
- 测试内墙线宽验证
  - 验证方法：找到 ";TYPE:INNER WALL"，根据 "E X" 挤出值计算线宽
  - 所需参数：耗材直径、当前层高、挤出长度
- 测试顶面线宽验证
  - 验证方法：找到 ";TYPE:Top surface"，根据 "E X" 挤出值计算线宽
  - 所需参数：耗材直径、当前层高、挤出长度
- 测试稀疏填充线宽验证
  - 验证方法：找到 ";TYPE:Sparse infill"，根据 "E X" 挤出值计算线宽
  - 所需参数：耗材直径、当前层高、挤出长度
- 测试内部实心填充线宽验证
  - 验证方法：找到 ";TYPE:Internal solid infill"，根据 "E X" 挤出值计算线宽
  - 所需参数：耗材直径、当前层高、挤出长度
- 测试支撑线宽验证
  - 验证方法：找到 ";TYPE:Support"，根据 "E X" 挤出值计算线宽
  - 所需参数：耗材直径、当前层高、挤出长度

### 1.4 接缝测试
- 测试接缝位置（seam_position）验证
- 测试交错的内墙接缝（staggered_inner_seams）验证
- 测试接缝间隔（seam_gap）验证
- 测试斜拼接缝（试验）（seam_slope_type）验证
- 测试擦拭速度验证（考虑基于角色的擦拭速度）
  - 特殊处理：如果 CONFIG_BLOCK 中的 role_based_wipe_speed 等于 "1"，则跳过测试并生成警告
  - 如果 role_based_wipe_speed 等于 "0"，则为每层找到 ";WIPE_START" 和 ";WIPE_END"，检查 "G1 V" 命令，验证 V/60 是否与预期值相符
- 测试闭环擦拭（wipe_on_loops）验证
- 测试额外的外墙打印前擦拭（wipe_before_external_loop）验证

### 1.5 精度测试
- 测试切片间隙闭合半径（slice_closing_radius）验证
- 测试分辨率（resolution）验证
- 测试圆弧拟合（enable_arc_fitting）验证
- 测试 XY 孔洞尺寸补偿（xy_hole_compensation）验证
- 测试 XY 外轮廓尺寸补偿（xy_contour_compensation）验证
- 测试象脚补偿（elefant_foot_compensation）验证
  - 验证方法：使用基准立方体 G-code（不使用补偿）作为参考，使用预期补偿值切片，找到第一层和所有墙，比较轮廓收缩值与预期值
- 测试象脚补偿层数（elefant_foot_compensation_layers）验证
  - 特殊处理：补偿具有线性递减效果（例如，elefant_foot_compensation=0.1mm 影响 5 层，每层结果为 [0.100, 0.080, 0.060, 0.040, 0.020]）
- 测试精准外墙尺寸（precise_outer_wall）验证
- 测试将圆孔转换为多边形孔（hole_to_polygon）验证
- 测试精准 Z 高度（precise_z_height）验证

### 1.6 熨烫类型测试
- 测试熨烫类型（ironing_type）验证
  - 验证方法：检查 G-code 中是否有 ";TYPE:IRONING" 来确认熨烫是否启用
  - TODO：熨烫类型能否通过 G-code 移动指令反推？

### 1.7 墙生成器测试
- 测试墙生成器（wall_generator）验证

### 1.8 墙和表面测试
- 测试墙顺序（wall_sequence）验证
  - 验证方法：检查每层 ";TYPE INNER WALL" 和 ";TYPE OUTER WALL" 的顺序
  - 特殊注意事项：
    1. 不要从第一层开始计数（它有固定的内/外顺序）
    2. 目前使用立方体模型进行验证
    3. G-code 中存在三种样式：
       a. 内墙/外墙（默认）
       b. 外墙/内墙
       c. 内-外-内墙
- 测试首先打印填充（is_infill_first）验证
  - 验证方法：检查稀疏填充和内部实心填充类型是否出现在内墙和外墙类型之前
- 测试围墙打印方向（wall_direction）验证
  - 验证方法：找到轮廓点，使用有向面积计算确定 cw/ccw 方向
- 测试顶部表面流量比例（top_solid_infill_flow_ratio）验证
- 测试底部表面流量比例（bottom_solod_infill_flow_ratio）验证
- 测试顶面单层墙（only_one_wall_top）验证
  - 验证方法：通过 ";TYPE:Top surface" 找到顶面，检查是否只有一层外墙
  - 特殊标记：查找 "; printing object" 和 "EXCLUDE_OBJECT_START NAME=立方体_id_0_copy_0"
- 测试单层墙阈值（min_width_top_surface）验证
- 测试首层仅单层墙（only_one_wall_first_layer）验证
  - 验证方法：找到第一层墙，计算墙层数
  - 计数规则：墙层数由轮廓的起点和终点是否在容差范围内确定
- 测试避免跨越外墙（reduce_crossing_wall）验证
- 测试小区域填充流量补偿（试验）（small_aera_infill_compensation）验证

### 1.9 桥接测试
- 测试桥接流量（bridge_flow）验证
- 测试内部桥接流量比例（internal_bridge_flow）验证
- 测试搭桥密度（bridge_density）验证
- 测试厚桥（thick_bridges）验证
- 测试内部搭桥用厚桥（thick_internal_bridges）验证
- 测试保留细微内部桥接（试验）（dont_filter_internal_bridges）验证
- 测试沉孔搭桥（counterbore_hole_bridging）验证

### 1.10 悬垂测试
- 测试识别悬空外墙（detect_overhang_wall）验证
- 测试悬垂可打印化（make_overhang_printable）验证
- 测试悬垂上的额外周长（extra_perimeters_on_overhangs）验证
- 测试反转奇数层悬垂方向（overhang_reverse）验证
- 测试悬垂优化（试验）（overhang_optimization）验证

## 2. 强度参数

### 2.1 墙测试
- 测试墙层数（wall_loops）验证
  - 验证方法：计算 ";TYPE INNER WALL" 和 ";TYPE OUTER WALL" 指令的数量
  - 特殊注意事项：
    1. 第一层墙打印速度可能与其他层不同
    2. 非第一层可能具有不同的内墙/外墙速度
- 测试交替添加额外内墙（alternate_extra_wall）验证
- 测试检查薄壁（detect_thin_wall）验证

### 2.2 顶/底壳测试
- 测试顶面图案（top_surface_pattern）验证
- 测试顶部壳体层数（top_shell_layers）验证
  - 验证方法：计算顶面、内部实心填充和内部桥接挤出类型的出现次数
  - 特殊注意事项：
    1. 如果没有稀疏填充，内部桥接类型可能不存在
    2. 目前使用具有这三种类型和单个顶面的固定模型
    3. 逻辑与顶部壳体厚度参数交织在一起
    4. TODO：为什么层数＜10 时，稀疏填充不会存在？
- 测试顶部壳体厚度（top_shell_thickness）验证
- 测试底面图案（bottom_surface_pattern）验证
- 测试底部壳体层数（bottom_shell_layers）验证
  - 验证方法：找到底面，向上计数内部实心填充层直到出现稀疏填充类型，记录底面+内部实心填充层的总数
- 测试底部壳体厚度（bottom_shell_thickness）验证
- 测试顶/底部实心填充/墙重叠率（top_bottom_infill_wall_overlap）验证

### 2.3 填充测试
- 测试稀疏填充密度（sparse_infill_density）验证
- 测试智能填充（ai_infill）验证
- 测试稀疏填充图案（sparse_infill_pattern）验证
- 测试稀疏填充锚线长度（infill_anchor）验证
- 测试填充锚线的最大长度（infill_anchor_max）验证
- 测试内部实心填充图案（internal_solid_infill_pattern）验证
- 测试启用间隙填充（gap_fill_target）验证
- 测试忽略微小间隙（filter_out_gap_fill）验证
- 测试填充/墙重叠（infill_wall_overlap）验证
- 测试顶部实心填充（external_infill_margin）验证

### 2.4 高级测试
- 测试稀疏填充方向（infill_direction）验证
- 测试实心填充方向（solid_infill_direction）验证
- 测试旋转实心填充方向（rotate_solid_infill_direction）验证
- 测试拉桥填充方向（bridge_angle）验证
- 测试稀疏填充最小阈值（minimum_sparse_infill_aera）验证
- 测试合并填充（infill_combination）验证
- 测试识别狭窄内部实心填充（detect_narrow_internal_solid_infill）验证
- 测试确保垂直外壳厚度（ensure_vertical_shell_thickness）验证

## 3. 特殊模式测试

### 3.1 其他测试
- 测试打印顺序（print_sequence）验证
  - 验证方法：检查层数据结构的连续性
  - 如果数据结构不是连续递增的，则为逐件打印模式
  - 如果连续，则为逐层打印模式

## 4. 测试结构

每个测试遵循以下结构：
1. 加载具有特定参数的 3MF 模型文件
2. 使用引擎切片并导出 G-code
3. 解析生成的 G-code
4. 验证参数是否符合预期值

测试夹具处理：
- 模型加载
- 切片和 G-code 生成
- 临时文件清理

## 5. 测试数据

测试数据组织在 `data/models` 目录中，按参数类别分为子目录：
- `quality/` - 质量参数测试的模型
- `strength/` - 强度参数测试的模型

每个模型文件都以指示正在测试的特定参数的方式命名：
- 格式：`{parameter_name}_{value}.{extension}`
- 示例：`layer_height_0.24mm.3mf`，`ironing_type_cube.3mf`

## 6. 测试执行

使用 pytest 和 `engine_params` 标记执行测试：
```
python -m pytest -m engine_params --slicer-exe="path/to/slicer/executable"
```

附加命令行选项：
- `--clean-gcode` - 自动清理生成的 G-code 文件
- `-v` - 详细输出以获取详细的测试信息

## 7. 预期结果

每个测试验证：
- 切片器是否正确解释输入参数
- 生成的 G-code 是否包含预期的参数值
- 参数值是否在可接受的容差范围内
- 是否正确处理边缘情况和边界条件

## 8. 测试分类

测试使用 pytest 标记进行分类：
- `@pytest.mark.engine_params` - 所有引擎参数测试的主要标记
- 特定类别的子标记：
  - `quality` - 质量参数测试
  - `strength` - 强度参数测试
  - 参数特定标记（例如，`layer_height`，`infill`）

## 9. 验证方法

基于 jobs-todo.csv 文件，验证方法包括：
- 3MF 切片和 G-code 分析
- 解析 `;LAYER_CHANGE`、`;TYPE:*`、`;WIPE_START`、`;WIPE_END` 等 G-code 注释
- 使用圆角矩形模型从挤出值计算线宽
- 检查特定的 G-code 命令
- 比较层结构和序列
- 分析几何属性
- 检查打印顺序检测的数据结构连续性

## 10. 特殊注意事项

- 所有参数在 G-code 中都应有 CONFIG_BLOCK
- 某些参数需要特殊处理（例如，role_based_wipe_speed）
- 第一层行为可能与其他层不同
- 某些测试可能需要特定的模型几何形状（例如，线宽计算的圆角矩形）
- 应为不兼容的测试配置生成警告消息
- 某些参数与其他参数有复杂的交互（例如，顶壳层数和顶壳厚度）
- 某些参数有特殊的验证规则（例如，象脚补偿层具有线性递减效果）