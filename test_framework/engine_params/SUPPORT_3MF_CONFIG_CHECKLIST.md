# 支撑参数 3MF 配置清单

配置路径：在 Creality Print 7.0 Beta 中打开 3MF → 右侧参数面板 → 支撑设置

⚠️ **重要提示**：
- 每个 3MF 文件名格式：`{参数名}_{期望值}.3mf`
- 配置完成后必须**重新导出**到相同路径覆盖原文件
- 建议按**参数组**批量配置，避免遗漏

---

## 一、support_basic（基础支撑）共 7 个参数

### 1. enable_support（启用支撑）
📁 `engine_params/data/models/process/support/support_basic/enable_support/`
- [ ] `enable_support_disabled.3mf` → 支撑：**关闭**
- [ ] `enable_support_enabled.3mf` → 支撑：**开启**

### 2. support_type（支撑类型）
📁 `engine_params/data/models/process/support/support_basic/support_type/`
- [ ] `support_type_normal_auto.3mf` → 支撑类型：**普通（自动）**
- [ ] `support_type_tree_auto.3mf` → 支撑类型：**树形（自动）**
- [ ] `support_type_normal_manual.3mf` → 支撑类型：**普通（手动）**
- [ ] `support_type_tree_manual.3mf` → 支撑类型：**树形（手动）**

### 3. support_style（支撑样式）
📁 `engine_params/data/models/process/support/support_basic/support_style/`
- [ ] `support_style_default.3mf` → 支撑样式：**默认**
- [ ] `support_style_grid.3mf` → 支撑样式：**网格**
- [ ] `support_style_snug.3mf` → 支撑样式：**贴合**
- [ ] `support_style_tree_slim.3mf` → 支撑样式：**树形（细**）
- [ ] `support_style_tree_strong.3mf` → 支撑样式：**树形（强**）
- [ ] `support_style_tree_hybrid.3mf` → 支撑样式：**树形（混合**）
- [ ] `support_style_organic.3mf` → 支撑样式：**有机**

### 4. support_threshold_angle（支撑阈值角度）
📁 `engine_params/data/models/process/support/support_basic/support_threshold_angle/`
- [ ] `support_threshold_angle_30.3mf` → 支撑阈值角度：**30°**（默认）
- [ ] `support_threshold_angle_45.3mf` → 支撑阈值角度：**45°**
- [ ] `support_threshold_angle_60.3mf` → 支撑阈值角度：**60°**

### 5. support_on_build_plate_only（仅在构建板上支撑）
📁 `engine_params/data/models/process/support/support_basic/support_on_build_plate_only/`
- [ ] `support_on_build_plate_only_disabled.3mf` → 仅构建板支撑：**关闭**
- [ ] `support_on_build_plate_only_enabled.3mf` → 仅构建板支撑：**开启**

### 6. support_critical_regions_only（仅关键区域支撑）
📁 `engine_params/data/models/process/support/support_basic/support_critical_regions_only/`
- [ ] `support_critical_regions_only_disabled.3mf` → 关键区域支撑：**关闭**
- [ ] `support_critical_regions_only_enabled.3mf` → 关键区域支撑：**开启**

### 7. support_remove_small_overhang（移除小悬垂）
📁 `engine_params/data/models/process/support/support_basic/support_remove_small_overhang/`
- [ ] `support_remove_small_overhang_disabled.3mf` → 移除小悬垂：**关闭**
- [ ] `support_remove_small_overhang_enabled.3mf` → 移除小悬垂：**开启**

---

## 二、support_raft（支撑底座）共 2 个参数

### 8. raft_layers（底座层数）
📁 `engine_params/data/models/process/support/support_raft/raft_layers/`
- [ ] `raft_layers_0.3mf` → 底座层数：**0**（关闭）
- [ ] `raft_layers_2.3mf` → 底座层数：**2**
- [ ] `raft_layers_4.3mf` → 底座层数：**4**

### 9. raft_contact_distance（底座接触距离）
📁 `engine_params/data/models/process/support/support_raft/raft_contact_distance/`
- [ ] `raft_contact_distance_0.1.3mf` → 接触距离：**0.1mm**（默认）
- [ ] `raft_contact_distance_0.2.3mf` → 接触距离：**0.2mm**

---

## 三、support_filament（支撑材料）共 3 个参数

### 10. support_filament（支撑材料选择）
📁 `engine_params/data/models/process/support/support_filament/support_filament/`
- [ ] `support_filament_0.3mf` → 支撑材料：**挤出机 0**
- [ ] `support_filament_1.3mf` → 支撑材料：**挤出机 1**

### 11. support_interface_filament（支撑接触面材料）
📁 `engine_params/data/models/process/support/support_filament/support_interface_filament/`
- [ ] `support_interface_filament_0.3mf` → 接触面材料：**挤出机 0**
- [ ] `support_interface_filament_1.3mf` → 接触面材料：**挤出机 1**

### 12. support_interface_not_for_body（接触面不用于主体）
📁 `engine_params/data/models/process/support/support_filament/support_interface_not_for_body/`
- [ ] `support_interface_not_for_body_disabled.3mf` → 接触面不用于主体：**关闭**
- [ ] `support_interface_not_for_body_enabled.3mf` → 接触面不用于主体：**开启**

---

## 四、support_advanced（高级支撑）共 8 个参数

### 13. support_interface_top_layers（顶部接触面层数）
📁 `engine_params/data/models/process/support/support_advanced/support_interface_top_layers/`
- [ ] `support_interface_top_layers_1.3mf` → 顶部接触层：**1**
- [ ] `support_interface_top_layers_2.3mf` → 顶部接触层：**2**（默认）
- [ ] `support_interface_top_layers_3.3mf` → 顶部接触层：**3**

### 14. support_interface_bottom_layers（底部接触面层数）
📁 `engine_params/data/models/process/support/support_advanced/support_interface_bottom_layers/`
- [ ] `support_interface_bottom_layers_1.3mf` → 底部接触层：**1**
- [ ] `support_interface_bottom_layers_2.3mf` → 底部接触层：**2**（默认）
- [ ] `support_interface_bottom_layers_3.3mf` → 底部接触层：**3**

### 15. support_interface_pattern（接触面图案）
📁 `engine_params/data/models/process/support/support_advanced/support_interface_pattern/`
- [ ] `support_interface_pattern_auto.3mf` → 接触面图案：**自动**
- [ ] `support_interface_pattern_rectilinear.3mf` → 接触面图案：**直线**
- [ ] `support_interface_pattern_concentric.3mf` → 接触面图案：**同心圆**
- [ ] `support_interface_pattern_rectilinear_interlaced.3mf` → 接触面图案：**直线（交错**）
- [ ] `support_interface_pattern_grid.3mf` → 接触面图案：**网格**
- [ ] `support_interface_pattern_monotonicline.3mf` → 接触面图案：**单调线**

### 16. support_interface_spacing（接触面间距）
📁 `engine_params/data/models/process/support/support_advanced/support_interface_spacing/`
- [ ] `support_interface_spacing_0.3mf` → 接触面间距：**0mm**（实心）
- [ ] `support_interface_spacing_0.3.3mf` → 接触面间距：**0.3mm**
- [ ] `support_interface_spacing_0.5.3mf` → 接触面间距：**0.5mm**（默认）

### 17. support_bottom_interface_spacing（底部接触面间距）
📁 `engine_params/data/models/process/support/support_advanced/support_bottom_interface_spacing/`
- [ ] `support_bottom_interface_spacing_0.3.3mf` → 底部间距：**0.3mm**
- [ ] `support_bottom_interface_spacing_0.5.3mf` → 底部间距：**0.5mm**（默认）

### 18. support_interface_loop_pattern（接触面环形图案）
📁 `engine_params/data/models/process/support/support_advanced/support_interface_loop_pattern/`
- [ ] `support_interface_loop_pattern_disabled.3mf` → 环形图案：**关闭**
- [ ] `support_interface_loop_pattern_enabled.3mf` → 环形图案：**开启**

### 19. support_interface_speed（接触面速度）
📁 `engine_params/data/models/process/support/support_advanced/support_interface_speed/`
- [ ] `support_interface_speed_60.3mf` → 接触面速度：**60mm/s**
- [ ] `support_interface_speed_80.3mf` → 接触面速度：**80mm/s**（默认）
- [ ] `support_interface_speed_100.3mf` → 接触面速度：**100mm/s**

### 20. support_interface_min_area（接触面最小面积）
📁 `engine_params/data/models/process/support/support_advanced/support_interface_min_area/`
- [ ] `support_interface_min_area_0.25.3mf` → 最小面积：**0.25mm²**（默认）
- [ ] `support_interface_min_area_5.3mf` → 最小面积：**5mm²**
- [ ] `support_interface_min_area_10.3mf` → 最小面积：**10mm²**
- [ ] `support_interface_min_area_20.3mf` → 最小面积：**20mm²**

---

## 五、support_tree（树形支撑）共 5 个参数

### 21. tree_support_branch_diameter（树形支撑分支直径）
📁 `engine_params/data/models/process/support/support_tree/tree_support_branch_diameter/`
- [ ] `tree_support_branch_diameter_2.3mf` → 分支直径：**2mm**（默认）
- [ ] `tree_support_branch_diameter_3.3mf` → 分支直径：**3mm**
- [ ] `tree_support_branch_diameter_5.3mf` → 分支直径：**5mm**

### 22. tree_support_branch_angle（树形支撑分支角度）
📁 `engine_params/data/models/process/support/support_tree/tree_support_branch_angle/`
- [ ] `tree_support_branch_angle_30.3mf` → 分支角度：**30°**
- [ ] `tree_support_branch_angle_45.3mf` → 分支角度：**45°**（默认）
- [ ] `tree_support_branch_angle_60.3mf` → 分支角度：**60°**

### 23. tree_support_wall_count（树形支撑壁数）
📁 `engine_params/data/models/process/support/support_tree/tree_support_wall_count/`
- [ ] `tree_support_wall_count_0.3mf` → 壁数：**0**（默认）
- [ ] `tree_support_wall_count_1.3mf` → 壁数：**1**
- [ ] `tree_support_wall_count_2.3mf` → 壁数：**2**

### 24. tree_support_branch_distance（树形支撑分支距离）
📁 `engine_params/data/models/process/support/support_tree/tree_support_branch_distance/`
- [ ] `tree_support_branch_distance_0.5.3mf` → 分支距离：**0.5mm**
- [ ] `tree_support_branch_distance_1.3mf` → 分支距离：**1mm**
- [ ] `tree_support_branch_distance_1.5.3mf` → 分支距离：**1.5mm**
- [ ] `tree_support_branch_distance_5.3mf` → 分支距离：**5mm**（默认）

### 25. tree_support_tip_diameter（树形支撑尖端直径）
📁 `engine_params/data/models/process/support/support_tree/tree_support_tip_diameter/`
- [ ] `tree_support_tip_diameter_0.6.3mf` → 尖端直径：**0.6mm**
- [ ] `tree_support_tip_diameter_0.8.3mf` → 尖端直径：**0.8mm**（默认）
- [ ] `tree_support_tip_diameter_1.3mf` → 尖端直径：**1mm**

---

## 配置流程建议

### 方法一：按参数组配置（推荐）
1. 打开所有 `support_basic` 组的 3MF（7 个文件）
2. 依次配置并导出（记得勾选清单）
3. 继续下一组...

### 方法二：按期望值批量配置
1. 先配置所有 "disabled/关闭" 类型（9 个文件）
2. 再配置所有 "enabled/开启" 类型（9 个文件）
3. 最后配置数值类型...

### 验证方法
配置完成后运行测试验证：
```powershell
$env:CREALITY_PRINTER_PATH = "C:\Program Files\Creality\Creality Print 7.0 Beta\CrealityPrint.exe"
$env:PYTHONPATH = "E:\wzx\C3DBaseline\test_framework"
pytest engine_params/case/params/process/test_support.py -v -p engine_params.pytest_engine_params
```

---

## 注意事项

⚠️ **枚举值格式说明**（当前已知问题）：
- JSON 期望值使用了 C++ 枚举名（如 `stNormalAuto`）
- G-code 实际输出小写格式（如 `normal(auto)`）
- **测试会失败**，需要后续修复校验函数的格式适配

⚠️ **布尔值格式说明**（当前已知问题）：
- JSON 期望值使用字符串（`"true"`/`"false"`）
- G-code 实际输出数字（`1`/`0`）
- **测试会失败**，需要后续修复校验函数的格式适配

✅ **数值参数**（角度、距离、层数等）：
- 格式匹配正确，配置后应能通过测试

---

**总计：73 个 3MF 文件需要配置**

🕐 **预计时间**：25-35 分钟（熟练操作后平均每个文件 20 秒）

💡 **技巧**：使用 Creality Print 的"另存为"功能比"导出"更快，直接覆盖原文件即可
