"""
耗材相关参数的测试用例模块

包含 enable_prime_tower, prime_tower_width 等耗材相关参数的测试用例
"""
from __future__ import annotations
from pathlib import Path
import pytest
from engine_params.src.gcode.filament.filament_check import (
    parse_enable_prime_tower,
    parse_prime_tower_width,
    parse_prime_tower_brim_width,
    parse_prime_volume,
    parse_wipe_tower_rotation_angle,
    parse_prime_tower_enhance_type,
)


# ================== enable_prime_tower ==================
@pytest.mark.engine_params
def test_enable_prime_tower(
        slice_and_export: Path,
        expected_on: bool,
) -> None:
    """
    测试 enable_prime_tower 参数是否正确生效。
    
    校验逻辑：
    1. 配置值是否与期望一致
    2. G-code 中是否存在/不存在 Prime tower 挤出块
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, tower_present, details = parse_enable_prime_tower(
        gcode_path,
        expected_on,
    )

    assert ok, (
        f"enable_prime_tower expected {expected_on}, tower_present={tower_present}, details: {details}"
    )


# ================== prime_tower_width ==================
@pytest.mark.engine_params
def test_prime_tower_width(
        slice_and_export: Path,
        expected_width: float,
) -> None:
    """
    测试 prime_tower_width 参数是否正确生效。
    
    校验逻辑：
    对比配置中的 prime_tower_width 值与期望值是否一致。
    
    参数说明：
    - prime_tower_width: Prime Tower 的宽度 (mm)
    - 最小值: 2.0mm
    - 默认值: 60.0mm
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual_width, details = parse_prime_tower_width(
        gcode_path,
        expected_width,
    )

    assert ok, (
        f"prime_tower_width expected {expected_width}, actual={actual_width}, details: {details}"
    )


# ================== prime_tower_brim_width ==================
@pytest.mark.engine_params
def test_prime_tower_brim_width(
        slice_and_export: Path,
        expected_brim_width: float,
) -> None:
    """
    测试 prime_tower_brim_width 参数是否正确生效。
    
    校验逻辑：
    对比配置中的 prime_tower_brim_width 值与期望值是否一致。
    
    参数说明：
    - prime_tower_brim_width: Prime Tower 的边缘（Brim）宽度 (mm)
    - 最小值: 0.0mm
    - 默认值: 3.0mm
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual_brim_width, details = parse_prime_tower_brim_width(
        gcode_path,
        expected_brim_width,
    )

    assert ok, (
        f"prime_tower_brim_width expected {expected_brim_width}, actual={actual_brim_width}, details: {details}"
    )


# ================== prime_volume ==================
@pytest.mark.engine_params
def test_prime_volume(
        slice_and_export: Path,
        expected_volume: float,
) -> None:
    """
    测试 prime_volume 参数是否正确生效。
    
    校验逻辑（Level 1 配置对比）：
    对比配置中的 prime_volume 值与期望值是否一致。
    
    参数说明：
    - prime_volume: 在擦料塔上预填充挤出机的材料体积 (mm³)
    - 最小值: 1.0mm³
    - 默认值: 45.0mm³
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual_volume, details = parse_prime_volume(
        gcode_path,
        expected_volume,
    )

    assert ok, (
        f"prime_volume expected {expected_volume}, actual={actual_volume}, details: {details}"
    )


# ================== wipe_tower_rotation_angle ==================
@pytest.mark.engine_params
def test_wipe_tower_rotation_angle(
        slice_and_export: Path,
        expected_angle: float,
) -> None:
    """
    测试 wipe_tower_rotation_angle 参数是否正确生效。
    
    校验逻辑（Level 1 配置对比）：
    对比配置中的 wipe_tower_rotation_angle 值与期望值是否一致。
    
    参数说明：
    - wipe_tower_rotation_angle: Prime Tower 相对于 X 轴的旋转角度 (°)
    - 默认值: 0°
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual_angle, details = parse_wipe_tower_rotation_angle(
        gcode_path,
        expected_angle,
    )

    assert ok, (
        f"wipe_tower_rotation_angle expected {expected_angle}, actual={actual_angle}, details: {details}"
    )


# ================== prime_tower_enhance_type ==================
@pytest.mark.engine_params
def test_prime_tower_enhance_type(
        slice_and_export: Path,
        expected_type: str,
        baseline_gcode: Path,
) -> None:
    """
    测试 prime_tower_enhance_type 参数是否正确生效。
    
    校验逻辑（Level 1 配置对比 + Level 3 基线对比）：
    1. Level 1: 对比配置中的 prime_tower_enhance_type 值与期望值是否一致
    2. Level 3: 如果提供了基线 G-code，对比 Prime tower 区域路径是否一致
    
    参数说明：
    - prime_tower_enhance_type: Prime Tower 底部增强类型
    - 可选值: "cone"（锥形）, "chamfer"（倒角）
    - 默认值: "chamfer"
    
    参数:
        slice_and_export: 切片生成的 G-code 文件路径
        expected_type: 期望的 prime_tower_enhance_type 值
        baseline_gcode: 基线 G-code 文件路径（可选，用于 Level 3 验证）
    """
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()

    ok, actual_type, details = parse_prime_tower_enhance_type(
        gcode_path,
        expected_type,
        baseline_gcode_path=baseline_gcode,
    )

    assert ok, (
        f"prime_tower_enhance_type expected {expected_type}, actual={actual_type}, details: {details}"
    )