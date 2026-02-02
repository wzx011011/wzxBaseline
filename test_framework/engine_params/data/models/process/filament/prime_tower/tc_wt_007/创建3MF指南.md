# TC-WT-007 3MF 文件创建指南

## 目标
创建3个测试用的3MF文件，用于验证工具切换时回抽/装填参数的正确性。

## 前置条件
- Creality Print 已安装: `E:\wzx\C3DSlicer\C3DSlicer\build_unified\src\RelWithDebInfo\CrealityPrint.exe`
- 支持双挤出的打印机配置（如CR-M4）

## 创建步骤

### 通用配置（所有3MF文件共用）

1. **打印机选择**:
   - 选择支持双挤出的打印机型号
   - 启用双挤出模式

2. **擦拭塔设置**:
   ```
   enable_prime_tower = 1
   prime_tower_width = 60
   wipe_tower_x = 170
   wipe_tower_y = 140
   ```

3. **模型准备**:
   - 使用简单的双色模型（建议20x20x10mm立方体）
   - **关键**：只需要有部分用T0打印，部分用T1打印即可触发工具切换
   - **不需要**每层交替，简单的左右分色或上下分色都可以
   - 例如：左半部分→T0 (PLA)，右半部分→T1 (TPU)
   - 或者：底部5层→T0，顶部5层→T1

---

### 文件1: tc_wt_007_pla_tpu.3mf

**T0 工具 (PLA) 配置**:
- Material: PLA
- Filament Settings → Setting Overrides → Retraction:
  - `Retraction length` (filament_retraction_length[0]) = 5.0
  - `Restart extra` (filament_retract_restart_extra[0]) = 0.0

**T1 工具 (TPU) 配置**:
- Material: TPU (软性材料)
- Filament Settings → Setting Overrides → Retraction:
  - `Retraction length` (filament_retraction_length[1]) = 8.0  ← 软性材料需要更长回抽
  - `Restart extra` (filament_retract_restart_extra[1]) = 0.5  ← 额外装填补偿

**模型设置**:
- 将模型分为两部分，分别分配给T0和T1
- 方式1：左右分色 - 左半部→T0 (PLA)，右半部→T1 (TPU)
- 方式2：上下分色 - 底部→T0 (PLA)，顶部→T1 (TPU)  
- 方式3：前后分色 - 前半部→T0，后半部→T1
- **目标**：确保至少触发1-2次T0→T1或T1→T0的工具切换

**保存路径**:
```
test_framework/engine_params/data/models/process/filament/prime_tower/tc_wt_007/tc_wt_007_pla_tpu.3mf
```

---

### 文件2: tc_wt_007_pla_petg.3mf

**T0 工具 (PLA) 配置**:
- Material: PLA
- Filament Settings → Setting Overrides → Retraction:
  - `Retraction length` = 5.0
  - `Restart extra` = 0.0

**T1 工具 (PETG) 配置**:
- Material: PETG
- Filament Settings → Setting Overrides → Retraction:
  - `Retraction length` = 6.0
  - `Restart extra` = 0.2

**模型设置**: 同上（T0/T1分色，任意分割方式）

**保存路径**:
```
test_framework/engine_params/data/models/process/filament/prime_tower/tc_wt_007/tc_wt_007_pla_petg.3mf
```

---

### 文件3: tc_wt_007_petg_tpu.3mf

**T0 工具 (PETG) 配置**:
- Material: PETG
- Filament Settings → Setting Overrides → Retraction:
  - `Retraction length` = 6.0
  - `Restart extra` = 0.2

**T1 工具 (TPU) 配置**:
- Material: TPU
- Filament Settings → Setting Overrides → Retraction:
  - `Retraction length` = 8.0
  - `Restart extra` = 0.5

**模型设置**: 同上（T0/T1分色，任意分割方式）

**保存路径**:
```
test_framework/engine_params/data/models/process/filament/prime_tower/tc_wt_007/tc_wt_007_petg_tpu.3mf
```

---

## 验证清单

创建完成后，确保每个3MF文件满足以下条件：

- [ ] 启用了擦拭塔 (enable_prime_tower = 1)
- [ ] 有T0/T1两个工具的配置
- [ ] Retraction length 参数正确设置
- [ ] Restart extra 参数正确设置
- [ ] 模型能触发工具切换（有多个颜色/材料）
- [ ] 文件保存在正确的目录

## 快速测试

创建完成后可以手动生成GCode验证：
```powershell
cd test_framework
$env:SLICER_PATH="E:\wzx\C3DSlicer\C3DSlicer\build_unified\src\RelWithDebInfo\CrealityPrint.exe"

# 测试文件1
& $env:SLICER_PATH --export-gcode --single-instance --output "output\tc_wt_007_pla_tpu.gcode" "engine_params\data\models\process\filament\prime_tower\tc_wt_007\tc_wt_007_pla_tpu.3mf"
```

检查生成的GCode中：
1. 搜索 `T1` - 应该能找到工具切换命令
2. 在T1前面应该有 `G1 E-5.0` (T0的回抽量)
3. 在T1后面应该有 `G1 E8.5` (T1的回抽量8.0 + 额外装填0.5)

## 常见问题

**Q: 如何在Creality Print中设置retraction参数？**
A: Filament Settings → Setting Overrides → Retraction → 找到对应的参数输入框（Retraction length 和 Restart extra）

**Q: 如何分配不同材料给模型？**
A: 右键模型 → Colors/Materials → 选择不同的挤出机

**Q: 如何确认参数已保存到3MF？**
A: 保存后用7-Zip打开3MF，检查Metadata/CrealityPrint.xml中的参数值

**Q: TPU的回抽量为什么是8.0？**
A: 软性材料需要更长的回抽距离来避免拉丝，这是行业常见配置
