"""
生成 special_mode 参数测试用的 3MF 文件

此脚本会从 template_model.3mf 复制并重命名文件到对应目录。
参数配置需要手动在切片器 UI 中设置后导出。
"""
from pathlib import Path
import shutil

# 模板3MF路径（使用 template_model.3mf）
TEMPLATE_3MF = Path(__file__).parent.parent.parent.parent / "data" / "models" / "template_model.3mf"

# 目标输出目录
TARGET_BASE_DIR = Path(__file__).parent.parent.parent.parent / "data" / "models" / "others" / "special_mode"

# special_mode 参数文件名列表（只需要文件名，参数手动配置）
SPECIAL_MODE_FILES = {
    "slicing_mode": [
        "slicing_mode_regular",
        "slicing_mode_even_odd",
        "slicing_mode_close_holes",
    ],
    "print_sequence": [
        "print_sequence_by_layer",
        "print_sequence_by_object",
        "print_sequence_by_default",
    ],
    "print_order": [
        "print_order_default",
        "print_order_as_object_list",
    ],
    "spiral_mode": [
        "spiral_mode_disabled",
        "spiral_mode_enabled",
    ],
    "spiral_mode_smooth": [
        "spiral_mode_smooth_disabled",
        "spiral_mode_smooth_enabled",
    ],
    "spiral_mode_max_xy_smoothing": [
        "spiral_mode_max_xy_smoothing_0",
        "spiral_mode_max_xy_smoothing_50",
        "spiral_mode_max_xy_smoothing_100",
    ],
    "ignore_inner_color": [
        "ignore_inner_color_disabled",
        "ignore_inner_color_enabled",
    ],
    "timelapse_type": [
        "timelapse_type_traditional",
        "timelapse_type_smooth",
        "timelapse_type_close",
    ],
    "fuzzy_skin": [
        "fuzzy_skin_none",
        "fuzzy_skin_external",
        "fuzzy_skin_all",
        "fuzzy_skin_all_walls",
    ],
    "fuzzy_skin_point_distance": [
        "fuzzy_skin_point_distance_0.5mm",
        "fuzzy_skin_point_distance_0.8mm",
        "fuzzy_skin_point_distance_1.5mm",
    ],
    "fuzzy_skin_thickness": [
        "fuzzy_skin_thickness_0.1mm",
        "fuzzy_skin_thickness_0.3mm",
        "fuzzy_skin_thickness_0.5mm",
    ],
    "fuzzy_skin_first_layer": [
        "fuzzy_skin_first_layer_disabled",
        "fuzzy_skin_first_layer_enabled",
    ],
}


def copy_template_file(template_path: Path, output_path: Path):
    """
    复制模板文件并重命名
    
    Args:
        template_path: 模板3MF文件路径
        output_path: 输出3MF文件路径
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(template_path, output_path)
    print(f"✓ 复制: {output_path.name}")


def main():
    """生成所有 special_mode 参数测试用的 3MF 文件（仅复制模板，不修改参数）"""
    
    if not TEMPLATE_3MF.exists():
        print(f"错误: 模板文件不存在: {TEMPLATE_3MF}")
        print("请确保 template_model.3mf 存在于 data/models/ 目录")
        return
    
    print(f"使用模板: {TEMPLATE_3MF}")
    print(f"输出目录: {TARGET_BASE_DIR}\n")
    
    total_files = 0
    
    # 遍历所有参数文件名
    for param_name, file_names in SPECIAL_MODE_FILES.items():
        param_dir = TARGET_BASE_DIR / param_name
        param_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"生成 {param_name} 测试文件:")
        
        for file_name in file_names:
            output_file = param_dir / f"{file_name}.3mf"
            copy_template_file(TEMPLATE_3MF, output_file)
            total_files += 1
        
        print()
    
    print(f"完成! 共生成 {total_files} 个 3MF 文件（从模板复制）")
    print(f"\n生成的文件位于:")
    for param_name in SPECIAL_MODE_FILES.keys():
        print(f"  - {TARGET_BASE_DIR / param_name}")
    
    print("\n重要提示:")
    print("  ⚠️  这些 3MF 文件是从模板直接复制的，不包含参数配置！")
    print("  ⚠️  请手动在切片器 UI 中设置参数后，导出对应的 3MF 文件！")
    print("\n手动配置步骤:")
    print("  1. 在切片器中打开对应的 3MF 文件")
    print("  2. 在 UI 中配置参数（如 slicing_mode=contour）")
    print("  3. 保存/导出 3MF 文件，覆盖原文件")
    print("  4. 重复以上步骤，直到所有测试文件都配置完毕")


if __name__ == "__main__":
    main()
