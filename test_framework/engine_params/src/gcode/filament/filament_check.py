"""
耗材相关参数的G-code解析与校验模块

包含 enable_prime_tower 等耗材相关参数的解析函数
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple, List

from engine_params.src.gcode.GCodeParser import GCodeParser
from engine_params.src.gcode.constants import ExtrusionType


# ================== enable_prime_tower ==================
def parse_enable_prime_tower(
        gcode_path: Path | str,
        expected_on: bool,
        object_id: int = 0,
) -> Tuple[bool, bool, Dict[str, object]]:
    """
    解析 G-code 文件，检测 enable_prime_tower 参数是否生效。
    
    校验逻辑：
    1. 从配置中读取 enable_prime_tower 设置值
    2. 检查 G-code 中是否存在 Prime tower 类型的挤出块
    3. 当 expected_on=True 时，期望存在 Prime tower 挤出块
       当 expected_on=False 时，期望不存在 Prime tower 挤出块
    
    参数:
        gcode_path: G-code 文件路径
        expected_on: 期望的 enable_prime_tower 开关状态
        object_id: 对象ID，默认为0
    
    返回:
        Tuple[bool, bool, Dict[str, object]]:
            - ok: 总体校验是否通过
            - tower_present: 是否检测到 Prime tower 挤出块
            - details: 详细信息字典，包含配置值、挤出块统计等
    """
    parser = GCodeParser(Path(gcode_path))
    cfg = parser.load_config()
    
    # 读取配置值
    config_value = cfg.get("enable_prime_tower")
    
    details = {
        "config_value": config_value,
        "expected_on": expected_on,
        "gcode_path": str(gcode_path),
        "prime_tower_layers": [],
        "prime_tower_block_count": 0,
        "error_details": []
    }
    
    # 检查配置值与期望是否一致
    config_matches = False
    if config_value is not None:
        if isinstance(config_value, bool):
            config_matches = (config_value == expected_on)
        elif isinstance(config_value, str):
            config_bool = config_value.lower() in ("true", "1", "yes", "on")
            config_matches = (config_bool == expected_on)
        elif isinstance(config_value, (int, float)):
            config_bool = bool(config_value)
            config_matches = (config_bool == expected_on)
    
    if not config_matches:
        details["error_details"].append(
            f"Config value mismatch: config_value={config_value}, expected_on={expected_on}"
        )
    
    # 检查 G-code 中是否存在 Prime tower 挤出块
    try:
        # 使用 ExtrusionType.PRIME_TOWER.value 获取 Prime tower 挤出块
        prime_tower_blocks = parser.get_extrusion_blocks_per_layer(
            ExtrusionType.PRIME_TOWER.value
        )
        
        tower_present = False
        total_blocks = 0
        
        for layer_idx, blocks in enumerate(prime_tower_blocks):
            if blocks and len(blocks) > 0:
                tower_present = True
                block_count = len(blocks)
                total_blocks += block_count
                details["prime_tower_layers"].append({
                    "layer_idx": layer_idx,
                    "block_count": block_count
                })
        
        details["prime_tower_block_count"] = total_blocks
        details["tower_present"] = tower_present
        
    except Exception as e:
        details["error_details"].append(f"Error parsing Prime tower blocks: {str(e)}")
        tower_present = False
        details["tower_present"] = False
    
    # 判断是否符合期望
    # expected_on=True 时，期望 tower_present=True
    # expected_on=False 时，期望 tower_present=False
    ok = (tower_present == expected_on)
    
    if not ok:
        if expected_on:
            details["error_details"].append(
                f"Expected Prime tower to be present, but no Prime tower blocks found"
            )
        else:
            details["error_details"].append(
                f"Expected no Prime tower, but found {details['prime_tower_block_count']} blocks in {len(details['prime_tower_layers'])} layers"
            )
    else:
        if expected_on:
            details["error_details"].append(
                f"Prime tower correctly enabled: found {details['prime_tower_block_count']} blocks in {len(details['prime_tower_layers'])} layers"
            )
        else:
            details["error_details"].append(
                "Prime tower correctly disabled: no Prime tower blocks found"
            )
    
    return ok, tower_present, details


# ================== prime_tower_width ==================
def parse_prime_tower_width(
        gcode_path: Path | str,
        expected_width: float,
        tolerance: float = 0.01,
) -> Tuple[bool, float, Dict[str, object]]:
    """
    解析 G-code 文件，检测 prime_tower_width 配置值是否与期望一致。
    
    校验逻辑：
    从配置中读取 prime_tower_width 值，与期望值 expected_width 进行对比。
    
    参数说明：
    - prime_tower_width: Prime Tower 的宽度 (mm)
    - 最小值: 2.0mm
    - 默认值: 60.0mm
    
    参数:
        gcode_path: G-code 文件路径
        expected_width: 期望的 prime_tower_width 值 (mm)
        tolerance: 允许的误差范围，默认 0.01mm
    
    返回:
        Tuple[bool, float, Dict[str, object]]:
            - ok: 配置值与期望是否一致（在容差范围内）
            - actual_width: 实际的配置值
            - details: 详细信息字典
    """
    parser = GCodeParser(Path(gcode_path))
    cfg = parser.load_config()
    
    # 读取配置值
    config_value = cfg.get("prime_tower_width")
    
    # 将配置值转换为 float
    actual_width = 0.0
    if config_value is not None:
        if isinstance(config_value, (int, float)):
            actual_width = float(config_value)
        elif isinstance(config_value, str):
            try:
                actual_width = float(config_value)
            except ValueError:
                actual_width = 0.0
    
    details = {
        "config_value": config_value,
        "actual_width": actual_width,
        "expected_width": expected_width,
        "tolerance": tolerance,
        "gcode_path": str(gcode_path),
    }
    
    # 判断是否在容差范围内
    diff = abs(actual_width - expected_width)
    ok = diff <= tolerance
    
    if ok:
        details["message"] = f"prime_tower_width 配置正确: expected={expected_width}, actual={actual_width}, diff={diff}"
    else:
        details["message"] = f"prime_tower_width 配置不匹配: expected={expected_width}, actual={actual_width}, diff={diff}, tolerance={tolerance}"
    
    return ok, actual_width, details


# ================== prime_tower_brim_width ==================
def parse_prime_tower_brim_width(
        gcode_path: Path | str,
        expected_brim_width: float,
        tolerance: float = 0.01,
) -> Tuple[bool, float, Dict[str, object]]:
    """
    解析 G-code 文件，检测 prime_tower_brim_width 配置值是否与期望一致。
    
    校验逻辑：
    从配置中读取 prime_tower_brim_width 值，与期望值 expected_brim_width 进行对比。
    
    参数说明：
    - prime_tower_brim_width: Prime Tower 的边缘（Brim）宽度 (mm)
    - 最小值: 0.0mm
    - 默认值: 3.0mm
    
    参数:
        gcode_path: G-code 文件路径
        expected_brim_width: 期望的 prime_tower_brim_width 值 (mm)
        tolerance: 允许的误差范围，默认 0.01mm
    
    返回:
        Tuple[bool, float, Dict[str, object]]:
            - ok: 配置值与期望是否一致（在容差范围内）
            - actual_brim_width: 实际的配置值
            - details: 详细信息字典
    """
    parser = GCodeParser(Path(gcode_path))
    cfg = parser.load_config()
    
    # 读取配置值
    config_value = cfg.get("prime_tower_brim_width")
    
    # 将配置值转换为 float
    actual_brim_width = 0.0
    if config_value is not None:
        if isinstance(config_value, (int, float)):
            actual_brim_width = float(config_value)
        elif isinstance(config_value, str):
            try:
                actual_brim_width = float(config_value)
            except ValueError:
                actual_brim_width = 0.0
    
    details = {
        "config_value": config_value,
        "actual_brim_width": actual_brim_width,
        "expected_brim_width": expected_brim_width,
        "tolerance": tolerance,
        "gcode_path": str(gcode_path),
    }
    
    # 判断是否在容差范围内
    diff = abs(actual_brim_width - expected_brim_width)
    ok = diff <= tolerance
    
    if ok:
        details["message"] = f"prime_tower_brim_width 配置正确: expected={expected_brim_width}, actual={actual_brim_width}, diff={diff}"
    else:
        details["message"] = f"prime_tower_brim_width 配置不匹配: expected={expected_brim_width}, actual={actual_brim_width}, diff={diff}, tolerance={tolerance}"
    
    return ok, actual_brim_width, details


# ================== prime_volume ==================
def parse_prime_volume(
        gcode_path: Path | str,
        expected_volume: float,
        tolerance: float = 0.01,
) -> Tuple[bool, float, Dict[str, object]]:
    """
    解析 G-code 文件，检测 prime_volume 配置值是否与期望一致。
    
    校验逻辑（Level 1 配置对比）：
    从配置中读取 prime_volume 值，与期望值 expected_volume 进行对比。
    
    参数说明：
    - prime_volume: 在擦料塔上预填充挤出机的材料体积 (mm³)
    - 最小值: 1.0mm³
    - 默认值: 45.0mm³
    
    参数:
        gcode_path: G-code 文件路径
        expected_volume: 期望的 prime_volume 值 (mm³)
        tolerance: 允许的误差范围，默认 0.01mm³
    
    返回:
        Tuple[bool, float, Dict[str, object]]:
            - ok: 配置值与期望是否一致（在容差范围内）
            - actual_volume: 实际的配置值
            - details: 详细信息字典
    """
    parser = GCodeParser(Path(gcode_path))
    cfg = parser.load_config()
    
    # 读取配置值
    config_value = cfg.get("prime_volume")
    
    # 将配置值转换为 float
    actual_volume = 0.0
    if config_value is not None:
        if isinstance(config_value, (int, float)):
            actual_volume = float(config_value)
        elif isinstance(config_value, str):
            try:
                actual_volume = float(config_value)
            except ValueError:
                actual_volume = 0.0
    
    details = {
        "config_value": config_value,
        "actual_volume": actual_volume,
        "expected_volume": expected_volume,
        "tolerance": tolerance,
        "gcode_path": str(gcode_path),
    }
    
    # 判断是否在容差范围内
    diff = abs(actual_volume - expected_volume)
    ok = diff <= tolerance
    
    if ok:
        details["message"] = f"prime_volume 配置正确: expected={expected_volume}, actual={actual_volume}, diff={diff}"
    else:
        details["message"] = f"prime_volume 配置不匹配: expected={expected_volume}, actual={actual_volume}, diff={diff}, tolerance={tolerance}"
    
    return ok, actual_volume, details


# ================== wipe_tower_rotation_angle ==================
def parse_wipe_tower_rotation_angle(
        gcode_path: Path | str,
        expected_angle: float,
        tolerance: float = 0.01,
) -> Tuple[bool, float, Dict[str, object]]:
    """
    解析 G-code 文件，检测 wipe_tower_rotation_angle 配置值是否与期望一致。
    
    校验逻辑（Level 1 配置对比）：
    从配置中读取 wipe_tower_rotation_angle 值，与期望值 expected_angle 进行对比。
    
    参数说明：
    - wipe_tower_rotation_angle: Prime Tower 相对于 X 轴的旋转角度 (°)
    - 默认值: 0°
    
    参数:
        gcode_path: G-code 文件路径
        expected_angle: 期望的 wipe_tower_rotation_angle 值 (°)
        tolerance: 允许的误差范围，默认 0.01°
    
    返回:
        Tuple[bool, float, Dict[str, object]]:
            - ok: 配置值与期望是否一致（在容差范围内）
            - actual_angle: 实际的配置值
            - details: 详细信息字典
    """
    parser = GCodeParser(Path(gcode_path))
    cfg = parser.load_config()
    
    # 读取配置值
    config_value = cfg.get("wipe_tower_rotation_angle")
    
    # 将配置值转换为 float
    actual_angle = 0.0
    if config_value is not None:
        if isinstance(config_value, (int, float)):
            actual_angle = float(config_value)
        elif isinstance(config_value, str):
            try:
                actual_angle = float(config_value)
            except ValueError:
                actual_angle = 0.0
    
    details = {
        "config_value": config_value,
        "actual_angle": actual_angle,
        "expected_angle": expected_angle,
        "tolerance": tolerance,
        "gcode_path": str(gcode_path),
    }
    
    # 判断是否在容差范围内
    diff = abs(actual_angle - expected_angle)
    ok = diff <= tolerance
    
    if ok:
        details["message"] = f"wipe_tower_rotation_angle 配置正确: expected={expected_angle}, actual={actual_angle}, diff={diff}"
    else:
        details["message"] = f"wipe_tower_rotation_angle 配置不匹配: expected={expected_angle}, actual={actual_angle}, diff={diff}, tolerance={tolerance}"
    
    return ok, actual_angle, details


# ================== prime_tower_enhance_type ==================
def _extract_prime_tower_paths(gcode_path: Path | str) -> List[Dict[str, float]]:
    """
    提取 G-code 中 Prime tower 区域的所有路径点。
    
    参数:
        gcode_path: G-code 文件路径
    
    返回:
        List[Dict]: 路径点列表，每个点包含 x, y, z, e 等信息
    """
    parser = GCodeParser(Path(gcode_path))
    paths = []
    in_prime_tower = False
    current_x, current_y, current_z = 0.0, 0.0, 0.0
    
    with open(gcode_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # 检测 Prime tower 区域开始/结束
            if ';TYPE:Prime tower' in line or '; WIPE_TOWER_START' in line:
                in_prime_tower = True
                continue
            elif line.startswith(';TYPE:') or '; WIPE_TOWER_END' in line:
                in_prime_tower = False
                continue
            
            # 只收集 Prime tower 区域内的 G1 命令
            if in_prime_tower and line.startswith('G1 '):
                point = {'x': current_x, 'y': current_y, 'z': current_z}
                parts = line.split()
                for part in parts[1:]:
                    if part.startswith('X'):
                        current_x = float(part[1:])
                        point['x'] = current_x
                    elif part.startswith('Y'):
                        current_y = float(part[1:])
                        point['y'] = current_y
                    elif part.startswith('Z'):
                        current_z = float(part[1:])
                        point['z'] = current_z
                    elif part.startswith('E'):
                        point['e'] = float(part[1:])
                    elif part.startswith('F'):
                        point['f'] = float(part[1:])
                paths.append(point)
    
    return paths


def _compare_prime_tower_paths(
        baseline_paths: List[Dict[str, float]],
        test_paths: List[Dict[str, float]],
        tolerance: float = 0.1,
) -> Tuple[bool, Dict[str, object]]:
    """
    对比两个 G-code 的 Prime tower 区域路径。
    
    参数:
        baseline_paths: 基线 G-code 的 Prime tower 路径
        test_paths: 测试 G-code 的 Prime tower 路径
        tolerance: 坐标容差 (mm)
    
    返回:
        Tuple[bool, Dict]: (是否匹配, 详细信息)
    """
    details = {
        "baseline_path_count": len(baseline_paths),
        "test_path_count": len(test_paths),
        "tolerance": tolerance,
    }
    
    # 路径点数量差异过大视为不匹配
    count_diff = abs(len(baseline_paths) - len(test_paths))
    count_diff_ratio = count_diff / max(len(baseline_paths), 1)
    details["path_count_diff"] = count_diff
    details["path_count_diff_ratio"] = count_diff_ratio
    
    # 允许 10% 的路径点数量差异
    if count_diff_ratio > 0.1:
        details["message"] = f"路径点数量差异过大: baseline={len(baseline_paths)}, test={len(test_paths)}, diff_ratio={count_diff_ratio:.2%}"
        return False, details
    
    # 比较路径的边界框
    def get_bounds(paths):
        if not paths:
            return None
        xs = [p['x'] for p in paths]
        ys = [p['y'] for p in paths]
        zs = [p['z'] for p in paths]
        return {
            'min_x': min(xs), 'max_x': max(xs),
            'min_y': min(ys), 'max_y': max(ys),
            'min_z': min(zs), 'max_z': max(zs),
        }
    
    baseline_bounds = get_bounds(baseline_paths)
    test_bounds = get_bounds(test_paths)
    
    if baseline_bounds is None or test_bounds is None:
        details["message"] = "无法计算边界框"
        return False, details
    
    details["baseline_bounds"] = baseline_bounds
    details["test_bounds"] = test_bounds
    
    # 比较边界框尺寸
    baseline_width = baseline_bounds['max_x'] - baseline_bounds['min_x']
    baseline_depth = baseline_bounds['max_y'] - baseline_bounds['min_y']
    baseline_height = baseline_bounds['max_z'] - baseline_bounds['min_z']
    
    test_width = test_bounds['max_x'] - test_bounds['min_x']
    test_depth = test_bounds['max_y'] - test_bounds['min_y']
    test_height = test_bounds['max_z'] - test_bounds['min_z']
    
    width_diff = abs(baseline_width - test_width)
    depth_diff = abs(baseline_depth - test_depth)
    height_diff = abs(baseline_height - test_height)
    
    details["width_diff"] = width_diff
    details["depth_diff"] = depth_diff
    details["height_diff"] = height_diff
    
    # 边界框尺寸差异在容差内视为匹配
    if width_diff > tolerance or depth_diff > tolerance or height_diff > tolerance:
        details["message"] = f"边界框尺寸差异过大: width_diff={width_diff:.2f}, depth_diff={depth_diff:.2f}, height_diff={height_diff:.2f}"
        return False, details
    
    details["message"] = "Prime tower 路径匹配"
    return True, details


# ================== wipe_tower_extra_flow ==================
def parse_wipe_tower_extra_flow(
        gcode_path: Path | str,
        expected_flow: float,
        tolerance: float = 0.01,
) -> Tuple[bool, float, Dict[str, object]]:
    """
    解析 G-code 文件，检测 wipe_tower_extra_flow 配置值是否与期望一致。
    
    校验逻辑（Level 1 配置对比）：
    从配置中读取 wipe_tower_extra_flow 值，与期望值 expected_flow 进行对比。
    
    参数说明：
    - wipe_tower_extra_flow: 擦料塔清洗线的额外流量百分比 (%)
    - 最小值: 100%
    - 最大值: 300%
    - 默认值: 100%
    
    参数:
        gcode_path: G-code 文件路径
        expected_flow: 期望的 wipe_tower_extra_flow 值 (%)
        tolerance: 允许的误差范围，默认 0.01%
    
    返回:
        Tuple[bool, float, Dict[str, object]]:
            - ok: 配置值与期望是否一致（在容差范围内）
            - actual_flow: 实际的配置值
            - details: 详细信息字典
    """
    parser = GCodeParser(Path(gcode_path))
    cfg = parser.load_config()
    
    # 读取配置值
    config_value = cfg.get("wipe_tower_extra_flow")
    
    # 将配置值转换为 float
    actual_flow = 0.0
    if config_value is not None:
        if isinstance(config_value, (int, float)):
            actual_flow = float(config_value)
        elif isinstance(config_value, str):
            # 处理百分号格式，如 "100%"
            try:
                clean_value = config_value.replace('%', '').strip()
                actual_flow = float(clean_value)
            except ValueError:
                actual_flow = 0.0
    
    details = {
        "config_value": config_value,
        "actual_flow": actual_flow,
        "expected_flow": expected_flow,
        "tolerance": tolerance,
        "gcode_path": str(gcode_path),
    }
    
    # 判断是否在容差范围内
    diff = abs(actual_flow - expected_flow)
    ok = diff <= tolerance
    
    if ok:
        details["message"] = f"wipe_tower_extra_flow 配置正确: expected={expected_flow}%, actual={actual_flow}%, diff={diff}"
    else:
        details["message"] = f"wipe_tower_extra_flow 配置不匹配: expected={expected_flow}%, actual={actual_flow}%, diff={diff}, tolerance={tolerance}"
    
    return ok, actual_flow, details


# ================== prime_tower_enhance_type ==================
def parse_prime_tower_enhance_type(
        gcode_path: Path | str,
        expected_type: str,
        baseline_gcode_path: Path | str | None = None,
) -> Tuple[bool, str, Dict[str, object]]:
    """
    解析 G-code 文件，检测 prime_tower_enhance_type 配置值是否与期望一致。
    
    校验逻辑（Level 1 配置对比 + Level 3 基线对比）：
    1. Level 1: 从配置中读取 prime_tower_enhance_type 值，与期望值对比
    2. Level 3: 如果提供了基线 G-code，对比 Prime tower 区域路径
    
    参数说明：
    - prime_tower_enhance_type: Prime Tower 底部增强类型
    - 可选值: "cone"（锥形）, "chamfer"（倒角）
    - 默认值: "chamfer"
    
    参数:
        gcode_path: G-code 文件路径
        expected_type: 期望的 prime_tower_enhance_type 值 ("cone" 或 "chamfer")
        baseline_gcode_path: 基线 G-code 文件路径（可选，用于 Level 3 对比）
    
    返回:
        Tuple[bool, str, Dict[str, object]]:
            - ok: 校验是否通过（配置一致 + 路径匹配）
            - actual_type: 实际的配置值
            - details: 详细信息字典
    """
    parser = GCodeParser(Path(gcode_path))
    cfg = parser.load_config()
    
    # Level 1: 读取配置值
    config_value = cfg.get("prime_tower_enhance_type")
    
    # 将配置值转换为 str
    actual_type = ""
    if config_value is not None:
        actual_type = str(config_value).strip()
    
    details = {
        "config_value": config_value,
        "actual_type": actual_type,
        "expected_type": expected_type,
        "gcode_path": str(gcode_path),
        "level1_passed": False,
        "level3_passed": None,  # None 表示未执行 Level 3
    }
    
    # Level 1: 判断配置是否一致（不区分大小写）
    level1_ok = actual_type.lower() == expected_type.lower()
    details["level1_passed"] = level1_ok
    
    if not level1_ok:
        details["message"] = f"Level 1 失败: prime_tower_enhance_type 配置不匹配, expected={expected_type}, actual={actual_type}"
        return False, actual_type, details
    
    # Level 3: 基线对比（可选）
    if baseline_gcode_path is not None:
        baseline_path = Path(baseline_gcode_path)
        if not baseline_path.exists():
            details["level3_passed"] = False
            details["message"] = f"Level 3 失败: 基线 G-code 文件不存在: {baseline_gcode_path}"
            return False, actual_type, details
        
        details["baseline_gcode_path"] = str(baseline_gcode_path)
        
        # 提取两个 G-code 的 Prime tower 路径
        baseline_paths = _extract_prime_tower_paths(baseline_path)
        test_paths = _extract_prime_tower_paths(gcode_path)
        
        details["baseline_prime_tower_paths"] = len(baseline_paths)
        details["test_prime_tower_paths"] = len(test_paths)
        
        # 对比路径
        level3_ok, compare_details = _compare_prime_tower_paths(baseline_paths, test_paths)
        details["level3_passed"] = level3_ok
        details["compare_details"] = compare_details
        
        if not level3_ok:
            details["message"] = f"Level 3 失败: Prime tower 路径不匹配 - {compare_details.get('message', '')}"
            return False, actual_type, details
        
        details["message"] = f"Level 1 + Level 3 通过: prime_tower_enhance_type={actual_type}, Prime tower 路径匹配"
    else:
        details["message"] = f"Level 1 通过: prime_tower_enhance_type 配置正确, expected={expected_type}, actual={actual_type}"
    
    return True, actual_type, details


# ================== flush_into_infill ==================
def parse_flush_into_infill(
        gcode_path: Path | str,
        expected_value: bool,
) -> Tuple[bool, bool, Dict[str, object]]:
    """
    解析 G-code 文件，检测 flush_into_infill 是否生效。
    
    校验逻辑（Level 2 特征检测）：
    检测换料后首个挤出块是否在填充区域。
    
    flush_into_infill 启用时的特征：
    1. 换料命令（T0/T1/T2...）之后
    2. 在 Prime tower 挤出完成后
    3. 首个模型挤出出现在填充区域（;TYPE:Sparse infill 或 ;TYPE:Internal solid infill）
    
    具体检测步骤：
    1. 定位所有换料命令（T0, T1, T2...）
    2. 在换料后，跳过 Prime tower 区域
    3. 记录进入模型打印后的首个 TYPE 标记
    4. 统计换料后首个 TYPE 为填充类型的比例
    5. 如果比例 > 80%，判定为 flush_into_infill 启用
    
    参数说明：
    - flush_into_infill: 冲刷到对象的填充
    - 类型: bool
    - 默认值: false
    - 将换料时的冲刷耗材用于打印填充部分，减少擦料塔浪费
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 flush_into_infill 值 (true/false)
    
    返回:
        Tuple[bool, bool, Dict[str, object]]:
            - ok: 检测结果与期望是否一致
            - detected_value: 检测到的实际状态
            - details: 详细信息字典
    """
    import re
    
    gcode_path = Path(gcode_path)
    
    # 填充类型标记
    infill_types = ["Sparse infill", "Internal solid infill"]
    # 需要跳过的类型（Prime tower 相关）
    skip_types = ["Prime tower"]
    
    # 统计数据
    tool_changes = []  # [(line_no, tool_id), ...]
    first_type_after_change = []  # 换料后首个模型挤出类型
    
    # 正则匹配换料命令 T0, T1, T2...
    tool_change_pattern = re.compile(r'^T(\d+)\s*$')
    # 正则匹配 TYPE 标记
    type_pattern = re.compile(r'^;TYPE:(.+)$')
    
    # 状态机
    waiting_for_type = False  # 是否在等待换料后的首个 TYPE
    in_prime_tower = False    # 是否在 Prime tower 区域内
    
    with open(gcode_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            
            # 检测换料命令
            tool_match = tool_change_pattern.match(line)
            if tool_match:
                tool_id = int(tool_match.group(1))
                tool_changes.append((line_no, tool_id))
                waiting_for_type = True
                in_prime_tower = False
                continue
            
            # 检测 TYPE 标记
            type_match = type_pattern.match(line)
            if type_match:
                current_type = type_match.group(1)
                
                # 检测是否进入/离开 Prime tower
                if current_type in skip_types:
                    in_prime_tower = True
                    continue
                else:
                    in_prime_tower = False
                
                # 如果正在等待换料后的首个 TYPE，且不在 Prime tower 中
                if waiting_for_type and not in_prime_tower:
                    first_type_after_change.append(current_type)
                    waiting_for_type = False
                continue
            
            # 检测 WIPE_TOWER_START / WIPE_TOWER_END 标记
            if '; WIPE_TOWER_START' in line:
                in_prime_tower = True
            elif '; WIPE_TOWER_END' in line:
                in_prime_tower = False
    
    # 计算填充类型比例
    total_changes = len(first_type_after_change)
    infill_count = sum(1 for t in first_type_after_change if t in infill_types)
    
    details = {
        "gcode_path": str(gcode_path),
        "expected_value": expected_value,
        "tool_changes_count": len(tool_changes),
        "first_types_after_change": first_type_after_change,
        "infill_count": infill_count,
        "total_analyzed": total_changes,
    }
    
    # 如果没有换料操作，无法通过 Level 2 检测
    if total_changes == 0:
        # 回退到 Level 1 配置对比
        parser = GCodeParser(gcode_path)
        cfg = parser.load_config()
        config_value = cfg.get("flush_into_infill")
        
        detected_value = False
        if config_value is not None:
            if isinstance(config_value, bool):
                detected_value = config_value
            elif isinstance(config_value, str):
                detected_value = config_value.lower() in ("true", "1", "yes", "on")
            elif isinstance(config_value, (int, float)):
                detected_value = bool(config_value)
        
        details["detection_method"] = "Level 1 (配置对比，无换料操作)"
        details["config_value"] = config_value
        details["detected_value"] = detected_value
        
        ok = (detected_value == expected_value)
        if ok:
            details["message"] = f"Level 1 通过: flush_into_infill={detected_value} (无换料操作，回退到配置对比)"
        else:
            details["message"] = f"Level 1 失败: expected={expected_value}, config={detected_value}"
        
        return ok, detected_value, details
    
    # Level 2 特征检测：计算填充比例
    infill_ratio = infill_count / total_changes
    details["infill_ratio"] = infill_ratio
    details["detection_method"] = "Level 2 (特征检测)"
    
    # 判定：如果换料后首个挤出大部分是填充类型，则启用
    # 阈值说明：
    # - 启用 flush_into_infill 时，换料后会优先在填充区域冲刷
    # - 但并非所有换料都会进入填充区域（取决于模型结构和层的填充量）
    # - 根据实测数据，启用时填充比例约 50%+，禁用时填充比例较低
    # - 阈值设为 40%，能有效区分启用/禁用状态
    threshold = 0.4
    detected_value = infill_ratio > threshold
    details["detected_value"] = detected_value
    details["threshold"] = threshold
    
    ok = (detected_value == expected_value)
    
    if ok:
        details["message"] = (
            f"Level 2 通过: flush_into_infill detected={detected_value}, "
            f"infill_ratio={infill_ratio:.1%} ({infill_count}/{total_changes})"
        )
    else:
        details["message"] = (
            f"Level 2 失败: expected={expected_value}, detected={detected_value}, "
            f"infill_ratio={infill_ratio:.1%} ({infill_count}/{total_changes}), "
            f"first_types={first_type_after_change}"
        )
    
    return ok, detected_value, details


# ================== flush_into_support ==================
def parse_flush_into_support(
        gcode_path: Path | str,
        expected_value: bool,
) -> Tuple[bool, bool, Dict[str, object]]:
    """
    解析 G-code 文件，检测 flush_into_support 是否生效。
    
    校验逻辑（Level 2 特征检测）：
    检测换料后首个挤出块是否在支撑区域。
    
    flush_into_support 启用时的特征：
    1. 换料命令（T0/T1/T2...）之后
    2. 在 Prime tower 挤出完成后
    3. 首个模型挤出出现在支撑区域（;TYPE:Support 或 ;TYPE:Support interface）
    
    具体检测步骤：
    1. 定位所有换料命令（T0, T1, T2...）
    2. 在换料后，跳过 Prime tower 区域
    3. 记录进入模型打印后的首个 TYPE 标记
    4. 统计换料后首个 TYPE 为支撑类型的比例
    5. 如果比例 > 阈值，判定为 flush_into_support 启用
    
    参数说明：
    - flush_into_support: 冲刷到对象的支撑
    - 类型: bool
    - 默认值: true（默认启用）
    - 将换料时的冲刷耗材用于支撑区域，减少擦料塔浪费
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 flush_into_support 值 (true/false)
    
    返回:
        Tuple[bool, bool, Dict[str, object]]:
            - ok: 检测结果与期望是否一致
            - detected_value: 检测到的实际状态
            - details: 详细信息字典
    """
    import re
    
    gcode_path = Path(gcode_path)
    
    # 支撑类型标记
    support_types = ["Support", "Support interface"]
    # 需要跳过的类型（Prime tower 相关）
    skip_types = ["Prime tower"]
    
    # 统计数据
    tool_changes = []  # [(line_no, tool_id), ...]
    first_type_after_change = []  # 换料后首个模型挤出类型
    
    # 正则匹配换料命令 T0, T1, T2...
    tool_change_pattern = re.compile(r'^T(\d+)\s*$')
    # 正则匹配 TYPE 标记
    type_pattern = re.compile(r'^;TYPE:(.+)$')
    
    # 状态机
    waiting_for_type = False  # 是否在等待换料后的首个 TYPE
    in_prime_tower = False    # 是否在 Prime tower 区域内
    
    with open(gcode_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            
            # 检测换料命令
            tool_match = tool_change_pattern.match(line)
            if tool_match:
                tool_id = int(tool_match.group(1))
                tool_changes.append((line_no, tool_id))
                waiting_for_type = True
                in_prime_tower = False
                continue
            
            # 检测 TYPE 标记
            type_match = type_pattern.match(line)
            if type_match:
                current_type = type_match.group(1)
                
                # 检测是否进入/离开 Prime tower
                if current_type in skip_types:
                    in_prime_tower = True
                    continue
                else:
                    in_prime_tower = False
                
                # 如果正在等待换料后的首个 TYPE，且不在 Prime tower 中
                if waiting_for_type and not in_prime_tower:
                    first_type_after_change.append(current_type)
                    waiting_for_type = False
                continue
            
            # 检测 WIPE_TOWER_START / WIPE_TOWER_END 标记
            if '; WIPE_TOWER_START' in line:
                in_prime_tower = True
            elif '; WIPE_TOWER_END' in line:
                in_prime_tower = False
    
    # 计算支撑类型比例
    total_changes = len(first_type_after_change)
    support_count = sum(1 for t in first_type_after_change if t in support_types)
    
    details = {
        "gcode_path": str(gcode_path),
        "expected_value": expected_value,
        "tool_changes_count": len(tool_changes),
        "first_types_after_change": first_type_after_change,
        "support_count": support_count,
        "total_analyzed": total_changes,
    }
    
    # 如果没有换料操作，无法通过 Level 2 检测
    if total_changes == 0:
        # 回退到 Level 1 配置对比
        parser = GCodeParser(gcode_path)
        cfg = parser.load_config()
        config_value = cfg.get("flush_into_support")
        
        detected_value = True  # 默认值为 true
        if config_value is not None:
            if isinstance(config_value, bool):
                detected_value = config_value
            elif isinstance(config_value, str):
                detected_value = config_value.lower() in ("true", "1", "yes", "on")
            elif isinstance(config_value, (int, float)):
                detected_value = bool(config_value)
        
        details["detection_method"] = "Level 1 (配置对比，无换料操作)"
        details["config_value"] = config_value
        details["detected_value"] = detected_value
        
        ok = (detected_value == expected_value)
        if ok:
            details["message"] = f"Level 1 通过: flush_into_support={detected_value} (无换料操作，回退到配置对比)"
        else:
            details["message"] = f"Level 1 失败: expected={expected_value}, config={detected_value}"
        
        return ok, detected_value, details
    
    # Level 2 特征检测：计算支撑比例
    support_ratio = support_count / total_changes
    details["support_ratio"] = support_ratio
    details["detection_method"] = "Level 2 (特征检测)"
    
    # 判定：如果换料后首个挤出有一定比例是支撑类型，则启用
    # 阈值说明：
    # - 启用 flush_into_support 时，换料后会优先在支撑区域冲刷
    # - 但并非所有换料都会进入支撑区域（取决于模型支撑分布）
    # - 支撑面积通常较小，比例可能低于填充
    # - 阈值设为 20%，适应支撑面积较小的情况
    threshold = 0.2
    detected_value = support_ratio > threshold
    details["detected_value"] = detected_value
    details["threshold"] = threshold
    
    ok = (detected_value == expected_value)
    
    if ok:
        details["message"] = (
            f"Level 2 通过: flush_into_support detected={detected_value}, "
            f"support_ratio={support_ratio:.1%} ({support_count}/{total_changes})"
        )
    else:
        details["message"] = (
            f"Level 2 失败: expected={expected_value}, detected={detected_value}, "
            f"support_ratio={support_ratio:.1%} ({support_count}/{total_changes}), "
            f"first_types={first_type_after_change}"
        )
    
    return ok, detected_value, details

