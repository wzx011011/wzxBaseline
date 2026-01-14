# 前置准备

## 1. 安装依赖

```bash
pip install -r requirements.txt
```

## 2. 设置环境变量

执行脚本 test_framework\docs\generate_env.py，生成 .env 文件，配置切片器路径等环境变量。

## 3. 手动配置C3DSlicer工程路径

## 示例 Prompt

### 示例 1：简单对比型参数（L1 级别）
```
一级分类为 printer
请帮我添加一个 prime_tower_brim_width 参数的测试用例：
1. 使用的策略用 printer_parameters_validation.md 文件总结的策略
2. 使用 generate_3mf.py 批量生成 3MF 文件
3. 目录结构：放在 printer/{分类} 下
4. 校验逻辑：简单对比型（L1），对比配置值与期望值
5. 测试用例：设计 2-3 个不同值的用例
6. 执行测试验证
```

### 示例 2：复杂校验型参数（L2/L3 级别）
```
一级分类为 process
请帮我添加一个 wall_sequence 参数的测试用例：
1. 使用的策略用 process_parameters_validation.md 文件总结的策略
2. 使用 generate_3mf.py 批量生成 3MF 文件
3. 目录结构：放在 process/quality/wall_and_surfaces 下
4. 校验逻辑：复杂校验型（L2），需要解析 G-code 中的 TYPE 标记顺序
5. 测试用例：设计 3 个不同打印顺序的用例
6. 执行测试验证
```

### 示例 3：完整工作流
```
请帮我为 small_area_infill_flow_compensation 参数添加测试用例：
1. 查询 process_parameters_validation.md 确认验证策略（L1 - CONFIG_BLOCK）
2. 创建 JSON 配置文件（标准格式）
3. 使用 generate_3mf.py 批量生成 3MF 文件（根据 JSON 中的 cases 自动生成）
4. 在 wall_and_surfaces_check.py 中添加 parse_small_area_infill_flow_compensation()
5. 在 test_wall_and_surfaces.py 中添加 test_small_area_infill_flow_compensation()
6. 运行测试验证
```

## 3MF 文件生成工具

### generate_3mf.py（推荐，批量生成）
根据 JSON 配置文件批量生成所有测试用例的 3MF 文件：
```bash
cd engine_params
python generate_3mf.py --json-file data/case_input/{path}/{param}.json
```
- 自动读取 JSON 中的 `param_name` 和每个 case 的配置值
- 自动创建模型目录并生成所有 3MF 文件
- 支持 `--dry-run` 预览将要生成的文件

### modify_3mf_params.py（单个文件生成）
生成单个 3MF 文件：
```bash
python modify_3mf_params.py --param {参数名}={值} --project-name {项目名}
```

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

2. **目录结构**： **一级分类 是printer,filament,process之一**
   - 测试文件：engine_params/case/params/{一级分类}/{分类}/{test_组名称}.py
   - 校验函数：engine_params/src/gcode/{一级分类}/{分类}/{组名称}_check.py
   - JSON配置：engine_params/data/case_input/{一级分类}/{分类}/{组名称}/{参数名}.json
   - 模型目录：engine_params/data/models/{一级分类}/{分类}/{组名称}/{参数名}/参数名_期望值.3mf

3. **校验逻辑**：
   - 简单对比型（L1 级别）：仅对比 G-code 配置中的参数值与期望值是否一致
   - 复杂校验型（L2/L3 级别）：需要解析 G-code 中的挤出块、坐标等进行验证

4. **参数信息**（需要从源码中获取）：
   - 参数类型（coFloat/coInt/coBool/coEnum等）
   - 最小值/最大值
   - 默认值
   - 参数含义

5. **测试用例配置**（JSON格式）：
   ```json
   {
     "cases": [
       {
         "project_name": "用例描述",
         "input_3mf": "模型文件名.3mf",
         "expected_xxx": 期望值
       }
     ]
   }
   ```

6. **执行测试**：使用切片器路径 .env里面 CREALITY_PRINTER_PATH=C:\Program Files\Creality\Creality Print 7.0 Alpha\CrealityPrint.exe
   
7. **资料**：所有的参数结构在这里：printer_parameters_validation.md，filament_parameters_validation.md，process_parameters_validation.md
