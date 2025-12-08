"""
生成 brim 参数测试用的 3MF 文件

此脚本会生成包含不同 brim 参数设置的 3MF 文件，用于自动化测试。
"""
import json
import zipfile
from pathlib import Path
import shutil

# 基础3MF模板路径（使用简单的立方体模型）
BASE_3MF_TEMPLATE = Path(__file__).parent / "base_cube.3mf"

# 目标输出目录
TARGET_BASE_DIR = Path(__file__).parent.parent.parent.parent / "data" / "models" / "others" / "brim"

# brim 参数配置
BRIM_CONFIGS = {
    "brim_type": [
        ("brim_type_auto_brim", {"brim_type": "auto_brim"}),
        ("brim_type_outer_only", {"brim_type": "outer_only"}),
        ("brim_type_outer_and_inner", {"brim_type": "outer_and_inner"}),
    ],
    "brim_width": [
        ("brim_width_3mm", {"brim_width": 3}),
        ("brim_width_5mm", {"brim_width": 5}),
        ("brim_width_10mm", {"brim_width": 10}),
    ],
    "brim_object_gap": [
        ("brim_object_gap_0mm", {"brim_object_gap": 0}),
        ("brim_object_gap_0.1mm", {"brim_object_gap": 0.1}),
        ("brim_object_gap_0.5mm", {"brim_object_gap": 0.5}),
    ],
    "brim_ears_max_angle": [
        ("brim_ears_max_angle_90", {"brim_ears_max_angle": 90}),
        ("brim_ears_max_angle_125", {"brim_ears_max_angle": 125}),
        ("brim_ears_max_angle_160", {"brim_ears_max_angle": 160}),
    ],
    "brim_ears_detection_length": [
        ("brim_ears_detection_length_0.5mm", {"brim_ears_detection_length": 0.5}),
        ("brim_ears_detection_length_1mm", {"brim_ears_detection_length": 1}),
        ("brim_ears_detection_length_2mm", {"brim_ears_detection_length": 2}),
    ],
}


def modify_3mf_config(template_path: Path, output_path: Path, param_updates: dict):
    """
    修改 3MF 文件中的参数配置
    
    Args:
        template_path: 模板3MF文件路径
        output_path: 输出3MF文件路径
        param_updates: 要更新的参数字典
    """
    # 创建临时目录
    temp_dir = output_path.parent / "_temp_3mf"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # 解压3MF文件
        with zipfile.ZipFile(template_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # 读取并修改配置文件
        config_file = temp_dir / "Metadata" / "project_settings.config"
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 更新参数
            for key, value in param_updates.items():
                config[key] = value
            
            # 写回配置文件
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        
        # 重新打包为3MF文件
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zip_out:
            for file_path in temp_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(temp_dir)
                    zip_out.write(file_path, arcname)
        
        print(f"✓ 生成: {output_path.name}")
    
    finally:
        # 清理临时目录
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


def main():
    """生成所有 brim 参数测试用的 3MF 文件"""
    
    if not BASE_3MF_TEMPLATE.exists():
        print(f"错误: 模板文件不存在: {BASE_3MF_TEMPLATE}")
        print("请先准备一个基础的 3MF 文件（例如简单立方体）作为模板")
        return
    
    print(f"使用模板: {BASE_3MF_TEMPLATE}")
    print(f"输出目录: {TARGET_BASE_DIR}\n")
    
    total_files = 0
    
    # 遍历所有参数配置
    for param_name, test_cases in BRIM_CONFIGS.items():
        param_dir = TARGET_BASE_DIR / param_name
        param_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"生成 {param_name} 测试文件:")
        
        for file_name, param_updates in test_cases:
            output_file = param_dir / f"{file_name}.3mf"
            modify_3mf_config(BASE_3MF_TEMPLATE, output_file, param_updates)
            total_files += 1
        
        print()
    
    print(f"完成! 共生成 {total_files} 个 3MF 文件")
    print(f"\n生成的文件位于:")
    for param_name in BRIM_CONFIGS.keys():
        print(f"  - {TARGET_BASE_DIR / param_name}")


if __name__ == "__main__":
    main()
