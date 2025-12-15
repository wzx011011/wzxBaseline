"""验证生成的 3MF 文件配置是否正确"""
import zipfile
import json
from pathlib import Path

# 验证 nozzle_diameter_0.6.3mf
test_file = Path("data/models/printer/extruder_x/size/nozzle_diameter/nozzle_diameter_0.6.3mf")

with zipfile.ZipFile(test_file, 'r') as zf:
    config_data = zf.read('Metadata/project_settings.config')
    config = json.loads(config_data)
    
    print(f"✓ 文件: {test_file.name}")
    
    nozzle_value = config.get('nozzle_diameter')
    print(f"✓ nozzle_diameter 配置值: {nozzle_value}")
    print(f"✓ 类型: {type(nozzle_value)}")
    
    # 验证 different_settings_to_system
    diff_settings = config.get('different_settings_to_system', [])
    print(f"✓ different_settings_to_system: {diff_settings}")
    
    # 检查值格式（应该是数组）
    if isinstance(nozzle_value, list) and len(nozzle_value) == 1 and nozzle_value[0] == '0.6':
        print("✓ 参数值格式正确！（数组格式）")
    else:
        print(f"✗ 参数值格式错误！期望 ['0.6']，实际 {nozzle_value}")
    
    if 'nozzle_diameter' in diff_settings:
        print("✓✓ 完全正确！nozzle_diameter 已在 different_settings_to_system 中")
    else:
        print(f"✗✗ 错误：nozzle_diameter 未在 different_settings_to_system 中")
