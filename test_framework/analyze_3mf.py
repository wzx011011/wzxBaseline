import zipfile
import json

# 提取配置文件
z = zipfile.ZipFile('e:/wzx/C3DBaseline/test_framework/engine_params/case/params/others/base_cube.3mf')
content = z.read('Metadata/project_settings.config')
data = json.loads(content)

# 搜索 print_order 相关参数
print("=== 搜索 print_order 相关参数 ===")
for key in sorted(data.keys()):
    if any(word in key.lower() for word in ['order', 'sequence', 'wall', 'perimeter']):
        print(f"{key}: {data[key]}")

print("\n=== Special Mode 参数 ===")
special_params = [
    'spiral_mode',
    'spiral_mode_smooth', 
    'spiral_mode_max_xy_smoothing',
    'fuzzy_skin',
    'fuzzy_skin_thickness',
    'fuzzy_skin_point_distance',
    'fuzzy_skin_first_layer',
    'slicing_mode',
    'print_sequence',
    'timelapse_type',
    'ignore_inner_color'
]

for param in special_params:
    print(f"{param}: {data.get(param, 'NOT FOUND')}")
