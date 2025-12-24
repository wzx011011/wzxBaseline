"""
Reorganize support parameter test files into correct directory structure.

This script reorganizes the support parameter test files according to the
subdirectory structure defined in process_parameters_validation.md:
- support_basic: Basic support parameters (7)
- support_raft: Raft parameters (2)
- support_filament: Support filament parameters (3)
- support_advanced: Advanced parameters (8)
- support_tree: Tree support parameters (5)
"""

import shutil
from pathlib import Path

# Define parameter groups
GROUPS = {
    'support_basic': [
        'enable_support',
        'support_type',
        'support_style',
        'support_threshold_angle',
        'support_on_build_plate_only',
        'support_critical_regions_only',
        'support_remove_small_overhang',
    ],
    'support_raft': [
        'raft_layers',
        'raft_contact_distance',
    ],
    'support_filament': [
        'support_filament',
        'support_interface_filament',
        'support_interface_not_for_body',
    ],
    'support_advanced': [
        'support_interface_top_layers',
        'support_interface_bottom_layers',
        'support_interface_pattern',
        'support_interface_spacing',
        'support_bottom_interface_spacing',
        'support_interface_loop_pattern',
        'support_interface_speed',
        'support_interface_min_area',
    ],
    'support_tree': [
        'tree_support_branch_diameter',
        'tree_support_branch_angle',
        'tree_support_wall_count',
        'tree_support_branch_distance',
        'tree_support_tip_diameter',
    ],
}

BASE_JSON = Path('data/case_input/process')
BASE_MODEL = Path('data/models/process')
OLD_DIR = 'support'


def main():
    """Reorganize files into correct directory structure."""
    print("🔄 Reorganizing support parameter files...")
    print()
    
    # Create new group directories
    for group in GROUPS:
        (BASE_JSON / group).mkdir(parents=True, exist_ok=True)
        (BASE_MODEL / group).mkdir(parents=True, exist_ok=True)
    
    moved_json = 0
    moved_model = 0
    
    # Move JSON files
    print("📄 Moving JSON configuration files:")
    for group, params in GROUPS.items():
        print(f"  {group}:")
        for param in params:
            src_json = BASE_JSON / OLD_DIR / f'{param}.json'
            dst_json = BASE_JSON / group / f'{param}.json'
            
            if src_json.exists():
                shutil.move(str(src_json), str(dst_json))
                print(f"    ✅ {param}.json")
                moved_json += 1
            else:
                print(f"    ⚠️  {param}.json (not found)")
    
    print()
    
    # Move model directories
    print("📁 Moving 3MF model directories:")
    for group, params in GROUPS.items():
        print(f"  {group}:")
        for param in params:
            src_model = BASE_MODEL / OLD_DIR / param
            dst_model = BASE_MODEL / group / param
            
            if src_model.exists():
                shutil.move(str(src_model), str(dst_model))
                print(f"    ✅ {param}/")
                moved_model += 1
            else:
                print(f"    ⚠️  {param}/ (not found)")
    
    print()
    
    # Try to remove old directory
    old_json_dir = BASE_JSON / OLD_DIR
    old_model_dir = BASE_MODEL / OLD_DIR
    
    if old_json_dir.exists() and not any(old_json_dir.iterdir()):
        old_json_dir.rmdir()
        print(f"🗑️  Removed empty directory: {old_json_dir}")
    
    if old_model_dir.exists() and not any(old_model_dir.iterdir()):
        old_model_dir.rmdir()
        print(f"🗑️  Removed empty directory: {old_model_dir}")
    
    print()
    print("=" * 60)
    print(f"✨ Summary:")
    print(f"   Moved {moved_json} JSON files")
    print(f"   Moved {moved_model} model directories")
    print()
    print("📋 New directory structure:")
    for group, params in GROUPS.items():
        print(f"   {group}: {len(params)} parameters")


if __name__ == "__main__":
    main()
