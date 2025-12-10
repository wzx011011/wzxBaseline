# engine_params/testing_utils/caseio.py
from __future__ import annotations
import json
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Tuple

# ---------------- 基础路径工具 ----------------

def repo_root(start: Path) -> Path:
    p = start.resolve()
    for q in [p, *p.parents]:
        if (q / "test_framework").exists():
            return q
    return p.parents[2]

def case_json_path(repo: Path, module_: str, group: str, param_name: str) -> Path:
    """JSON: test_framework/engine_params/data/case_input/<module>/<group>/<param_name>.json"""
    base = (repo / "test_framework" / "engine_params" / "data" / "case_input" / module_ / group)
    direct = base / f"{param_name}.json"
    if direct.exists():
        return direct
    # 如果存在子分类目录（如 module/group/<subgroup>/<param>.json），尝试在子目录中查找
    if base.exists():
        matches = list(base.rglob(f"{param_name}.json"))
        if matches:
            return matches[0]
    # 返回预期路径（不存在时，调用者会抛出 FileNotFound）
    return direct

def model_or_baseline_path(repo: Path, module_: str, group: str, param_name: str, filename: str) -> Path:
    """
    3MF 与 GCODE 都在：
    test_framework/engine_params/data/models/<module>/<group>/<param_name>/<filename>
    """
    expected = (repo / "test_framework" / "engine_params" / "data" / "models"
            / module_ / group / param_name / filename).resolve()
    if expected.exists():
        return expected
    # 容错：如果文件不在预期位置，尝试在 models/ 下全局查找相同文件名的候选项
    models_root = (repo / "test_framework" / "engine_params" / "data" / "models")
    matches = list(models_root.rglob(filename)) if models_root.exists() else []
    if matches:
        return matches[0].resolve()
    return expected

# ---------------- 元信息推断 ----------------

def infer_module_and_group_from_file(file_path: Path) -> Tuple[str, str]:
    """
    约定：engine_params/case/params/<module>/<group>_*.py
    """
    fp = file_path.resolve()
    parts = list(fp.parts)
    try:
        i = parts.index("params")
        module_name = parts[i + 1]
        stem = Path(parts[i + 2]).stem  # e.g. line_width_check
    except (ValueError, IndexError):
        raise RuntimeError(f"无法从路径提取 module/group：{fp}")
    group = stem.removeprefix("test_")
    return module_name, group

def param_name_from_test_func_name(func_name: str) -> str:
    return func_name[5:] if func_name.startswith("test_") else func_name

# ---------------- JSON 读取/校验 ----------------

def load_cases_json(json_path: Path) -> List[dict]:
    if not json_path.exists():
        raise FileNotFoundError(f"用例 JSON 不存在：{json_path}")
    data = json.loads(json_path.read_text(encoding="utf-8"))
    cases = data.get("cases", [])
    if not isinstance(cases, list):
        raise ValueError(f"{json_path} 顶层必须包含 'cases' 列表")
    return cases

# ---------------- 通用参数构建 ----------------

def normalize_case_for_fixture(
    case: dict, *, repo: Path, module_: str, group: str, param_name: str
) -> dict:
    """
    JSON 里的 input_3mf 只写文件名，这里映射为绝对 3MF 路径：
    models/<module>/<group>/<param_name>/<filename>
    """
    if "project_name" not in case:
        raise ValueError(f"case 缺 'project_name': {case}")
    if "input_3mf" not in case:
        raise ValueError(f"case 缺 'input_3mf': {case}")
    filename = str(case["input_3mf"])
    abs_model = model_or_baseline_path(repo, module_, group, param_name, filename)
    newc = dict(case)
    newc["input_3mf"] = str(abs_model)
    return newc

def pick_expected_values(case: dict, expected_param_names: Iterable[str]) -> List[object]:
    values = []
    for name in expected_param_names:
        if name not in case:
            raise ValueError(f"case 缺期望字段 '{name}': {case}")
        values.append(case[name])
    return values

Resolver = Callable[[Path, str, str, str, object], object]
# 解析器签名： (repo, module, group, param_name, raw_value) -> resolved_value

def resolve_extra_params(
    case: dict,
    extra_param_names: Iterable[str],
    *,
    repo: Path,
    module_: str,
    group: str,
    param_name: str,
    resolvers: Dict[str, Resolver] | None = None,
) -> List[object]:
    resolvers = resolvers or {}
    out = []
    for name in extra_param_names:
        if name not in case:
            raise ValueError(f"case 缺字段 '{name}': {case}")
        raw = case[name]
        if name in resolvers:
            out.append(resolvers[name](repo, module_, group, param_name, raw))
        else:
            out.append(raw)
    return out
