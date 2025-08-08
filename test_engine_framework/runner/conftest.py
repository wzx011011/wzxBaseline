"""
模块名称: conftest.py
功能描述: conftest.py 是 pytest 的约定俗成的配置文件，用来定义 fixture、钩子函数和插件代码。
    pytest 会自动递归搜索测试目录及其上层目录的所有 conftest.py，并加载里面的钩子和 fixture。
    如果把 pytest_addoption 函数放在其他文件（比如测试用例文件）里，pytest 不会自动调用，导致命令行参数无法识别。
    有 @pytest.fixture 装饰器的是自定义钩子函数（hook)
"""

import pytest
from pathlib import Path

# 递归获取所有测试用例json文件路径
ROOT = Path(__file__).resolve().parent.parent
ALL_CASES = list((ROOT / "cases").rglob("*.json"))

def pytest_addoption(parser):
    """注册命令行参数 --tag"""
    parser.addoption(
        "--tag",
        action="store",
        default=None,
        help="Only run tests with this tag.Default means filtering nothing."
    )

@pytest.fixture(scope="session")
def selected_tag(pytestconfig):
    """会话级fixture，获取命令行传入的--tag参数"""
    return pytestconfig.getoption("tag")

@pytest.fixture(params=ALL_CASES, ids=lambda p: f"{p.parent.name}/{p.stem}")
def case_path(request, selected_tag):
    """动态参数化的fixture，根据--tag过滤测试用例"""
    path: Path = request.param

    if selected_tag and path.parent.name != selected_tag:
        # return None
        pytest.skip(f"Skipping case '{path.name}' (tag: {path.parent.name}) due to tag filter: {selected_tag}")
    return path
