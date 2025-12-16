
## 添加新参数测试用例的 Prompt 模板
请帮我添加一个 {参数名} 参数的测试用例，要求如下：

1. **参考 C3DSlicer 源码**：读取 E:\wzx\C3DSlicer\C3DSlicer 路径下的工程，了解该参数的定义和使用方式

2. **目录结构**： **一级分类 是printer,filament,process之一**
   - 测试文件：engine_params/case/params/{一级分类}/{分类}/{test_组名称}.py
   - 校验函数：engine_params/src/gcode/{一级分类}/{分类}/{组名称}_check.py
   - JSON配置：engine_params/data/case_input/{一级分类}/{分类}/{组名称}/{参数名}.json
   - 模型目录：engine_params/data/models/{一级分类}/{分类}/{组名称}/{参数名}/参数名_期望值.3mf

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


## 忽略测试用例 (ignored_tests.json)

某些测试用例可能因为硬件/软件版本差异、功能未实现或其他原因需要暂时跳过。使用 `engine_params/data/ignored_tests.json` 集中管理：

### 配置文件格式
```json
{
  "description": "忽略的测试用例列表 - 这些测试在运行时会被自动跳过",
  "ignored_tests": [
    {
      "test_path": "printer/multimaterial/test_multimaterial.py::test_extruders_count",
      "test_case": "extruders_count_1",
      "reason": "Creality Print 不输出 extruders_count 参数到配置块",
      "date_added": "2025-12-16"
    }
  ],
  "notes": [
    "test_path: 相对于 engine_params/case/params/ 的路径（支持 :: 指定函数）",
    "test_case: 可选，参数化测试的用例ID（如 'extruders_count_1'）",
    "reason: 忽略原因说明",
    "date_added: 添加日期（YYYY-MM-DD 格式）"
  ]
}
```

### 匹配规则
- **test_path**: 支持部分匹配（如 `multimaterial/test_multimaterial.py` 匹配所有相关测试）
- **test_case**: 指定时只跳过特定参数化用例，不指定则跳过整个函数的所有用例
- **函数名**: 使用 `::` 指定函数（如 `test_multimaterial.py::test_extruders_count`）

### 示例用法
```powershell
# 自动跳过 ignored_tests.json 中配置的用例
pytest engine_params/case/params/printer/multimaterial/test_multimaterial.py -v

# 输出示例：
# SKIPPED [1] ... 忽略: Creality Print 不输出 extruders_count 参数到配置块
```

### 最佳实践
1. **记录清晰原因**: 说明为什么跳过（硬件限制、版本差异、待修复bug等）
2. **定期审查**: 每次更新切片器或测试框架时检查是否还需要忽略
3. **限制使用**: 只在确实无法解决的情况下使用，避免隐藏真正的问题
4. **版本说明**: 在 `reason` 中注明适用的软件版本


## 示例 Prompt
一级分类为 printer
请帮我添加一个 prime_tower_brim_width 参数的测试用例：
1. 使用的策略用{一级分类}_parameters_validation.md文件总结的策略
2. 要准备哪些gcode或者3mf文件提前告诉我，需要的3mf从template_model.3mf拷贝
3. 目录结构：放在 {一级分类}/{分类} 下
4. 校验逻辑：简单对比型，对比配置值与期望值
5. 测试用例：设计 2-3 个不同值的用例
6. 执行测试验证




## 以前的文档 ##
TODO
####
src/slicerctl文件夹下放客户端实现。
####
src/slicerctl放GCodeParser解析器实现以及具体的检验函数（check结尾的文件）。
####
该测试组的conftest实例化客户端（会话级）。
case/params下面是真正的入口测试组函数，函数调用xxx_check.py的函数实现校验，本体test_xxx负责接收动态参数系统输入的参数（pytest_generate_tests生成）和assert断言期望。
####
  项目中约定俗成的命名规则（会影响文件的查找）以及调用路径：入口文件的命名为：engine_params/case/params/<module>/test_<group>.py，里面有具体的test_<parameter>函数,负责接收动态参数系统输入的参数（pytest_generate_tests生成）和assert断言期望，本身函数体内并不处理具体的校验逻辑，但会去调用engine_params/src/gcode/<module>/<group>_check.py里面的parse_<parameter>()函数，该函数实现了具体的解析逻辑。  
动态参数系统给测试入口函数注入的json文件路径为engine_params/data/case_input/<module>/<group>/<parameter>.json，里面存放了每个测试的数据。其中最重要的是[input_3mf]键，里面存放了3mf的文件名，当传递给测试入口函数的时候，会自动解析成绝对路径，例如：your_project_root_in_disk/test_framework/engine_params/data/models/<module>/<group>/<parameter>/your_3mf.3mf。  
有些测试需要基准轮廓，json文件中存放基准文件的键为[baseline_gcode]，同样输入文件名即可。
####
data/models按测试组类别和存放用于测试的.3mf文件和.gcode文。
####
output文件夹默认是由夹具自动管理的输出gcode文件，可用命令行--clean-gcode自动清理。
####
在项目根目录使用python -m pytest -m engine_params --slicer-exe="D:\C3D_Automation\C3DSlicer\build_Release\src\Release\CrealityPrint.exe"类似的命令即刻启动测试。