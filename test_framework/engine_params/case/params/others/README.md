# Skirt 参数测试用例

基于 `template_model.3mf` 模板自动生成的 skirt 参数测试套件。

## 完成状态

✅ **已完成所有测试基础设施**

- ✅ 6 个参数的 JSON 测试定义文件（16 个测试用例）
- ✅ 16 个 3MF 模型文件（从模板自动生成并配置参数）
- ✅ 6 个测试函数（test_skirt_type.py）
- ✅ 6 个 G-code 解析函数（skirt_type_check.py）
- ✅ pytest 参数化配置（使用 root conftest.py）

## 目录结构

```
engine_params/
├── data/
│   ├── case_input/
│   │   └── others/
│   │       └── skirt_type/         # Skirt 参数测试用例定义（6个JSON）
│   │           ├── skirt_type.json
│   │           ├── skirt_loops.json
│   │           ├── skirt_distance.json
│   │           ├── skirt_height.json
│   │           ├── skirt_speed.json
│   │           └── draft_shield.json
│   └── models/
│       └── others/
│           └── skirt_type/         # Skirt 参数测试模型文件（16个3MF）
│               ├── skirt_type_normal.3mf
│               ├── skirt_type_shield.3mf
│               ├── skirt_loops_1.3mf
│               ├── skirt_loops_2.3mf
│               ├── skirt_loops_3.3mf
│               ├── skirt_distance_3mm.3mf
│               ├── skirt_distance_6mm.3mf
│               ├── skirt_distance_12mm.3mf
│               ├── skirt_height_1.3mf
│               ├── skirt_height_3.3mf
│               ├── skirt_height_5.3mf
│               ├── skirt_speed_50.3mf
│               ├── skirt_speed_100.3mf
│               ├── skirt_speed_150.3mf
│               ├── draft_shield_false.3mf
│               └── draft_shield_true.3mf
├── case/
│   └── params/
│       └── others/
│           └── test_skirt_type.py  # 6个测试函数
├── src/
│   └── gcode/
│       └── others/
│           └── skirt_type_check.py # 6个解析函数
└── create_skirt_3mf_files.py       # 自动生成3MF文件的脚本
```

## 测试参数说明

### 1. skirt_type（Level 2 特征检测）
- **normal**: 普通裙边（只在首层）
- **shield**: 挡板/draft_shield（多层延伸）

### 2. skirt_loops（Level 1 配置对比）
- 裙边圈数：1, 2, 3

### 3. skirt_distance（Level 1 配置对比）
- 裙边与模型的距离：3mm, 6mm, 12mm

### 4. skirt_height（Level 1 配置对比）
- 裙边高度（层数）：1, 3, 5

### 5. skirt_speed（Level 1 配置对比）
- 裙边速度（通过 initial_layer_speed）：50mm/s, 100mm/s, 150mm/s

### 6. draft_shield（Level 2 特征检测）
- 是否启用挡板：disabled (false), enabled (true)

## 运行测试

**注意**：测试需要使用切片器路径 `C:/Program Files/Creality/Creality Print 7.0 Beta/CrealityPrint.exe`

### 运行所有 skirt 参数测试
```powershell
pytest engine_params/case/params/others/test_skirt_type.py -v
```

### 运行单个参数的测试
```powershell
# 测试 skirt_type 参数
pytest engine_params/case/params/others/test_skirt_type.py::test_skirt_type -v

# 测试 skirt_loops 参数
pytest engine_params/case/params/others/test_skirt_type.py::test_skirt_loops -v

# 测试 skirt_distance 参数
pytest engine_params/case/params/others/test_skirt_type.py::test_skirt_distance -v
```

### 运行单个测试用例
```powershell
# 测试 skirt_loops=1 的用例
pytest engine_params/case/params/others/test_skirt_type.py::test_skirt_loops[skirt_loops_1] -v
```

### 收集测试（不执行）
```powershell
pytest engine_params/case/params/others/test_skirt_type.py --collect-only
```

## 工作原理

1. **测试框架使用 root conftest.py 的参数化逻辑**：
   - 从 `case_input/others/skirt_type/{param_name}.json` 读取测试用例
   - 构建 3MF 文件路径：`models/others/skirt_type/{filename}.3mf`
   - 调用 `slice_and_export` fixture 触发实时切片

2. **slice_and_export fixture 流程**：
   - 读取 3MF 文件（已包含配置的参数值）
   - 调用 Bambu Studio API 进行切片
   - 导出 G-code 文件到临时目录
   - 返回 G-code 文件路径给测试函数

3. **测试函数验证逻辑**：
   - 接收切片生成的 G-code 路径
   - 调用对应的 parser 函数（如 `parse_skirt_loops`）
   - 验证检测结果与期望值是否一致

## 3MF 文件生成

所有 3MF 文件已通过 `create_skirt_3mf_files.py` 脚本从 `template_model.3mf` 自动生成。

脚本工作流程：
1. 读取 `template_model.3mf` 模板文件
2. 解压 3MF（ZIP 格式）
3. 修改内部配置文件（.ini 格式）设置对应参数
4. 重新打包为 3MF 文件
5. 保存到 `models/others/skirt_type/` 目录

如需重新生成：
```powershell
python engine_params\create_skirt_3mf_files.py
```

## 参数映射说明

| 测试参数 | 3MF 配置参数 | 说明 |
|---------|-------------|------|
| skirt_type | draft_shield | disabled=normal, enabled=shield |
| skirt_loops | skirt_loops | 直接映射 |
| skirt_distance | skirt_distance | 直接映射 |
| skirt_height | skirt_height | 直接映射 |
| skirt_speed | initial_layer_speed | skirt 使用初始层速度 |
| draft_shield | draft_shield | 直接映射 |

## 下一步

测试框架已完成，可以开始执行测试：

1. **运行初始测试**：`pytest engine_params/case/params/others/test_skirt_type.py -v`
2. **查看测试结果**：检查哪些测试通过，哪些失败
3. **调整阈值**（如需要）：根据实际 G-code 输出调整 `skirt_type_check.py` 中的检测逻辑
4. **验证 Level 2 检测**：特别关注 `skirt_type` 和 `draft_shield` 的特征检测逻辑

## 故障排查

### 测试收集失败
```powershell
# 检查 JSON 文件是否存在
Get-ChildItem engine_params\data\case_input\others\skirt_type\*.json

# 检查 3MF 文件是否存在
Get-ChildItem engine_params\data\models\others\skirt_type\*.3mf
```

### 切片失败
- 确保 Bambu Studio 服务正在运行
- 检查 3MF 文件是否损坏（可用 Bambu Studio 手动打开验证）

### 检测逻辑失败
- 查看测试输出中的 `details` 字段，包含详细的检测信息
- 根据实际 G-code 特征调整 `skirt_type_check.py` 中的阈值
