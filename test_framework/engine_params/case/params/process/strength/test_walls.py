from pathlib import Path

import pytest
from engine_params.src.gcode.process.strength.walls_check import parse_wall_loops, parse_alternate_extra_wall, parse_detect_thin_wall

# ================== wall_loops ==================

@pytest.mark.engine_params
def test_wall_loops(slice_and_export: Path,
                     expected_wall_loops: int):
    # 验证方法：使用实体、薄壁、桥接或填充专用 3MF切片，解析Inner/Outer wall 的每层路径数、顺序和几何覆盖；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ret = parse_wall_loops(gcode_path, expected_wall_loops=expected_wall_loops)

    assert ret[0], (
        f"期望的墙数：{expected_wall_loops}, 但是找到不匹配的: {ret[2]}"
    )

# ================== alternate_extra_wall ==================

@pytest.mark.engine_params
def test_alternate_extra_wall(slice_and_export: Path, expected_on: bool):
    """
    测试alternate_extra_wall功能，包括：
    1. 配置检查
    2. 依赖条件验证  
    3. G-code效果验证
    """
    # 验证方法：使用实体、薄壁、桥接或填充专用 3MF切片，解析Inner/Outer wall 的每层路径数、顺序和几何覆盖；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    # 默认启用配置和依赖检查
    ret = parse_alternate_extra_wall(gcode_path, expected_on, 
                                   check_config=True,
                                   check_dependencies=True)

    # 详细的错误信息
    if not ret[0]:
        bad_layers = ret[2]
        config_errors = [e for e in bad_layers if e[1].startswith('config-')]
        dependency_errors = [e for e in bad_layers if e[1].startswith('dependency-')]
        effect_errors = [e for e in bad_layers if not e[1].startswith(('config-', 'dependency-'))]
        
        error_details = []
        if config_errors:
            error_details.append(f"配置错误: {config_errors}")
        if dependency_errors:
            error_details.append(f"依赖错误: {dependency_errors}")
        if effect_errors:
            error_details.append(f"效果错误: {effect_errors}")
        
        assert False, (
            f"期望是否打开交替添加额外内墙功能：{expected_on}, "
            f"但检测结果不符合预期：{ret[1]}\\n"
            f"错误详情: {'; '.join(error_details)}"
        )

    assert ret[0], (
        f"期望是否打开交替添加额外内墙功能：{expected_on}, 但是检测到的结果不符合预期：{ret[1]}, 详情: {ret[2]}"
    )


# ================== detect_thin_wall ==================
@pytest.mark.engine_params
def test_detect_thin_wall(slice_and_export: Path, expected_detect_thin_wall: bool, tolerance: float):
    """验证方法：窄壁模型关闭时每层仅有主外墙路径，开启后 C3DSlicer
    的薄壁补偿会增加 OUTER_WALL 路径；同时核对 CONFIG_BLOCK 参数值。"""
    # 验证方法：使用实体、薄壁、桥接或填充专用 3MF切片，解析Inner/Outer wall 的每层路径数、顺序和几何覆盖；配置值仅用于确认输入，最终由实际 G-code 行为断言。
    gcode_path: Path = slice_and_export
    #assert gcode_path.exists()

    ok, _, details = parse_detect_thin_wall(
        gcode_path,
        expected_detect_thin_wall,
        tolerance,
    )

    assert ok, f"expected={expected_detect_thin_wall}, details={details}"
