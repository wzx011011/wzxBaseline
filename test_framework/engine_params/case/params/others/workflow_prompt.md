# Special Mode 参数测试用例生成工作流

## 工作流程概述

为 Special mode（Others 类别下）的参数生成完整的自动化测试用例，包括：测试文件、检测函数、JSON 配置、3MF 模型文件。

---

## 步骤 1: 分析参数列表

**输入**: 参数名称列表（如 slicing_mode, print_sequence, spiral_mode 等）

**输出**: 
- 每个参数的测试用例定义（参数值、预期行为）
- 参数分类（布尔型、枚举型、数值型）
- 检测策略（Level 1/2/3）

**示例参数**:
```python
slicing_mode: "regular" | "contour"
print_sequence: "by layer" | "by object"
spiral_mode: 0 | 1 (布尔型)
fuzzy_skin: "none" | "external" | "all"
fuzzy_skin_thickness: 0.1~0.5 (数值型)
```

---

## 步骤 2: 创建 JSON 配置文件

**路径**: `engine_params/data/case_input/others/special_mode/<param_name>.json`

**格式**:
```json
{
  "cases": [
    {
      "case_id": "<param>_<value>",
      "description": "描述",
      "model_file": "data/models/others/special_mode/<param>/<case_id>.3mf",
      "expected": {
        "<param_name>": <expected_value>
      }
    }
  ]
}
```

**示例**:
```json
{
  "cases": [
    {
      "case_id": "slicing_mode_contour",
      "description": "测试轮廓切片模式",
      "model_file": "data/models/others/special_mode/slicing_mode/slicing_mode_contour.3mf",
      "expected": {
        "slicing_mode": "contour"
      }
    }
  ]
}
```

---

## 步骤 3: 实现检测函数

**路径**: `engine_params/src/gcode/others/<category>_check.py`

**函数命名**: `parse_<param_name>(gcode_path, expected_value) -> (bool, actual_value, dict)`

**检测策略**:

### Level 1: 配置对比
从 G-code 注释中提取参数值
```python
def parse_<param>(gcode_path, expected_value):
    config = extract_config_from_gcode(gcode_path)
    config_value = config.get('<param_name>')
    detected_value = _normalize(config_value)
    ok = detected_value == expected_value
    return ok, detected_value, {...}
```

### Level 2: 特征检测
分析 G-code 路径特征（如 Z 轴连续性、路径偏移）
```python
def parse_spiral_mode(gcode_path, expected_value):
    z_increments = 0
    z_jumps = 0
    # 分析 Z 轴移动模式
    z_continuity = z_increments / total_samples
    detected = z_continuity > 0.8
    return detected == expected_value, detected, {...}
```

### Level 3: 路径分析
分析打印路径的几何特性（如模糊皮肤的偏移量）
```python
def parse_fuzzy_skin_thickness(gcode_path, expected_value):
    deviations = []
    # 计算路径偏移量
    avg_deviation = mean(deviations)
    ok = abs(avg_deviation - expected_value) < tolerance
    return ok, avg_deviation, {...}
```

**辅助函数**:
```python
def _normalize_to_float(val):
    if val.endswith('%'):
        return float(val[:-1])
    return float(val)

def _normalize_to_bool(val):
    return val in (1, "1", True, "true")
```

---

## 步骤 4: 编写测试函数

**路径**: `engine_params/case/params/others/test_<category>.py`

**函数模板**:
```python
@pytest.mark.parametrize("slice_and_export", 
    read_test_cases("others/special_mode/<param>.json"), 
    indirect=True)
def test_<param_name>(slice_and_export):
    """测试 <param_name> 参数"""
    gcode_path, case_config = slice_and_export
    expected_value = case_config["expected"]["<param_name>"]
    
    # 调用检测函数
    ok, actual_value, details = parse_<param_name>(
        gcode_path, expected_value
    )
    
    # 打印检测详情
    print(f"\n=== <param_name> 检测详情 ===")
    print(f"  期望值: {expected_value}")
    print(f"  检测值: {actual_value}")
    print(f"  检测方法: {details['detection_method']}")
    print(f"  结果消息: {details['message']}")
    print("=" * 45)
    
    # 断言
    assert ok, (
        f"<param_name> expected {expected_value}, "
        f"actual {actual_value}, details: {details}"
    )
```

---

## 步骤 5: 生成 3MF 文件脚本

**路径**: `engine_params/case/params/others/create_<category>_3mf_files.py`

**策略**: 从 `template_model.3mf` 复制文件，手动配置参数

```python
from pathlib import Path
import shutil

TEMPLATE_3MF = Path(__file__).parent.parent.parent.parent / "data" / "models" / "template_model.3mf"
TARGET_BASE_DIR = Path(__file__).parent.parent.parent.parent / "data" / "models" / "others" / "special_mode"

FILES = {
    "param_name": [
        "param_value1",
        "param_value2",
    ]
}

def copy_template_file(template_path, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(template_path, output_path)
    print(f"✓ 复制: {output_path.name}")

def main():
    for param_name, file_names in FILES.items():
        param_dir = TARGET_BASE_DIR / param_name
        for file_name in file_names:
            output_file = param_dir / f"{file_name}.3mf"
            copy_template_file(TEMPLATE_3MF, output_file)
```

**运行**: `python create_<category>_3mf_files.py`

**手动配置**: 在切片器 UI 中打开 3MF 文件，设置参数，保存覆盖

---

## 步骤 6: 运行测试

```bash
cd test_framework
$env:PYTHONPATH='e:\wzx\C3DBaseline\test_framework'
$env:CREALITY_PRINTER_PATH='C:\Program Files\Creality\Creality Print 7.0 Beta\CrealityPrint.exe'
pytest engine_params/case/params/others/test_special_mode.py -v
```

---

## 目录结构

```
engine_params/
├── case/params/others/
│   ├── test_special_mode.py          # 测试函数
│   └── create_special_mode_3mf_files.py  # 3MF 生成脚本
├── data/
│   ├── case_input/others/special_mode/
│   │   ├── slicing_mode.json         # 测试配置
│   │   ├── print_sequence.json
│   │   └── ...
│   └── models/others/special_mode/
│       ├── slicing_mode/
│       │   ├── slicing_mode_regular.3mf
│       │   └── slicing_mode_contour.3mf
│       └── ...
└── src/gcode/others/
    └── special_mode_check.py          # 检测函数
```

---

## 关键点总结

1. **JSON 配置**: 定义测试用例，指定模型文件和预期值
2. **检测函数**: 3 级检测策略（配置对比 → 特征检测 → 路径分析）
3. **测试函数**: 使用 pytest 参数化，打印详细检测信息
4. **3MF 文件**: 从模板复制，手动在 UI 中配置参数
5. **辅助函数**: 类型标准化（float/int/bool）

---

## 常见问题

**Q: 3MF 参数不生效？**
A: 某些参数需要手动在切片器 UI 配置后导出，不支持程序化修改

**Q: 如何选择检测策略？**
A: Level 1 优先 → 配置不可靠时用 Level 2/3

**Q: 如何处理百分比值？**
A: 解析时去掉 `%` 符号：`float(val[:-1]) if val.endswith('%') else float(val)`

**Q: 测试失败如何调试？**
A: 检查打印的检测详情，查看 `detection_method` 和 `message`
