TODO
####
src/slicerctl放客户端实现
####
src/slicerctl放GCodeParser解析器实现以及具体的检验函数（check结尾的文件）
####
该测试组的conftest实例化客户端（会话级）
####
case/params下面是真正的入口测试组函数，函数调用xxx_check.py的函数实现校验，本体test_xxx负责输入参数化（TODO，现在代码和输入耦合）和assert断言期望
####
data/case_input：TODO，日后复用metafunc的输入规则，存放metadata.json描述输入案例
####
data/models按测试组类别存放用于测试的.3mf文件和.gcode文件
####
output文件夹默认是由夹具自动管理的输出gcode文件，可用命令行--clean-gcode自动清理
####
在项目根目录使用python -m pytest -m engine_params --slicer-exe="D:\C3D_Automation\C3DSlicer\build_Release\src\Release\CrealityPrint.exe"类似的命令即刻启动测试