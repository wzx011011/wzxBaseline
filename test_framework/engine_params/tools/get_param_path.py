"""
根据参数名获取完整的测试路径

用法:
    python get_param_path.py small_area_infill_flow_compensation
    python get_param_path.py wall_sequence
    python get_param_path.py --search infill

输出格式: {一级分类}.{分类}.{组名称}.{参数名}
例如: process.quality.wall_and_surfaces.small_area_infill_flow_compensation
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Tuple


def find_param_in_json(json_file: Path) -> List[str]:
    """从 JSON 文件中提取参数名（expected_xxx 字段）"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if 'cases' not in data:
            return []
        
        # 提取所有 expected_xxx 键的参数名
        params = set()
        for case in data['cases']:
            for key in case.keys():
                if key.startswith('expected_'):
                    param_name = key.replace('expected_', '')
                    params.add(param_name)
        
        return list(params)
    except:
        return []


def search_param(param_name: str, case_input_dir: Path) -> List[Tuple[str, str, str, str]]:
    """
    搜索参数名对应的完整路径
    
    Returns:
        List[(一级分类, 分类, 组名称, 参数名)]
    """
    results = []
    
    # 遍历 case_input 目录结构
    # engine_params/data/case_input/{一级分类}/{分类}/{组名称}/{参数名}.json
    
    if not case_input_dir.exists():
        return results
    
    for level1_dir in case_input_dir.iterdir():
        if not level1_dir.is_dir():
            continue
        
        level1 = level1_dir.name  # printer, filament, process
        
        for level2_dir in level1_dir.iterdir():
            if not level2_dir.is_dir():
                continue
            
            level2 = level2_dir.name  # 例如: quality, strength, speed
            
            for group_dir in level2_dir.iterdir():
                if not group_dir.is_dir():
                    continue
                
                group = group_dir.name  # 例如: wall_and_surfaces
                
                # 检查该组下的 JSON 文件（直接从文件名匹配）
                for json_file in group_dir.glob('*.json'):
                    # 从文件名提取参数名（去掉 .json 后缀）
                    file_param = json_file.stem
                    
                    # 检查参数名是否匹配
                    if param_name.lower() in file_param.lower():
                        results.append((level1, level2, group, file_param))
    
    return results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='根据参数名获取完整测试路径',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python get_param_path.py small_area_infill_flow_compensation
  python get_param_path.py wall_sequence
  python get_param_path.py --search infill
        """
    )
    parser.add_argument('param_name', 
                       help='参数名（支持部分匹配）')
    parser.add_argument('--search', '-s',
                       action='store_true',
                       help='模糊搜索模式')
    parser.add_argument('--root',
                       default=None,
                       help='指定 engine_params 根目录（默认自动检测）')
    
    args = parser.parse_args()
    
    # 确定根目录
    if args.root:
        root_dir = Path(args.root)
    else:
        # 从当前脚本位置推断
        script_dir = Path(__file__).resolve().parent
        root_dir = script_dir.parent
    
    case_input_dir = root_dir / 'data' / 'case_input'
    
    if not case_input_dir.exists():
        print(f"错误: 找不到目录 {case_input_dir}", file=sys.stderr)
        return 1
    
    # 搜索参数
    results = search_param(args.param_name, case_input_dir)
    
    if not results:
        print(f"未找到参数: {args.param_name}", file=sys.stderr)
        return 1
    
    # 输出结果
    if len(results) == 1:
        level1, level2, group, param = results[0]
        print(f"{level1}.{level2}.{group}.{param}")
    else:
        print(f"找到 {len(results)} 个匹配:")
        for level1, level2, group, param in results:
            print(f"  {level1}.{level2}.{group}.{param}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
