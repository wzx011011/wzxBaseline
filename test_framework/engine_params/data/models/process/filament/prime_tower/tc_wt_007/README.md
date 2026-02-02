# TC-WT-007: 回抽量和装填量计算 Test Models

## 概述
本目录包含用于测试TC-WT-007的3MF文件，验证在工具切换时回抽量和装填量是否使用正确的耗材参数。

## 测试场景
测试3种耗材组合，每种组合验证T0→T1工具切换时的参数正确性：

### 1. tc_wt_007_pla_tpu.3mf
- **T0 (PLA)**:
  - retraction_length = 5.0mm
  - retraction_extra_prime_amount = 0.0mm
- **T1 (TPU)**:
  - retraction_length = 8.0mm (软性耗材需要更长回抽)
  - retraction_extra_prime_amount = 0.5mm (补偿挤出)

### 2. tc_wt_007_pla_petg.3mf
- **T0 (PLA)**:
  - retraction_length = 5.0mm
  - retraction_extra_prime_amount = 0.0mm
- **T1 (PETG)**:
  - retraction_length = 6.0mm
  - retraction_extra_prime_amount = 0.2mm

### 3. tc_wt_007_petg_tpu.3mf
- **T0 (PETG)**:
  - retraction_length = 6.0mm
  - retraction_extra_prime_amount = 0.2mm
- **T1 (TPU)**:
  - retraction_length = 8.0mm
  - retraction_extra_prime_amount = 0.5mm

## 创建步骤
需要使用Creality Print手动创建这些3MF文件：

1. **启用双挤出机配置**:
   - 机型选择：支持双挤出的打印机（如CR-M4）
   - 启用擦拭塔：enable_prime_tower = true

2. **设置耗材参数**:
   - 按照上述参数分别配置T0和T1的回抽参数
   - 配置路径：Process Settings → Filament → Retraction
   - 关键参数：
     - retraction_length (回抽长度)
     - retraction_extra_prime_amount (额外装填量)

3. **模型设置**:
   - 使用简单模型（如多色立方体）
   - 为不同颜色分配不同的挤出机（T0/T1）
   - 确保模型能触发多次工具切换

4. **保存配置**:
   - 导出为3MF格式
   - 命名格式：tc_wt_007_<material1>_<material2>.3mf
   - 保存到本目录

## 验证要点
GCode应包含：
- CONFIG_BLOCK中正确的耗材参数
- T0/T1工具切换命令
- 切换前回抽使用from_tool的参数
- 切换后装填使用to_tool的参数 + extra_prime_amount

## 相关Bug
- #11460: PLA→TPU切换时用错参数回抽
- #11462: PLA→PETG切换时装填量错误
- #11463: PETG→TPU切换时参数混乱
- #13303, #13309, #13379: 额外装填量计算错误
- #13534, #13537, #13555: 工具参数获取问题
