"""
批量为测试文件添加详细的预期值/实际值输出

使用方法：
python add_test_output.py
"""
import re
from pathlib import Path


def add_output_to_test_function(content: str, func_name: str, param_name: str) -> str:
    """为单个测试函数添加print输出"""
    
    # 匹配测试函数的pattern（包括函数定义到第一个assert）
    pattern = rf'(@pytest\.mark\.engine_params\s+def {func_name}\([^)]+\):\s+"""[^"]*"""\s+[^a]+ok, actual[^,]*, details[^=]+=\s+{param_name}\([^)]+\))'
    
    # 添加print输出的代码
    output_code = f'''
    
    print(f"\\n=== {param_name} 检测详情 ===")
    print(f"  预期值: {{expected_value}}")
    print(f"  实际值: {{actual}}")
    print(f"  检测方法: {{details.get('detection_method', 'N/A')}}")
    print(f"  结果: {{'✓ 通过' if ok else '✗ 失败'}}")
    print("=" * 50)
'''
    
    def replacer(match):
        return match.group(1) + output_code
    
    new_content = re.sub(pattern, replacer, content, flags=re.MULTILINE | re.DOTALL)
    
    return new_content


def process_test_file(file_path: Path) -> bool:
    """处理单个测试文件"""
    print(f"处理: {file_path}")
    
    content = file_path.read_text(encoding='utf-8')
    original_content = content
    
    # 查找所有测试函数和对应的parse函数
    test_funcs = re.findall(r'def (test_\w+)\(', content)
    
    modified = False
    for func_name in test_funcs:
        # 提取参数名（去掉test_前缀）
        param_name = func_name.replace('test_', '')
        
        # 检查是否已经有print输出
        if f'=== {param_name} 检测详情 ===' in content:
            print(f"  ✓ {func_name} 已有输出，跳过")
            continue
        
        # 检查函数是否调用了parse函数
        parse_func_pattern = rf'parse_{param_name}\('
        if not re.search(parse_func_pattern, content):
            print(f"  ? {func_name} 未找到对应的parse函数，跳过")
            continue
        
        # 添加输出
        content = add_output_to_test_function(content, func_name, f'parse_{param_name}')
        modified = True
        print(f"  + 添加输出到 {func_name}")
    
    # 保存修改
    if modified and content != original_content:
        file_path.write_text(content, encoding='utf-8')
        return True
    
    return False


def main():
    """主函数"""
    # 查找所有测试文件
    test_root = Path(__file__).parent / 'engine_params' / 'case' / 'params'
    test_files = list(test_root.rglob('test_*.py'))
    
    print(f"找到 {len(test_files)} 个测试文件\n")
    
    modified_count = 0
    for test_file in test_files:
        if process_test_file(test_file):
            modified_count += 1
        print()
    
    print(f"\n完成！修改了 {modified_count} 个文件")


if __name__ == '__main__':
    main()
