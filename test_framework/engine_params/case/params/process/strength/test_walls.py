from pathlib import Path

import pytest
from engine_params.src.gcode.process.strength.walls_check import parse_wall_loops, parse_alternate_extra_wall, parse_detect_thin_wall

# ================== wall_loops ==================

@pytest.mark.engine_params
def test_wall_loops(slice_and_export: Path,
                     expected_wall_loops: int):
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
    """检测 detect_thin_wall：非首层 OUTER_WALL 分成双孤岛，一条线宽多变，一条线宽恒定。"""
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, _, details = parse_detect_thin_wall(
        gcode_path,
        expected_detect_thin_wall,
        tolerance,
    )

    assert ok, f"expected={expected_detect_thin_wall}, details={details}"
