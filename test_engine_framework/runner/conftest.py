# conftest.py
import re
import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALL_CASES = list((ROOT / "cases").rglob("*.json"))


# 用法示例

# pytest -q --tags geometry,slicing

# pytest -q --tags "geometry slicing"

# pytest -q --tags geometry --tags slicing
def pytest_addoption(parser):
    """注册命令行参数 --tags（可多值）"""
    parser.addoption(
        "--tags",
        action="append",  # 可多次传：--tags a --tags b
        default=[],  # 默认为空列表
        help=(
            "Run only cases whose parent folder (tag) matches any of the given tags. "
            "Repeat --tags or use comma/space separated values, e.g. "
            "--tags geometry --tags slicing  or  --tags geometry,slicing"
        ),
    )


@pytest.fixture(scope="session")
def selected_tag(pytestconfig) -> set[str]:
    """会话级 fixture，规范化 --tags 为 set[str]；若未提供则返回空集合"""
    raw = pytestconfig.getoption("tags")  # List[str] 来自 action="append"
    tokens = []
    for item in raw:
        # 兼容逗号、空白分隔：--tags "a,b c"
        tokens.extend(t for t in re.split(r"[,\s]+", item) if t)
    return set(tokens)  # 空集合表示未筛选


def _collect_tags_from_path_to_root(file_path: Path, root: Path) -> set[str]:
    """
    从 file_path 的父目录一路回溯到 root（不含 root 本身），
    收集每一级目录名作为标签。
    例：ROOT/cases/geometry/triangles/case_001.json
    -> {"cases", "geometry", "triangles"}
    """
    file_path = file_path.resolve()
    root = root.resolve()
    rel = file_path.relative_to(root)       # cases/geometry/triangles/case_001.json
    return set(rel.parts[:-1])              # 去掉文件名，只保留目录层级


@pytest.fixture(params=ALL_CASES, ids=lambda p: f"{p.parent.name}/{p.stem}")
def case_path(request, selected_tag) -> Path:
    """动态参数化的 fixture：支持多级目录作为标签并与 --tags 匹配（任一匹配即保留）"""
    path: Path = request.param
    # 从 path 回溯到 ROOT，收集多级标签
    CASE_ROOT = ROOT / "cases"
    path_tags = _collect_tags_from_path_to_root(path, CASE_ROOT)  # e.g. {"Geometry","triangles"}

    # 只有在用户传了 --tags 时才进行过滤；若两者无交集则跳过
    if selected_tag and selected_tag.isdisjoint(path_tags):
        pytest.skip(
            f"Skipping case '{path.name}' "
            f"(path tags: {sorted(path_tags)}) due to tag filter: {sorted(selected_tag)}"
        )
    return path