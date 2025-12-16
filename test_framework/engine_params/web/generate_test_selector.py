"""
测试用例收集器 - 使用pytest收集所有测试用例
"""
import json
import re
import subprocess
import sys
import os
import time
import hashlib
from pathlib import Path

def get_directory_hash(directory):
    """计算目录内容的哈希值（用于检测变化）"""
    hash_md5 = hashlib.md5()
    try:
        for file_path in sorted(Path(directory).rglob("test_*.py")):
            if file_path.is_file():
                hash_md5.update(str(file_path).encode())
                hash_md5.update(str(file_path.stat().st_mtime).encode())
        return hash_md5.hexdigest()
    except Exception as e:
        return None

def check_cache_valid():
    """检查缓存是否有效"""
    cache_file = Path(__file__).parent / ".test_cache.json"
    json_file = Path(__file__).parent / "tests_data.json"
    params_dir = Path(__file__).parent.parent.parent / "engine_params" / "case" / "params"
    
    if not cache_file.exists() or not json_file.exists():
        return False
    
    try:
        with open(cache_file, 'r') as f:
            cache_info = json.load(f)
        
        current_hash = get_directory_hash(params_dir)
        if current_hash != cache_info.get('directory_hash'):
            return False
        
        # 检查缓存时间（超过24小时自动失效）
        cache_age = time.time() - cache_info.get('timestamp', 0)
        if cache_age > 86400:  # 24小时
            return False
        
        return True
    except Exception:
        return False

def save_cache_info(tests_data):
    """保存缓存信息"""
    cache_file = Path(__file__).parent / ".test_cache.json"
    params_dir = Path(__file__).parent.parent.parent / "engine_params" / "case" / "params"
    
    cache_info = {
        'timestamp': time.time(),
        'directory_hash': get_directory_hash(params_dir),
        'test_count': count_tests(tests_data)
    }
    
    with open(cache_file, 'w') as f:
        json.dump(cache_info, f)

def collect_tests():
    """使用pytest收集所有测试用例（包括参数化的）"""
    try:
        tests = {}
        params_dir = Path(__file__).parent.parent.parent / "engine_params" / "case" / "params"
        
        if not params_dir.exists():
            print(f"错误: 找不到目录 {params_dir}")
            return {}
        
        # 检查缓存
        if check_cache_valid():
            print("检测到有效缓存，使用现有数据（如需强制更新，请删除 .test_cache.json）")
            json_file = Path(__file__).parent / "tests_data.json"
            with open(json_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # 使用pytest收集测试用例
        print("正在运行 pytest --collect-only...")
        start_time = time.time()
        
        # 设置环境变量
        env = os.environ.copy()
        env['PYTHONPATH'] = str(Path(__file__).parent.parent.parent)
        
        result = subprocess.run(
            ["pytest", str(params_dir), "--collect-only"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
            encoding='utf-8',
            env=env
        )
        
        elapsed = time.time() - start_time
        print(f"pytest 收集完成，耗时: {elapsed:.2f} 秒")
        
        if result.returncode not in [0, 5]:  # 0=成功, 5=没有测试收集
            print(f"警告: pytest 返回代码 {result.returncode}")
            print(f"stderr: {result.stderr[:500]}")
        
        # 合并stdout和stderr（pytest有时会输出到stderr）
        output = result.stdout + '\n' + result.stderr
        lines = output.strip().split('\n')
        
        # 统计信息
        total_lines = len(lines)
        matched_lines = 0
        
        for line in lines:
            # 匹配格式: engine_params/case/params/printer/extruder_x/test_size.py::test_nozzle_diameter[case0]
            if '::' in line and 'engine_params/case/params' in line:
                matched_lines += 1
                # 提取文件路径和测试名称
                parts = line.split('::')
                if len(parts) >= 2:
                    file_path = parts[0].strip()
                    test_name = parts[1].strip()
                    
                    # 移除参数化标记 [case0], [case1] 等
                    test_name_clean = re.sub(r'\[.*?\]', '', test_name)
                    
                    # 解析路径: engine_params/case/params/printer/extruder_x/test_size.py
                    path_parts = Path(file_path).parts
                    if len(path_parts) < 5:  # 至少要有 engine_params/case/params/module/group
                        continue
                    
                    # 跳过前缀部分
                    idx = path_parts.index('params')
                    path_parts = path_parts[idx+1:]  # printer/extruder_x/test_size.py
                    
                    if len(path_parts) < 2:
                        continue
                    
                    module = path_parts[0]  # printer 或 process
                    
                    if module not in tests:
                        tests[module] = {}
                    
                    if len(path_parts) == 3:  # module/group/test_file.py
                        group = path_parts[1]
                        test_file_name = path_parts[2].replace('test_', '').replace('.py', '')
                        
                        if group not in tests[module]:
                            tests[module][group] = {}
                        if test_file_name not in tests[module][group]:
                            tests[module][group][test_file_name] = []
                        
                        # 添加测试名称（去重）
                        if test_name not in tests[module][group][test_file_name]:
                            tests[module][group][test_file_name].append(test_name)
                    
                    elif len(path_parts) == 4:  # module/group/subgroup/test_file.py
                        group = path_parts[1]
                        subgroup = path_parts[2]
                        test_file_name = path_parts[3].replace('test_', '').replace('.py', '')
                        
                        if group not in tests[module]:
                            tests[module][group] = {}
                        if subgroup not in tests[module][group]:
                            tests[module][group][subgroup] = {}
                        if test_file_name not in tests[module][group][subgroup]:
                            tests[module][group][subgroup][test_file_name] = []
                        
                        # 添加测试名称（去重）
                        if test_name not in tests[module][group][subgroup][test_file_name]:
                            tests[module][group][subgroup][test_file_name].append(test_name)
        
        # 打印收集统计
        print(f"\n收集统计:")
        print(f"  - 扫描行数: {total_lines}")
        print(f"  - 匹配测试: {matched_lines}")
        print(f"  - 模块数量: {len(tests)}")
        
        return tests
    
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return {}

def generate_html_with_data(tests_data):
    """读取HTML模板并嵌入测试数据"""
    html_file = Path(__file__).parent / "test_selector_template.html"
    
    if not html_file.exists():
        print(f"错误: 找不到 {html_file}", file=sys.stderr)
        return
    
    # 读取HTML内容
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # 将测试数据转换为JSON字符串
    json_data = json.dumps(tests_data, ensure_ascii=False, indent=2)
    
    # 替换模拟数据
    html_content = html_content.replace(
        'const mockTestData = {};',
        f'const mockTestData = {json_data};'
    )
    
    # 保存更新后的HTML
    output_file = Path(__file__).parent / "test_selector_hierarchical.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"测试选择器已生成: {output_file}")
    print(f"📊 收集到 {count_tests(tests_data)} 个测试用例")
    print(f"\n💡 请运行: python test_runner_server.py")
    print(f"   然后在浏览器打开: http://localhost:8888")

def count_tests(tests_data):
    """统计测试用例总数"""
    count = 0
    for module_data in tests_data.values():
        for group_data in module_data.values():
            if isinstance(group_data, dict):
                for item in group_data.values():
                    if isinstance(item, list):
                        count += len(item)
                    elif isinstance(item, dict):
                        for subitem in item.values():
                            if isinstance(subitem, list):
                                count += len(subitem)
            elif isinstance(group_data, list):
                count += len(group_data)
    return count

if __name__ == "__main__":
    # 设置标准输出编码为UTF-8
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    print("正在收集测试用例...")
    tests = collect_tests()
    
    if tests:
        # 保存为JSON文件（保存到web目录）
        json_file = Path(__file__).parent / "tests_data.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(tests, f, ensure_ascii=False, indent=2)
        
        # 保存缓存信息
        save_cache_info(tests)
        
        print(f"测试数据已保存: {json_file}")
        
        # 生成带数据的HTML
        generate_html_with_data(tests)
    else:
        print("未收集到测试用例")
        sys.exit(1)
