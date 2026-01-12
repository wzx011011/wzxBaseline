#!/usr/bin/env python3
"""
通用 3MF 参数修改工具

用法:
    python modify_3mf_params.py <input.3mf> <output.3mf> --param key=value [--param key2=value2 ...]
    python modify_3mf_params.py template.3mf output.3mf --param small_area_infill_flow_compensation=1
    
特性:
    - 正确修改 JSON 格式的配置文件
    - 自动更新 different_settings_to_system 列表
    - 支持批量修改多个参数
    - 保持 3MF 文件结构完整
"""

import argparse
import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple


def parse_param(param_str: str) -> Tuple[str, str]:
    """
    解析参数字符串 "key=value" 返回 (key, value)
    
    Args:
        param_str: 格式为 "key=value" 的字符串
        
    Returns:
        (key, value) 元组
        
    Raises:
        ValueError: 如果格式不正确
    """
    if '=' not in param_str:
        raise ValueError(f"参数格式错误: {param_str}，应该是 'key=value' 格式")
    
    key, value = param_str.split('=', 1)
    return key.strip(), value.strip()


def modify_3mf_params(
    input_3mf: Path,
    output_3mf: Path,
    params: Dict[str, str],
    verbose: bool = True
) -> bool:
    """
    修改 3MF 文件中的参数
    
    Args:
        input_3mf: 输入的 3MF 文件路径
        output_3mf: 输出的 3MF 文件路径
        params: 要修改的参数字典 {key: value}
        verbose: 是否打印详细信息
        
    Returns:
        是否成功
    """
    if not input_3mf.exists():
        if verbose:
            print(f"❌ 输入文件不存在: {input_3mf}")
        return False
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # 1. 解压 3MF 文件
            if verbose:
                print(f"📦 解压 3MF: {input_3mf.name}")
            
            with zipfile.ZipFile(input_3mf, 'r') as zf:
                zf.extractall(tmppath)
            
            # 2. 查找配置文件
            config_file = tmppath / "Metadata" / "project_settings.config"
            if not config_file.exists():
                config_file = tmppath / "Metadata" / "model_settings.config"
            if not config_file.exists():
                if verbose:
                    print(f"⚠️  未找到配置文件，使用简单复制模式")
                output_3mf.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(input_3mf, output_3mf)
                return True
            
            # 3. 读取配置文件
            if verbose:
                print(f"📄 读取配置: {config_file.name}")
            
            content = config_file.read_text(encoding='utf-8')
            
            # 4. 解析 JSON（整个文件就是一个 JSON 对象）
            try:
                config_data = json.loads(content)
            except json.JSONDecodeError as e:
                if verbose:
                    print(f"❌ JSON 解析失败: {e}")
                return False
            
            # 5. 获取或创建 different_settings_to_system 列表
            diff_settings = config_data.get('different_settings_to_system', [])
            if not isinstance(diff_settings, list):
                diff_settings = []
            
            # 移除空字符串
            diff_settings = [s for s in diff_settings if s.strip()]
            
            # 6. 修改参数
            if verbose:
                print(f"🔧 修改参数:")
            
            for key, value in params.items():
                old_value = config_data.get(key, '<不存在>')
                config_data[key] = value
                
                # 添加到 different_settings_to_system（如果还不在列表中）
                if key not in diff_settings:
                    diff_settings.append(key)
                
                if verbose:
                    print(f"   {key}: {old_value} → {value}")
            
            # 7. 更新 different_settings_to_system
            # 确保列表有3个元素（切片器格式要求）
            while len(diff_settings) < 3:
                diff_settings.append("")
            
            config_data['different_settings_to_system'] = diff_settings[:3]  # 只保留前3个
            
            # 8. 写回配置文件（格式化 JSON）
            config_file.write_text(
                json.dumps(config_data, indent=4, ensure_ascii=False),
                encoding='utf-8'
            )
            
            if verbose:
                print(f"💾 更新 different_settings_to_system: {diff_settings[:3]}")
            
            # 9. 重新打包为 3MF
            if verbose:
                print(f"📦 重新打包 3MF: {output_3mf.name}")
            
            output_3mf.parent.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(output_3mf, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file_path in tmppath.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(tmppath)
                        zf.write(file_path, arcname)
            
            if verbose:
                print(f"✅ 成功: {output_3mf}")
            
            return True
            
    except Exception as e:
        if verbose:
            print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="通用 3MF 参数修改工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 修改单个参数
  python modify_3mf_params.py template.3mf output.3mf --param small_area_infill_flow_compensation=1
  
  # 修改多个参数
  python modify_3mf_params.py template.3mf output.3mf \\
      --param small_area_infill_flow_compensation=1 \\
      --param detect_thin_wall=0 \\
      --param wall_loops=3
  
  # 批量生成（结合 shell 脚本）
  for val in 0 1; do
      python modify_3mf_params.py template.3mf "output_$val.3mf" \\
          --param small_area_infill_flow_compensation=$val
  done
        """
    )
    
    parser.add_argument(
        'input_3mf',
        type=Path,
        help='输入的 3MF 模板文件'
    )
    
    parser.add_argument(
        'output_3mf',
        type=Path,
        help='输出的 3MF 文件'
    )
    
    parser.add_argument(
        '--param', '-p',
        action='append',
        dest='params',
        required=True,
        help='要修改的参数，格式: key=value（可多次使用）'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='静默模式，不输出详细信息'
    )
    
    args = parser.parse_args()
    
    # 解析参数
    try:
        params_dict = {}
        for param_str in args.params:
            key, value = parse_param(param_str)
            params_dict[key] = value
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1
    
    # 执行修改
    success = modify_3mf_params(
        args.input_3mf,
        args.output_3mf,
        params_dict,
        verbose=not args.quiet
    )
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
