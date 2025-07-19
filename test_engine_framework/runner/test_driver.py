import pytest
import json
import subprocess
import os
from pathlib import Path

# 根目录，例如 test_framework/
ROOT = Path(__file__).resolve().parent.parent

# C++ Catch2 测试可执行文件路径
EXE = ROOT / "Engine" /"Debug"/ "Engine_tests"

# 遍历所有 cases/*/*.json 文件
CASES = list(ROOT.glob("cases/*/*.json"))

def get_catch_tag(case_path: Path) -> str:
    """从路径推导 Catch2 测试 tag，例如 'cases/infill/case001.json' -> '[infill]'"""
    return f"[{case_path.parent.name}]"

@pytest.mark.parametrize("case_path", CASES, ids=lambda p: f"{p.parent.name}/{p.stem}")
def test_case(case_path: Path):
    """每个 case 文件执行一次 C++ 测试程序"""
    case = json.loads(case_path.read_text())
    env = os.environ.copy()

    # 基本环境变量
    env["MODEL_PATH"] = str(ROOT / case["model_file"])
    env["CONFIG_PATH"] = str(ROOT / case["config_file"])

    # 注入所有 expected_XXX 变量
    for key, value in case.items():
        if key.startswith("expected_"):
            env[key.upper()] = str(value).lower()

    tag = get_catch_tag(case_path)

    # 执行 C++ 可执行测试程序，并传入 tag 过滤器
    print(f"\n▶ Running case: {case_path.name} (tag: {tag})")
    result = subprocess.run([str(EXE), tag], env=env, capture_output=True, text=True)

    print(result.stdout)
    if result.stderr:
        print("stderr:", result.stderr)

    # 判断是否成功
    assert result.returncode == 0, f"Test failed: {case_path.name}"
