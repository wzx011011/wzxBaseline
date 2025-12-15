"""
自动生成 Extruder X 参数的 3MF 文件

流程：
1. 读取 JSON 配置获取所有测试用例和期望值
2. 从 template_model.3mf 解压
3. 修改 Metadata/project_settings.config 中的参数值
4. 重新打包成新的 3MF 文件
5. (可选) 通过 slicerctl 加载验证参数生效

注意：
- 3MF 文件是 ZIP 格式
- 配置在 Metadata/project_settings.config (JSON 格式)
- 切片器加载 3MF 时会读取配置
"""

import json
import zipfile
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Tuple


# ==================== 参数映射配置 ====================

# 参数所属子分组映射
# 格式: "param_name": "subgroup"
PARAM_TO_SUBGROUP = {
    # size 子分组
    "nozzle_diameter": "size",
    
    # layer_height_limits 子分组
    "min_layer_height": "layer_height_limits",
    "max_layer_height": "layer_height_limits",
    
    # position 子分组
    "extruder_offset": "position",
    
    # retraction 子分组
    "retraction_length": "retraction",
    "retract_restart_extra": "retraction",
    "z_hop": "retraction",
    "z_hop_types": "retraction",
    "travel_slope": "retraction",
    "retraction_speed": "retraction",
    "deretraction_speed": "retraction",
    "retraction_minimum_travel": "retraction",
    "retract_when_changing_layer": "retraction",
    "wipe": "retraction",
    "wipe_distance": "retraction",
    "retract_before_wipe": "retraction",
    
    # lift_z_enforcement 子分组
    "retract_lift_above": "lift_z_enforcement",
    "retract_lift_below": "lift_z_enforcement",
    "retract_lift_enforce": "lift_z_enforcement",
    
    # switching_material 子分组
    "retract_length_toolchange": "switching_material",
    "retract_restart_extra_toolchange": "switching_material",
    "long_retractions_when_cut": "switching_material",
    "retraction_distances_when_cut": "switching_material",
}

# 将 JSON 中的键名映射到 3MF 配置中的实际键名
# 格式: "json_key": "3mf_config_key"
PARAM_MAPPING = {k: k for k in PARAM_TO_SUBGROUP.keys()}  # 大部分参数名一致

# 参数类型转换（某些参数需要特殊处理）
# 注意：大部分数值参数在 3MF 中都是字符串数组格式 ["value"]
VALUE_CONVERTERS = {
    # 布尔型参数：JSON 中是 int (0/1)，3MF 中可能是 bool 或 "0"/"1"
    "retract_when_changing_layer": lambda v: "1" if v else "0",
    "wipe": lambda v: "1" if v else "0",
    "long_retractions_when_cut": lambda v: "1" if v else "0",
    
    # 数组格式参数（所有数值参数都需要转换为字符串数组）
    "nozzle_diameter": lambda v: [str(v)],
    "min_layer_height": lambda v: [str(v)],
    "max_layer_height": lambda v: [str(v)],
    "retraction_length": lambda v: [str(v)],
    "retract_restart_extra": lambda v: [str(v)],
    "z_hop": lambda v: [str(v)],
    "travel_slope": lambda v: [str(v)],
    "retraction_speed": lambda v: [str(v)],
    "deretraction_speed": lambda v: [str(v)],
    "retraction_minimum_travel": lambda v: [str(v)],
    "wipe_distance": lambda v: [str(v)],
    "retract_lift_above": lambda v: [str(v)],
    "retract_lift_below": lambda v: [str(v)],
    "retract_length_toolchange": lambda v: [str(v)],
    "retract_restart_extra_toolchange": lambda v: [str(v)],
    "retraction_distances_when_cut": lambda v: [str(v)],
    
    # 字符串型参数（枚举）- 这些也可能需要数组格式
    "z_hop_types": lambda v: [str(v)],
    "retract_lift_enforce": lambda v: [str(v)],
    "extruder_offset": lambda v: [str(v)],
    "retract_before_wipe": lambda v: [str(v)],
}


# ==================== 核心函数 ====================

def load_json_cases(json_path: Path) -> List[Dict[str, Any]]:
    """加载 JSON 配置文件中的测试用例"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('cases', [])


def extract_3mf(src_3mf: Path, dest_dir: Path) -> None:
    """解压 3MF 文件到指定目录"""
    with zipfile.ZipFile(src_3mf, 'r') as zf:
        zf.extractall(dest_dir)


def load_3mf_config(extracted_dir: Path) -> Dict[str, Any]:
    """读取 3MF 配置文件"""
    config_path = extracted_dir / "Metadata" / "project_settings.config"
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_3mf_config(extracted_dir: Path, config: Dict[str, Any]) -> None:
    """
    保存 3MF 配置文件
    
    注意：different_settings_to_system 必须紧跟在 detect_thin_wall 之后
    Python 3.7+ 的 dict 保持插入顺序，所以需要重新构建有序字典
    """
    config_path = extracted_dir / "Metadata" / "project_settings.config"
    
    # 如果存在 different_settings_to_system，需要确保它在正确的位置
    if "different_settings_to_system" in config:
        # 重新构建字典，将 different_settings_to_system 放在 detect_thin_wall 之后
        ordered_config = {}
        diff_settings = config.pop("different_settings_to_system")
        
        for key, value in config.items():
            ordered_config[key] = value
            # 在 detect_thin_wall 之后插入 different_settings_to_system
            if key == "detect_thin_wall":
                ordered_config["different_settings_to_system"] = diff_settings
        
        config = ordered_config
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def create_3mf(src_dir: Path, dest_3mf: Path) -> None:
    """将目录打包成 3MF 文件"""
    dest_3mf.parent.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(dest_3mf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in src_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(src_dir)
                zf.write(file_path, arcname)


def modify_config_value(config: Dict[str, Any], param_name: str, expected_value: Any) -> Dict[str, Any]:
    """修改配置中的参数值"""
    # 获取 3MF 中的实际键名
    config_key = PARAM_MAPPING.get(param_name, param_name)
    
    # 转换值类型
    converter = VALUE_CONVERTERS.get(param_name, lambda x: x)
    converted_value = converter(expected_value)
    
    # 修改配置值
    config[config_key] = converted_value
    
    # 关键：将修改的参数添加到 different_settings_to_system 数组中
    # 格式固定为 ["", "", "param1", "param2", ...]
    # 前两个空字符串是必需的
    if "different_settings_to_system" not in config:
        config["different_settings_to_system"] = ["", ""]
    
    settings_list = config["different_settings_to_system"]
    
    # 确保前两个元素是空字符串（如果不存在则添加）
    while len(settings_list) < 2:
        settings_list.insert(0, "")
    
    # 确保参数在列表中（避免重复）
    if config_key not in settings_list:
        settings_list.append(config_key)
    
    config["different_settings_to_system"] = settings_list
    
    return config


def generate_single_3mf(
    template_3mf: Path,
    output_3mf: Path,
    param_name: str,
    expected_value: Any,
    dry_run: bool = False
) -> bool:
    """
    生成单个 3MF 文件
    
    Args:
        template_3mf: 模板 3MF 文件路径
        output_3mf: 输出 3MF 文件路径
        param_name: 参数名称
        expected_value: 期望值
        dry_run: 是否仅显示操作而不实际执行
        
    Returns:
        bool: 是否成功
    """
    try:
        if dry_run:
            print(f"[DRY RUN] Generate: {output_3mf.name}")
            print(f"          Parameter: {param_name} = {expected_value}")
            return True
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 1. 解压模板
            extract_3mf(template_3mf, temp_path)
            
            # 2. 读取配置
            config = load_3mf_config(temp_path)
            
            # 3. 修改参数
            config = modify_config_value(config, param_name, expected_value)
            
            # 4. 保存配置
            save_3mf_config(temp_path, config)
            
            # 5. 打包成新 3MF
            create_3mf(temp_path, output_3mf)
        
        print(f"[OK] Generated: {output_3mf.name} ({param_name} = {expected_value})")
        return True
        
    except Exception as e:
        print(f"[FAIL] Generation failed: {output_3mf.name} - {e}")
        return False


def generate_3mf_for_parameter(
    repo_root: Path,
    module: str,
    group: str,
    param_name: str,
    dry_run: bool = False
) -> Tuple[int, int]:
    """
    为指定参数生成所有测试用例的 3MF 文件
    
    Args:
        repo_root: 仓库根目录
        module: 模块名 (如 "printer")
        group: 分组名 (如 "extruder_x")
        param_name: 参数名称
        dry_run: 是否仅预览
        
    Returns:
        (成功数, 总数)
    """
    # 获取参数所属的子分组
    subgroup = PARAM_TO_SUBGROUP.get(param_name)
    if not subgroup:
        print(f"[ERROR] Unknown parameter: {param_name} (no subgroup mapping)")
        return 0, 0
    
    # 路径定义（注意：JSON 在子分组目录里）
    json_path = repo_root / "data" / "case_input" / module / group / subgroup / f"{param_name}.json"
    template_3mf = repo_root / "data" / "models" / "template_model.3mf"
    # 模型目录结构: models/{module}/{group}/{subgroup}/{param}/
    models_base = repo_root / "data" / "models" / module / group / subgroup
    
    # 检查文件是否存在
    if not json_path.exists():
        print(f"[ERROR] JSON file not found: {json_path}")
        return 0, 0
    
    if not template_3mf.exists():
        print(f"[ERROR] Template not found: {template_3mf}")
        return 0, 0
    
    # 加载测试用例
    cases = load_json_cases(json_path)
    if not cases:
        print(f"[WARN] No test cases found: {json_path}")
        return 0, 0
    
    print(f"\n{'='*60}")
    print(f"Parameter: {param_name} ({len(cases)} test cases)")
    print(f"{'='*60}")
    
    # 生成每个测试用例的 3MF
    success_count = 0
    for case in cases:
        input_3mf_name = case.get("input_3mf")
        expected_value = case.get("expected_value")
        
        if not input_3mf_name:
            print(f"[WARN] Skipping: missing input_3mf field")
            continue
        
        # 推断输出路径（根据目录结构）
        # 格式: models/{module}/{group}/{param}/{filename}
        output_3mf = models_base / param_name / input_3mf_name
        
        if generate_single_3mf(template_3mf, output_3mf, param_name, expected_value, dry_run):
            success_count += 1
    
    print(f"\n[SUCCESS] Completed: {success_count}/{len(cases)} files generated")
    return success_count, len(cases)


def generate_all_extruder_x_3mf(repo_root: Path, dry_run: bool = False) -> None:
    """
    生成所有 Extruder X 参数的 3MF 文件
    
    Args:
        repo_root: 仓库根目录
        dry_run: 是否仅预览操作
    """
    module = "printer"
    group = "extruder_x"
    
    # 所有参数列表
    parameters = list(PARAM_TO_SUBGROUP.keys())
    
    print(f"\n{'#'*60}")
    print(f"# Auto-generate Extruder X 3MF files")
    print(f"# Module: {module}/{group}")
    print(f"# Parameters: {len(parameters)}")
    print(f"# Mode: {'DRY RUN (preview only)' if dry_run else 'GENERATE'}")
    print(f"{'#'*60}\n")
    
    total_success = 0
    total_cases = 0
    
    for param_name in parameters:
        success, total = generate_3mf_for_parameter(
            repo_root, module, group, param_name, dry_run
        )
        total_success += success
        total_cases += total
    
    print(f"\n{'='*60}")
    print(f"Total: {total_success}/{total_cases} 3MF files generated successfully")
    print(f"{'='*60}\n")


# ==================== CLI 入口 ====================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="自动生成 Extruder X 参数的 3MF 文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 预览模式（不实际生成）
  python generate_extruder_x_3mf.py --dry-run
  
  # 生成所有文件
  python generate_extruder_x_3mf.py
  
  # 仅生成指定参数
  python generate_extruder_x_3mf.py --param nozzle_diameter
  python generate_extruder_x_3mf.py --param retraction_length --param z_hop
        """
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="预览模式：仅显示将要执行的操作，不实际生成文件"
    )
    
    parser.add_argument(
        "--param",
        action="append",
        dest="params",
        metavar="PARAM_NAME",
        help="仅生成指定参数的 3MF 文件（可多次使用）"
    )
    
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).parent,
        help="仓库根目录路径（默认：脚本所在目录，即 engine_params/）"
    )
    
    args = parser.parse_args()
    
    # repo_root 应该是 engine_params 目录
    repo_root = args.repo_root.resolve()
    print(f"仓库根目录: {repo_root}")
    
    if args.params:
        # 仅生成指定参数
        print(f"\n{'#'*60}")
        print(f"# 生成指定参数的 3MF 文件: {', '.join(args.params)}")
        print(f"{'#'*60}\n")
        
        total_success = 0
        total_cases = 0
        
        for param_name in args.params:
            if param_name not in PARAM_TO_SUBGROUP:
                print(f"[ERROR] Unknown parameter: {param_name}")
                print(f"Available parameters: {', '.join(sorted(PARAM_TO_SUBGROUP.keys()))}")
                continue
            
            success, total = generate_3mf_for_parameter(
                repo_root, "printer", "extruder_x", param_name, args.dry_run
            )
            total_success += success
            total_cases += total
        
        print(f"\n{'='*60}")
        print(f"Total: {total_success}/{total_cases} 3MF files generated successfully")
        print(f"{'='*60}\n")
    else:
        # 生成所有参数
        generate_all_extruder_x_3mf(repo_root, args.dry_run)
