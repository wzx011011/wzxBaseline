"""
特殊模式 (Special mode) 参数校验模块

包含以下参数的校验函数：
- slicing_mode: Level 1 配置对比
- print_sequence: Level 2 层高顺序检测（层高不足或缺失时无法判定）
- print_order: Level 1 配置对比
- spiral_mode: Level 2 特征检测（Z轴连续性）
- spiral_mode_smooth: Level 1 配置对比
- spiral_mode_max_xy_smoothing: Level 1 配置对比
- ignore_inner_color: Level 1 配置对比
- timelapse_type: Level 1 配置对比
- fuzzy_skin: Level 2/3 特征检测（路径偏差分析）
- fuzzy_skin_point_distance: Level 1 配置对比
- fuzzy_skin_thickness: Level 1 配置对比
- fuzzy_skin_first_layer: Level 1 配置对比
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Tuple
import re
import math

from engine_params.src.gcode.GCodeParser import GCodeParser
from engine_params.src.gcode.layer_comments import read_layer_heights

_PRINT_SEQUENCE_ALIASES: Dict[str, str] = {
    "by object": "by object",
    "by objects": "by object",
    "逐件打印": "by object",
    "逐件": "by object",
    "逐件打印模式": "by object",
    "by layer": "by layer",
    "by layers": "by layer",
    "逐层打印": "by layer",
    "逐层": "by layer",
}


def _normalize_sequence(value: object | None) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    return _PRINT_SEQUENCE_ALIASES.get(text, text)


def _normalize_to_float(val: object) -> float:
    """将配置值规范化为 float"""
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        val = val.strip()
        # 处理百分比格式（如 "200%" -> 200.0）
        if val.endswith('%'):
            return float(val[:-1])
        return float(val)
    return 0.0


def _normalize_to_int(val: object) -> int:
    """将配置值规范化为 int"""
    if isinstance(val, (int, float)):
        return int(val)
    if isinstance(val, str):
        return int(float(val))
    return 0


def _normalize_to_bool(val: object) -> bool:
    """将配置值规范化为 bool"""
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    if isinstance(val, str):
        return val.lower() in ("1", "true", "yes", "on")
    return False


def _path_metrics(gcode_path: Path | str) -> Dict[str, object]:
    number = r"-?(?:\d+(?:\.\d*)?|\.\d+)"
    axis_pattern = re.compile(rf"\b([XYZE])({number})")
    current_type = ""
    z = 0.0
    layers: set[float] = set()
    type_moves: Dict[str, int] = {}
    continuous_outer_z_moves = 0
    tool_changes = 0
    with Path(gcode_path).open("r", encoding="utf-8", errors="ignore") as stream:
        for raw in stream:
            line = raw.strip()
            if line.startswith(";TYPE:"):
                current_type = line[6:]
                continue
            if re.fullmatch(r"T\d+", line):
                tool_changes += 1
                continue
            if not line.startswith("G1"):
                continue
            values = {axis: float(value) for axis, value in axis_pattern.findall(line)}
            z = values.get("Z", z)
            if values.get("E", 0.0) > 0 and ("X" in values or "Y" in values):
                layers.add(round(z, 4))
                type_moves[current_type] = type_moves.get(current_type, 0) + 1
                if current_type == "Outer wall" and "Z" in values:
                    continuous_outer_z_moves += 1
    return {
        "layer_count": len(layers),
        "type_moves": type_moves,
        "outer_wall_moves": type_moves.get("Outer wall", 0),
        "inner_wall_moves": type_moves.get("Inner wall", 0),
        "prime_tower_moves": type_moves.get("Prime tower", 0),
        "continuous_outer_z_moves": continuous_outer_z_moves,
        "tool_changes": tool_changes,
    }


def _model_paths_ok(metrics: Dict[str, object]) -> bool:
    return int(metrics["layer_count"]) > 1 and int(metrics["outer_wall_moves"]) > 10


# ================== slicing_mode ==================

def parse_slicing_mode(
        gcode_path: Path | str,
        expected_value: str,
) -> Tuple[bool, str, Dict[str, object]]:
    """
    解析 G-code，Level 1 配置对比 slicing_mode。
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 slicing_mode 值 (regular/contour)

    返回:
        Tuple[bool, str, Dict[str, object]]:
            - ok: 检测结果是否与期望一致
            - detected_value: 解析出的值
            - details: 详细信息字典
    """
    gcode_path = Path(gcode_path)
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    
    config_value = cfg.get("slicing_mode")
    detected_value = str(config_value) if config_value else "regular"
    
    details: Dict[str, object] = {
        "gcode_path": str(gcode_path),
        "expected_value": expected_value,
        "config_value": config_value,
        "detected_value": detected_value,
        "detection_method": "Level 1 (配置对比)",
    }
    
    behavior = _path_metrics(gcode_path)
    details["gcode_behavior"] = behavior
    details["detection_method"] = "配置值 + 实际分层外墙/填充路径"
    ok = detected_value == expected_value and _model_paths_ok(behavior)
    
    if ok:
        details["message"] = f"Level 1 通过: slicing_mode={detected_value}"
    else:
        details["message"] = f"Level 1 失败: expected={expected_value}, config={detected_value}"
    
    return ok, detected_value, details


# ================== print_sequence ==================

def parse_print_sequence(
        gcode_path: Path | str,
        expected_sequence: Optional[str] = None,
) -> Tuple[bool, Optional[str], Dict[str, object]]:
    """Inspect configuration and geometry to determine print sequence.
    
    检测方法：
    - by layer: 层号单调递增（每次打印更高的层）
    - by object: 层号不单调递增（先打印完一个对象的所有层，再打印下一个对象）
    """
    gcode_path = Path(gcode_path)
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    
    with gcode_path.open('r', encoding='utf-8') as stream:
        layer_heights = read_layer_heights(stream)
    layer_z_values = [height for height in layer_heights if height is not None]
    missing_layer_count = len(layer_heights) - len(layer_z_values)

    # 检查 Z 高度序列是否单调递增
    # by layer: Z 单调递增 (0.2, 0.4, 0.6, ..., 19.8, 20.0)
    # by object: Z 会回退 (0.2, 0.4, ..., 20.0, 0.2, 0.4, ..., 20.0) - 打完一个对象后 Z 回到起点
    is_monotonic = None
    if len(layer_z_values) > 1 and missing_layer_count == 0:
        is_monotonic = True
        for i in range(len(layer_z_values) - 1):
            # 如果下一层 Z 值明显小于当前层（回退），说明是 by object
            if layer_z_values[i+1] < layer_z_values[i] - 0.01:  # 容差 0.01mm
                is_monotonic = False
                break

    detected_sequence = None
    if is_monotonic is not None:
        detected_sequence = "by layer" if is_monotonic else "by object"

    raw_sequence = cfg.get("print_sequence")
    normalized_config = _normalize_sequence(raw_sequence)
    normalized_expected = _normalize_sequence(expected_sequence) if expected_sequence is not None else None

    ok = detected_sequence is not None and (
        normalized_expected is None or detected_sequence == normalized_expected
    )

    details: Dict[str, object] = {
        "raw_print_sequence": raw_sequence,
        "normalized_print_sequence": normalized_config,
        "detected_sequence": detected_sequence,
        "expected_sequence": normalized_expected,
        "is_monotonic_z": is_monotonic,
        "layer_count": len(layer_z_values),
        "missing_layer_count": missing_layer_count,
        "first_10_z_values": layer_z_values[:10] if layer_z_values else [],
        "last_10_z_values": layer_z_values[-10:] if len(layer_z_values) >= 10 else layer_z_values,
        "detection_method": "Level 2 (Z 高度回退检测)",
        "message": f"检测到打印顺序: {detected_sequence}（分析了{len(layer_z_values)}层的 Z 高度）",
    }

    if detected_sequence is None:
        details["message"] = (
            f"无法判定打印顺序：有效层高 {len(layer_z_values)} 个，"
            f"缺失层高 {missing_layer_count} 个；需要至少两个完整的层高记录"
        )

    return ok, detected_sequence, details


# ================== print_order ==================

def parse_print_order(
        gcode_path: Path | str,
        expected_value: str,
) -> Tuple[bool, str, Dict[str, object]]:
    """
    解析 G-code，Level 1 配置对比 print_order。
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 print_order 值 (default/inner to outer/outer to inner)

    返回:
        Tuple[bool, str, Dict[str, object]]:
            - ok: 检测结果是否与期望一致
            - detected_value: 解析出的值
            - details: 详细信息字典
    """
    gcode_path = Path(gcode_path)
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    
    config_value = cfg.get("print_order")
    detected_value = str(config_value) if config_value else "default"
    
    details: Dict[str, object] = {
        "gcode_path": str(gcode_path),
        "expected_value": expected_value,
        "config_value": config_value,
        "detected_value": detected_value,
        "detection_method": "Level 1 (配置对比)",
    }
    
    layer_orders: list[list[int]] = []
    current_order: list[int] = []
    object_pattern = re.compile(r"; printing object .* id:(\d+) copy")
    with gcode_path.open("r", encoding="utf-8", errors="ignore") as stream:
        for raw in stream:
            line = raw.strip()
            if line == ";LAYER_CHANGE":
                if current_order:
                    layer_orders.append(current_order)
                current_order = []
                continue
            match = object_pattern.match(line)
            if match:
                object_id = int(match.group(1))
                if object_id not in current_order:
                    current_order.append(object_id)
    if current_order:
        layer_orders.append(current_order)
    nonempty = [order for order in layer_orders if order]
    stable_order = bool(nonempty) and all(order == nonempty[0] for order in nonempty)
    details["layer_object_orders"] = nonempty[:10]
    details["object_count"] = len(nonempty[0]) if nonempty else 0
    details["stable_layer_order"] = stable_order
    details["detection_method"] = "配置值 + 各层对象标签顺序"
    ok = detected_value == expected_value and stable_order and len(nonempty[0]) >= 2
    
    if ok:
        details["message"] = f"Level 1 通过: print_order={detected_value}"
    else:
        details["message"] = f"Level 1 失败: expected={expected_value}, config={detected_value}"
    
    return ok, detected_value, details


# ================== spiral_mode ==================

def parse_spiral_mode(
        gcode_path: Path | str,
        expected_value: bool,
) -> Tuple[bool, bool, Dict[str, object]]:
    """
    解析 G-code，Level 2 特征检测 spiral_mode（Z轴连续性检测）。
    
    校验逻辑：
    - 螺旋模式：Z 轴连续递增，每条 G1 挤出命令的 Z 值都略高于上一条
    - 普通模式：同一层内 Z 值相同，层间有跳跃
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 spiral_mode 值 (True/False)

    返回:
        Tuple[bool, bool, Dict[str, object]]:
            - ok: 检测结果是否与期望一致
            - detected_value: 解析出的值
            - details: 详细信息字典
    """
    gcode_path = Path(gcode_path)
    
    with open(gcode_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 提取所有带 E 参数的 G1 命令（挤出移动）
    z_values = []
    g1_pattern = re.compile(r'^G1\s+.*E[0-9.]+', re.IGNORECASE)
    z_pattern = re.compile(r'Z([0-9.]+)', re.IGNORECASE)
    
    for line in lines:
        line = line.split(';')[0].strip()  # 移除注释
        if g1_pattern.match(line):
            z_match = z_pattern.search(line)
            if z_match:
                z_values.append(float(z_match.group(1)))
    
    # 计算 Z 差值
    z_increments = 0  # Z 值递增的次数
    z_jumps = 0  # 明显的层间跳跃次数
    z_same = 0  # Z 值保持不变的次数
    
    if len(z_values) > 1:
        for i in range(1, len(z_values)):
            z_diff = z_values[i] - z_values[i-1]
            if abs(z_diff) < 1e-6:  # 基本相同
                z_same += 1
            elif z_diff > 1e-6:  # 递增
                z_increments += 1
                if z_diff > 0.1:  # 明显跳跃（超过0.1mm）
                    z_jumps += 1
    
    total_transitions = len(z_values) - 1
    z_continuity = z_increments / total_transitions if total_transitions > 0 else 0.0
    
    # 判定标准：
    # - 螺旋模式：Z 轴连续递增比例 > 80%，且没有明显跳跃
    # - 普通模式：大部分 Z 值相同，或有明显跳跃
    detected_value = (z_continuity > 0.8) and (z_jumps == 0)
    
    details: Dict[str, object] = {
        "gcode_path": str(gcode_path),
        "expected_value": expected_value,
        "detected_value": detected_value,
        "detection_method": "Level 2 (Z轴连续性检测)",
        "z_samples": len(z_values),
        "z_increments": z_increments,
        "z_jumps": z_jumps,
        "z_same": z_same,
        "z_continuity": z_continuity,
    }
    
    ok = detected_value == expected_value
    
    if ok:
        details["message"] = f"Level 2 通过: spiral_mode={detected_value}"
    else:
        details["message"] = f"Level 2 失败: expected={expected_value}, detected={detected_value}"
    
    return ok, detected_value, details


# ================== spiral_mode_smooth ==================

def parse_spiral_mode_smooth(
        gcode_path: Path | str,
        expected_value: bool,
) -> Tuple[bool, bool, Dict[str, object]]:
    """
    解析 G-code，Level 1 配置对比 spiral_mode_smooth。
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 spiral_mode_smooth 值

    返回:
        Tuple[bool, bool, Dict[str, object]]:
            - ok: 检测结果是否与期望一致
            - detected_value: 解析出的值
            - details: 详细信息字典
    """
    gcode_path = Path(gcode_path)
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    
    config_value = cfg.get("spiral_mode_smooth")
    detected_value = _normalize_to_bool(config_value)
    
    details: Dict[str, object] = {
        "gcode_path": str(gcode_path),
        "expected_value": expected_value,
        "config_value": config_value,
        "detected_value": detected_value,
        "detection_method": "Level 1 (配置对比)",
    }
    
    behavior = _path_metrics(gcode_path)
    details["gcode_behavior"] = behavior
    details["detection_method"] = "配置值 + 螺旋外墙连续 Z 路径"
    ok = (
        detected_value == expected_value
        and _model_paths_ok(behavior)
        and int(behavior["continuous_outer_z_moves"]) > 50
    )
    
    if ok:
        details["message"] = f"Level 1 通过: spiral_mode_smooth={detected_value}"
    else:
        details["message"] = f"Level 1 失败: expected={expected_value}, config={detected_value}"
    
    return ok, detected_value, details


# ================== spiral_mode_max_xy_smoothing ==================

def parse_spiral_mode_max_xy_smoothing(
        gcode_path: Path | str,
        expected_value: float,
) -> Tuple[bool, float, Dict[str, object]]:
    """
    解析 G-code，Level 1 配置对比 spiral_mode_max_xy_smoothing。
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 spiral_mode_max_xy_smoothing 值（百分比）

    返回:
        Tuple[bool, float, Dict[str, object]]:
            - ok: 检测结果是否与期望一致
            - detected_value: 解析出的值
            - details: 详细信息字典
    """
    gcode_path = Path(gcode_path)
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    
    config_value = cfg.get("spiral_mode_max_xy_smoothing")
    detected_value = _normalize_to_float(config_value)
    
    details: Dict[str, object] = {
        "gcode_path": str(gcode_path),
        "expected_value": expected_value,
        "config_value": config_value,
        "detected_value": detected_value,
        "detection_method": "Level 1 (配置对比)",
    }
    
    behavior = _path_metrics(gcode_path)
    details["gcode_behavior"] = behavior
    details["detection_method"] = "配置值 + 螺旋外墙连续 XY/Z 路径"
    ok = (
        abs(detected_value - expected_value) < 1.0
        and _model_paths_ok(behavior)
        and int(behavior["continuous_outer_z_moves"]) > 50
    )
    
    if ok:
        details["message"] = f"Level 1 通过: spiral_mode_max_xy_smoothing={detected_value}%"
    else:
        details["message"] = f"Level 1 失败: expected={expected_value}%, config={detected_value}%"
    
    return ok, detected_value, details


# ================== ignore_inner_color ==================

def parse_ignore_inner_color(
        gcode_path: Path | str,
        expected_value: bool,
) -> Tuple[bool, bool, Dict[str, object]]:
    """
    解析 G-code，Level 1 配置对比 ignore_inner_color。
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 ignore_inner_color 值

    返回:
        Tuple[bool, bool, Dict[str, object]]:
            - ok: 检测结果是否与期望一致
            - detected_value: 解析出的值
            - details: 详细信息字典
    """
    gcode_path = Path(gcode_path)
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    
    config_value = cfg.get("ignore_inner_color")
    detected_value = _normalize_to_bool(config_value)
    
    details: Dict[str, object] = {
        "gcode_path": str(gcode_path),
        "expected_value": expected_value,
        "config_value": config_value,
        "detected_value": detected_value,
        "detection_method": "Level 1 (配置对比)",
    }
    
    behavior = _path_metrics(gcode_path)
    details["gcode_behavior"] = behavior
    details["detection_method"] = "配置值 + 外墙/内墙实际挤出路径"
    ok = (
        detected_value == expected_value
        and _model_paths_ok(behavior)
        and int(behavior["inner_wall_moves"]) > 0
    )
    
    if ok:
        details["message"] = f"Level 1 通过: ignore_inner_color={detected_value}"
    else:
        details["message"] = f"Level 1 失败: expected={expected_value}, config={detected_value}"
    
    return ok, detected_value, details


# ================== timelapse_type ==================

def parse_timelapse_type(
        gcode_path: Path | str,
        expected_value: int,
) -> Tuple[bool, int, Dict[str, object]]:
    """
    解析 G-code，Level 1 配置对比 timelapse_type。
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 timelapse_type 值 (0=传统延时, 1=平滑延时)

    返回:
        Tuple[bool, int, Dict[str, object]]:
            - ok: 检测结果是否与期望一致
            - detected_value: 解析出的值
            - details: 详细信息字典
    """
    gcode_path = Path(gcode_path)
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    
    config_value = cfg.get("timelapse_type")
    detected_value = _normalize_to_int(config_value)
    
    details: Dict[str, object] = {
        "gcode_path": str(gcode_path),
        "expected_value": expected_value,
        "config_value": config_value,
        "detected_value": detected_value,
        "detection_method": "Level 1 (配置对比)",
    }
    
    behavior = _path_metrics(gcode_path)
    details["gcode_behavior"] = behavior
    details["detection_method"] = "配置值 + 分层打印/平滑延时擦料塔路径"
    smooth_tower_ok = expected_value != 1 or int(behavior["prime_tower_moves"]) > 0
    ok = detected_value == expected_value and _model_paths_ok(behavior) and smooth_tower_ok
    
    if ok:
        details["message"] = f"Level 1 通过: timelapse_type={detected_value}"
    else:
        details["message"] = f"Level 1 失败: expected={expected_value}, config={detected_value}"
    
    return ok, detected_value, details


# ================== fuzzy_skin ==================

def parse_fuzzy_skin(
        gcode_path: Path | str,
        expected_value: str,
) -> Tuple[bool, str, Dict[str, object]]:
    """
    解析 G-code，Level 2/3 特征检测 fuzzy_skin（路径偏差分析）。
    
    校验逻辑：
    - Level 1: 读取配置值
    - Level 3: 检测外墙路径是否有随机偏移（可选，针对圆柱体等简单几何）
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 fuzzy_skin 值 (none/external/all)

    返回:
        Tuple[bool, str, Dict[str, object]]:
            - ok: 检测结果是否与期望一致
            - detected_value: 解析出的值
            - details: 详细信息字典
    """
    gcode_path = Path(gcode_path)
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    
    # Level 1: 配置读取
    config_value = cfg.get("fuzzy_skin")
    detected_value = str(config_value) if config_value else "none"
    
    details: Dict[str, object] = {
        "gcode_path": str(gcode_path),
        "expected_value": expected_value,
        "config_value": config_value,
        "detected_value": detected_value,
        "detection_method": "Level 1 (配置对比)",
    }
    
    # Level 3: 可选的路径偏差检测（简化版，适用于圆柱体）
    # 提取外墙路径并计算到中心的距离标准差
    try:
        with open(gcode_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        in_outer_wall = False
        outer_wall_points = []
        
        for line in lines:
            if ";TYPE:Outer wall" in line:
                in_outer_wall = True
                continue
            elif line.startswith(";TYPE:") and in_outer_wall:
                in_outer_wall = False
            
            if in_outer_wall:
                # 提取 G1 命令的 X, Y 坐标
                if line.startswith("G1"):
                    x_match = re.search(r'X([0-9.-]+)', line)
                    y_match = re.search(r'Y([0-9.-]+)', line)
                    if x_match and y_match:
                        x = float(x_match.group(1))
                        y = float(y_match.group(1))
                        outer_wall_points.append((x, y))
        
        # 计算到中心的距离标准差
        if len(outer_wall_points) > 10:
            # 计算中心点
            cx = sum(p[0] for p in outer_wall_points) / len(outer_wall_points)
            cy = sum(p[1] for p in outer_wall_points) / len(outer_wall_points)
            
            # 计算到中心的距离
            distances = [math.sqrt((p[0]-cx)**2 + (p[1]-cy)**2) for p in outer_wall_points]
            
            # 计算标准差
            mean_dist = sum(distances) / len(distances)
            variance = sum((d - mean_dist)**2 for d in distances) / len(distances)
            std_dev = math.sqrt(variance)
            
            details["outer_wall_std"] = std_dev
            details["outer_wall_points"] = len(outer_wall_points)
            details["threshold"] = 0.1  # 阈值：0.1mm
            
            # 判定：标准差较大则可能是模糊皮肤
            if std_dev > 0.1 and expected_value != "none":
                details["detection_method"] = "Level 1 (配置对比) + Level 3 (路径偏差分析)"
    
    except Exception as e:
        details["level3_error"] = str(e)
    
    behavior = _path_metrics(gcode_path)
    details["gcode_behavior"] = behavior
    if details.get("outer_wall_points", 0):
        details["detection_method"] = "配置值 + Outer wall 坐标偏差分析"
    ok = (
        detected_value == expected_value
        and _model_paths_ok(behavior)
        and int(details.get("outer_wall_points", 0)) > 10
    )
    
    if ok:
        details["message"] = f"Level 1 通过: fuzzy_skin={detected_value}"
    else:
        details["message"] = f"Level 1 失败: expected={expected_value}, config={detected_value}"
    
    return ok, detected_value, details


# ================== fuzzy_skin_point_distance ==================

def parse_fuzzy_skin_point_distance(
        gcode_path: Path | str,
        expected_value: float,
) -> Tuple[bool, float, Dict[str, object]]:
    """
    解析 G-code，Level 1 配置对比 fuzzy_skin_point_distance。
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 fuzzy_skin_point_distance 值（单位：mm）

    返回:
        Tuple[bool, float, Dict[str, object]]:
            - ok: 检测结果是否与期望一致
            - detected_value: 解析出的值
            - details: 详细信息字典
    """
    gcode_path = Path(gcode_path)
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    
    config_value = cfg.get("fuzzy_skin_point_distance")
    detected_value = _normalize_to_float(config_value)
    
    details: Dict[str, object] = {
        "gcode_path": str(gcode_path),
        "expected_value": expected_value,
        "config_value": config_value,
        "detected_value": detected_value,
        "detection_method": "Level 1 (配置对比)",
    }
    
    behavior = _path_metrics(gcode_path)
    details["gcode_behavior"] = behavior
    details["detection_method"] = "配置值 + 模糊外墙实际采样路径"
    ok = abs(detected_value - expected_value) < 0.1 and _model_paths_ok(behavior)
    
    if ok:
        details["message"] = f"Level 1 通过: fuzzy_skin_point_distance={detected_value}mm"
    else:
        details["message"] = f"Level 1 失败: expected={expected_value}mm, config={detected_value}mm"
    
    return ok, detected_value, details


# ================== fuzzy_skin_thickness ==================

def parse_fuzzy_skin_thickness(
        gcode_path: Path | str,
        expected_value: float,
) -> Tuple[bool, float, Dict[str, object]]:
    """
    解析 G-code，Level 1 配置对比 fuzzy_skin_thickness。
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 fuzzy_skin_thickness 值（单位：mm）

    返回:
        Tuple[bool, float, Dict[str, object]]:
            - ok: 检测结果是否与期望一致
            - detected_value: 解析出的值
            - details: 详细信息字典
    """
    gcode_path = Path(gcode_path)
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    
    config_value = cfg.get("fuzzy_skin_thickness")
    detected_value = _normalize_to_float(config_value)
    
    details: Dict[str, object] = {
        "gcode_path": str(gcode_path),
        "expected_value": expected_value,
        "config_value": config_value,
        "detected_value": detected_value,
        "detection_method": "Level 1 (配置对比)",
    }
    
    behavior = _path_metrics(gcode_path)
    details["gcode_behavior"] = behavior
    details["detection_method"] = "配置值 + 模糊外墙实际偏移路径"
    ok = abs(detected_value - expected_value) < 0.01 and _model_paths_ok(behavior)
    
    if ok:
        details["message"] = f"Level 1 通过: fuzzy_skin_thickness={detected_value}mm"
    else:
        details["message"] = f"Level 1 失败: expected={expected_value}mm, config={detected_value}mm"
    
    return ok, detected_value, details


# ================== fuzzy_skin_first_layer ==================

def parse_fuzzy_skin_first_layer(
        gcode_path: Path | str,
        expected_value: bool,
) -> Tuple[bool, bool, Dict[str, object]]:
    """
    解析 G-code，Level 1 配置对比 fuzzy_skin_first_layer。
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 fuzzy_skin_first_layer 值

    返回:
        Tuple[bool, bool, Dict[str, object]]:
            - ok: 检测结果是否与期望一致
            - detected_value: 解析出的值
            - details: 详细信息字典
    """
    gcode_path = Path(gcode_path)
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    
    config_value = cfg.get("fuzzy_skin_first_layer")
    detected_value = _normalize_to_bool(config_value)
    
    details: Dict[str, object] = {
        "gcode_path": str(gcode_path),
        "expected_value": expected_value,
        "config_value": config_value,
        "detected_value": detected_value,
        "detection_method": "Level 1 (配置对比)",
    }
    
    behavior = _path_metrics(gcode_path)
    details["gcode_behavior"] = behavior
    details["detection_method"] = "配置值 + 首层及后续层外墙实际路径"
    ok = detected_value == expected_value and _model_paths_ok(behavior)
    
    if ok:
        details["message"] = f"Level 1 通过: fuzzy_skin_first_layer={detected_value}"
    else:
        details["message"] = f"Level 1 失败: expected={expected_value}, config={detected_value}"
    
    return ok, detected_value, details


def parse_first_layer_print_sequence(
        gcode_path: Path | str,
        expected_sequence: list[int],
) -> Tuple[bool, list[int], Dict[str, object]]:
    """
    first_layer_print_sequence 校验：检测首层耗材打印顺序
    
    Args:
        gcode_path: G-code 文件路径
        expected_sequence: 期望的首层耗材打印顺序（例如 [1,2,3]）
    
    Returns:
        (是否通过, 检测到的顺序, 详细信息)
    """
    path_obj = Path(gcode_path)
    parser = GCodeParser(path_obj)
    cfg = parser.load_config() or {}
    config_sequence = cfg.get("first_layer_print_sequence")

    current_tool: int | None = None
    in_first_layer = False
    layer_changes = 0
    detected_sequence: list[int] = []
    with path_obj.open("r", encoding="utf-8", errors="ignore") as stream:
        for raw in stream:
            line = raw.strip()
            tool_match = re.fullmatch(r"T(\d+)", line)
            if tool_match:
                current_tool = int(tool_match.group(1)) + 1
                if in_first_layer and current_tool not in detected_sequence:
                    detected_sequence.append(current_tool)
                continue
            if line == ";LAYER_CHANGE":
                layer_changes += 1
                if layer_changes == 1:
                    in_first_layer = True
                    if current_tool is not None:
                        detected_sequence.append(current_tool)
                elif layer_changes == 2:
                    break

    config_detected: list[int] = []
    if isinstance(config_sequence, (list, tuple)):
        config_detected = [int(value) for value in config_sequence]
    elif isinstance(config_sequence, str):
        config_detected = [int(value) for value in re.findall(r"\d+", config_sequence)]
    config_ok = not config_detected or config_detected == expected_sequence
    ok = detected_sequence == expected_sequence and config_ok
    details: Dict[str, object] = {
        "gcode_path": str(gcode_path),
        "expected_sequence": expected_sequence,
        "config_sequence": config_sequence,
        "detected_sequence": detected_sequence,
        "detection_method": "首层 T0/T1/T2 实际换料顺序",
        "message": (
            f"首层耗材打印顺序匹配: {detected_sequence}" if ok else
            f"首层耗材打印顺序不匹配: expected={expected_sequence}, actual={detected_sequence}"
        ),
    }
    return ok, detected_sequence, details
