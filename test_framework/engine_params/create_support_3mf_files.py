"""
Generate 3MF files for Support parameters testing.

This script copies the template model to create test cases for all support parameters.
After running this script, you need to manually configure each 3MF file in Creality Print
to set the corresponding parameter values.
"""

import shutil
from pathlib import Path

# Template model path
TEMPLATE_3MF = Path("data/models/template_model.3mf")

# Base directory for support parameter models
SUPPORT_BASE_DIR = Path("data/models/process/support")

# Define all test cases for each parameter
TEST_CASES = {
    "enable_support": [
        "support_disabled.3mf",
        "support_enabled.3mf",
    ],
    "support_type": [
        "support_type_normal.3mf",
        "support_type_tree.3mf",
    ],
    "support_style": [
        "support_style_default.3mf",
        "support_style_grid.3mf",
        "support_style_tree_organic.3mf",
    ],
    "support_threshold_angle": [
        "support_threshold_angle_30.3mf",
        "support_threshold_angle_45.3mf",
        "support_threshold_angle_60.3mf",
    ],
    "support_on_build_plate_only": [
        "support_on_build_plate_only_disabled.3mf",
        "support_on_build_plate_only_enabled.3mf",
    ],
    "support_critical_regions_only": [
        "support_critical_regions_only_disabled.3mf",
        "support_critical_regions_only_enabled.3mf",
    ],
    "support_remove_small_overhang": [
        "support_remove_small_overhang_disabled.3mf",
        "support_remove_small_overhang_enabled.3mf",
    ],
    "raft_layers": [
        "raft_layers_0.3mf",
        "raft_layers_2.3mf",
        "raft_layers_4.3mf",
    ],
    "raft_contact_distance": [
        "raft_contact_distance_0.1.3mf",
        "raft_contact_distance_0.2.3mf",
    ],
    "support_filament": [
        "support_filament_0.3mf",
        "support_filament_1.3mf",
    ],
    "support_interface_filament": [
        "support_interface_filament_0.3mf",
        "support_interface_filament_1.3mf",
    ],
    "support_interface_not_for_body": [
        "support_interface_not_for_body_disabled.3mf",
        "support_interface_not_for_body_enabled.3mf",
    ],
    "support_interface_top_layers": [
        "support_interface_top_layers_1.3mf",
        "support_interface_top_layers_2.3mf",
        "support_interface_top_layers_3.3mf",
    ],
    "support_interface_bottom_layers": [
        "support_interface_bottom_layers_1.3mf",
        "support_interface_bottom_layers_2.3mf",
        "support_interface_bottom_layers_3.3mf",
    ],
    "support_interface_pattern": [
        "support_interface_pattern_rectilinear.3mf",
        "support_interface_pattern_concentric.3mf",
        "support_interface_pattern_grid.3mf",
    ],
    "support_interface_spacing": [
        "support_interface_spacing_0.3.3mf",
        "support_interface_spacing_0.5.3mf",
        "support_interface_spacing_0.3mf",
    ],
    "support_bottom_interface_spacing": [
        "support_bottom_interface_spacing_0.3.3mf",
        "support_bottom_interface_spacing_0.5.3mf",
    ],
    "support_interface_loop_pattern": [
        "support_interface_loop_pattern_disabled.3mf",
        "support_interface_loop_pattern_enabled.3mf",
    ],
    "support_interface_speed": [
        "support_interface_speed_60.3mf",
        "support_interface_speed_80.3mf",
        "support_interface_speed_100.3mf",
    ],
    "support_interface_min_area": [
        "support_interface_min_area_5.3mf",
        "support_interface_min_area_10.3mf",
        "support_interface_min_area_20.3mf",
    ],
    "tree_support_branch_diameter": [
        "tree_support_branch_diameter_2.3mf",
        "tree_support_branch_diameter_3.3mf",
        "tree_support_branch_diameter_5.3mf",
    ],
    "tree_support_branch_angle": [
        "tree_support_branch_angle_30.3mf",
        "tree_support_branch_angle_45.3mf",
        "tree_support_branch_angle_60.3mf",
    ],
    "tree_support_wall_count": [
        "tree_support_wall_count_0.3mf",
        "tree_support_wall_count_1.3mf",
        "tree_support_wall_count_2.3mf",
    ],
    "tree_support_branch_distance": [
        "tree_support_branch_distance_0.5.3mf",
        "tree_support_branch_distance_1.3mf",
        "tree_support_branch_distance_1.5.3mf",
    ],
    "tree_support_tip_diameter": [
        "tree_support_tip_diameter_0.6.3mf",
        "tree_support_tip_diameter_0.8.3mf",
        "tree_support_tip_diameter_1.3mf",
    ],
}


def main():
    """Generate all 3MF files for support parameters."""
    if not TEMPLATE_3MF.exists():
        print(f"❌ Template model not found: {TEMPLATE_3MF}")
        print(f"   Please ensure the template model exists at this location.")
        return
    
    print(f"📦 Using template: {TEMPLATE_3MF}")
    print(f"🎯 Target directory: {SUPPORT_BASE_DIR}")
    print()
    
    total_created = 0
    total_skipped = 0
    
    for param_name, file_list in TEST_CASES.items():
        param_dir = SUPPORT_BASE_DIR / param_name
        
        if not param_dir.exists():
            print(f"⚠️  Directory not found: {param_dir}")
            continue
        
        print(f"📁 {param_name}:")
        
        for filename in file_list:
            target_path = param_dir / filename
            
            if target_path.exists():
                print(f"   ⏭️  {filename} (already exists)")
                total_skipped += 1
            else:
                shutil.copy2(TEMPLATE_3MF, target_path)
                print(f"   ✅ {filename}")
                total_created += 1
        
        print()
    
    print("=" * 60)
    print(f"✨ Summary:")
    print(f"   Created: {total_created} files")
    print(f"   Skipped: {total_skipped} files")
    print()
    print("⚠️  IMPORTANT: Next Steps")
    print("=" * 60)
    print("1. Open each 3MF file in Creality Print 7.0 Beta")
    print("2. Configure the corresponding parameter value in the UI")
    print("3. Save/Export the 3MF file to apply the configuration")
    print()
    print("Example for 'support_type_normal.3mf':")
    print("  - Open the file in Creality Print")
    print("  - Go to Support settings")
    print("  - Set 'Support Type' to 'Normal (Auto)'")
    print("  - Click 'Save Project' or 'Export'")
    print()


if __name__ == "__main__":
    main()
