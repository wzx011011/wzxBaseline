"""
生成 post_process_notes 参数测试用的 3MF 文件

此脚本会从 template_model.3mf 复制并重命名文件到对应目录。
参数配置需要手动在切片器 UI 中设置后导出。
"""
from pathlib import Path
import shutil

# 模板3MF路径（使用 template_model.3mf）
TEMPLATE_3MF = Path(__file__).parent.parent.parent.parent / "data" / "models" / "template_model.3mf"

# 目标输出目录
TARGET_BASE_DIR = Path(__file__).parent.parent.parent.parent / "data" / "models" / "others" / "post_process_notes"

# post_process_notes 参数文件名列表（只需要文件名，参数手动配置）
POST_PROCESS_NOTES_FILES = {
    "post_process": [
        "post_process_none",
    ],
    "notes": [
        "notes_empty",
        "notes_custom",
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
    """生成所有 post_process_notes 参数测试用的 3MF 文件（仅复制模板，不修改参数）"""
    
    if not TEMPLATE_3MF.exists():
        print(f"错误: 模板文件不存在: {TEMPLATE_3MF}")
        print("请确保 template_model.3mf 存在于 data/models/ 目录")
        return
    
    print(f"使用模板: {TEMPLATE_3MF}")
    print(f"输出目录: {TARGET_BASE_DIR}\n")
    
    total_files = 0
    
    # 遍历所有参数文件名
    for param_name, file_names in POST_PROCESS_NOTES_FILES.items():
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
    for param_name in POST_PROCESS_NOTES_FILES.keys():
        print(f"  - {TARGET_BASE_DIR / param_name}")
    
    print("\n重要提示:")
    print("  ⚠️  这些 3MF 文件是从模板直接复制的，不包含参数配置！")
    print("  ⚠️  请手动在切片器 UI 中设置参数后，导出对应的 3MF 文件！")
    print("\n手动配置步骤:")
    print("  1. 在切片器中打开对应的 3MF 文件")
    print("  2. 找到对应的参数面板")
    print("  3. 配置对应参数")
    print("  4. 保存/导出 3MF 文件，覆盖原文件")
    print("  5. 重复以上步骤，直到所有测试文件都配置完毕")
    print("\n配置位置说明:")
    print("  - post_process: Others → Post-processing Scripts")
    print("    注意：此参数无法通过 G-code 内容直接校验")
    print("  - notes: Others → Notes")
    print("    示例备注内容：'Test notes for G-code validation'")


if __name__ == "__main__":
    main()
