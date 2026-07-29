"""
Test extruder assignment parameters
"""

from pathlib import Path
import pytest

from engine_params.src.gcode.process.extruder_assignment_check import (
    parse_wall_filament,
)


@pytest.mark.engine_params
def test_wall_filament(
    slice_and_export: Path,
    expected_value: str,
):
    """Test wall_filament parameter (Level 1 - Config)"""
    # 验证方法：使用双材料悬挑及擦料塔专用 3MF切片，解析Inner/Outer wall 的每层路径数、顺序和几何覆盖；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path = slice_and_export
    ok, actual, details = parse_wall_filament(gcode_path, expected_value)
    
    assert ok, f"wall_filament expected {expected_value}, got {actual}: {details}"
