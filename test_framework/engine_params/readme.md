
## 添加新参数测试用例的 Prompt 模板
请帮我添加一个 {参数名} 参数的测试用例，要求如下：

1. **参考 C3DSlicer 源码**：读取 E:\wzx\C3DSlicer\C3DSlicer 路径下的工程，了解该参数的定义和使用方式

2. **目录结构**： **一级分类 是printer,filament,process之一**
   - 测试文件：engine_params/case/params/{一级分类}/{分类}/{test_文件名}.py
   - 校验函数：engine_params/src/gcode/{一级分类}/{分类}/{文件名}_check.py
   - JSON配置：engine_params/data/case_input/{一级分类}/{分类}/{子分类}/{参数名}.json
   - 模型目录：engine_params/data/models/{一级分类}/{分类}/{子分类}/{参数名}/

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
一级分类为 printer
请帮我添加一个 prime_tower_brim_width 参数的测试用例：
1. 使用的策略用{一级分类}_parameters_validation.md文件总结的策略
2. 要准备哪些gcode或者3mf文件提前告诉我，等我准备好再执行下一步
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