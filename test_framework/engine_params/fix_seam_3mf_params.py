#!/usr/bin/env python
"""
批量修改 Seam 参数的 3MF 文件中的参数值为期望值
"""
import zipfile
import json
import os
import shutil
from pathlib import Path

# Seam 参数用例的参数和期望值映射
SEAM_CASES = [
    # seam_position
    {"param": "seam_position", "value": "aligned", "3mf": "seam_position_aligned.3mf", "group": "seam_position"},
    {"param": "seam_position", "value": "nearest", "3mf": "seam_position_nearest.3mf", "group": "seam_position"},
    {"param": "seam_position", "value": "random", "3mf": "seam_position_random.3mf", "group": "seam_position"},
    
    # seam_gap
    {"param": "seam_gap", "value": "0", "3mf": "seam_gap_0.3mf", "group": "seam_gap"},
    {"param": "seam_gap", "value": "0.15", "3mf": "seam_gap_0.15.3mf", "group": "seam_gap"},
    
    # staggered_inner_seams
    {"param": "staggered_inner_seams", "value": "0", "3mf": "staggered_inner_seams_false.3mf", "group": "staggered_inner_seams"},
    {"param": "staggered_inner_seams", "value": "1", "3mf": "staggered_inner_seams_true.3mf", "group": "staggered_inner_seams"},
    
    # seam_slope_type
    {"param": "seam_slope_type", "value": "none", "3mf": "seam_slope_type_none.3mf", "group": "seam_slope_type"},
    {"param": "seam_slope_type", "value": "linear", "3mf": "seam_slope_type_linear.3mf", "group": "seam_slope_type"},
    
    # scarf_joint_flow_ratio
    {"param": "scarf_joint_flow_ratio", "value": "80%", "3mf": "scarf_joint_flow_ratio_0.8.3mf", "group": "scarf_joint_flow_ratio"},
    {"param": "scarf_joint_flow_ratio", "value": "100%", "3mf": "scarf_joint_flow_ratio_1.0.3mf", "group": "scarf_joint_flow_ratio"},
    {"param": "scarf_joint_flow_ratio", "value": "120%", "3mf": "scarf_joint_flow_ratio_1.2.3mf", "group": "scarf_joint_flow_ratio"},
]

BASE_PATH = Path(__file__).parent / "data" / "models" / "process" / "quality" / "seam"


def modify_config_value(config: dict, param_name: str, expected_value) -> dict:
    """
    修改配置中的参数值（参考 generate_extruder_x_3mf.py）
    
    关键：将修改的参数添加到 different_settings_to_system 中
    """
    old_value = config.get(param_name, "<未设置>")
    
    # 修改配置值
    config[param_name] = expected_value
    
    # 处理 different_settings_to_system - 应该是字符串格式
    if "different_settings_to_system" not in config:
        config["different_settings_to_system"] = param_name
    else:
        existing = config["different_settings_to_system"]
        # 如果是列表格式，转换为字符串
        if isinstance(existing, list) and len(existing) > 0:
            existing = existing[0] if existing[0] else ""
        
        if existing:
            # 解析现有参数
            existing_params = existing.split(";") if isinstance(existing, str) else []
            # 添加新参数（避免重复）
            if param_name not in existing_params:
                existing_params.append(param_name)
            config["different_settings_to_system"] = ";".join(existing_params)
        else:
            config["different_settings_to_system"] = param_name
    
    print(f"  {param_name}: {old_value} -> {expected_value}")
    return config


def save_3mf_config(extracted_dir: Path, config: dict) -> None:
    """
    保存 3MF 配置文件
    """
    config_path = extracted_dir / "Metadata" / "project_settings.config"
    
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
    print("批量修改 Seam 参数的 3MF 文件参数值")
    print("=" * 60)
    
    success_count = 0
    fail_count = 0
    
    for case in SEAM_CASES:
        param = case["param"]
        value = case["value"]
        filename = case["3mf"]
        group = case["group"]
        
        # 构建文件路径
        file_path = BASE_PATH / group / filename
        
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
