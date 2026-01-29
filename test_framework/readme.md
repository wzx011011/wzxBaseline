# 切片引擎参数自动化测试框架

## 一、快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
```bash
cd test_framework
python generate_env.py
```
自动检测 CrealityPrint.exe 路径，生成 `.env` 文件。

### 3. 运行测试
```bash
$env:PYTHONPATH="e:\wzx\C3DBaseline\test_framework"
pytest engine_params/case/params/{path}/test_{name}.py::test_{param} -v
```

---

## 二、目录结构

```
engine_params/
├── data/
│   ├── case_input/{一级分类}/{分类}/{组名称}/{参数名}.json    # 测试配置
│   └── models/{一级分类}/{分类}/{组名称}/{参数名}/            # 3MF模型文件
│       ├── {参数名}_值1.3mf
│       ├── {参数名}_值2.3mf
│       └── baseline_值1.gcode                                # L3级别基线文件
├── src/gcode/{一级分类}/{分类}/{组名称}_check.py              # 校验函数
└── case/params/{一级分类}/{分类}/test_{组名称}.py             # 测试代码
```

**一级分类**：`printer` / `filament` / `process`

---

## 三、添加测试用例步骤

### Step 1: 创建 JSON 配置
```json
{
  "cases": [
    {
      "project_name": "参数名_值1",
      "input_3mf": "参数名_值1.3mf",
      "expected_value": 值1,
      "baseline_gcode": "baseline_值1.gcode"  // L3级别需要，用于对比基线
    },
    {
      "project_name": "参数名_值2", 
      "input_3mf": "参数名_值2.3mf",
      "expected_value": 值2
    }
  ]
}
```

### Step 2: 生成 3MF 文件
```bash
cd engine_params
python generate_3mf.py --json-file data/case_input/{path}/{param}.json
```

### Step 3: 编写校验函数 (`*_check.py`)
```python
def parse_{参数名}(gcode_path: Path) -> Any:
    """从 G-code 中解析参数值"""
    # L1: 从 CONFIG_BLOCK 提取
    # L2/L3: 解析 G-code 指令
    return actual_value
```

### Step 4: 编写测试函数 (`test_*.py`)
```python
@pytest.mark.engine_params
def test_{参数名}(slice_and_export: Path, expected_value):
    actual = parse_{参数名}(slice_and_export)
    assert actual == expected_value
```

### Step 5: 执行测试
```bash
pytest engine_params/case/params/{path}/test_{name}.py::test_{param} -v
```

---

## 四、校验级别说明

| 层次 | 名称 | 适用场景 | 复杂度 | 可靠性 |
|------|------|---------|--------|--------|
| Level 1 (L1) | 配置对比 | 简单值校验，直接从 G-code 配置注释读取 | 简单 | 快速预检 |
| Level 2 (L2) | 特征检测 | 开关型参数，检测 TYPE 标记是否存在 | 中等 | 效果验证 |
| Level 3 (L3) | 路径分析/基线对比 | 几何验证，需要分析实际打印路径 | 复杂 | 精确验证 |

---

## 五、工具脚本

| 脚本 | 用途 |
|------|------|
| `generate_env.py` | 自动检测环境，生成 .env 文件 |
| `generate_3mf.py` | 根据 JSON 批量生成 3MF 文件 |
| `modify_3mf_params.py` | 生成单个 3MF 文件 |
| `get_test_path.py` | 根据 project_name 查找完整路径 |

---

## 六、Prompt 模板

```
请帮我添加一个 {参数名} 参数的测试用例：

1. 一级分类：printer / filament / process
2. 参考源码：E:\wzx\C3DSlicer\C3DSlicer\src\libslic3r\PrintConfig.cpp
3. 参考策略：{一级分类}_parameters_validation.md
4. 校验级别：L1(简单对比) / L2(G-code解析) / L3(复杂逻辑)
5. 测试用例：设计 2-3 个不同值
6. 执行测试验证
```

---

## 七、自动化原理

```
JSON配置 → pytest_generate_tests 参数化
    ↓
3MF模型 → slice_and_export fixture 切片
    ↓
G-code → 校验函数解析 → 断言验证
```

pytest + conftest.py 自动完成：参数注入、模型切片、G-code 生成、断言校验。
