import pytest
import json
import subprocess
import os
from pathlib import Path
from typing import List
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

from utils import *

# 忽略这些键，不处理为环境变量
# IGNORE_KEYS = {"tags", "name"}
IGNORE_KEYS = {}

yaml_parser = YAML()
yaml_parser.preserve_quotes = True  # 保留引号和格式

DEV = True
ROOT = Path(__file__).resolve().parent.parent
EXE = ROOT / "engine" / "Debug" / "engine_tests"
ENV_YAML_PATH = ROOT / "runner" / "envs.yaml"

if DEV:
    ENV_YAML = load_env_yaml(yaml_parser, ENV_YAML_PATH) or CommentedMap()
    ENV_YAML.setdefault("tags", CommentedMap())


def test_case(case_path: Path):
    # # 直接跳过被过滤的标签，不在终端中显示
    # if case_path is None:
    #     return None

    case = json.loads(case_path.read_text())
    env = os.environ.copy()
    populate_env_from_case(env, case, IGNORE_KEYS, ROOT)
    tag = get_catch_tag(case_path)
    tag_name = case_path.parent.stem

    if DEV:
        changed = False
        case_keys = {k for k in case if k not in IGNORE_KEYS}
        tags = ENV_YAML.setdefault("tags", CommentedMap())
        for k in case_keys:
            if k not in tags.setdefault(tag_name, []):
                tags[tag_name].append(k)
                changed = True
        unused_keys = set(tags[tag_name]) - case_keys
        for k in unused_keys:
            tags[tag_name].remove(k)
            changed = True
        if changed:
            save_env_yaml(yaml_parser, ENV_YAML_PATH, ENV_YAML)
            print("\n同步更新 envs.yaml 中的 tags 字段。")

    print(f"\nRunning case: {case_path.name} (tag: {tag})")
    result = subprocess.run([str(EXE), tag], env=env, capture_output=True, text=True, encoding='utf-8')
    print(result.stdout)
    if result.stderr:
        print("stderr:", result.stderr)
    assert result.returncode == 0, f"Test failed: {case_path.name}"
