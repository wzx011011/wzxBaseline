"""
批量修复JSON命名问题：
1. 移除 input_3mf 中的路径前缀（只保留文件名）
2. 简化过长的 project_name（在不冲突的前提下）
"""

import json
from pathlib import Path
from collections import defaultdict
import re

def simplify_project_name(project_name: str, param_name: str) -> str:
    """
    简化 project_name，移除冗余的参数名前缀
    
    策略：
    - 如果 project_name 以 param_name_ 开头，尝试移除前缀
    - 保留语义清晰的部分
    """
    # 如果完全一样，不处理（避免变成空字符串）
    if project_name == param_name:
        return project_name
    
    # 如果以 param_name_ 开头，移除前缀
    prefix = f"{param_name}_"
    if project_name.startswith(prefix):
        simplified = project_name[len(prefix):]
        # 确保简化后不为空
        if simplified:
            return simplified
    
    return project_name

def extract_filename_from_path(input_3mf: str) -> str:
    """从可能包含路径的 input_3mf 中提取文件名"""
    # 将正斜杠和反斜杠统一处理
    input_3mf = input_3mf.replace('\\', '/')
    
    # 如果包含路径，只取文件名
    if '/' in input_3mf:
        return Path(input_3mf).name
    
    return input_3mf

def check_name_conflicts(cases: list, param_name: str) -> dict:
    """
    检查简化后的名称是否有冲突
    返回：{原名: 简化后的名, ...}
    """
    name_mapping = {}
    simplified_to_original = defaultdict(list)
    
    for case in cases:
        original = case.get('project_name', '')
        simplified = simplify_project_name(original, param_name)
        name_mapping[original] = simplified
        simplified_to_original[simplified].append(original)
    
    # 检查冲突：如果简化后的名称对应多个原始名称，保留原名
    for simplified, originals in simplified_to_original.items():
        if len(originals) > 1:
            # 有冲突，所有相关的原名都不简化
            for original in originals:
                name_mapping[original] = original
    
    return name_mapping

def fix_json_file(json_path: Path, dry_run: bool = False) -> dict:
    """
    修复单个JSON文件
    返回修改统计信息
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'cases' not in data:
            return {'status': 'skipped', 'reason': 'no cases'}
        
        param_name = json_path.stem
        cases = data['cases']
        
        # 检查是否需要修改
        needs_fix = False
        path_fixes = 0
        name_simplifications = 0
        
        # 先检查名称冲突
        name_mapping = check_name_conflicts(cases, param_name)
        
        for case in cases:
            # 检查 input_3mf 路径
            input_3mf = case.get('input_3mf', '')
            if '/' in input_3mf or '\\' in input_3mf:
                needs_fix = True
                path_fixes += 1
            
            # 检查 project_name 简化
            project_name = case.get('project_name', '')
            simplified = name_mapping.get(project_name, project_name)
            if simplified != project_name:
                needs_fix = True
                name_simplifications += 1
        
        if not needs_fix:
            return {'status': 'ok', 'path_fixes': 0, 'name_simplifications': 0}
        
        # 执行修复
        if not dry_run:
            for case in cases:
                # 修复路径
                if 'input_3mf' in case:
                    case['input_3mf'] = extract_filename_from_path(case['input_3mf'])
                
                # 简化名称
                if 'project_name' in case:
                    original = case['project_name']
                    case['project_name'] = name_mapping.get(original, original)
            
            # 写回文件
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        return {
            'status': 'fixed',
            'path_fixes': path_fixes,
            'name_simplifications': name_simplifications
        }
        
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def main():
    case_input_dir = Path('data/case_input')
    
    if not case_input_dir.exists():
        print(f"❌ 目录不存在: {case_input_dir}")
        return
    
    # 先运行 dry-run 检查
    print("=" * 80)
    print("阶段 1: 检查需要修复的文件 (dry-run)")
    print("=" * 80)
    
    all_files = list(case_input_dir.rglob('*.json'))
    stats = {
        'total': len(all_files),
        'ok': 0,
        'needs_fix': 0,
        'skipped': 0,
        'error': 0,
        'total_path_fixes': 0,
        'total_name_simplifications': 0
    }
    
    files_to_fix = []
    
    for json_file in all_files:
        result = fix_json_file(json_file, dry_run=True)
        
        if result['status'] == 'ok':
            stats['ok'] += 1
        elif result['status'] == 'fixed':
            stats['needs_fix'] += 1
            stats['total_path_fixes'] += result['path_fixes']
            stats['total_name_simplifications'] += result['name_simplifications']
            files_to_fix.append((json_file, result))
        elif result['status'] == 'skipped':
            stats['skipped'] += 1
        elif result['status'] == 'error':
            stats['error'] += 1
            print(f"❌ 错误: {json_file.relative_to(case_input_dir)}")
            print(f"   {result['error']}\n")
    
    print(f"\n📊 统计:")
    print(f"  总文件数: {stats['total']}")
    print(f"  ✅ 无需修复: {stats['ok']}")
    print(f"  🔧 需要修复: {stats['needs_fix']}")
    print(f"  ⏭️  跳过: {stats['skipped']}")
    print(f"  ❌ 错误: {stats['error']}")
    print(f"\n  📝 路径修复数: {stats['total_path_fixes']}")
    print(f"  ✂️  名称简化数: {stats['total_name_simplifications']}")
    
    if stats['needs_fix'] == 0:
        print("\n✅ 所有文件都正常，无需修复！")
        return
    
    # 显示需要修复的文件示例（前10个）
    print(f"\n需要修复的文件示例（前10个）:")
    for json_file, result in files_to_fix[:10]:
        rel_path = json_file.relative_to(case_input_dir)
        print(f"  📄 {rel_path}")
        if result['path_fixes'] > 0:
            print(f"     路径修复: {result['path_fixes']} 个")
        if result['name_simplifications'] > 0:
            print(f"     名称简化: {result['name_simplifications']} 个")
    
    if len(files_to_fix) > 10:
        print(f"  ... 还有 {len(files_to_fix) - 10} 个文件")
    
    # 询问是否执行修复
    print("\n" + "=" * 80)
    response = input(f"是否执行修复？(yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("❌ 取消修复")
        return
    
    # 执行实际修复
    print("\n" + "=" * 80)
    print("阶段 2: 执行修复")
    print("=" * 80)
    
    fixed_count = 0
    error_count = 0
    
    for json_file, _ in files_to_fix:
        result = fix_json_file(json_file, dry_run=False)
        
        if result['status'] == 'fixed':
            fixed_count += 1
            rel_path = json_file.relative_to(case_input_dir)
            print(f"✅ {rel_path}")
        elif result['status'] == 'error':
            error_count += 1
            rel_path = json_file.relative_to(case_input_dir)
            print(f"❌ {rel_path}: {result['error']}")
    
    print(f"\n" + "=" * 80)
    print(f"修复完成！")
    print(f"  ✅ 成功修复: {fixed_count}")
    print(f"  ❌ 失败: {error_count}")
    print("=" * 80)

if __name__ == '__main__':
    main()
