#!/usr/bin/env python
"""
通用的 3MF 文件生成器

核心功能：
1. 根据 JSON 配置中的 key（参数名）拷贝模板 3MF
2. 根据期望值修改 3MF 内部配置参数

使用方法：
  # 从 JSON 配置文件生成 3MF
  python generate_3mf.py path/to/config.json
  
  # 或直接指定参数和值
  python generate_3mf.py --key bridge_flow --values 0.95,1.0,1.1
  
  # 强制覆盖
  python generate_3mf.py config.json --force
"""

import argparse
import json
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import List, Optional


# ==================== 辅助函数 ====================

def _slug(s: str) -> str:
    """将参数值转换为文件名安全的字符串"""
    s = str(s)
    s = s.replace("%", "percent")
    s = s.replace(",", "_")
    s = s.replace("(", "_").replace(")", "")
    s = s.replace(" ", "_")
    s = s.replace(".", "_")
    s = re.sub(r"[^A-Za-z0-9_-]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "value"


def modify_3mf_config(
    template_3mf: Path,
    output_3mf: Path,
    key: str,
    value: str,
    verbose: bool = True
) -> bool:
    """
    修改 3MF 文件内部的配置参数
    
    Args:
        template_3mf: 模板3MF文件路径
        output_3mf: 输出3MF文件路径
        key: 参数名（配置文件中的 key）
        value: 参数值
        verbose: 是否打印详细信息
    
    Returns:
        是否成功修改
    """
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # 1. 解压 3MF 文件
            with zipfile.ZipFile(template_3mf, 'r') as zip_ref:
                zip_ref.extractall(tmppath)
            
            # 2. 查找配置文件
            config_file = tmppath / "Metadata" / "project_settings.config"
            if not config_file.exists():
                config_file = tmppath / "Metadata" / "model_settings.config"
            if not config_file.exists():
                config_file = tmppath / "Metadata" / "slice_info.config"
            
            if not config_file.exists():
                if verbose:
                    print(f"    [WARN] Config file not found in 3MF, using copy mode")
                # 降级为简单复制
                output_3mf.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(template_3mf, output_3mf)
                return True
            
            # 3. 读取并修改配置
            config_content = config_file.read_text(encoding='utf-8')
            lines = config_content.split('\n')
            
            # 4. 查找并替换参数行
            # 匹配格式: key = value 或 key=value
            pattern = rf'^\s*{re.escape(key)}\s*=\s*.*$'
            new_line = f"{key} = {value}"
            
            found = False
            for i, line in enumerate(lines):
                if re.match(pattern, line):
                    lines[i] = new_line
                    found = True
                    if verbose:
                        print(f"    Modified: {key} = {value}")
                    break
            
            if not found:
                # 参数不存在，添加到末尾
                lines.append(new_line)
                if verbose:
                    print(f"    Added: {key} = {value}")
            
            # 5. 写回配置文件
            config_file.write_text('\n'.join(lines), encoding='utf-8')
            
            # 6. 重新打包为 3MF
            output_3mf.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(output_3mf, 'w', zipfile.ZIP_DEFLATED) as zip_out:
                for file_path in tmppath.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(tmppath)
                        zip_out.write(file_path, arcname)
            
            return True
            
    except Exception as e:
        if verbose:
            print(f"    [ERROR] Failed to modify 3MF: {e}")
        return False


def copy_template_3mf(
    template_3mf: Path,
    output_3mf: Path,
    verbose: bool = True
) -> bool:
    """
    简单复制模板 3MF 文件
    
    Args:
        template_3mf: 模板文件路径
        output_3mf: 输出文件路径
        verbose: 是否打印详细信息
    
    Returns:
        是否成功
    """
    try:
        output_3mf.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(template_3mf, output_3mf)
        if verbose:
            print(f"    Copied: {output_3mf.name}")
        return True
    except Exception as e:
        if verbose:
            print(f"    [ERROR] Failed to copy: {e}")
        return False


def generate_3mf_from_json(
    json_path: Path,
    template_3mf: Path,
    output_base_dir: Path,
    force: bool = False,
    dry_run: bool = False
) -> tuple[int, int]:
    """
    从 JSON 配置文件生成 3MF 文件
    
    JSON 格式示例:
    {
        "param_name": "bridge_flow",
        "cases": [
            {
                "case_id": "bridge_flow_0_95",
                "input_3mf": "models/bridge_flow_0_95.3mf",
                "expected_value": "0.95"
            }
        ]
    }
    
    Args:
        json_path: JSON配置文件路径
        template_3mf: 模板3MF文件路径
        output_base_dir: 输出基础目录
        force: 是否强制覆盖
        dry_run: 是否干运行
    
    Returns:
        (成功数, 总数)
    """
    # 读取 JSON 配置
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to read JSON: {e}")
        return 0, 0
    
    param_name = config.get("param_name", "unknown")
    cases = config.get("cases", [])
    
    if not cases:
        print(f"[WARN] No cases found in {json_path.name}")
        return 0, 0
    
    print(f"\n[{param_name}] Processing {len(cases)} cases from {json_path.name}")
    
    success_count = 0
    total_count = len(cases)
    
    for case in cases:
        case_id = case.get("case_id", "")
        input_3mf_rel = case.get("input_3mf", "")
        expected_value = case.get("expected_value", "")
        
        if not input_3mf_rel or not expected_value:
            print(f"  [SKIP] Invalid case: {case_id}")
            continue
        
        # 构造输出路径
        output_3mf = output_base_dir / input_3mf_rel
        
        # 检查是否已存在
        if output_3mf.exists() and not force:
            print(f"  [EXISTS] {output_3mf.relative_to(output_base_dir)}")
            success_count += 1
            continue
        
        if dry_run:
            print(f"  [DRY RUN] Would create: {output_3mf.relative_to(output_base_dir)}")
            print(f"    {param_name} = {expected_value}")
            success_count += 1
            continue
        
        # 生成 3MF
        print(f"  Generating: {output_3mf.name}")
        if modify_3mf_config(template_3mf, output_3mf, param_name, str(expected_value)):
            success_count += 1
        
    return success_count, total_count


def generate_3mf_from_params(
    key: str,
    values: List[str],
    template_3mf: Path,
    output_dir: Path,
    force: bool = False,
    dry_run: bool = False
) -> tuple[int, int]:
    """
    直接从参数和值生成 3MF 文件
    
    Args:
        key: 参数名
        values: 期望值列表
        template_3mf: 模板文件
        output_dir: 输出目录
        force: 是否强制覆盖
        dry_run: 是否干运行
    
    Returns:
        (成功数, 总数)
    """
    print(f"\n[{key}] Generating {len(values)} files")
    
    success_count = 0
    total_count = len(values)
    
    for value in values:
        slug = _slug(str(value))
        output_3mf = output_dir / f"{key}_{slug}.3mf"
        
        if output_3mf.exists() and not force:
            print(f"  [EXISTS] {output_3mf.name}")
            success_count += 1
            continue
        
        if dry_run:
            print(f"  [DRY RUN] Would create: {output_3mf.name}")
            print(f"    {key} = {value}")
            success_count += 1
            continue
        
        print(f"  Generating: {output_3mf.name}")
        if modify_3mf_config(template_3mf, output_3mf, key, str(value)):
            success_count += 1
    
    return success_count, total_count


# ==================== 主函数 ====================

def main():
    parser = argparse.ArgumentParser(
        description="3MF 文件生成器 - 根据 key 和期望值修改配置",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：

1. 从 JSON 配置文件生成：
   python generate_3mf.py data/case_input/process/quality/bridging/bridge_flow.json
   
2. 直接指定参数和值：
   python generate_3mf.py --key bridge_flow --values 0.95,1.0,1.1
   python generate_3mf.py --key ironing_type --values no_ironing,top_surface,all_solid
   
3. 指定输出目录：
   python generate_3mf.py --key bridge_flow --values 0.95,1.0 --output models/test/
   
4. 强制覆盖：
   python generate_3mf.py config.json --force
   
5. 干运行（预览）：
   python generate_3mf.py config.json --dry-run
        """
    )
    
    parser.add_argument(
        "json_file",
        nargs="?",
        type=Path,
        help="JSON 配置文件路径"
    )
    parser.add_argument(
        "--key", "-k",
        help="参数名（配置文件中的 key）"
    )
    parser.add_argument(
        "--values", "-v",
        help="期望值列表，用逗号分隔（如: 0.95,1.0,1.1）"
    )
    parser.add_argument(
        "--template", "-t",
        type=Path,
        help="模板 3MF 文件路径（默认: data/models/template_model.3mf）"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="输出目录（默认: data/models/）"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="强制覆盖已存在的文件"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="干运行模式，只显示将要执行的操作"
    )
    
    args = parser.parse_args()
    
    # 验证参数
    if not args.json_file and not (args.key and args.values):
        parser.print_help()
        print("\n[ERROR] 请指定 JSON 文件或使用 --key 和 --values 参数")
        return 1
    
    # 获取脚本目录
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent  # test_framework
    
    # 查找模板文件
    if args.template:
        template_3mf = args.template
    else:
        template_3mf = script_dir / "data" / "models" / "template_model.3mf"
        if not template_3mf.exists():
            template_3mf = repo_root / "template_model.3mf"
    
    if not template_3mf.exists():
        print(f"[ERROR] Template 3MF not found: {template_3mf}")
        print("[INFO] Please specify with --template option")
        return 1
    
    print("=" * 80)
    print("3MF 文件生成器")
    print("=" * 80)
    print(f"模板: {template_3mf}")
    print(f"模式: {'干运行' if args.dry_run else '正常'}")
    print(f"覆盖: {'是' if args.force else '否'}")
    
    # 模式1: 从 JSON 文件生成
    if args.json_file:
        if not args.json_file.exists():
            print(f"[ERROR] JSON file not found: {args.json_file}")
            return 1
        
        output_base = args.output or (script_dir / "data" / "models")
        
        success, total = generate_3mf_from_json(
            args.json_file,
            template_3mf,
            output_base,
            args.force,
            args.dry_run
        )
    
    # 模式2: 从命令行参数生成
    else:
        values_list = [v.strip() for v in args.values.split(',')]
        output_dir = args.output or (script_dir / "data" / "models" / args.key)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        success, total = generate_3mf_from_params(
            args.key,
            values_list,
            template_3mf,
            output_dir,
            args.force,
            args.dry_run
        )
    
    # 打印结果
    print("\n" + "=" * 80)
    print(f"完成: {success}/{total} 个文件")
    print("=" * 80)
    
    if not args.dry_run and success < total:
        print("[WARN] 部分文件生成失败")
    
    return 0 if success == total else 1


if __name__ == "__main__":
    sys.exit(main())
