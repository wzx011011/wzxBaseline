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