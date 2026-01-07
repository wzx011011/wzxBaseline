#!/usr/bin/env python
"""
批量生成 Quality 页面的 3MF 文件
从 test_framework/template_model.3mf 复制
"""

import shutil
from pathlib import Path

# 所有需要生成的 3MF 文件配置
QUALITY_3MF_FILES = {
    "line_width": {
        "line_width": ["0.4mm", "0.5mm", "0.6mm"],
        "internal_solid_infill_line_width": ["0.4mm", "0.45mm", "0.5mm"],
    },
    "seam": {
        "seam_slope_conditional": ["enabled", "disabled"],
        "seam_slope_entire_loop": ["enabled", "disabled"],
        "seam_slope_inner_walls": ["enabled", "disabled"],
        "seam_slope_min_length": ["0mm", "10mm", "20mm"],
        "seam_slope_start_height": ["0mm", "0.5mm", "1.0mm"],
        "seam_slope_steps": ["0", "5", "10"],
        "scarf_angle_threshold": ["0deg", "30deg", "60deg"],
        "scarf_joint_speed": ["0", "30", "50"],
        "scarf_overhang_threshold": ["0mm", "10mm", "20mm"],
    },
    "bridging": {
        "bridge_angle": ["0deg", "45deg", "90deg"],
        "bridge_flow": ["0.95", "1.0", "1.1"],
        "bridge_density": ["80percent", "100percent"],
        "bridge_speed": ["20", "25", "30"],
        "thick_bridges": ["enabled", "disabled"],
        "dont_filter_internal_bridges": ["enabled", "disabled"],
        "thick_internal_bridges": ["enabled", "disabled"],
        "internal_bridge_speed": ["100percent", "150percent"],
        "counterbore_hole_bridging": ["none", "sparse_infill"],
    },
    "overhangs": {
        "extra_perimeters_on_overhangs": ["enabled", "disabled"],
        "make_overhang_printable": ["enabled", "disabled"],
        "make_overhang_printable_angle": ["45deg", "55deg", "65deg"],
        "make_overhang_printable_hole_size": ["0mm", "5mm", "10mm"],
        "overhang_optimization": ["enabled", "disabled"],
    },
    "ironing": {
        "ironing_type": ["no_ironing", "top_surface", "all_solid"],
        "ironing_pattern": ["rectilinear", "concentric"],
        "ironing_flow": ["10percent", "15percent", "20percent"],
        "ironing_spacing": ["0.1mm", "0.15mm", "0.2mm"],
        "ironing_speed": ["15", "20", "30"],
        "ironing_angle": ["0deg", "45deg", "90deg"],
    },
    "wall_generator": {
        "wall_transition_angle": ["5deg", "10deg", "15deg"],
        "wall_transition_filter_deviation": ["20percent", "25percent", "30percent"],
        "wall_transition_length": ["80percent", "100percent", "120percent"],
        "wall_distribution_count": ["1", "2", "3"],
        "min_feature_size": ["20percent", "25percent", "30percent"],
        "min_bead_width": ["80percent", "85percent", "90percent"],
        "initial_layer_min_bead_width": ["80percent", "85percent", "90percent"],
    },
    "precision": {
        "slice_closing_radius": ["0.03mm", "0.049mm", "0.06mm"],
        "resolution": ["0.01mm", "0.012mm", "0.02mm"],
        "hole_to_polyhole": ["enabled", "disabled"],
        "hole_to_polyhole_threshold": ["0.01mm", "0.02mm"],
        "hole_to_polyhole_twisted": ["enabled", "disabled"],
        "precise_outer_wall": ["enabled", "disabled"],
        "precise_z_height": ["0mm", "0.1mm", "0.2mm"],
    },
    "wall_and_surfaces": {
        "min_width_top_surface": ["150percent", "200percent", "250percent"],
        "only_one_wall_first_layer": ["enabled", "disabled"],
        "detect_thin_wall": ["enabled", "disabled"],
        "detect_overhang_wall": ["enabled", "disabled"],
        "overhang_reverse": ["enabled", "disabled"],
        "overhang_reverse_internal_only": ["enabled", "disabled"],
        "overhang_reverse_threshold": ["40percent", "50percent", "60percent"],
        "wipe_on_loops": ["enabled", "disabled"],
        "wipe_before_external_loop": ["enabled", "disabled"],
    },
}


def main():
    """生成所有 3MF 文件"""
    base_path = Path(__file__).resolve().parent.parent  # 回到 test_framework 目录
    template_path = base_path / "template_model.3mf"
    
    if not template_path.exists():
        print(f"❌ 模板文件不存在: {template_path}")
        return 1
    
    print("=" * 70)
    print("批量生成 Quality 页面 3MF 文件")
    print("=" * 70)
    print(f"模板: {template_path}")
    
    models_root = base_path / "engine_params" / "data" / "models"
    total_created = 0
    total_skipped = 0
    
    for category, params in QUALITY_3MF_FILES.items():
        print(f"\n【{category}】")
        
        for param_name, slugs in params.items():
            param_dir = models_root / "process" / "quality" / category / param_name
            param_dir.mkdir(parents=True, exist_ok=True)
            
            for slug in slugs:
                filename = f"{param_name}_{slug}.3mf"
                target_path = param_dir / filename
                
                if target_path.exists():
                    print(f"  ⏭️  {filename}")
                    total_skipped += 1
                else:
                    shutil.copy2(template_path, target_path)
                    print(f"  ✅ {filename}")
                    total_created += 1
    
    print("\n" + "=" * 70)
    print("生成完成!")
    print("=" * 70)
    print(f"创建: {total_created} 个")
    print(f"跳过: {total_skipped} 个")
    print(f"总计: {total_created + total_skipped} 个")
    
    if total_created > 0:
        print("\n⚠️  重要提示:")
        print("=" * 70)
        print("所有新生成的 3MF 文件需要在 CrealityPrint 中:")
        print("1. 打开 3MF 文件")
        print("2. 在 Process → Quality 页面设置对应参数值")
        print("3. 保存文件")
        print(f"\n建议使用 batch_fix_new_3mf_only.py 批量配置参数值")
    
    return 0


if __name__ == "__main__":
    exit(main())
