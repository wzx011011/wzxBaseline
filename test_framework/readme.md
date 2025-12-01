# 使用说明

## 1. 安装依赖

```bash
pip install -r requirements.txt
```

## 2. 设置环境变量

1. 设置 Creality 的 log 路径：

    ```bash
    set CREALITY_PRINTER_LOG_PATH=C:\Users\118909\AppData\Roaming\Creality\Creality Print\0.0 Alpha\log
    ```

2. 设置 Creality 的 exe 路径：

    ```bash
    set CREALITY_PRINTER_PATH=C:\Program Files\Creality\Creality Print 7.0 Beta\CrealityPrint.exe
    ```

---

## 自动化测试流程说明

### 1. 测试用例参数准备
- 每个测试函数（如 `test_internal_bridge_flow`）声明参数（如 `slice_and_export`, `expected_ratio`, `baseline_gcode`, `tol`）。
- 测试参数由 `pytest_generate_tests` 钩子自动从对应的 JSON 文件（如 `engine_params/data/case_input/quality/bridging/internal_bridge_flow.json`）读取，并参数化到测试函数。

---

### 2. 模型与基线文件准备
- JSON 文件中指定的 3MF 模型、基线 G-code 文件等，会自动解析为绝对路径，传递给测试用例。

---

### 3. G-code 生成（slice_and_export fixture）
- `slice_and_export` fixture 会：
  1. 调用 slicer 软件加载 3MF 模型。
  2. 触发切片操作。
  3. 导出 G-code 文件到指定路径。
  4. 使用 watchdog 等待 G-code 文件写入完成。
  5. 返回 G-code 路径给测试函数。

---

### 4. 测试函数执行
- 测试函数拿到参数（如 G-code 路径、期望值等），调用实际的解析/校验函数（如 `parse_internal_bridge_flow`），进行断言。

---

### 5. pytest 自动化管理
- pytest 负责发现测试、参数化、执行、收集结果。
- 你可以通过命令行参数（如 `--slicer-exe`）指定 slicer 路径，或用 `-m engine_params` 只运行带标记的测试。

---

### 6. 结果输出与清理
- pytest 输出测试结果。
- 可选参数（如 `--clean-gcode`）自动清理生成的 G-code 文件。

---

**总结：**  
你只需写好测试函数和参数 JSON，pytest + conftest.py 会自动完成参数注入、模型切片、G-code 生成、断言校验等全流程，无需手动干预。


## 添加新参数测试用例的 Prompt 模板
请帮我添加一个 {参数名} 参数的测试用例，要求如下：

1. **参考 C3DSlicer 源码**：读取 E:\wzx\C3DSlicer\C3DSlicer 路径下的工程，了解该参数的定义和使用方式

2. **目录结构**：
   - 测试文件：engine_params/case/params/{分类}/{test_文件名}.py
   - 校验函数：engine_params/src/gcode/{分类}/{文件名}_check.py
   - JSON配置：engine_params/data/case_input/{分类}/{子分类}/{参数名}.json
   - 模型目录：engine_params/data/models/{分类}/{子分类}/{参数名}/

3. **校验逻辑**：
   - 简单对比型：仅对比 G-code 配置中的参数值与期望值是否一致
   - 复杂校验型：需要解析 G-code 中的挤出块、坐标等进行验证

4. **参数信息**（需要从源码中获取）：
   - 参数类型（coFloat/coInt/coBool/coEnum等）
   - 最小值/最大值
   - 默认值
   - 参数含义

5. **测试用例配置**（JSON格式）：
   {
     "cases": [
       {
         "project_name": "用例描述",
         "input_3mf": "模型文件名.3mf",
         "expected_xxx": 期望值
       }
     ]
   }

6. **执行测试**：使用切片器路径 C:/Program Files/Creality/Creality Print 7.0 Beta/CrealityPrint.exe
   
7. **资料**：所有的参数结构在这里：process_parameters.md


## 示例 Prompt
请帮我添加一个 prime_tower_brim_width 参数的测试用例：
1. 使用的策略用multimaterial_others_validation_design.md文件总结的策略
2. 要准备哪些gcode或者3mf文件提前告诉我，等我准备好再执行下一步
3. 目录结构：放在 filament/prime_tower 分类下
4. 校验逻辑：简单对比型，对比配置值与期望值
5. 测试用例：设计 2-3 个不同值的用例
6. 执行测试验证