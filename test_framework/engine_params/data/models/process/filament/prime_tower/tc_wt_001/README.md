# TC-WT-001 测试用例配置指南

## 文件位置
- **3MF 文件**: `test_framework/engine_params/data/models/process/filament/prime_tower/tc_wt_001/`
- **JSON 配置**: `test_framework/engine_params/data/case_input/process/filament/prime_tower/tc_wt_001.json`

## 已创建的 3MF 文件

### 1. tc_wt_001_vertical_0.5mm.3mf
**测试目的**: 垂直抬升 0.5mm
**需要手动设置的参数**:
- ✓ 启用擦拭塔 (`enable_prime_tower = 1`)
- ✓ 使用多色/多材料（至少2个喷头/材料）
- ✓ Z hop 高度: `z_hop[0] = 0.5` (mm)
- ✓ Z hop 方式: `z_hop_types = vertical` 或 `z_hop_types = 0`
- 推荐模型: 简单的立方体或圆柱，高度 10-20mm，确保有足够的层

### 2. tc_wt_001_vertical_1.0mm.3mf
**测试目的**: 垂直抬升 1.0mm（更高的抬升）
**需要手动设置的参数**:
- ✓ 启用擦拭塔 (`enable_prime_tower = 1`)
- ✓ 使用多色/多材料
- ✓ Z hop 高度: `z_hop[0] = 1.0` (mm)
- ✓ Z hop 方式: `z_hop_types = vertical` 或 `z_hop_types = 0`

### 3. tc_wt_001_contour_0.5mm.3mf
**测试目的**: 梯形抬升（沿轮廓）0.5mm
**需要手动设置的参数**:
- ✓ 启用擦拭塔 (`enable_prime_tower = 1`)
- ✓ 使用多色/多材料
- ✓ Z hop 高度: `z_hop[0] = 0.5` (mm)
- ✓ Z hop 方式: `z_hop_types = contour` 或 `z_hop_types = 1`
- **关键**: 此模式下抬升时会同时移动XY，而不是纯垂直

### 4. tc_wt_001_vertical_2.0mm.3mf (额外测试)
**测试目的**: 大幅抬升 2.0mm
**需要手动设置的参数**:
- ✓ 启用擦拭塔
- ✓ 使用多色/多材料
- ✓ Z hop 高度: `z_hop[0] = 2.0` (mm)
- ✓ Z hop 方式: `z_hop_types = vertical`

## 通用配置建议

### 擦拭塔设置
```
enable_prime_tower = 1
prime_tower_width = 60          # 擦拭塔宽度 (mm)
wipe_tower_x = 150              # 擦拭塔X坐标
wipe_tower_y = 150              # 擦拭塔Y坐标
```

### 多材料设置
```
single_extruder_multi_material = 1    # 单喷头多材料
extruders_count = 2                   # 至少2个材料
```

### 模型布置
- 确保模型与擦拭塔有一定距离（建议 >30mm）
- 模型尺寸: 建议 20x20x15mm 以上
- 至少有5层以上，确保有多次从模型到擦拭塔的转换

## 手动配置步骤

### 在 Creality Print 中:
1. **打开 3MF 文件**
2. **设置材料**:
   - 点击"材料"→选择至少2种不同颜色/材料
   - 为模型的不同部分分配不同材料
3. **启用擦拭塔**:
   - 打开"高级设置"
   - 找到"擦拭塔"/"Prime Tower"选项
   - 勾选"启用擦拭塔"
4. **配置 Z hop**:
   - 找到"Z hop"或"抬升高度"设置
   - 设置对应的高度（0.5mm / 1.0mm / 2.0mm）
   - 选择抬升方式（垂直 vertical / 梯形 contour）
5. **保存配置**:
   - 点击"项目"→"另存为"
   - 覆盖原 3MF 文件

## 验证配置是否正确

### 方法1: 查看预览
- 切片后，在预览中检查:
  - ✓ 是否生成了擦拭塔
  - ✓ 从模型到擦拭塔的路径有抬升
  - ✓ 抬升方式符合预期（垂直/梯形）

### 方法2: 检查 GCode
切片后导出 GCode，搜索关键特征:
```gcode
;TYPE:External perimeter   # 模型外壁
G1 E-5.0 F2400             # 回抽
G0 Z{z+hop} F300           # 抬升
G0 X{tower_x} Y{tower_y}   # 空走到擦拭塔
;TYPE:Wipe tower           # 擦拭塔
```

## 运行测试

### 使用 pytest (需要切片器连接):
```powershell
cd e:\wzx\C3DBaseline
$env:PYTHONPATH="e:\wzx\C3DBaseline\test_framework"
pytest test_framework/engine_params/case/params/process/filament/test_prime_tower_gcode.py::test_tc_wt_001 -v \
  --slicer-exe="C:/Program Files/Creality/Creality Print 7.0 Beta/CrealityPrint.exe"
```

### 使用离线 GCode 测试:
```powershell
# 1. 手动切片导出 GCode
# 2. 运行独立测试脚本
python test_framework/engine_params/case/params/process/filament/test_tc_wt_001_standalone.py
```

## 覆盖的 Bug

TC-WT-001 测试用例覆盖以下 5 个 bug:
- **10735**: 打完模型去擦拭塔外墙前无抬升
- **11182**: 打印完模型空驶去打擦拭塔外墙前没抬升
- **11193**: 打完模型去擦拭塔前的空走路径多余
- **11320**: 完成换料后空走到擦拭塔时空走路径逻辑错误
- **13826**: 擦拭塔到模型的抬升逻辑错误

## 预期测试结果

所有3个用例应该通过验证:
- ✓ 打完模型后有回抽动作
- ✓ 回抽后有 Z 抬升（高度符合配置）
- ✓ 抬升后空走到擦拭塔
- ✓ 抬升方式符合配置（垂直/梯形）
