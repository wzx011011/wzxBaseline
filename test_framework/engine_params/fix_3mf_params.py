#!/usr/bin/env python
"""
批量修改 3MF 文件中的参数值为期望值
"""
import zipfile
import json
import os
import shutil
from pathlib import Path

# 失败用例的参数和期望值映射
FAILED_CASES = [
    # support_style
    {"param": "support_style", "value": "snug", "3mf": "support_style_snug.3mf", "group": "support_basic"},
    
    # support_on_build_plate_only - 需要特殊模型，跳过
    
    # support_base_pattern
    {"param": "support_base_pattern", "value": "rectilinear-grid", "3mf": "support_base_pattern_grid.3mf", "group": "support_advanced"},
    
    # support_base_pattern_tree
    {"param": "support_base_pattern_tree", "value": "grid", "3mf": "support_base_pattern_tree_grid.3mf", "group": "support_tree"},
    
    # support_object_xy_distance
    {"param": "support_object_xy_distance", "value": "0.2", "3mf": "support_object_xy_distance_0.2.3mf", "group": "support_advanced"},
    {"param": "support_object_xy_distance", "value": "0.6", "3mf": "support_object_xy_distance_0.6.3mf", "group": "support_advanced"},
    
    # support_xy_overrides_z - 两个值反了
    {"param": "support_xy_overrides_z", "value": "xy_overrides_z", "3mf": "support_xy_overrides_z_xy_overrides_z.3mf", "group": "support_advanced"},
    {"param": "support_xy_overrides_z", "value": "z_overrides_xy", "3mf": "support_xy_overrides_z_z_overrides_xy.3mf", "group": "support_advanced"},
    
    # max_bridge_length
    {"param": "max_bridge_length", "value": "5", "3mf": "max_bridge_length_5.3mf", "group": "support_advanced"},
    {"param": "max_bridge_length", "value": "20", "3mf": "max_bridge_length_20.3mf", "group": "support_advanced"},
    
    # independent_support_layer_height
    {"param": "independent_support_layer_height", "value": "0", "3mf": "independent_support_layer_height_0.3mf", "group": "support_advanced"},
    
    # tree_hybrid_cross_height
    {"param": "tree_hybrid_cross_height", "value": "5", "3mf": "tree_hybrid_cross_height_5.3mf", "group": "support_advanced"},
    {"param": "tree_hybrid_cross_height", "value": "10", "3mf": "tree_hybrid_cross_height_10.3mf", "group": "support_advanced"},
    
    # support_material_interface_fan_speed - 格式特殊，需要处理
    {"param": "support_material_interface_fan_speed", "value": "-1", "3mf": "support_material_interface_fan_speed_-1_-1.3mf", "group": "support_advanced"},
    {"param": "support_material_interface_fan_speed", "value": "0", "3mf": "support_material_interface_fan_speed_0_0.3mf", "group": "support_advanced"},
    {"param": "support_material_interface_fan_speed", "value": "100", "3mf": "support_material_interface_fan_speed_100_100.3mf", "group": "support_advanced"},
    
    # support_interface_spacing
    {"param": "support_interface_spacing", "value": "0", "3mf": "support_interface_spacing_0.3mf", "group": "support_advanced"},
    {"param": "support_bottom_interface_spacing", "value": "0.3", "3mf": "support_bottom_interface_spacing_0.3.3mf", "group": "support_advanced"},
    
    # support_interface_loop_pattern
    {"param": "support_interface_loop_pattern", "value": "1", "3mf": "support_interface_loop_pattern_enabled.3mf", "group": "support_advanced"},
    
    # support_interface_speed
    {"param": "support_interface_speed", "value": "60", "3mf": "support_interface_speed_60.3mf", "group": "support_advanced"},
    {"param": "support_interface_speed", "value": "100", "3mf": "support_interface_speed_100.3mf", "group": "support_advanced"},
    
    # tree_support_branch_diameter
    {"param": "tree_support_branch_diameter", "value": "3", "3mf": "tree_support_branch_diameter_3.3mf", "group": "support_tree"},
    {"param": "tree_support_branch_diameter", "value": "5", "3mf": "tree_support_branch_diameter_5.3mf", "group": "support_tree"},
    
    # tree_support_branch_angle
    {"param": "tree_support_branch_angle", "value": "30", "3mf": "tree_support_branch_angle_30.3mf", "group": "support_tree"},
    {"param": "tree_support_branch_angle", "value": "60", "3mf": "tree_support_branch_angle_60.3mf", "group": "support_tree"},
    
    # tree_support_wall_count
    {"param": "tree_support_wall_count", "value": "1", "3mf": "tree_support_wall_count_1.3mf", "group": "support_advanced"},
    {"param": "tree_support_wall_count", "value": "2", "3mf": "tree_support_wall_count_2.3mf", "group": "support_advanced"},
    
    # tree_support_wall_count_tree
    {"param": "tree_support_wall_count_tree", "value": "1", "3mf": "tree_support_wall_count_tree_1.3mf", "group": "support_tree"},
    {"param": "tree_support_wall_count_tree", "value": "2", "3mf": "tree_support_wall_count_tree_2.3mf", "group": "support_tree"},
    
    # tree_support_branch_distance
    {"param": "tree_support_branch_distance", "value": "0.5", "3mf": "tree_support_branch_distance_0.5.3mf", "group": "support_tree"},
    {"param": "tree_support_branch_distance", "value": "1", "3mf": "tree_support_branch_distance_1.3mf", "group": "support_tree"},
    {"param": "tree_support_branch_distance", "value": "1.5", "3mf": "tree_support_branch_distance_1.5.3mf", "group": "support_tree"},
    
    # tree_support_tip_diameter
    {"param": "tree_support_tip_diameter", "value": "0.6", "3mf": "tree_support_tip_diameter_0.6.3mf", "group": "support_tree"},
    {"param": "tree_support_tip_diameter", "value": "1", "3mf": "tree_support_tip_diameter_1.3mf", "group": "support_tree"},
]

BASE_PATH = Path(__file__).parent / "data" / "models" / "process" / "support"


def modify_config_value(config: dict, param_name: str, expected_value) -> dict:
    """
    修改配置中的参数值（参考 generate_extruder_x_3mf.py）
    
    关键：将修改的参数添加到 different_settings_to_system 数组中
    格式: ["param1;param2;param3", ""] - 分号分隔的字符串
    """
    old_value = config.get(param_name, "<未设置>")
    
    # 修改配置值
    config[param_name] = expected_value
    
    # 处理 different_settings_to_system
    if "different_settings_to_system" not in config:
        config["different_settings_to_system"] = [param_name, ""]
    else:
        settings_list = config["different_settings_to_system"]
        
        if settings_list and len(settings_list) >= 1:
            first_elem = settings_list[0] if settings_list[0] else ""
            
            if first_elem:
                # 解析现有参数
                existing_params = first_elem.split(";")
                # 添加新参数（避免重复）
                if param_name not in existing_params:
                    existing_params.append(param_name)
                settings_list[0] = ";".join(existing_params)
            else:
                settings_list[0] = param_name
        
        config["different_settings_to_system"] = settings_list
    
    print(f"  {param_name}: {old_value} -> {expected_value}")
    return config


def save_3mf_config(extracted_dir: Path, config: dict) -> None:
    """
    保存 3MF 配置文件
    
    注意：different_settings_to_system 必须紧跟在 detect_thin_wall 之后
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
        
        # 如果没有 detect_thin_wall，就放在末尾
        if "different_settings_to_system" not in ordered_config:
            ordered_config["different_settings_to_system"] = diff_settings
        
        config = ordered_config
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def modify_3mf_param(file_path: Path, param_name: str, new_value: str):
    """修改 3MF 文件中的参数值"""
    if not file_path.exists():
        print(f"  [SKIP] 文件不存在: {file_path}")
        return False
    
    temp_dir = file_path.parent / "_temp_3mf"
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # 解压 3MF
        with zipfile.ZipFile(file_path, 'r') as zf:
            zf.extractall(temp_dir)
        
        # 修改配置文件
        config_path = temp_dir / "Metadata" / "project_settings.config"
        if not config_path.exists():
            print(f"  [SKIP] 配置文件不存在: {config_path}")
            return False
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 修改参数（使用 modify_config_value）
        config = modify_config_value(config, param_name, new_value)
        
        # 保存配置（使用 save_3mf_config 确保顺序正确）
        save_3mf_config(temp_dir, config)
        
        # 重新打包
        with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path_full = Path(root) / file
                    arcname = file_path_full.relative_to(temp_dir)
                    zf.write(file_path_full, arcname)
        
        return True
        
    finally:
        # 清理临时目录
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


def main():
    print("=" * 60)
    print("批量修改 3MF 文件参数值")
    print("=" * 60)
    
    success_count = 0
    fail_count = 0
    
    for case in FAILED_CASES:
        param = case["param"]
        value = case["value"]
        filename = case["3mf"]
        group = case["group"]
        
        # 构建文件路径
        file_path = BASE_PATH / group / param / filename
        
        print(f"\n处理: {filename}")
        print(f"  参数: {param} = {value}")
        
        if modify_3mf_param(file_path, param, value):
            success_count += 1
            print(f"  [OK] 修改成功")
        else:
            fail_count += 1
            print(f"  [FAIL] 修改失败")
    
    print("\n" + "=" * 60)
    print(f"完成: {success_count} 成功, {fail_count} 失败")
    print("=" * 60)


if __name__ == "__main__":
    main()
