"""
从模板创建 skirt 参数测试用例的 3MF 文件
"""
import zipfile
import shutil
import os
import json
from pathlib import Path
import xml.etree.ElementTree as ET

# 定义模板和目标路径
TEMPLATE_PATH = Path("engine_params/data/models/template_model.3mf")
TARGET_BASE_DIR = Path("engine_params/data/models/others/skirt_type")

# 确保目标目录存在
TARGET_BASE_DIR.mkdir(parents=True, exist_ok=True)

# 定义所有测试用例配置
test_cases = [
    # skirt_type 参数 (使用模板默认值 "combined")
    {
        "filename": "skirt_type_combined.3mf",
        "params": {}  # 使用默认值
    },
    
    # skirt_loops 参数
    {
        "filename": "skirt_loops_1.3mf",
        "params": {
            "skirt_loops": "1"
        }
    },
    {
        "filename": "skirt_loops_2.3mf",
        "params": {
            "skirt_loops": "2"
        }
    },
    {
        "filename": "skirt_loops_3.3mf",
        "params": {
            "skirt_loops": "3"
        }
    },
    
    # skirt_distance 参数
    {
        "filename": "skirt_distance_3mm.3mf",
        "params": {
            "skirt_distance": "3"
        }
    },
    {
        "filename": "skirt_distance_6mm.3mf",
        "params": {
            "skirt_distance": "6"
        }
    },
    {
        "filename": "skirt_distance_12mm.3mf",
        "params": {
            "skirt_distance": "12"
        }
    },
    
    # skirt_height 参数
    {
        "filename": "skirt_height_1.3mf",
        "params": {
            "skirt_height": "1"
        }
    },
    {
        "filename": "skirt_height_3.3mf",
        "params": {
            "skirt_height": "3"
        }
    },
    {
        "filename": "skirt_height_5.3mf",
        "params": {
            "skirt_height": "5"
        }
    },
    
    # skirt_speed 参数
    {
        "filename": "skirt_speed_50.3mf",
        "params": {
            "initial_layer_speed": "50"  # skirt使用初始层速度
        }
    },
    {
        "filename": "skirt_speed_100.3mf",
        "params": {
            "initial_layer_speed": "100"
        }
    },
    {
        "filename": "skirt_speed_150.3mf",
        "params": {
            "initial_layer_speed": "150"
        }
    },
    
    # min_skirt_length 参数
    {
        "filename": "min_skirt_length_100mm.3mf",
        "params": {
            "min_skirt_length": "100"
        }
    },
    {
        "filename": "min_skirt_length_250mm.3mf",
        "params": {
            "min_skirt_length": "250"
        }
    },
    {
        "filename": "min_skirt_length_500mm.3mf",
        "params": {
            "min_skirt_length": "500"
        }
    },
    
    # draft_shield 参数
    {
        "filename": "draft_shield_disabled.3mf",
        "params": {
            "draft_shield": "disabled"
        }
    },
    {
        "filename": "draft_shield_limited.3mf",
        "params": {
            "draft_shield": "limited"
        }
    },
    {
        "filename": "draft_shield_enabled.3mf",
        "params": {
            "draft_shield": "enabled"
        }
    },
]


def modify_3mf_config(template_path: Path, output_path: Path, params: dict):
    """
    修改 3MF 文件中的配置参数
    
    Args:
        template_path: 模板 3MF 文件路径
        output_path: 输出 3MF 文件路径
        params: 要修改的参数字典
    """
    # 创建临时目录
    temp_dir = Path("temp_3mf_extract")
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # 解压 3MF 文件（3MF 本质是 ZIP 格式）
        with zipfile.ZipFile(template_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Creality Print 使用 Metadata/project_settings.config 文件（JSON格式）
        config_file = temp_dir / "Metadata" / "project_settings.config"
        
        # 如果找到配置文件，修改参数
        if config_file.exists():
            modify_json_config_file(config_file, params)
        else:
            print(f"  警告: 找不到配置文件 {config_file}")
        
        # 重新打包为 3MF 文件
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in temp_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(temp_dir)
                    zipf.write(file_path, arcname)
        
        print(f"✓ 创建: {output_path.name}")
        
    finally:
        # 清理临时目录
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


def modify_json_config_file(config_path: Path, params: dict):
    """
    修改 JSON 格式的配置文件中的参数（Creality Print 使用）
    
    Args:
        config_path: 配置文件路径
        params: 要修改的参数字典
    """
    # 读取 JSON 配置文件
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 修改参数
    for param_name, param_value in params.items():
        if param_name in config:
            print(f"  修改参数: {param_name} = {param_value}")
        else:
            print(f"  添加新参数: {param_name} = {param_value}")
        config[param_name] = str(param_value)  # Creality Print 使用字符串值
    
    # 写回配置文件
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


def main():
    """主函数：批量创建所有测试用例的 3MF 文件"""
    
    if not TEMPLATE_PATH.exists():
        print(f"❌ 错误: 找不到模板文件 {TEMPLATE_PATH}")
        return
    
    print(f"📦 使用模板: {TEMPLATE_PATH}")
    print(f"📁 基础目录: {TARGET_BASE_DIR}")
    print(f"🔧 创建 {len(test_cases)} 个测试用例文件...\n")
    
    # 批量创建文件
    for i, test_case in enumerate(test_cases, 1):
        filename = test_case["filename"]
        params = test_case["params"]
        
        # 根据文件名确定子目录
        if filename.startswith("skirt_type_"):
            sub_dir = "skirt_type"
        elif filename.startswith("skirt_loops_"):
            sub_dir = "skirt_loops"
        elif filename.startswith("skirt_distance_"):
            sub_dir = "skirt_distance"
        elif filename.startswith("skirt_height_"):
            sub_dir = "skirt_height"
        elif filename.startswith("skirt_speed_"):
            sub_dir = "skirt_speed"
        elif filename.startswith("min_skirt_length_"):
            sub_dir = "min_skirt_length"
        elif filename.startswith("draft_shield_"):
            sub_dir = "draft_shield"
        else:
            sub_dir = "other"
        
        # 创建子目录
        target_dir = TARGET_BASE_DIR / sub_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = target_dir / filename
        
        print(f"[{i}/{len(test_cases)}] 参数: {params} → {sub_dir}/{filename}")
        modify_3mf_config(TEMPLATE_PATH, output_path, params)
    
    print(f"\n✅ 完成! 已创建 {len(test_cases)} 个 3MF 文件")
    print(f"📍 文件位置: {TARGET_BASE_DIR.absolute()}")


if __name__ == "__main__":
    main()
