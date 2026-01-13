#!/usr/bin/env python3
"""
修复纯数字的 project_name，添加参数名前缀
例如: "99" -> "filament_shrinkage_compensation_z_99"
"""

import json
from pathlib import Path
from collections import defaultdict


def is_pure_numeric(name: str) -> bool:
    """检查是否为纯数字（包含小数点、负号、下划线）"""
    return name.replace('.', '').replace('-', '').replace('_', '').isdigit()


def fix_json_file(json_path: Path, dry_run: bool = True) -> dict:
    """修复单个JSON文件的纯数字命名"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'cases' not in data:
            return {'status': 'skipped', 'reason': 'no cases'}
        
        param_name = json_path.stem
        cases = data['cases']
        
        modified = False
        fixed_count = 0
        
        for case in cases:
            project_name = case.get('project_name', '')
            
            # 只处理纯数字命名
            if is_pure_numeric(project_name):
                # 生成新名称: param_name_数字
                new_name = f"{param_name}_{project_name}"
                
                if not dry_run:
                    case['project_name'] = new_name
                
                modified = True
                fixed_count += 1
        
        if modified and not dry_run:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        if modified:
            return {
                'status': 'fixed',
                'fixed_count': fixed_count,
                'param_name': param_name
            }
        else:
            return {'status': 'ok'}
            
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


def main():
    case_input_dir = Path(__file__).parent / 'data' / 'case_input'
    
    if not case_input_dir.exists():
        print(f"[ERROR] 目录不存在: {case_input_dir}")
        return
    
    print("=" * 80)
    print("阶段 1: 检查需要修复的文件 (dry-run)")
    print("=" * 80)
    
    all_files = list(case_input_dir.rglob('*.json'))
    files_to_fix = []
    stats = {
        'total': 0,
        'ok': 0,
        'needs_fix': 0,
        'skipped': 0,
        'error': 0,
        'total_fixes': 0
    }
    
    for json_file in sorted(all_files):
        stats['total'] += 1
        result = fix_json_file(json_file, dry_run=True)
        
        if result['status'] == 'ok':
            stats['ok'] += 1
        elif result['status'] == 'fixed':
            stats['needs_fix'] += 1
            stats['total_fixes'] += result['fixed_count']
            files_to_fix.append((json_file, result))
        elif result['status'] == 'skipped':
            stats['skipped'] += 1
        elif result['status'] == 'error':
            stats['error'] += 1
            print(f"[ERROR] 错误: {json_file.relative_to(case_input_dir)}")
            print(f"   {result['error']}\n")
    
    print(f"\n[统计]")
    print(f"  总文件数: {stats['total']}")
    print(f"  [OK] 无需修复: {stats['ok']}")
    print(f"  [FIX] 需要修复: {stats['needs_fix']}")
    print(f"  [SKIP] 跳过: {stats['skipped']}")
    print(f"  [ERROR] 错误: {stats['error']}")
    print(f"\n  总修复数: {stats['total_fixes']} 个 project_name")
    
    if stats['needs_fix'] == 0:
        print("\n[OK] 所有文件都正常，无需修复！")
        return
    
    # 显示需要修复的文件示例（前20个）
    print(f"\n需要修复的文件示例（前20个）:")
    for json_file, result in files_to_fix[:20]:
        rel_path = json_file.relative_to(case_input_dir)
        print(f"  [FILE] {rel_path}")
        print(f"     修复数量: {result['fixed_count']} 个")
    
    if len(files_to_fix) > 20:
        print(f"  ... 还有 {len(files_to_fix) - 20} 个文件")
    
    # 询问是否执行修复
    print("\n" + "=" * 80)
    response = input(f"是否执行修复？(yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("[CANCEL] 取消修复")
        return
    
    # 执行实际修复
    print("\n" + "=" * 80)
    print("阶段 2: 执行修复")
    print("=" * 80 + "\n")
    
    fixed_count = 0
    error_count = 0
    
    for json_file, _ in files_to_fix:
        rel_path = json_file.relative_to(case_input_dir)
        result = fix_json_file(json_file, dry_run=False)
        
        if result['status'] == 'fixed':
            print(f"[OK] {rel_path}")
            fixed_count += 1
        else:
            print(f"[ERROR] {rel_path}: {result.get('error', 'unknown')}")
            error_count += 1
    
    print("\n" + "=" * 80)
    print(f"  [OK] 成功修复: {fixed_count}")
    print(f"  [ERROR] 失败: {error_count}")
    print(f"\n[DONE] 完成！共修复 {fixed_count} 个文件")


if __name__ == '__main__':
    main()
