from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
from pathlib import Path
import json

def load_env_yaml(yaml_parser: YAML, yaml_path: Path):
    with open(yaml_path, 'r', encoding='utf-8') as f:
        return yaml_parser.load(f)


# 这个空行不起作用，不知道为什么
def add_blank_lines_between_top_keys(data: CommentedMap):
    """在每个顶层 key 之间插入空行"""
    if not isinstance(data, CommentedMap):
        return
    keys = list(data.keys())
    for i, key in enumerate(keys[1:], start=1):  # 从第二个 key 开始，在其前加空行
        data.yaml_set_comment_before_after_key(key, before='\n')


def save_env_yaml(yaml_parser: YAML, yaml_path: Path, data):
    add_blank_lines_between_top_keys(data)
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml_parser.dump(data, f)

# .json 文件的父目录就是 tag
def get_catch_tag(case_path: Path) -> str:
    """从路径推导 Catch2 测试 tag，例如 'cases/infill/case001.json' -> '[infill]'"""
    return f"[{case_path.parent.stem}]"

def matrix_to_env_string(matrix):
    """二维矩阵转换为字符串，用于写入环境变量"""
    return ';'.join(','.join(str(value) for value in row) for row in matrix)

def tensor_to_env_string(matrix):
    """
    将三维矩阵（多个 polyline）转为字符串格式，适合用作环境变量：
    [[x1,y1;x2,y2]; [x3,y3,x3z;x4,y4,z4]; ...]
    """
    polyline_strings = []
    for polyline in matrix:
        # 每个点用逗号连接，点与点之间用分号
        point_strings = ['{}'.format(','.join(map(str, point))) for point in polyline]
        polyline_str = '[' + ';'.join(point_strings) + ']'
        polyline_strings.append(polyline_str)
    return ''.join(polyline_strings)


def array_to_env_string(array):
    """
    将 array 转换为字符串格式，用于写入环境变量。
    输入: array = [x1, y1, z1, ...]
    输出: "x1,y1,z1..."
    """
    return ','.join(str(value) for value in array)

def populate_env_from_case(env: dict,
                           case: dict,
                           ignore: set[str],
                           test_root: Path):
    """
    根据 `case` 字典填充环境变量字典 `env`。

    - *_file   : 单文件路径
    - *_files  : 多文件路径（列表）
    - list     : 根据维度判定（一维/二维/三维张量字符串）
    - dict 或包含 dict 的 list : 转为合法 JSON 字符串
    - bool/int/float/str      : 直接转为字符串（bool 小写）
    """
    for k, v in case.items():
        if k in ignore:
            continue

        # ---------- 文件路径 ----------
        if k.endswith("_file"):
            env[k.upper()] = str(v)

        elif k.endswith("_files"):
            new_v = [str(file) for file in v]
            env[k.upper()] = array_to_env_string(new_v)

        # ---------- 纯 dict ----------
        elif isinstance(v, dict):
            env[k.upper()] = json.dumps(v, ensure_ascii=False)

        # ---------- list ----------
        elif isinstance(v, list):
            # 如果列表中含有 dict，则整体按 JSON 字符串处理
            if any(isinstance(item, dict) for item in v):
                env[k.upper()] = json.dumps(v, ensure_ascii=False)
            # 三维张量
            elif all(isinstance(item, list) and
                     all(isinstance(subitem, list) for subitem in item)
                     for item in v):
                env[k.upper()] = tensor_to_env_string(v)

            # 二维矩阵
            elif all(isinstance(item, list) for item in v):
                env[k.upper()] = matrix_to_env_string(v)

            # 一维数组
            else:
                env[k.upper()] = array_to_env_string(v)

        # ---------- 基础类型 ----------
        elif isinstance(v, bool):
            env[k.upper()] = str(v).lower()
        elif isinstance(v, (int, float)):
            env[k.upper()] = str(v)
        elif isinstance(v, str):
            env[k.upper()] = v
        else:
            raise NotImplementedError(f"Unsupported type: {k} = {v}")

# def populate_env_from_case(env, case, ignore: set[str], test_root: Path):
#     for k, v in case.items():
#         if k in ignore:
#             continue
#         if k.endswith("_file"):
#             env[k.upper()] = str(test_root / v)
#
#         elif k.endswith("_files"):
#             new_v = [str(test_root / file) for file in v]
#             env[k.upper()] = array_to_env_string(new_v)
#             tmp = array_to_env_string(new_v)
#             pass
#
#         elif isinstance(v, list):
#             # 三维情况
#             if all(isinstance(item, list) and all(isinstance(subitem, list) for subitem in item) for item in v):
#                 env[k.upper()] = tensor_to_env_string(v)
#             # 二维情况
#             elif all(isinstance(item, list) for item in v):
#                 env[k.upper()] = matrix_to_env_string(v)
#             # 一维情况
#             elif all(not isinstance(item, list) for item in v):
#                 env[k.upper()] = array_to_env_string(v)
#
#
#         elif isinstance(v, bool):
#             env[k.upper()] = str(v).lower()
#         elif isinstance(v, (int, float)):
#             env[k.upper()] = str(v)
#         elif isinstance(v,str):
#             env[k.upper()] = v
#         else:
#             raise NotImplementedError(f"Unsupported type: {k} = {v}")
#
# # def filter_cases_by_tag(all_cases: List[Path], tag: str = None) -> List[Path]:
# #     if tag is None:
# #         return all_cases
# #     return [p for p in all_cases if p.parent.name == tag]