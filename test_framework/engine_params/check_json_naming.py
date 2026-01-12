import json
from pathlib import Path
import re

def check_json_naming(json_path: Path):
    """检查JSON文件的命名是否有冗余"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'cases' not in data:
            return None
        
        # 获取参数名（从文件路径中提取）
        param_name = json_path.stem
        
        issues = []
        for case in data['cases']:
            project_name = case.get('project_name', '')
            input_3mf = case.get('input_3mf', '')
            
            # 检查 project_name 是否包含重复的参数名前缀
            # 例如: cooling_slowdown_logic_cooling_slowdown_smart_zone
            if param_name in project_name:
                # 统计参数名出现次数
                count = project_name.count(param_name)
                if count > 1:
                    issues.append({
                        'type': 'duplicate_param_in_project_name',
                        'project_name': project_name,
                        'param_name': param_name,
                        'count': count
                    })
            
            # 检查 project_name 和 input_3mf 是否匹配
            expected_3mf = f"{project_name}.3mf"
            if input_3mf != expected_3mf:
                issues.append({
                    'type': 'name_mismatch',
                    'project_name': project_name,
                    'input_3mf': input_3mf,
                    'expected': expected_3mf
                })
            
            # 检查是否有过长的命名（超过3个下划线可能是冗余）
            underscore_count = project_name.count('_')
            if underscore_count > 4:
                issues.append({
                    'type': 'too_long',
                    'project_name': project_name,
                    'underscore_count': underscore_count
                })
        
        return issues if issues else None
        
    except Exception as e:
        return [{'type': 'error', 'message': str(e)}]

def main():
    case_input_dir = Path('data/case_input')
    
    all_issues = {}
    
    for json_file in case_input_dir.rglob('*.json'):
        issues = check_json_naming(json_file)
        if issues:
            rel_path = json_file.relative_to(case_input_dir)
            all_issues[str(rel_path)] = issues
    
    if not all_issues:
        print("✅ 所有JSON文件命名规范，无冗余问题")
        return
    
    print(f"发现 {len(all_issues)} 个文件有命名问题：\n")
    
    for file_path, issues in sorted(all_issues.items()):
        print(f"📄 {file_path}")
        for issue in issues:
            if issue['type'] == 'duplicate_param_in_project_name':
                print(f"  ⚠️  project_name 包含重复参数名:")
                print(f"      {issue['project_name']}")
                print(f"      参数名 '{issue['param_name']}' 出现 {issue['count']} 次")
            elif issue['type'] == 'name_mismatch':
                print(f"  ⚠️  project_name 和 input_3mf 不匹配:")
                print(f"      project_name: {issue['project_name']}")
                print(f"      input_3mf: {issue['input_3mf']}")
                print(f"      预期: {issue['expected']}")
            elif issue['type'] == 'too_long':
                print(f"  ⚠️  命名过长 ({issue['underscore_count']} 个下划线):")
                print(f"      {issue['project_name']}")
            elif issue['type'] == 'error':
                print(f"  ❌ 错误: {issue['message']}")
        print()

if __name__ == '__main__':
    main()
