"""
自动生成 Filament 参数的 3MF 文件

流程：
1. 读取 JSON 配置获取所有测试用例和期望值
2. 从 template_model.3mf 解压
3. 修改 Metadata/project_settings.config 中的参数值
4. 重新打包成新的 3MF 文件

参数分组：
- advanced: 3 个参数
- cooling: 22 个参数
- filament_basic: 19 个参数
- filament_temperature: 20 个参数
- multimaterial: 14 个参数
- setting_overrides: 16 个参数
- 总计: 94 个参数
"""

import json
import zipfile
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Tuple


# ==================== 参数映射配置 ====================

# 参数所属子分组映射 (从 JSON 目录结构提取)
# 格式: "param_name": "subgroup"
PARAM_TO_SUBGROUP = {
    # advanced 子分组 (3 个)
    "filament_end_gcode": "advanced",
    "filament_notes": "advanced",
    "filament_start_gcode": "advanced",
    
    # cooling 子分组 (22 个)
    "activate_air_filtration": "cooling",
    "additional_cooling_fan_speed": "cooling",
    "close_fan_the_first_x_layers": "cooling",
    "complete_print_exhaust_fan_speed": "cooling",
    "cooling_perimeter_transition_distance": "cooling",
    "cooling_slowdown_logic": "cooling",
    "cool_cds_fan_start_at_height": "cooling",
    "cool_special_cds_fan_speed": "cooling",
    "during_print_exhaust_fan_speed": "cooling",
    "enable_overhang_bridge_fan": "cooling",
    "enable_special_area_additional_cooling_fan": "cooling",
    "fan_cooling_layer_time": "cooling",
    "fan_max_speed": "cooling",
    "fan_min_speed": "cooling",
    "full_fan_speed_layer": "cooling",
    "overhang_fan_speed": "cooling",
    "overhang_fan_threshold": "cooling",
    "reduce_fan_stop_start_freq": "cooling",
    "slow_down_for_layer_cooling": "cooling",
    "slow_down_layer_time": "cooling",
    "slow_down_min_speed": "cooling",
    "support_material_interface_fan_speed": "cooling",
    
    # filament_basic 子分组 (19 个)
    "default_filament_colour": "filament_basic",
    "enable_pressure_advance": "filament_basic",
    "filament_adhesiveness_category": "filament_basic",
    "filament_cost": "filament_basic",
    "filament_density": "filament_basic",
    "filament_diameter": "filament_basic",
    "filament_flow_ratio": "filament_basic",
    "filament_is_support": "filament_basic",
    "filament_shrink": "filament_basic",
    "filament_shrinkage_compensation_z": "filament_basic",
    "filament_soluble": "filament_basic",
    "filament_type": "filament_basic",
    "filament_vendor": "filament_basic",
    "idle_temperature": "filament_basic",
    "nozzle_temperature_range_high": "filament_basic",
    "nozzle_temperature_range_low": "filament_basic",
    "pressure_advance": "filament_basic",
    "required_nozzle_HRC": "filament_basic",
    "temperature_vitrification": "filament_basic",
    
    # filament_temperature 子分组 (20 个)
    "activate_chamber_layer": "filament_temperature",
    "activate_chamber_temp_control": "filament_temperature",
    "chamber_temperature": "filament_temperature",
    "cool_plate_temp": "filament_temperature",
    "cool_plate_temp_initial_layer": "filament_temperature",
    "customized_plate_temp": "filament_temperature",
    "customized_plate_temp_initial_layer": "filament_temperature",
    "eng_plate_temp": "filament_temperature",
    "eng_plate_temp_initial_layer": "filament_temperature",
    "epoxy_resin_plate_temp": "filament_temperature",
    "epoxy_resin_plate_temp_initial_layer": "filament_temperature",
    "filament_max_volumetric_speed": "filament_temperature",
    "hot_plate_temp": "filament_temperature",
    "hot_plate_temp_initial_layer": "filament_temperature",
    "material_flow_dependent_temperature": "filament_temperature",
    "material_flow_temp_graph": "filament_temperature",
    "nozzle_temperature": "filament_temperature",
    "nozzle_temperature_initial_layer": "filament_temperature",
    "textured_plate_temp": "filament_temperature",
    "textured_plate_temp_initial_layer": "filament_temperature",
    
    # multimaterial 子分组 (14 个)
    "filament_cooling_final_speed": "multimaterial",
    "filament_cooling_initial_speed": "multimaterial",
    "filament_cooling_moves": "multimaterial",
    "filament_loading_speed": "multimaterial",
    "filament_loading_speed_start": "multimaterial",
    "filament_minimal_purge_on_wipe_tower": "multimaterial",
    "filament_multitool_ramming": "multimaterial",
    "filament_multitool_ramming_flow": "multimaterial",
    "filament_multitool_ramming_volume": "multimaterial",
    "filament_stamping_distance": "multimaterial",
    "filament_stamping_loading_speed": "multimaterial",
    "filament_toolchange_delay": "multimaterial",
    "filament_unloading_speed": "multimaterial",
    "filament_unloading_speed_start": "multimaterial",
    
    # setting_overrides 子分组 (16 个)
    "filament_deretraction_speed": "setting_overrides",
    "filament_long_retractions_when_cut": "setting_overrides",
    "filament_retraction_distances_when_cut": "setting_overrides",
    "filament_retraction_length": "setting_overrides",
    "filament_retraction_minimum_travel": "setting_overrides",
    "filament_retraction_speed": "setting_overrides",
    "filament_retract_before_wipe": "setting_overrides",
    "filament_retract_lift_above": "setting_overrides",
    "filament_retract_lift_below": "setting_overrides",
    "filament_retract_lift_enforce": "setting_overrides",
    "filament_retract_restart_extra": "setting_overrides",
    "filament_retract_when_changing_layer": "setting_overrides",
    "filament_wipe": "setting_overrides",
    "filament_wipe_distance": "setting_overrides",
    "filament_z_hop": "setting_overrides",
}

# 参数类型转换 - Filament 参数都是数组格式 ["value"]
# 根据参数类型定义转换器
VALUE_CONVERTERS = {
    # 布尔型参数 - 值为 "0" 或 "1"
    "activate_air_filtration": lambda v: [str(v)],
    "activate_chamber_temp_control": lambda v: [str(v)],
    "enable_overhang_bridge_fan": lambda v: [str(v)],
    "enable_pressure_advance": lambda v: [str(v)],
    "enable_special_area_additional_cooling_fan": lambda v: [str(v)],
    "filament_is_support": lambda v: [str(v)],
    "filament_multitool_ramming": lambda v: [str(v)],
    "filament_soluble": lambda v: [str(v)],
    "filament_long_retractions_when_cut": lambda v: [str(v)],
    "filament_retract_when_changing_layer": lambda v: [str(v)],
    "filament_wipe": lambda v: [str(v)],
    "material_flow_dependent_temperature": lambda v: [str(v)],
    "reduce_fan_stop_start_freq": lambda v: [str(v)],
    "slow_down_for_layer_cooling": lambda v: [str(v)],
    
    # 数值型参数 - 转换为字符串数组
    # 大多数参数都是这种格式
    
    # 枚举型参数 - 字符串值
    "cooling_slowdown_logic": lambda v: [str(v)],
    "filament_adhesiveness_category": lambda v: [str(v)],
    "filament_type": lambda v: [str(v)],
    "filament_retract_lift_enforce": lambda v: [str(v)],
    "overhang_fan_threshold": lambda v: [str(v)],
    "filament_retract_before_wipe": lambda v: [str(v)],
    
    # 字符串型参数 - G-code 等
    "filament_end_gcode": lambda v: [str(v)],
    "filament_notes": lambda v: [str(v)],
    "filament_start_gcode": lambda v: [str(v)],
    "filament_vendor": lambda v: [str(v)],
    "default_filament_colour": lambda v: [str(v)],
    
    # 特殊格式参数
    "material_flow_temp_graph": lambda v: [str(v)] if isinstance(v, str) else v,
}


def _default_converter(v):
    """默认转换器 - 将值转换为字符串数组格式"""
    if isinstance(v, (list, tuple)):
        return [str(x) for x in v]
    return [str(v)]


def get_converter(param_name: str):
    """获取参数的值转换器"""
    return VALUE_CONVERTERS.get(param_name, _default_converter)


# ==================== 核心函数 ====================

def load_json_cases(json_path: Path) -> List[Dict[str, Any]]:
    """加载 JSON 配置文件中的测试用例"""
    with open(json_path, 'r', encoding='utf-8-sig') as f:
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
    """保存 3MF 配置文件"""
    config_path = extracted_dir / "Metadata" / "project_settings.config"
    
    # 如果存在 different_settings_to_system，需要确保它在正确的位置
    if "different_settings_to_system" in config:
        ordered_config = {}
        diff_settings = config.pop("different_settings_to_system")
        
        for key, value in config.items():
            ordered_config[key] = value
            if key == "detect_thin_wall":
                ordered_config["different_settings_to_system"] = diff_settings
        
        # 如果循环结束后仍未插入，添加到末尾
        if "different_settings_to_system" not in ordered_config:
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


# Filament type to preset ID mapping (K1C 0.4 nozzle)
# 当修改 filament_type 时，需要同步更新 filament_settings_id
FILAMENT_TYPE_TO_PRESET_ID = {
    "PLA": "Hyper PLA @Creality K1C 0.4 nozzle",
    "ABS": "CR-ABS @Creality K1C 0.4 nozzle",
    "PETG": "CR-PETG @Creality K1C 0.4 nozzle",
    "TPU": "CR-TPU @Creality K1C 0.4 nozzle",
    "PA": "CR-Nylon @Creality K1C 0.4 nozzle",
    "PA-CF": "CR-PA-CF @Creality K1C 0.4 nozzle",
    "PLA-CF": "CR-PLA-CF @Creality K1C 0.4 nozzle",
    "ASA": "CR-ASA @Creality K1C 0.4 nozzle",
    "PC": "CR-PC @Creality K1C 0.4 nozzle",
    "HIPS": "CR-HIPS @Creality K1C 0.4 nozzle",
    "PVA": "CR-PVA @Creality K1C 0.4 nozzle",
}


def modify_config_value(config: Dict[str, Any], param_name: str, expected_value: Any) -> Dict[str, Any]:
    """修改配置中的参数值"""
    # 转换值类型
    converter = get_converter(param_name)
    converted_value = converter(expected_value)
    
    # 修改配置值
    config[param_name] = converted_value
    
    # 特殊处理：当修改 filament_type 时，同步更新 filament_settings_id
    if param_name == "filament_type" and expected_value in FILAMENT_TYPE_TO_PRESET_ID:
        preset_id = FILAMENT_TYPE_TO_PRESET_ID[expected_value]
        config["filament_settings_id"] = [preset_id]
        # 同时更新 default_filament_type
        config["default_filament_type"] = expected_value
    
    # 将修改的参数添加到 different_settings_to_system 数组中
    # 根据实际 3MF 分析，格式为: [process_params, filament_params, '', '']
    # Filament 参数应放在 **索引 1** 位置，用分号分隔多个参数名
    if "different_settings_to_system" not in config or config["different_settings_to_system"] is None:
        config["different_settings_to_system"] = ["", "", "", ""]
    
    settings_list = config["different_settings_to_system"]
    
    # 确保有 4 个元素
    while len(settings_list) < 4:
        settings_list.append("")
    
    # Filament 参数放在索引 1 (不是索引 2!)
    filament_params = settings_list[1] if settings_list[1] else ""
    if filament_params:
        # 已有其他参数，用分号分隔
        existing_params = set(filament_params.split(";"))
        if param_name not in existing_params:
            settings_list[1] = filament_params + ";" + param_name
    else:
        settings_list[1] = param_name
    
    config["different_settings_to_system"] = settings_list
    
    return config


def generate_single_3mf(
    template_3mf: Path,
    output_3mf: Path,
    param_name: str,
    expected_value: Any,
    dry_run: bool = False
) -> bool:
    """生成单个 3MF 文件"""
    try:
        if dry_run:
            print(f"  [DRY RUN] {output_3mf.name} ({param_name} = {expected_value})")
            return True
        
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
        
        print(f"  [OK] {output_3mf.name} ({param_name} = {expected_value})")
        return True
        
    except Exception as e:
        print(f"  [FAIL] {output_3mf.name} - {e}")
        return False


def generate_3mf_for_parameter(
    repo_root: Path,
    param_name: str,
    dry_run: bool = False
) -> Tuple[int, int]:
    """为指定参数生成所有测试用例的 3MF 文件"""
    subgroup = PARAM_TO_SUBGROUP.get(param_name)
    if not subgroup:
        print(f"[ERROR] Unknown parameter: {param_name}")
        return 0, 0
    
    # 路径定义
    json_path = repo_root / "data" / "case_input" / "filament" / subgroup / f"{param_name}.json"
    template_3mf = repo_root / "data" / "models" / "template_model.3mf"
    models_base = repo_root / "data" / "models" / "filament" / subgroup
    
    if not json_path.exists():
        print(f"[ERROR] JSON not found: {json_path}")
        return 0, 0
    
    if not template_3mf.exists():
        print(f"[ERROR] Template not found: {template_3mf}")
        return 0, 0
    
    cases = load_json_cases(json_path)
    if not cases:
        print(f"[WARN] No cases: {json_path}")
        return 0, 0
    
    print(f"\n  {subgroup}/{param_name} ({len(cases)} cases)")
    
    success_count = 0
    for case in cases:
        input_3mf_name = case.get("input_3mf")
        expected_value = case.get("expected_value")
        
        if not input_3mf_name:
            continue
        
        output_3mf = models_base / param_name / input_3mf_name
        
        if generate_single_3mf(template_3mf, output_3mf, param_name, expected_value, dry_run):
            success_count += 1
    
    return success_count, len(cases)


def generate_all_filament_3mf(repo_root: Path, dry_run: bool = False, subgroups: List[str] = None) -> None:
    """生成所有 Filament 参数的 3MF 文件"""
    
    # 按子分组组织参数
    subgroup_params: Dict[str, List[str]] = {}
    for param, subgroup in PARAM_TO_SUBGROUP.items():
        if subgroups and subgroup not in subgroups:
            continue
        if subgroup not in subgroup_params:
            subgroup_params[subgroup] = []
        subgroup_params[subgroup].append(param)
    
    print(f"\n{'#'*60}")
    print(f"# Auto-generate Filament 3MF files")
    print(f"# Mode: {'DRY RUN (preview only)' if dry_run else 'GENERATE'}")
    print(f"# Subgroups: {list(subgroup_params.keys())}")
    print(f"# Parameters: {sum(len(p) for p in subgroup_params.values())}")
    print(f"{'#'*60}")
    
    total_success = 0
    total_cases = 0
    
    for subgroup in sorted(subgroup_params.keys()):
        print(f"\n{'='*60}")
        print(f"Subgroup: {subgroup} ({len(subgroup_params[subgroup])} params)")
        print(f"{'='*60}")
        
        for param_name in sorted(subgroup_params[subgroup]):
            success, total = generate_3mf_for_parameter(repo_root, param_name, dry_run)
            total_success += success
            total_cases += total
    
    print(f"\n{'='*60}")
    print(f"Total: {total_success}/{total_cases} 3MF files generated")
    print(f"{'='*60}\n")


# ==================== CLI 入口 ====================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="自动生成 Filament 参数的 3MF 文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 预览模式（不实际生成）
  python generate_filament_3mf.py --dry-run
  
  # 生成所有文件
  python generate_filament_3mf.py
  
  # 仅生成指定子分组
  python generate_filament_3mf.py --subgroup cooling --subgroup filament_basic
  
  # 仅生成指定参数
  python generate_filament_3mf.py --param fan_max_speed --param fan_min_speed
        """
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="预览模式：仅显示将要执行的操作"
    )
    
    parser.add_argument(
        "--param",
        action="append",
        dest="params",
        metavar="PARAM_NAME",
        help="仅生成指定参数的 3MF 文件（可多次使用）"
    )
    
    parser.add_argument(
        "--subgroup",
        action="append",
        dest="subgroups",
        metavar="SUBGROUP",
        choices=["advanced", "cooling", "filament_basic", "filament_temperature", "multimaterial", "setting_overrides"],
        help="仅生成指定子分组的 3MF 文件"
    )
    
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).parent,
        help="仓库根目录路径（默认：engine_params/）"
    )
    
    args = parser.parse_args()
    
    repo_root = args.repo_root.resolve()
    print(f"Repository root: {repo_root}")
    
    if args.params:
        # 仅生成指定参数
        print(f"\nGenerating specified parameters: {args.params}")
        
        total_success = 0
        total_cases = 0
        
        for param_name in args.params:
            if param_name not in PARAM_TO_SUBGROUP:
                print(f"[ERROR] Unknown parameter: {param_name}")
                continue
            
            success, total = generate_3mf_for_parameter(repo_root, param_name, args.dry_run)
            total_success += success
            total_cases += total
        
        print(f"\nTotal: {total_success}/{total_cases}")
    else:
        # 生成所有或指定子分组
        generate_all_filament_3mf(repo_root, args.dry_run, args.subgroups)
