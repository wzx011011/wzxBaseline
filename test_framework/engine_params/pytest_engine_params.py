# ==============================
# Pytest 命令行选项注册
# ==============================
def pytest_addoption(parser):
    grp = parser.getgroup("slicer")
    grp.addoption("--slicer-exe", help="CrealityPrint.exe 路径（优先于环境变量）")
    grp.addoption("--slicer-log", default="slicer_stdout.log")
    grp.addoption("--slicer-host", default="127.0.0.1")
    grp.addoption("--slicer-port", type=int, default=12345)
    grp.addoption("--slicer-timeout", type=float, default=30.0)
    grp.addoption("--slicer-inter-delay", type=float, default=0.20)
    grp.addoption("--slicer-retries", type=int, default=1)
    grp.addoption("--slicer-backoff", type=float, default=0.5)
    grp.addoption("--slicer-arg", action="append", default=[],
                  help="追加 CLI 参数（可多次）")
    grp.addoption("--slicer-args-str", default="",
                  help="一串空格分隔的 CLI 参数，会与 --slicer-arg 合并")

    # 自动管理输出的 gcode 目录相关
    grp.addoption("--gcode-root", default=r"D:\C3DBaseline\test_framework\engine_params\output",
                  help="G-code 输出根目录（默认使用临时目录）")
    grp.addoption("--gcode-scope", choices=["function", "module", "session"], default="module",
                  help="按哪个作用域自动分配输出子目录")
    grp.addoption("--clean-gcode", action="store_true",
                  default=False,
                  help="测试结束后清理生成的 G-code（默认不清理）")