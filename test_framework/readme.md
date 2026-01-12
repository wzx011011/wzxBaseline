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


## 工程文档说明

### 核心文档 (test_framework/engine_params/)

#### **[readme.md](engine_params/readme.md)**
- **作用**：测试用例开发指南
- **内容**：
  - 添加新参数测试用例的 Prompt 模板
  - 忽略测试用例配置说明 (ignored_tests.json)
  - 示例 Prompt 和最佳实践
- **使用场景**：编写新测试用例时的参考手册

#### **[generate_3mf.py](engine_params/generate_3mf.py)**（已废弃，使用 modify_3mf_params.py 替代）
- **作用**：旧版 3MF 文件生成脚本
- **问题**：只修改配置文件末尾的键值对，不更新 JSON 中的参数值
- **状态**：不推荐使用

#### **[modify_3mf_params.py](engine_params/modify_3mf_params.py)**（推荐）
- **作用**：通用 3MF 参数修改工具
- **特性**：
  - ✅ 正确修改 JSON 格式配置
  - ✅ 自动更新 `different_settings_to_system` 标记数组
  - ✅ 支持批量修改多个参数
  - ✅ 保持 3MF 文件结构完整
- **用法**：
  ```bash
  # 单个参数
  python modify_3mf_params.py template.3mf output.3mf --param key=value
  
  # 多个参数
  python modify_3mf_params.py template.3mf output.3mf \
      --param small_area_infill_flow_compensation=1 \
      --param detect_thin_wall=0 \
      --param wall_loops=3
  ```
- **使用场景**：生成测试用例所需的 3MF 文件

#### **参数验证文档**

**[printer_parameters_validation.md](engine_params/printer_parameters_validation.md)**
- **作用**：打印机参数验证策略文档
- **内容**：printer 分类下所有参数的验证方法和测试策略
- **使用场景**：添加 printer 相关测试用例时查阅

**[filament_parameters_validation.md](engine_params/filament_parameters_validation.md)**
- **作用**：耗材参数验证策略文档
- **内容**：filament 分类下所有参数的验证方法和测试策略
- **使用场景**：添加 filament 相关测试用例时查阅

**[process_parameters_validation.md](engine_params/process_parameters_validation.md)**
- **作用**：工艺参数验证策略文档
- **内容**：process 分类下所有参数的验证方法和测试策略
- **使用场景**：添加 process 相关测试用例时查阅

### 文档使用流程

1. **规划阶段**：查看 `*_parameters_validation.md` 确定参数的验证策略（L1/L2/L3 级别）
2. **开发阶段**：参考 `readme.md` 中的模板编写测试代码
3. **文件生成**：使用 `modify_3mf_params.py` 生成测试所需的 3MF 文件

---

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

6. **执行测试**：使用切片器路径 C:/Program Files/Creality/Creality Print 7.0 Beta/CrealityPrint.exe
   
7. **资料**：所有的参数结构在这里：printer_parameters_validation.md，filament_parameters_validation.md，process_parameters_validation.md


## 示例 Prompt

### 示例 1：简单对比型参数（L1 级别）
```
一级分类为 printer
请帮我添加一个 prime_tower_brim_width 参数的测试用例：
1. 使用的策略用 printer_parameters_validation.md 文件总结的策略
2. 使用 modify_3mf_params.py 生成 3MF 文件
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
2. 使用 modify_3mf_params.py 生成 3MF 文件
3. 目录结构：放在 process/quality/wall_and_surfaces 下
4. 校验逻辑：复杂校验型（L2），需要解析 G-code 中的 TYPE 标记顺序
5. 测试用例：设计 3 个不同打印顺序的用例
6. 执行测试验证
```

### 示例 3：完整工作流
```
请帮我为 small_area_infill_flow_compensation 参数添加测试用例：
1. 查询 process_parameters_validation.md 确认验证策略（L1 - CONFIG_BLOCK）
2. 使用 modify_3mf_params.py 生成两个 3MF 文件：
   - enabled: --param small_area_infill_flow_compensation=1
   - disabled: --param small_area_infill_flow_compensation=0
3. 创建 JSON 配置文件（标准格式）
4. 在 wall_and_surfaces_check.py 中添加 parse_small_area_infill_flow_compensation()
5. 在 test_wall_and_surfaces.py 中添加 test_small_area_infill_flow_compensation()
6. 运行测试验证
```