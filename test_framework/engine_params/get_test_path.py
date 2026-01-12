"""
快速查找测试用例路径的脚本
输入 project_name，输出完整的文件路径和测试命令
"""

import json
import os
from pathlib import Path


def find_test_case_paths(project_name: str):
    """根据 project_name 查找所有相关路径"""
    
    base_dir = Path(__file__).parent
    data_dir = base_dir / "data" / "case_input"
    case_dir = base_dir / "case" / "params"
    
    results = {
        "project_name": project_name,
        "full_path": None,
        "json_config": None,
        "3mf_file": None,
        "test_file": None,
        "test_function": None,
        "pytest_command": None,
        "expected_value": None
    }
    
    # 搜索所有 JSON 配置文件
    for json_file in data_dir.rglob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if "cases" in data:
                for case in data["cases"]:
                    if case.get("project_name") == project_name:
                        results["json_config"] = str(json_file)
                        results["expected_value"] = case.get("expected_value")
                        
                        # 构建完整路径: process.support.support_advanced.tree_support_wall_count_0
                        # JSON路径: data/case_input/process/support/support_advanced/tree_support_wall_count.json
                        relative_path = json_file.relative_to(data_dir)
                        path_parts = list(relative_path.parent.parts) + [project_name]
                        full_path = '.'.join(path_parts)
                        results["full_path"] = full_path
                        
                        # 构建 3MF 文件路径
                        mf_file = case.get("input_3mf")
                        if mf_file:
                            mf_path = json_file.parent / mf_file
                            results["3mf_file"] = str(mf_path)
                        
                        # 推断测试文件路径
                        # JSON路径: data/case_input/process/support/support_advanced/tree_support_wall_count.json
                        # 测试路径: case/params/process/support/support_advanced/test_tree_support_wall_count.py
                        test_relative = relative_path.parent / f"test_{relative_path.stem}.py"
                        test_file = case_dir / test_relative
                        
                        if test_file.exists():
                            results["test_file"] = str(test_file)
                            
                            # 推断测试函数名（从参数名提取）
                            # tree_support_wall_count_0 -> test_tree_support_wall_count
                            param_base = '_'.join(project_name.rsplit('_', 1)[:-1])  # 去掉最后的数字
                            test_func = f"test_{param_base}"
                            results["test_function"] = test_func
                            
                            # 构建 pytest 命令
                            results["pytest_command"] = (
                                f'$env:PYTHONPATH="E:\\wzx\\C3DBaseline\\test_framework"; '
                                f'pytest {test_file}::{test_func} -v -k "{project_name}"'
                            )
                        
                        return results
        except Exception as e:
            continue
    
    return results


def main():
    import sys
    
    if len(sys.argv) < 2:
        return
    
    project_name = sys.argv[1]
    results = find_test_case_paths(project_name)
    
    if results["full_path"]:
        print(results['full_path'])
    else:
        print("")


if __name__ == "__main__":
    main()
