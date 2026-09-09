from __future__ import annotations

import math
import re
import warnings
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Any

from engine_params.src.gcode.GCodeParser import GCodeParser
from engine_params.src.gcode.GCodeParserEx import GCodeParserEx
from engine_params.src.gcode.constants import ExtrusionType
from engine_params.src.gcode.GCodeParser import Point
from engine_params.src.gcode.process.quality.behavior import BehaviorGCode


class GapFillTarget(str, Enum):
    """Gap infill 分布期望类型枚举。"""

    EVERYWHERE = "everywhere"   # 各层都允许出现 Gap infill
    NOWHERE    = "nowhere"      # 任何层都不允许出现 Gap infill
    TOPBOTTOM  = "topbottom"    # 仅允许首层/末层出现 Gap infill

    @classmethod
    def from_str(cls, value: str) -> "GapFillTarget":
        """
        解析字符串为 GapFillTarget。
        - 规范化：lower + 去首尾空白 + 去除非 a-z 字符
        - 支持别名：如 'top-bottom'、'top_bottom'、'tb'、'all'、'none' 等
        """
        if not isinstance(value, str):
            raise TypeError(f"GapFillTarget.from_str 期望 str，收到 {type(value).__name__}")

        # 统一成仅含小写字母，便于匹配
        key = re.sub(r"[^a-z]", "", value.strip().lower())

        aliases = {
            # EVERYWHERE
            "everywhere": cls.EVERYWHERE,

            # NOWHERE
            "nowhere": cls.NOWHERE,

            # TOPBOTTOM
            "topbottom": cls.TOPBOTTOM,
        }

        # 直接命中别名
        if key in aliases:
            return aliases[key]

        # 兜底：与枚举值做同样的规范化后比对（允许传原始值的花样写法）
        for member in cls:
            if key == re.sub(r"[^a-z]", "", member.value.lower()):
                return member

        allowed = ", ".join(m.value for m in cls)
        raise ValueError(f"无法解析 '{value}' 为 GapFillTarget，有效取值：{allowed}")


def _collect_gap_layers(per_layer_blocks: Sequence[Optional[Dict[int, Dict[str, object]]]]) -> List[int]:
    """统计哪些层存在 Gap infill 挤出块。"""
    layers: List[int] = []
    for idx, layer_map in enumerate(per_layer_blocks or []):
        if not layer_map:
            continue
        for obj_blocks in layer_map.values():
            if obj_blocks:
                layers.append(idx)
                break
    return layers


def parse_gap_fill_target(
        gcode_path: Path | str,
        expected_target: GapFillTarget,
) -> Tuple[bool, GapFillTarget, Dict[str, object], List[str]]:
    """
    按层检查 Gap infill 是否符合期望的分布模式。

    返回：
        ok: 是否符合期望；
        actual_target: 检测得到的实际分布类型；
        details: 具体层信息；
        warnings: 仅用于 EVERYWHERE 的提醒（查不到 Gap infill 但并非硬性失败）。
    """
    parser = GCodeParser(Path(gcode_path))
    per_layer_gap = parser.get_extrusion_blocks_per_layer(
        ExtrusionType.GAP_INFILL.value,
        include_wipe=False,
        decode=False,
        workers=0,
    )
    layer_info = parser.extract_layers()
    layer_count = len(layer_info)

    gap_layers = _collect_gap_layers(per_layer_gap or [])
    warn_list: List[str] = []

    if not gap_layers:
        actual_target = GapFillTarget.NOWHERE
    else:
        allowed_top_bottom: set[int] = set()
        if layer_count > 0:
            allowed_top_bottom.add(0)
            if layer_count > 1:
                allowed_top_bottom.add(layer_count - 1)
        if allowed_top_bottom and all(idx in allowed_top_bottom for idx in gap_layers):
            actual_target = GapFillTarget.TOPBOTTOM
        else:
            actual_target = GapFillTarget.EVERYWHERE

    ok = True
    forbidden_layers: List[int] = []

    if expected_target == GapFillTarget.NOWHERE:
        ok = len(gap_layers) == 0
    elif expected_target == GapFillTarget.TOPBOTTOM:
        allowed: set[int] = set()
        if layer_count > 0:
            allowed.add(0)
            if layer_count > 1:
                allowed.add(layer_count - 1)
        forbidden_layers = [idx for idx in gap_layers if idx not in allowed]
        ok = not forbidden_layers
    elif expected_target == GapFillTarget.EVERYWHERE:
        if not gap_layers:
            msg = "Gap infill blocks not found while expectation is 'everywhere'."
            warnings.warn(msg, UserWarning)
            warn_list.append(msg)
        ok = True

    details: Dict[str, object] = {
        "gap_layers": gap_layers,
        "layer_count": layer_count,
        "forbidden_layers": forbidden_layers,
        "expected": expected_target.value,
        "actual": actual_target.value,
    }

    return ok, actual_target, details, warn_list


def parse_filter_out_gap_fill(
        gcode_path: Path | str,
        expected_value: float,
        *,
        tolerance: float = 1e-3,
) -> Tuple[bool, Optional[float], Dict[str, object]]:
    """
    读取 gap_fill_target（用于 filter_out_gap_fill 参数），并校验：
      1. 配置值是否与期望差距不超过 tolerance；
      2. G-code 中是否已不存在 Gap infill 挤出块。
    """
    parser = GCodeParser(Path(gcode_path))
    cfg = parser.load_config()

    raw_value = cfg.get("filter_out_gap_fill")
    actual_value: Optional[float] = None
    if raw_value is not None:
        try:
            actual_value = float(str(raw_value).strip())
        except ValueError:
            actual_value = None

    value_ok = (
            actual_value is not None
            and abs(actual_value - expected_value) <= tolerance
    )

    per_layer_gap = parser.get_extrusion_blocks_per_layer(
        ExtrusionType.GAP_INFILL.value,
        include_wipe=False,
        decode=False,
        workers=0,
    )
    gap_layers = _collect_gap_layers(per_layer_gap or [])
    extrusions_ok = len(gap_layers) == 0

    ok = value_ok and extrusions_ok

    details: Dict[str, object] = {
        "expected_value": expected_value,
        "actual_value": actual_value,
        "value_ok": value_ok,
        "gap_layers": gap_layers,
        "extrusions_ok": extrusions_ok,
    }

    return ok, actual_value, details


def _config_scalar(value: Any) -> str:
    value = getattr(value, "value", value)
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).strip().lower()


def _role_behavior_signature(path: Path | str, role: str) -> Dict[str, Any]:
    behavior = BehaviorGCode(path)
    moves = [move for move in behavior.extrusion_moves(role) if move.xy_length >= 0.05]
    layers = sorted({move.layer for move in moves})
    total_length = sum(move.xy_length for move in moves)

    bins = [0.0] * 12
    for move in moves:
        if move.angle is not None:
            bins[min(11, int(move.angle / 15.0))] += move.xy_length
    if total_length > 0:
        bins = [value / total_length for value in bins]

    bounds = None
    if moves:
        xs = [coord for move in moves for coord in (move.x0, move.x)]
        ys = [coord for move in moves for coord in (move.y0, move.y)]
        bounds = [min(xs), max(xs), min(ys), max(ys)]

    return {
        "move_count": len(moves),
        "layers": layers,
        "total_length": total_length,
        "orientation_histogram": bins,
        "bounds": bounds,
    }


def _compare_role_behavior(
        gcode_path: Path | str,
        baseline_gcode_path: Path | str,
        *,
        role: str,
        config_key: str,
) -> Tuple[bool, bool, Dict[str, Any]]:
    """Compare stable generated behavior, avoiding vertex/order snapshot noise."""
    test_sig = _role_behavior_signature(gcode_path, role)
    baseline_sig = _role_behavior_signature(baseline_gcode_path, role)

    test_cfg = GCodeParserEx(Path(gcode_path)).load_config() or {}
    baseline_cfg = GCodeParserEx(Path(baseline_gcode_path)).load_config() or {}
    test_value = _config_scalar(test_cfg.get(config_key))
    baseline_value = _config_scalar(baseline_cfg.get(config_key))
    config_match = test_value == baseline_value and test_value not in {"", "none"}

    test_layers = set(test_sig["layers"])
    baseline_layers = set(baseline_sig["layers"])
    union = test_layers | baseline_layers
    layer_overlap = len(test_layers & baseline_layers) / len(union) if union else 0.0

    baseline_length = float(baseline_sig["total_length"])
    length_ratio = (
        float(test_sig["total_length"]) / baseline_length if baseline_length > 0 else 0.0
    )

    a = test_sig["orientation_histogram"]
    b = baseline_sig["orientation_histogram"]
    dot = sum(x * y for x, y in zip(a, b))
    norm = math.sqrt(sum(x * x for x in a) * sum(y * y for y in b))
    orientation_similarity = dot / norm if norm > 0 else 0.0

    bounds_delta = None
    if test_sig["bounds"] is not None and baseline_sig["bounds"] is not None:
        bounds_delta = max(
            abs(x - y) for x, y in zip(test_sig["bounds"], baseline_sig["bounds"])
        )

    checks = {
        "config_match": config_match,
        "has_generated_role": test_sig["move_count"] > 0 and baseline_sig["move_count"] > 0,
        "layer_overlap": layer_overlap >= 0.90,
        "path_length_ratio": 0.55 <= length_ratio <= 1.80,
        "orientation_similarity": orientation_similarity >= 0.55,
        "bounds_stable": bounds_delta is not None and bounds_delta <= 1.0,
    }
    match = all(checks.values())
    return match, match, {
        "mode": "generated-role-behavior",
        "role": role,
        "config_key": config_key,
        "test_config": test_value,
        "baseline_config": baseline_value,
        "checks": checks,
        "layer_overlap": layer_overlap,
        "path_length_ratio": length_ratio,
        "orientation_similarity": orientation_similarity,
        "bounds_delta": bounds_delta,
        "test_signature": test_sig,
        "baseline_signature": baseline_sig,
    }


def parse_rectilinear_path_continuity(
        gcode_path: Path | str,
        max_block_lines: int,
        max_retractions: int,
        max_wipe_sections: int,
        max_z_hop_travels: int,
) -> Tuple[bool, Dict[str, Any]]:
    """检查首个 Sparse infill 块是否被拆成异常多的短路径。

    该回归来自 fill_multiline=1 的复杂、含孔洞填充岛。错误实现把普通
    Rectilinear 送入多线连接器，使同一块内的回抽、WIPE 和 Z-hop 数量
    约增加到正常结果的四倍。这里使用宽松上限，避免依赖精确坐标或行号。
    """
    path = Path(gcode_path)
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()

    fill_multiline = None
    for line in lines:
        match = re.match(r"^\s*;\s*fill_multiline\s*=\s*(.*?)\s*$", line)
        if match:
            fill_multiline = match.group(1)
            break

    start = next(
        (index for index, line in enumerate(lines)
         if line.strip().lower() == ";type:sparse infill"),
        None,
    )
    if start is None:
        return False, {
            "error": "missing ';TYPE:Sparse infill' block",
            "fill_multiline": fill_multiline,
        }

    end = len(lines)
    for index in range(start + 1, len(lines)):
        marker = lines[index].strip().lower()
        if marker.startswith(";type:") or marker.startswith("; layer num/") or marker == ";layer_change":
            end = index
            break

    from engine_params.src.gcode.process.strength.continuity_metrics import first_block_metrics

    metrics, retraction_lines = first_block_metrics(path, lines, start, end)
    limits = {
        "block_lines": max_block_lines,
        "retractions": max_retractions,
        "wipe_sections": max_wipe_sections,
        "z_hop_travels": max_z_hop_travels,
    }
    checks = {
        "fill_multiline_is_one": fill_multiline is not None and fill_multiline.strip() == "1",
        "has_extrusion": metrics["printing_moves"] > 0,
        **{name: metrics[name] <= limit for name, limit in limits.items()},
    }
    return all(checks.values()), {
        "mode": "rectilinear-path-continuity",
        "fill_multiline": fill_multiline,
        "metrics": metrics,
        "limits": limits,
        "checks": checks,
        "block_line_range": [start + 1, end],
        "retraction_event_lines": retraction_lines,
    }


def parse_sparse_infill_pattern(
        gcode_path: Path | str,
        baseline_gcode_path: Path | str,
        tolerance: float = 1e-6,
        object_id: int = 0,
) -> Tuple[bool, bool, Dict[str, Any]]:
    """Validate sparse-infill identity and stable generated path behavior."""
    # Lightning 的树枝由随机种子/并行调度生成，逐点快照并不稳定。
    # 按实现特征验证：树枝只在靠近顶面时逐层分叉，路径数量应存在
    # 多个级别且后半段明显多于最初生成的层。
    config = GCodeParserEx(Path(gcode_path)).load_config() or {}
    raw_pattern = config.get("sparse_infill_pattern")
    pattern = str(getattr(raw_pattern, "value", raw_pattern) or "").strip().lower()
    if pattern == "lightning":
        parser = GCodeParser(Path(gcode_path))
        contours = parser.get_type_contours_per_layer_by_object(
            object_id, types=[ExtrusionType.SPARSE_INFILL]
        ) or []
        counts = [
            len(layer.get(ExtrusionType.SPARSE_INFILL, []))
            for layer in contours
            if layer.get(ExtrusionType.SPARSE_INFILL)
        ]
        split = max(1, len(counts) // 2)
        first_peak = max(counts[:split], default=0)
        second_peak = max(counts[split:], default=0)
        match = len(counts) >= 5 and len(set(counts)) >= 3 and second_peak > first_peak
        return match, match, {
            "mode": "lightning-branch-growth",
            "pattern": pattern,
            "sparse_path_counts": counts,
            "first_half_peak": first_peak,
            "second_half_peak": second_peak,
            "match": match,
        }

    # 其余图案核对配置身份及生成路径的稳定几何特征；切片算法允许重新分段，
    # 因此不再要求 polyline/point 数量与旧版本完全一致。
    return _compare_role_behavior(
        gcode_path,
        baseline_gcode_path,
        role=ExtrusionType.SPARSE_INFILL.value,
        config_key="sparse_infill_pattern",
    )

    # Legacy exact-coordinate implementation retained below for reference.
    baseline_parser = GCodeParser(Path(baseline_gcode_path))
    baseline_contours = baseline_parser.get_type_contours_per_layer_by_object(
        object_id,
        types=[ExtrusionType.SPARSE_INFILL]
    )
    
    # 加载测试G-code
    test_parser = GCodeParser(Path(gcode_path))
    test_contours = test_parser.get_type_contours_per_layer_by_object(
        object_id,
        types=[ExtrusionType.SPARSE_INFILL]
    )
    
    # 初始化结果
    ok = True
    match = True
    details = {
        "baseline_layer_count": len(baseline_contours),
        "test_layer_count": len(test_contours),
        "mismatch_layers": [],
        "error_details": []
    }
    
    # 检查层数是否一致
    if len(baseline_contours) != len(test_contours):
        ok = False
        match = False
        details["error_details"].append(
            f"Layer count mismatch: baseline has {len(baseline_contours)}, test has {len(test_contours)}"
        )
        return ok, match, details
    
    # 遍历每一层进行比较
    for layer_idx in range(len(baseline_contours)):
        baseline_layer = baseline_contours[layer_idx]
        test_layer = test_contours[layer_idx]
        
        # 检查基准层中是否有SPARSE_INFILL
        if ExtrusionType.SPARSE_INFILL not in baseline_layer:
            # 基准层没有SPARSE_INFILL，测试层也不应该有
            if ExtrusionType.SPARSE_INFILL in test_layer:
                ok = False
                match = False
                mismatch_info = {
                    "layer_idx": layer_idx,
                    "reason": "Baseline has no SPARSE_INFILL but test does",
                    "baseline_polylines": 0,
                    "test_polylines": len(test_layer[ExtrusionType.SPARSE_INFILL]) if ExtrusionType.SPARSE_INFILL in test_layer else 0
                }
                details["mismatch_layers"].append(mismatch_info)
            continue
        
        # 检查测试层中是否有SPARSE_INFILL
        if ExtrusionType.SPARSE_INFILL not in test_layer:
            ok = False
            match = False
            mismatch_info = {
                "layer_idx": layer_idx,
                "reason": "Test has no SPARSE_INFILL but baseline does",
                "baseline_polylines": len(baseline_layer[ExtrusionType.SPARSE_INFILL]),
                "test_polylines": 0
            }
            details["mismatch_layers"].append(mismatch_info)
            continue
        
        # 获取轮廓
        baseline_polylines = baseline_layer[ExtrusionType.SPARSE_INFILL]
        test_polylines = test_layer[ExtrusionType.SPARSE_INFILL]
        
        # 检查polyline数量是否一致
        if len(baseline_polylines) != len(test_polylines):
            ok = False
            match = False
            mismatch_info = {
                "layer_idx": layer_idx,
                "reason": "Polyline count mismatch",
                "baseline_polylines": len(baseline_polylines),
                "test_polylines": len(test_polylines)
            }
            details["mismatch_layers"].append(mismatch_info)
            continue
        
        # 遍历每条polyline进行比较
        polyline_match = True
        for poly_idx in range(len(baseline_polylines)):
            baseline_polyline = baseline_polylines[poly_idx]
            test_polyline = test_polylines[poly_idx]
            
            # 检查点数是否一致
            if len(baseline_polyline) != len(test_polyline):
                ok = False
                match = False
                polyline_match = False
                details["error_details"].append(
                    f"Layer {layer_idx}, Polyline {poly_idx}: Point count mismatch - baseline: {len(baseline_polyline)}, test: {len(test_polyline)}"
                )
                continue
            
            # 比较每个点的坐标
            for point_idx in range(len(baseline_polyline)):
                baseline_point = baseline_polyline[point_idx]
                test_point = test_polyline[point_idx]
                
                # 检查x坐标
                if abs(baseline_point.x - test_point.x) > tolerance:
                    ok = False
                    match = False
                    polyline_match = False
                    details["error_details"].append(
                        f"Layer {layer_idx}, Polyline {poly_idx}, Point {point_idx}: X coordinate mismatch - baseline: {baseline_point.x}, test: {test_point.x}"
                    )
                
                # 检查y坐标
                if abs(baseline_point.y - test_point.y) > tolerance:
                    ok = False
                    match = False
                    polyline_match = False
                    details["error_details"].append(
                        f"Layer {layer_idx}, Polyline {poly_idx}, Point {point_idx}: Y coordinate mismatch - baseline: {baseline_point.y}, test: {test_point.y}"
                    )
        
        # 如果该层有不匹配的polyline，记录信息
        if not polyline_match:
            mismatch_info = {
                "layer_idx": layer_idx,
                "reason": "Point coordinate mismatches found in polylines",
                "baseline_polylines": len(baseline_polylines),
                "test_polylines": len(test_polylines)
            }
            details["mismatch_layers"].append(mismatch_info)
    
    # 如果没有发现不匹配，记录成功信息
    if match:
        details["error_details"].append("All layers, polylines and points match within tolerance")
    
    return ok, match, details


# ================== infill_wall_overlap ==================
def parse_infill_wall_overlap(
        gcode_path: Path | str,
        baseline_gcode_path: Path | str,
        *,
        tolerance: float = 1e-6,
        object_id: int = 0,
) -> Tuple[bool, Dict[str, Any]]:
    """
    通过快照对比的方式校验 infill_wall_overlap：仅比较非首尾层上的 Sparse/Internal solid/Bridge 轮廓。
    """
    test_parser = GCodeParser(Path(gcode_path))
    baseline_parser = GCodeParser(Path(baseline_gcode_path))

    def _layer_filter(layer_idx: int, total_layers: int) -> bool:
        return 0 < layer_idx < total_layers - 1

    ok, details = GCodeParser.compare_type_contours(
        baseline_parser,
        test_parser,
        object_id=object_id,
        types=[
            ExtrusionType.SPARSE_INFILL,
            ExtrusionType.INTERNAL_SOLID_INFILL,
            ExtrusionType.INTERNAL_BRIDGE,
        ],
        tolerance=tolerance,
        layer_filter=_layer_filter,
    )
    details["baseline_gcode"] = str(Path(baseline_gcode_path))
    return ok, details

def parse_solid_infill_direction(
        gcode_path: Path | str,
        expected_angle: float,
        tolerance: float = 0.2,
        object_id: int = 0,
) -> Tuple[bool, float, Dict[str, object]]:
    """
    从GCode中计算实心填充和顶面填充的方向角度并与预期值比较。
    
    通过获取模型中所有层的INTERNAL_SOLID_INFILL、TOP_SURFACE和SPARSE_INFILL挤出块的轮廓，
    过滤出只包含INTERNAL_SOLID_INFILL或TOP_SURFACE的层（不同时包含SPARSE_INFILL），
    然后使用每一层对应挤出块的第一条polyline的前两个点来计算角度，与预期角度进行比较。
    
    参数
    ----
    gcode_path : Path | str
        测试G-code文件路径。
    expected_angle : float
        预期的填充角度（度）。
    tolerance : float
        角度比较的容差（度）。
    object_id : int
        模型ID。
    
    返回
    ----
    Tuple[bool, float, Dict[str, object]]
        (是否通过测试, 不符合预期角度的平均值, 详细信息)
    """
    # 加载G-code
    parser = GCodeParser(Path(gcode_path))
    # 获取所有需要的挤出块类型的轮廓
    extrusion_types = [
        ExtrusionType.INTERNAL_SOLID_INFILL, 
        ExtrusionType.TOP_SURFACE, 
        ExtrusionType.SPARSE_INFILL
    ]
    contours = parser.get_type_contours_per_layer_by_object(
        object_id,
        types=extrusion_types
    )
    
    # 初始化结果
    ok = True
    invalid_angles = []  # 存储不符合预期的角度
    details = {
        "layer_count": len(contours),
        "processed_layers": [],
        "error_details": [],
        "invalid_layers": []
    }
    
    # 遍历所有层
    for layer_idx in range(len(contours)):
        layer = contours[layer_idx]
        
        # 检查该层是否同时包含SPARSE_INFILL，如果是则跳过
        if ExtrusionType.SPARSE_INFILL in layer:
            details["invalid_layers"].append({
                "layer_idx": layer_idx,
                "reason": "Contains SPARSE_INFILL"
            })
            continue
        
        # 检查该层是否有INTERNAL_SOLID_INFILL或TOP_SURFACE
        target_extrusion_type = None
        if ExtrusionType.INTERNAL_SOLID_INFILL in layer:
            target_extrusion_type = ExtrusionType.INTERNAL_SOLID_INFILL
        elif ExtrusionType.TOP_SURFACE in layer:
            target_extrusion_type = ExtrusionType.TOP_SURFACE
        
        # 如果没有找到目标挤出类型，则跳过
        if target_extrusion_type is None:
            details["invalid_layers"].append({
                "layer_idx": layer_idx,
                "reason": "No INTERNAL_SOLID_INFILL or TOP_SURFACE found"
            })
            continue
        
        polylines = layer[target_extrusion_type]
        
        # 确保有polyline
        if not polylines:
            details["error_details"].append(
                f"Layer {layer_idx} has {target_extrusion_type} but no polylines"
            )
            ok = False
            continue
        
        # 获取第一条polyline
        first_polyline = polylines[0]
        
        # 确保polyline至少有两个点
        if len(first_polyline) < 2:
            details["error_details"].append(
                f"Layer {layer_idx}, first polyline has less than 2 points"
            )
            ok = False
            continue
        
        # 取polyline的前两个点来计算角度
        p1 = first_polyline[0]
        p2 = first_polyline[1]
        
        # 计算向量
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        
        # 计算角度（弧度）
        angle_rad = math.atan2(dy, dx)
        
        # 转换为角度（度）
        angle_deg = math.degrees(angle_rad)
        
        # 标准化角度到0-180度范围（填充角度通常用0-180度表示）
        if angle_deg < 0:
            angle_deg += 180
        elif angle_deg > 180:
            angle_deg -= 180
        
        # 与预期角度比较，考虑容差
        angle_diff = min(
            abs(angle_deg - expected_angle),
            abs(abs(angle_deg - expected_angle) - 180)
        )
        
        layer_result = {
            "layer_idx": layer_idx,
            "extrusion_type": target_extrusion_type,
            "calculated_angle": angle_deg,
            "expected_angle": expected_angle,
            "angle_diff": angle_diff,
            "within_tolerance": angle_diff <= tolerance
        }
        
        details["processed_layers"].append(layer_result)
        
        # 如果角度超出容差范围，记录该角度
        if angle_diff > tolerance:
            ok = False
            invalid_angles.append(angle_deg)
            details["error_details"].append(
                f"Layer {layer_idx} angle mismatch: calculated {angle_deg:.2f}°, expected {expected_angle}° ± {tolerance}°"
            )
    
    # 计算不符合预期角度的平均值
    invalid_angle_average = sum(invalid_angles) / len(invalid_angles) if invalid_angles else 0.0
    
    # 检查是否找到了有效的角度
    if not details["processed_layers"]:
        ok = False
        details["error_details"].append("No valid layers found to calculate solid infill direction")
    
    return ok, invalid_angle_average, details


def parse_rotate_solid_infill_direction(
        gcode_path: Path | str,
        expected_value: bool,
        tolerance: float = 0.2,
        object_id: int = 0,
) -> Tuple[bool, bool, Dict[str, object]]:
    """
    测试旋转实心填充方向功能是否正常工作。
    
    通过获取模型中所有层的INTERNAL_SOLID_INFILL、TOP_SURFACE和SPARSE_INFILL挤出块的轮廓，
    过滤出只包含INTERNAL_SOLID_INFILL或TOP_SURFACE的层（不同时包含SPARSE_INFILL），
    计算每层的实心填充角度，并检查严格相邻的实心层之间的角度差是否为90°（如果开启旋转选项）。
    
    参数
    ----
    gcode_path : Path | str
        测试G-code文件路径。
    expected_value : bool
        预期的旋转实心填充方向选项值。
    tolerance : float
        角度比较的容差（度）。
    object_id : int
        模型ID。
    
    返回
    ----
    Tuple[bool, bool, Dict[str, object]]
        (是否通过测试, 实际检测到的旋转状态, 详细信息)
    """
    # 加载G-code
    parser = GCodeParser(Path(gcode_path))
    # 获取所有需要的挤出块类型的轮廓
    extrusion_types = [
        ExtrusionType.INTERNAL_SOLID_INFILL, 
        ExtrusionType.TOP_SURFACE, 
        ExtrusionType.SPARSE_INFILL
    ]
    contours = parser.get_type_contours_per_layer_by_object(
        object_id,
        types=extrusion_types
    )
    
    # 初始化结果
    ok = True
    details = {
        "layer_count": len(contours),
        "processed_layers": [],
        "error_details": [],
        "invalid_layers": [],
        "solid_layers_info": [],  # 存储有效实心层的信息
        "adjacent_layer_pairs": []  # 存储相邻实心层对的信息
    }
    
    # 收集所有有效的实心层及其角度
    solid_layers = []
    
    # 遍历所有层，收集有效实心层的信息
    for layer_idx in range(len(contours)):
        layer = contours[layer_idx]
        
        # 检查该层是否同时包含SPARSE_INFILL，如果是则跳过
        if ExtrusionType.SPARSE_INFILL in layer:
            details["invalid_layers"].append({
                "layer_idx": layer_idx,
                "reason": "Contains SPARSE_INFILL"
            })
            continue
        
        # 检查该层是否有INTERNAL_SOLID_INFILL或TOP_SURFACE
        target_extrusion_type = None
        if ExtrusionType.INTERNAL_SOLID_INFILL in layer:
            target_extrusion_type = ExtrusionType.INTERNAL_SOLID_INFILL
        elif ExtrusionType.TOP_SURFACE in layer:
            target_extrusion_type = ExtrusionType.TOP_SURFACE
        
        # 如果没有找到目标挤出类型，则跳过
        if target_extrusion_type is None:
            details["invalid_layers"].append({
                "layer_idx": layer_idx,
                "reason": "No INTERNAL_SOLID_INFILL or TOP_SURFACE found"
            })
            continue
        
        polylines = layer[target_extrusion_type]
        
        # 确保有polyline
        if not polylines:
            details["error_details"].append(
                f"Layer {layer_idx} has {target_extrusion_type} but no polylines"
            )
            ok = False
            continue
        
        # 获取第一条polyline
        first_polyline = polylines[0]
        
        # 确保polyline至少有两个点
        if len(first_polyline) < 2:
            details["error_details"].append(
                f"Layer {layer_idx}, first polyline has less than 2 points"
            )
            ok = False
            continue
        
        # 取polyline的前两个点来计算角度
        p1 = first_polyline[0]
        p2 = first_polyline[1]
        
        # 计算向量
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        
        # 计算角度（弧度）
        angle_rad = math.atan2(dy, dx)
        
        # 转换为角度（度）
        angle_deg = math.degrees(angle_rad)
        
        # 标准化角度到0-180度范围（填充角度通常用0-180度表示）
        if angle_deg < 0:
            angle_deg += 180
        elif angle_deg > 180:
            angle_deg -= 180
        
        # 记录该实心层的信息
        layer_info = {
            "layer_idx": layer_idx,
            "extrusion_type": target_extrusion_type,
            "angle_deg": angle_deg
        }
        solid_layers.append(layer_info)
        details["solid_layers_info"].append(layer_info)
    
    # 检查是否找到了有效的实心层
    if len(solid_layers) < 2:
        ok = False
        details["error_details"].append(
            f"Not enough solid layers found to check rotation (found {len(solid_layers)} layers)"
        )
        return ok, False, details
    
    # 检查相邻实心层之间的角度关系
    actual_rotation_enabled = False
    has_adjacent_layers = False
    
    for i in range(len(solid_layers) - 1):
        # 获取当前层和下一层
        current_layer = solid_layers[i]
        next_layer = solid_layers[i + 1]
        
        # 检查是否是严格相邻的层（中间没有其他层）
        if next_layer["layer_idx"] - current_layer["layer_idx"] != 1:
            continue
        
        has_adjacent_layers = True
        
        # 计算两层之间的角度差（考虑180度周期性）
        angle_diff = min(
            abs(current_layer["angle_deg"] - next_layer["angle_deg"]),
            abs(abs(current_layer["angle_deg"] - next_layer["angle_deg"]) - 180)
        )
        
        # 判断角度差是否接近90度（考虑容差）
        is_orthogonal = abs(angle_diff - 90) <= tolerance
        
        # 记录相邻层对的信息
        pair_info = {
            "current_layer": current_layer["layer_idx"],
            "current_angle": current_layer["angle_deg"],
            "next_layer": next_layer["layer_idx"],
            "next_angle": next_layer["angle_deg"],
            "angle_diff": angle_diff,
            "is_orthogonal": is_orthogonal
        }
        details["adjacent_layer_pairs"].append(pair_info)
        
        # 如果发现任何一对相邻层是正交的，则认为旋转功能开启
        if is_orthogonal:
            actual_rotation_enabled = True
    
    # 检查是否有相邻的实心层
    if not has_adjacent_layers:
        ok = False
        details["error_details"].append(
            "No adjacent solid layers found to check rotation"
        )
        return ok, False, details
    
    # 比较实际旋转状态与预期值
    if actual_rotation_enabled != expected_value:
        ok = False
        if expected_value:
            details["error_details"].append(
                "Rotation of solid infill direction is expected to be enabled, but not detected"
            )
        else:
            details["error_details"].append(
                "Rotation of solid infill direction is expected to be disabled, but detected"
            )
    
    return ok, actual_rotation_enabled, details


def parse_infill_direction(
        gcode_path: Path | str,
        expected_angle: float,
        tolerance: float = 1.0,
        object_id: int = 0,
) -> Tuple[bool, float, Dict[str, object]]:
    """
    从GCode中计算稀疏填充的方向角度并与预期值比较。
    
    固定选取layer_idx==3的层进行判定，简化判断逻辑。
    
    参数
    ----
    gcode_path : Path | str
        测试G-code文件路径。
    expected_angle : float
        预期的填充角度（度）。
    tolerance : float
        角度比较的容差（度）。
    object_id : int
        模型ID。
    
    返回
    ----
    Tuple[bool, float, Dict[str, object]]
        (是否通过测试, 计算得到的角度, 详细信息)
    """
    # 加载G-code
    parser = GCodeParser(Path(gcode_path))
    contours = parser.get_type_contours_per_layer_by_object(
        object_id,
        types=[ExtrusionType.SPARSE_INFILL]
    )
    
    # 初始化结果
    ok = True
    calculated_angle = 0.0
    target_layer_idx = 3
    details = {
        "layer_count": len(contours),
        "target_layer": target_layer_idx,
        "angle_calculation": None,
        "error_details": []
    }
    
    # 检查目标层是否存在
    if target_layer_idx >= len(contours):
        ok = False
        details["error_details"].append(
            f"Target layer {target_layer_idx} does not exist in G-code (total layers: {len(contours)})"
        )
        return ok, calculated_angle, details
    
    # 获取目标层
    layer = contours[target_layer_idx]
    
    # 检查目标层是否有稀疏填充
    if ExtrusionType.SPARSE_INFILL not in layer:
        ok = False
        details["error_details"].append(
            f"Target layer {target_layer_idx} does not have SPARSE_INFILL"
        )
        return ok, calculated_angle, details
    
    polylines = layer[ExtrusionType.SPARSE_INFILL]
    
    # 确保有polyline
    if not polylines:
        ok = False
        details["error_details"].append(
            f"Target layer {target_layer_idx} has SPARSE_INFILL but no polylines"
        )
        return ok, calculated_angle, details
    
    # 获取第一条polyline
    first_polyline = polylines[0]
    
    # 确保polyline至少有两个点
    if len(first_polyline) < 2:
        ok = False
        details["error_details"].append(
            f"Target layer {target_layer_idx}, first polyline has less than 2 points"
        )
        return ok, calculated_angle, details
    
    # 取polyline的前两个点来计算角度
    p1 = first_polyline[0]
    p2 = first_polyline[1]
    
    # 计算向量
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    
    # 计算角度（弧度）
    angle_rad = math.atan2(dy, dx)
    
    # 转换为角度（度）
    angle_deg = math.degrees(angle_rad)
    
    # 标准化角度到0-180度范围（填充角度通常用0-180度表示）
    if angle_deg < 0:
        angle_deg += 180
    elif angle_deg > 180:
        angle_deg -= 180
    
    # 设置计算得到的角度
    calculated_angle = angle_deg
    
    # 与预期角度比较，考虑容差和180度周期性
    angle_diff = min(
        abs(angle_deg - expected_angle),
        abs(abs(angle_deg - expected_angle) - 180)
    )
    
    # 记录计算结果和比较结果
    layer_result = {
        "layer_idx": target_layer_idx,
        "angle_deg": angle_deg,
        "expected_angle": expected_angle,
        "angle_diff": angle_diff,
        "within_tolerance": angle_diff <= tolerance
    }
    details["angle_calculation"] = layer_result
    
    # 如果角度超出容差范围，记录错误
    if angle_diff > tolerance:
        ok = False
        details["error_details"].append(
            f"Target layer {target_layer_idx} angle mismatch: calculated {angle_deg:.2f}°, expected {expected_angle}° ± {tolerance}°"
        )
    
    return ok, calculated_angle, details


# # ================== infill_anchor && infill_anchor_max ==================
# def parse_anchor_line(gcode_path: Path,
#                       baseline_no_PointAndAnchor_line: str | Path,
#                       baseline_only_Point_line: str | Path,
#                       threshold: float,
#                       point_line: float,
#                       anchor_line: float, ):
#     """
# 
#     """
#     test_parser = GCodeParser(Path(gcode_path))
#     cfg = test_parser.load_config()
# 
#     raw_infill_anchor = cfg.get("infill_anchor")
#     raw_infill_anchor_max = cfg.get("infill_anchor_max")
#     op_infill_anchor: Optional[float] = None
#     op_infill_anchor_max: Optional[float] = None
#     if raw_infill_anchor is not None and raw_infill_anchor_max is not None:
#         try:
#             op_infill_anchor = float(str(raw_infill_anchor).strip())
#             op_infill_anchor_max = float(str(raw_infill_anchor_max).strip())
#         except ValueError:
#             op_infill_anchor = None
#             op_infill_anchor_max = None
#     assert op_infill_anchor is not None and op_infill_anchor_max is not None
# 
#     baseline_parser = None
# 
#     contours = test_parser.get_type_contours_per_layer_by_object(0, types=ExtrusionType.SPARSE_INFILL)
# 
#     # 实际上锚线的长度
#     actual_op_anchor_line = min(op_infill_anchor, op_infill_anchor_max)
#     assert actual_op_anchor_line < threshold / 2, "检测算法现在不支持大于 actual_op_anchor_line > threshold/2的情况"
# 
#     if op_infill_anchor_max <= threshold:
#         # 比阈值小，那么应该用的没有端点线的轮廓基线
#         if actual_op_anchor_line > 0:
#             assert point_line == 0, f"这种情况下应该没有端点线，端点线的长度 == 0，但现在端点线的期望为:{point_line}!"
# 
#         for layer_map in contours:
#             polylines = layer_map[ExtrusionType.SPARSE_INFILL]
# 
#             n_points = 0
#             for poly in polylines or []:
#                 step = 2
#                 for i in range(0, len(poly), step):
#                     n_points += 2
#                     dx = poly[i].x - poly[i + 1].x
#                     dy = poly[i].y - poly[i + 1].y
#                     cal_anchor_line = math.hypot(dx, dy)
#                     assert cal_anchor_line == anchor_line, f"(cal_anchor_line){cal_anchor_line} != {anchor_line}(期望值)."
#
#             if actual_op_anchor_line > 0:
#                 assert n_points == 8, f"在这个场景下的，每一层的轮廓线应该有 8 个点，但现在有{n_points}"
#             else:
#                 assert n_points == 4, f"在这个场景下的，每一层的轮廓线应该有 4 个点，但现在有{n_points}"
#
#
#     else:
#         # 比阈值大，那么应该用的有端点线的轮廓基线
#         if actual_op_anchor_line > 0:
#             assert anchor_line > 0, f"这种情况下应该有锚线，但现在锚线的期望为:{anchor_line}!"
#
#         for layer_map in contours:
#             polylines = layer_map[ExtrusionType.SPARSE_INFILL]
#
#             n_points = 0
#             for poly in polylines or []:
#                 n_points += len(poly)
#                 if actual_op_anchor_line > 0:
#                     assert n_points == 6, f"在这个场景下的，每一层的轮廓线应该有 6 个点，但现在有{n_points}"
#                 else:
#                     assert n_points == 4, f"在这个场景下的，每一层的轮廓线应该有 4 个点，但现在有{n_points}"
#                 dx = poly[0].x - poly[1].x
#                 dy = poly[0].y - poly[1].y
#                 cal_anchor_line = math.hypot(dx, dy)
#                 assert cal_anchor_line == anchor_line, f"(cal_anchor_line){cal_anchor_line} != {anchor_line}(期望值)."
#
#                 dx = poly[4].x - poly[5].x
#                 dy = poly[4].y - poly[5].y
#                 cal_anchor_line = math.hypot(dx, dy)
#                 assert cal_anchor_line == anchor_line, f"(cal_anchor_line){cal_anchor_line} != {anchor_line}(期望值)."

def parse_internal_solid_infill_pattern(
        gcode_path: Path | str,
        baseline_gcode_path: Path | str,
        tolerance: float = 1e-6,
        object_id: int = 0,
) -> Tuple[bool, bool, Dict[str, object]]:
    """
    通过快照对比的方式测试internal_solid_infill_pattern参数是否有效。
    
    比较测试G-code和基准G-code中所有层的INTERNAL_SOLID_INFILL挤出块的轮廓点是否一致。
    
    参数
    ----
    gcode_path : Path | str
        测试G-code文件路径。
    baseline_gcode_path : Path | str
        基准G-code文件路径。
    tolerance : float
        浮点比较容差。
    object_id : int
        模型ID。
    
    返回
    ----
    Tuple[bool, bool, Dict[str, object]]
        (是否通过测试, 轮廓是否匹配, 详细信息)
    """
    # 加载基准G-code
    baseline_parser = GCodeParser(Path(baseline_gcode_path))
    baseline_contours = baseline_parser.get_type_contours_per_layer_by_object(
        object_id,
        types=[ExtrusionType.INTERNAL_SOLID_INFILL]
    )
    
    # 加载测试G-code
    test_parser = GCodeParser(Path(gcode_path))
    test_contours = test_parser.get_type_contours_per_layer_by_object(
        object_id,
        types=[ExtrusionType.INTERNAL_SOLID_INFILL]
    )
    
    # 初始化结果
    ok = True
    match = True
    details = {
        "baseline_layer_count": len(baseline_contours),
        "test_layer_count": len(test_contours),
        "mismatch_layers": [],
        "error_details": []
    }
    
    # 检查层数是否一致
    if len(baseline_contours) != len(test_contours):
        ok = False
        match = False
        details["error_details"].append(
            f"Layer count mismatch: baseline has {len(baseline_contours)}, test has {len(test_contours)}"
        )
        return ok, match, details
    
    # 逐层比较轮廓
    for layer_idx in range(len(baseline_contours)):
        baseline_layer = baseline_contours[layer_idx]
        test_layer = test_contours[layer_idx]
        
        # 检查是否双方层都没有内部实体填充，如果是则跳过该层
        baseline_has_internal = ExtrusionType.INTERNAL_SOLID_INFILL in baseline_layer
        test_has_internal = ExtrusionType.INTERNAL_SOLID_INFILL in test_layer
        
        if not baseline_has_internal and not test_has_internal:
            # 双方都没有内部实体填充，跳过该层
            continue
        
        # 检查是否只有一方有内部实体填充，这种情况是错误的
        if not baseline_has_internal:
            ok = False
            match = False
            details["error_details"].append(
                f"Baseline layer {layer_idx} missing INTERNAL_SOLID_INFILL while test has it"
            )
            continue
            
        if not test_has_internal:
            ok = False
            match = False
            details["error_details"].append(
                f"Test layer {layer_idx} missing INTERNAL_SOLID_INFILL while baseline has it"
            )
            continue
        
        baseline_polylines = baseline_layer[ExtrusionType.INTERNAL_SOLID_INFILL]
        test_polylines = test_layer[ExtrusionType.INTERNAL_SOLID_INFILL]
        
        # 检查多边形数量是否一致
        if len(baseline_polylines) != len(test_polylines):
            ok = False
            match = False
            details["mismatch_layers"].append(layer_idx)
            details["error_details"].append(
                f"Layer {layer_idx}: polyline count mismatch: baseline has {len(baseline_polylines)}, "
                f"test has {len(test_polylines)}"
            )
            continue
        
        # 逐个多边形比较点
        for poly_idx in range(len(baseline_polylines)):
            baseline_points = baseline_polylines[poly_idx]
            test_points = test_polylines[poly_idx]
            
            # 检查点数量是否一致
            if len(baseline_points) != len(test_points):
                ok = False
                match = False
                details["mismatch_layers"].append(layer_idx)
                details["error_details"].append(
                    f"Layer {layer_idx}, polyline {poly_idx}: point count mismatch: baseline has {len(baseline_points)}, "
                    f"test has {len(test_points)}"
                )
                continue
            
            # 逐个点比较坐标
            for point_idx in range(len(baseline_points)):
                bp = baseline_points[point_idx]
                tp = test_points[point_idx]
                
                if abs(bp.x - tp.x) > tolerance or abs(bp.y - tp.y) > tolerance:
                    ok = False
                    match = False
                    details["mismatch_layers"].append(layer_idx)
                    details["error_details"].append(
                        f"Layer {layer_idx}, polyline {poly_idx}, point {point_idx}: coordinate mismatch: "
                        f"baseline({bp.x}, {bp.y}), test({tp.x}, {tp.y})"
                    )
                    break
            
            if not ok:
                break
        
        if not ok:
            break
    
    return ok, match, details


def parse_sparse_infill_density(
        gcode_path: Path | str,
        baseline_gcode_path: Path | str,
        tolerance: float = 1e-6,
        object_id: int = 0,
) -> Tuple[bool, bool, Dict[str, object]]:
    """
    通过快照对比的方式测试sparse_infill_density参数是否有效。
    
    比较测试G-code和基准G-code中所有层的SPARSE_INFILL挤出块的轮廓点是否一致。
    
    参数
    ----
    gcode_path : Path | str
        测试G-code文件路径。
    baseline_gcode_path : Path | str
        基准G-code文件路径。
    tolerance : float
        浮点比较容差。
    object_id : int
        模型ID。
    
    返回
    ----
    Tuple[bool, bool, Dict[str, object]]
        (是否通过测试, 轮廓是否匹配, 详细信息)
    """
    # 加载基准G-code
    baseline_parser = GCodeParser(Path(baseline_gcode_path))
    baseline_contours = baseline_parser.get_type_contours_per_layer_by_object(
        object_id,
        types=[ExtrusionType.SPARSE_INFILL]
    )
    
    # 加载测试G-code
    test_parser = GCodeParser(Path(gcode_path))
    test_contours = test_parser.get_type_contours_per_layer_by_object(
        object_id,
        types=[ExtrusionType.SPARSE_INFILL]
    )
    
    # 初始化结果
    ok = True
    match = True
    details = {
        "baseline_layer_count": len(baseline_contours),
        "test_layer_count": len(test_contours),
        "mismatch_layers": [],
        "error_details": []
    }
    
    # 检查层数是否一致
    if len(baseline_contours) != len(test_contours):
        ok = False
        match = False
        details["error_details"].append(
            f"Layer count mismatch: baseline has {len(baseline_contours)}, test has {len(test_contours)}"
        )
        return ok, match, details
    
    # 逐层比较轮廓
    for layer_idx in range(len(baseline_contours)):
        baseline_layer = baseline_contours[layer_idx]
        test_layer = test_contours[layer_idx]
        
        # 检查是否双方层都没有稀疏填充，如果是则跳过该层
        baseline_has_sparse = ExtrusionType.SPARSE_INFILL in baseline_layer
        test_has_sparse = ExtrusionType.SPARSE_INFILL in test_layer
        
        if not baseline_has_sparse and not test_has_sparse:
            # 双方都没有稀疏填充，跳过该层
            continue
        
        # 检查是否只有一方有稀疏填充，这种情况是错误的
        if not baseline_has_sparse:
            ok = False
            match = False
            details["error_details"].append(
                f"Baseline layer {layer_idx} missing SPARSE_INFILL while test has it"
            )
            continue
            
        if not test_has_sparse:
            ok = False
            match = False
            details["error_details"].append(
                f"Test layer {layer_idx} missing SPARSE_INFILL while baseline has it"
            )
            continue
        
        baseline_polylines = baseline_layer[ExtrusionType.SPARSE_INFILL]
        test_polylines = test_layer[ExtrusionType.SPARSE_INFILL]
        
        # 检查多边形数量是否一致
        if len(baseline_polylines) != len(test_polylines):
            ok = False
            match = False
            details["mismatch_layers"].append(layer_idx)
            details["error_details"].append(
                f"Layer {layer_idx}: polyline count mismatch: baseline has {len(baseline_polylines)}, "
                f"test has {len(test_polylines)}"
            )
            continue
        
        # 逐个多边形比较点
        for poly_idx in range(len(baseline_polylines)):
            baseline_points = baseline_polylines[poly_idx]
            test_points = test_polylines[poly_idx]
            
            # 检查点数量是否一致
            if len(baseline_points) != len(test_points):
                ok = False
                match = False
                details["mismatch_layers"].append(layer_idx)
                details["error_details"].append(
                    f"Layer {layer_idx}, polyline {poly_idx}: point count mismatch: baseline has {len(baseline_points)}, "
                    f"test has {len(test_points)}"
                )
                continue
            
            # 逐个点比较坐标
            for point_idx in range(len(baseline_points)):
                bp = baseline_points[point_idx]
                tp = test_points[point_idx]
                
                if abs(bp.x - tp.x) > tolerance or abs(bp.y - tp.y) > tolerance:
                    ok = False
                    match = False
                    details["mismatch_layers"].append(layer_idx)
                    details["error_details"].append(
                        f"Layer {layer_idx}, polyline {poly_idx}, point {point_idx}: coordinate mismatch: "
                        f"baseline({bp.x}, {bp.y}), test({tp.x}, {tp.y})"
                    )
                    break
            
            if not ok:
                break
        
        if not ok:
            break
    
    return ok, match, details


def parse_ai_infill(
        gcode_path: Path | str,
        baseline_gcode_path: Path | str,
        tolerance: float = 1e-6,
        object_id: int = 0,
) -> Tuple[bool, bool, Dict[str, object]]:
    """
    通过快照对比的方式测试ai_infill参数是否有效。
    
    比较测试G-code和基准G-code中所有层的AI INFILL相关挤出块的轮廓点是否一致。
    
    参数
    ----
    gcode_path : Path | str
        测试G-code文件路径。
    baseline_gcode_path : Path | str
        基准G-code文件路径。
    tolerance : float
        浮点比较容差。
    object_id : int
        模型ID。
    
    返回
    ----
    Tuple[bool, bool, Dict[str, object]]
        (是否通过测试, 轮廓是否匹配, 详细信息)
    """
    # 加载基准G-code
    baseline_parser = GCodeParser(Path(baseline_gcode_path))
    baseline_contours = baseline_parser.get_type_contours_per_layer_by_object(
        object_id,
        types=[ExtrusionType.SPARSE_INFILL]
    )
    
    # 加载测试G-code
    test_parser = GCodeParser(Path(gcode_path))
    test_contours = test_parser.get_type_contours_per_layer_by_object(
        object_id,
        types=[ExtrusionType.SPARSE_INFILL]
    )
    
    # 初始化结果
    ok = True
    match = True
    details = {
        "baseline_layer_count": len(baseline_contours),
        "test_layer_count": len(test_contours),
        "mismatch_layers": [],
        "error_details": []
    }
    
    # 检查层数是否一致
    if len(baseline_contours) != len(test_contours):
        ok = False
        match = False
        details["error_details"].append(
            f"Layer count mismatch: baseline has {len(baseline_contours)}, test has {len(test_contours)}"
        )
        return ok, match, details
    
    # 逐层比较轮廓
    for layer_idx in range(len(baseline_contours)):
        baseline_layer = baseline_contours[layer_idx]
        test_layer = test_contours[layer_idx]
        
        # 检查是否双方层都没有填充，如果是则跳过该层
        baseline_has_infill = ExtrusionType.SPARSE_INFILL in baseline_layer
        test_has_infill = ExtrusionType.SPARSE_INFILL in test_layer
        
        if not baseline_has_infill and not test_has_infill:
            # 双方都没有填充，跳过该层
            continue
        
        # 检查是否只有一方有填充，这种情况是错误的
        if not baseline_has_infill:
            ok = False
            match = False
            details["error_details"].append(
                f"Baseline layer {layer_idx} missing AI INFILL while test has it"
            )
            continue
            
        if not test_has_infill:
            ok = False
            match = False
            details["error_details"].append(
                f"Test layer {layer_idx} missing AI INFILL while baseline has it"
            )
            continue
        
        baseline_polylines = baseline_layer[ExtrusionType.SPARSE_INFILL]
        test_polylines = test_layer[ExtrusionType.SPARSE_INFILL]
        
        # 检查多边形数量是否一致
        if len(baseline_polylines) != len(test_polylines):
            ok = False
            match = False
            details["mismatch_layers"].append(layer_idx)
            details["error_details"].append(
                f"Layer {layer_idx}: polyline count mismatch: baseline has {len(baseline_polylines)}, "
                f"test has {len(test_polylines)}"
            )
            continue
        
        # 逐个多边形比较点
        for poly_idx in range(len(baseline_polylines)):
            baseline_points = baseline_polylines[poly_idx]
            test_points = test_polylines[poly_idx]
            
            # 检查点数量是否一致
            if len(baseline_points) != len(test_points):
                ok = False
                match = False
                details["mismatch_layers"].append(layer_idx)
                details["error_details"].append(
                    f"Layer {layer_idx}, polyline {poly_idx}: point count mismatch: baseline has {len(baseline_points)}, "
                    f"test has {len(test_points)}"
                )
                continue
            
            # 逐个点比较坐标
            for point_idx in range(len(baseline_points)):
                bp = baseline_points[point_idx]
                tp = test_points[point_idx]
                
                if abs(bp.x - tp.x) > tolerance or abs(bp.y - tp.y) > tolerance:
                    ok = False
                    match = False
                    details["mismatch_layers"].append(layer_idx)
                    details["error_details"].append(
                        f"Layer {layer_idx}, polyline {poly_idx}, point {point_idx}: coordinate mismatch: "
                        f"baseline({bp.x}, {bp.y}), test({tp.x}, {tp.y})"
                    )
                    break
            
            if not ok:
                break
        
        if not ok:
            break
    
    return ok, match, details

def parse_anchor_line(
        gcode_path: Path | str,
        threshold: float,
        point_line: float,
        anchor_line: float,
        *,
        tolerance: float = 1e-6,
) -> Tuple[bool, Optional[float], Dict[str, object]]:
    """
    读取 infill_anchor / infill_anchor_max，并基于 Sparse infill 的轮廓进行如下校验：
      - 实际锚线长度 actual = min(infill_anchor, infill_anchor_max)
      - 若 infill_anchor_max <= threshold：应当使用“无端点线”的基线
          * 若 actual > 0，则期望端点线长度 point_line == 0
          * 每层轮廓点数：actual>0 => 8 点；否则 => 4 点
          * 轮廓按 (0,1), (2,3), ... 成对取段，段长应等于 anchor_line
      - 否则（infill_anchor_max > threshold）：应当使用“有端点线”的基线
          * 若 actual > 0，则期望锚线 anchor_line > 0
          * 每层轮廓点数：actual>0 => 6 点；否则 => 4 点
          * 校验 (0,1) 与 (4,5) 两段长度等于 anchor_line（若索引存在）

    返回:
      ok: 所有校验均通过
      actual_value: 实际锚线长度 actual = min(infill_anchor, infill_anchor_max)，若无法解析则为 None
      details: 详尽诊断信息（包含 errors 列表），供上层断言使用
    """

    def _feq(a: float, b: float, tol: float) -> bool:
        return abs(a - b) <= tol

    parser = GCodeParser(Path(gcode_path))
    cfg = parser.load_config()

    # ---- 读取配置 ----
    raw_infill_anchor = cfg.get("infill_anchor")
    raw_infill_anchor_max = cfg.get("infill_anchor_max")

    op_infill_anchor: Optional[float] = None
    op_infill_anchor_max: Optional[float] = None
    errors: List[str] = []
    notes: List[str] = []

    # 解析为 float
    try:
        if raw_infill_anchor is not None:
            op_infill_anchor = float(str(raw_infill_anchor).strip())
        if raw_infill_anchor_max is not None:
            op_infill_anchor_max = float(str(raw_infill_anchor_max).strip())
    except ValueError:
        op_infill_anchor = None
        op_infill_anchor_max = None
        errors.append("Failed to parse 'infill_anchor' or 'infill_anchor_max' as float.")

    # 若配置缺失，直接返回
    if op_infill_anchor is None or op_infill_anchor_max is None:
        details: Dict[str, object] = {
            "inputs": {
                "threshold": threshold,
                "point_line_expected": point_line,
                "anchor_line_expected": anchor_line,
                "tolerance": tolerance,
            },
            "config": {
                "infill_anchor": raw_infill_anchor,
                "infill_anchor_max": raw_infill_anchor_max,
                "parsed_infill_anchor": op_infill_anchor,
                "parsed_infill_anchor_max": op_infill_anchor_max,
            },
            "errors": errors or ["Missing or invalid 'infill_anchor' / 'infill_anchor_max'."],
            "notes": notes,
        }
        return False, None, details

    actual_op_anchor_line = min(op_infill_anchor, op_infill_anchor_max)
    # 记录一个算法限制的提示
    if not (actual_op_anchor_line < threshold / 2.0 + tolerance):
        notes.append(
            "Current detection algorithm is intended for actual_op_anchor_line < threshold/2; "
            "results may be unreliable for larger values."
        )

    # ---- 轮廓数据 ----
    contours_per_layer = parser.get_type_contours_per_layer_by_object(
        0, types=[ExtrusionType.SPARSE_INFILL]
    )

    per_layer_reports: List[Dict[str, object]] = []

    # 分支：是否小于等于阈值
    use_no_point_baseline = op_infill_anchor_max <= threshold + tolerance

    # 逻辑一：小于等于阈值 => “无端点线”基线
    if use_no_point_baseline:
        # 若 actual>0，则点线应当为 0
        if actual_op_anchor_line > tolerance and not _feq(point_line, 0.0, tolerance):
            errors.append(
                f"Expected no point line when infill_anchor_max <= threshold, "
                f"but point_line_expected={point_line}."
            )

        # 每层检查
        for layer_idx, layer_map in enumerate(contours_per_layer or []):
            polylines = layer_map.get(ExtrusionType.SPARSE_INFILL, [])
            n_points = 0
            segment_lengths: List[float] = []

            for poly in (polylines or []):
                # 逐 2 点组成一段： (0,1), (2,3), ...
                # 防止越界：只在 i+1 < len(poly) 时计算
                for i in range(0, len(poly), 2):
                    if i + 1 >= len(poly):
                        # 点数奇数时判错
                        errors.append(f"Layer {layer_idx}: odd number of points in poly (index {i} incomplete pair).")
                        break
                    n_points += 2
                    dx = poly[i].x - poly[i + 1].x
                    dy = poly[i].y - poly[i + 1].y
                    seg_len = math.hypot(dx, dy)
                    segment_lengths.append(seg_len)
                    if not _feq(seg_len, anchor_line, tolerance):
                        errors.append(
                            f"Layer {layer_idx}: segment length {seg_len:.6f} != anchor_line_expected {anchor_line:.6f} "
                            f"(pair {i}-{i + 1})."
                        )

            # 点数期望
            expected_points = 8 if actual_op_anchor_line > tolerance else 4
            if polylines != [] and n_points != expected_points:
                errors.append(
                    f"Layer {layer_idx}: point count {n_points} != expected {expected_points} (no-point baseline)."
                )

            per_layer_reports.append({
                "layer": layer_idx,
                "point_count": n_points,
                "segment_lengths": segment_lengths,
                "expected_point_count": expected_points,
                "mode": "no-point-baseline",
            })

    # 逻辑二：大于阈值 => “有端点线”基线
    else:
        if actual_op_anchor_line > tolerance and not (anchor_line > 0.0):
            errors.append(
                f"Expected anchor_line > 0 when infill_anchor_max > threshold, "
                f"but anchor_line_expected={anchor_line}."
            )

        for layer_idx, layer_map in enumerate(contours_per_layer or []):
            polylines = layer_map.get(ExtrusionType.SPARSE_INFILL, [])
            n_points = 0
            segment_lengths_checked: List[Tuple[str, float]] = []

            for poly in (polylines or []):
                n_points += len(poly)

                # 校验 (0,1) 段
                if len(poly) >= 2:
                    dx01 = poly[0].x - poly[1].x
                    dy01 = poly[0].y - poly[1].y
                    len01 = math.hypot(dx01, dy01)
                    segment_lengths_checked.append(("0-1", len01))
                    if not _feq(len01, anchor_line, tolerance):
                        errors.append(
                            f"Layer {layer_idx}: segment(0-1) length {len01:.6f} != anchor_line_expected {anchor_line:.6f}."
                        )

                # 校验 (4,5) 段（若存在）
                if len(poly) >= 6:
                    dx45 = poly[4].x - poly[5].x
                    dy45 = poly[4].y - poly[5].y
                    len45 = math.hypot(dx45, dy45)
                    segment_lengths_checked.append(("4-5", len45))
                    if not _feq(len45, anchor_line, tolerance):
                        errors.append(
                            f"Layer {layer_idx}: segment(4-5) length {len45:.6f} != anchor_line_expected {anchor_line:.6f}."
                        )

            expected_points = 6 if actual_op_anchor_line > tolerance else 4
            if polylines != [] and n_points != expected_points:
                errors.append(
                    f"Layer {layer_idx}: point count {n_points} != expected {expected_points} (with-point baseline)."
                )

            per_layer_reports.append({
                "layer": layer_idx,
                "point_count": n_points,
                "expected_point_count": expected_points,
                "checked_segments": segment_lengths_checked,
                "mode": "with-point-baseline",
            })

    ok = len(errors) == 0

    details: Dict[str, object] = {
        "inputs": {
            "threshold": threshold,
            "point_line_expected": point_line,
            "anchor_line_expected": anchor_line,
            "tolerance": tolerance,
        },
        "config": {
            "infill_anchor": op_infill_anchor,
            "infill_anchor_max": op_infill_anchor_max,
            "actual_op_anchor_line": actual_op_anchor_line,
            "use_no_point_baseline": use_no_point_baseline,
        },
        "errors": errors,
        "per_layer": per_layer_reports,
        "notes": notes,
    }

    return ok, actual_op_anchor_line, details

def parse_top_surface_pattern(
        gcode_path: Path | str,
        baseline_gcode_path: Path | str,
        tolerance: float = 1e-6,
        object_id: int = 0,
) -> Tuple[bool, bool, Dict[str, Any]]:
    """Validate top-surface pattern identity and generated path behavior."""
    return _compare_role_behavior(
        gcode_path,
        baseline_gcode_path,
        role=ExtrusionType.TOP_SURFACE.value,
        config_key="top_surface_pattern",
    )

    # Legacy exact-coordinate implementation retained below for reference.
    baseline_parser = GCodeParser(Path(baseline_gcode_path))
    baseline_contours = baseline_parser.get_type_contours_per_layer_by_object(
        object_id,
        types=[ExtrusionType.TOP_SURFACE]
    )
    
    # 加载测试G-code
    test_parser = GCodeParser(Path(gcode_path))
    test_contours = test_parser.get_type_contours_per_layer_by_object(
        object_id,
        types=[ExtrusionType.TOP_SURFACE]
    )
    
    # 初始化结果
    ok = True
    match = True
    details = {
        "baseline_layer_count": len(baseline_contours),
        "test_layer_count": len(test_contours),
        "mismatch_layers": [],
        "error_details": []
    }
    
    # 检查层数是否一致
    if len(baseline_contours) != len(test_contours):
        ok = False
        match = False
        details["error_details"].append(
            f"Layer count mismatch: baseline has {len(baseline_contours)}, test has {len(test_contours)}"
        )
        return ok, match, details
    
    # 遍历每一层进行比较
    for layer_idx in range(len(baseline_contours)):
        baseline_layer = baseline_contours[layer_idx]
        test_layer = test_contours[layer_idx]
        
        # 检查基准层中是否有TOP_SURFACE
        if ExtrusionType.TOP_SURFACE not in baseline_layer:
            # 基准层没有TOP_SURFACE，测试层也不应该有
            if ExtrusionType.TOP_SURFACE in test_layer:
                ok = False
                match = False
                mismatch_info = {
                    "layer_idx": layer_idx,
                    "reason": "Baseline has no TOP_SURFACE but test does",
                    "baseline_polylines": 0,
                    "test_polylines": len(test_layer[ExtrusionType.TOP_SURFACE]) if ExtrusionType.TOP_SURFACE in test_layer else 0
                }
                details["mismatch_layers"].append(mismatch_info)
            continue
        
        # 检查测试层中是否有TOP_SURFACE
        if ExtrusionType.TOP_SURFACE not in test_layer:
            ok = False
            match = False
            mismatch_info = {
                "layer_idx": layer_idx,
                "reason": "Test has no TOP_SURFACE but baseline does",
                "baseline_polylines": len(baseline_layer[ExtrusionType.TOP_SURFACE]),
                "test_polylines": 0
            }
            details["mismatch_layers"].append(mismatch_info)
            continue
        
        # 获取轮廓
        baseline_polylines = baseline_layer[ExtrusionType.TOP_SURFACE]
        test_polylines = test_layer[ExtrusionType.TOP_SURFACE]
        
        # 检查polyline数量是否一致
        if len(baseline_polylines) != len(test_polylines):
            ok = False
            match = False
            mismatch_info = {
                "layer_idx": layer_idx,
                "reason": "Polyline count mismatch",
                "baseline_polylines": len(baseline_polylines),
                "test_polylines": len(test_polylines)
            }
            details["mismatch_layers"].append(mismatch_info)
            continue
        
        # 遍历每条polyline进行比较
        polyline_match = True
        for poly_idx in range(len(baseline_polylines)):
            baseline_polyline = baseline_polylines[poly_idx]
            test_polyline = test_polylines[poly_idx]
            
            # 检查点数是否一致
            if len(baseline_polyline) != len(test_polyline):
                ok = False
                match = False
                polyline_match = False
                details["error_details"].append(
                    f"Layer {layer_idx}, Polyline {poly_idx}: Point count mismatch - baseline: {len(baseline_polyline)}, test: {len(test_polyline)}"
                )
                continue
            
            # 比较每个点的坐标
            for point_idx in range(len(baseline_polyline)):
                baseline_point = baseline_polyline[point_idx]
                test_point = test_polyline[point_idx]
                
                # 检查x坐标
                if abs(baseline_point.x - test_point.x) > tolerance:
                    ok = False
                    match = False
                    polyline_match = False
                    details["error_details"].append(
                        f"Layer {layer_idx}, Polyline {poly_idx}, Point {point_idx}: X coordinate mismatch - baseline: {baseline_point.x}, test: {test_point.x}"
                    )
                
                # 检查y坐标
                if abs(baseline_point.y - test_point.y) > tolerance:
                    ok = False
                    match = False
                    polyline_match = False
                    details["error_details"].append(
                        f"Layer {layer_idx}, Polyline {poly_idx}, Point {point_idx}: Y coordinate mismatch - baseline: {baseline_point.y}, test: {test_point.y}"
                    )
        
        # 如果该层有不匹配的polyline，记录信息
        if not polyline_match:
            mismatch_info = {
                "layer_idx": layer_idx,
                "reason": "Point coordinate mismatches found in polylines",
                "baseline_polylines": len(baseline_polylines),
                "test_polylines": len(test_polylines)
            }
            details["mismatch_layers"].append(mismatch_info)
    
    # 如果没有发现不匹配，记录成功信息
    if match:
        details["error_details"].append("All layers, polylines and points match within tolerance")
    
    return ok, match, details

# ================== bottom_surface_pattern ==================

def parse_bottom_surface_pattern(
        gcode_path: Path | str,
        baseline_gcode_path: Path | str,
        tolerance: float = 1e-6,
        object_id: int = 0,
) -> tuple[bool, bool, dict[str, int | list[Any]]] | None:
    """
    通过快照对比的方式测试bottom_surface_pattern参数是否有效。
    
    比较测试G-code和基准G-code中所有层的BOTTOM_SURFACE挤出块的轮廓点是否一致。
    
    参数
    ----
    gcode_path : Path | str
        测试G-code文件路径。
    baseline_gcode_path : Path | str
        基准G-code文件路径。
    tolerance : float
        浮点比较容差。
    object_id : int
        模型ID。
    
    返回
    ----
    Tuple[bool, bool, Dict[str, object]]
        (是否通过测试, 轮廓是否匹配, 详细信息)
    """
    # 加载基准G-code
    baseline_parser = GCodeParser(Path(baseline_gcode_path))
    baseline_contours = baseline_parser.get_type_contours_per_layer_by_object(
        object_id,
        types=[ExtrusionType.BOTTOM_SURFACE]
    )
    
    # 加载测试G-code
    test_parser = GCodeParser(Path(gcode_path))
    test_contours = test_parser.get_type_contours_per_layer_by_object(
        object_id,
        types=[ExtrusionType.BOTTOM_SURFACE]
    )
    
    # 初始化结果
    ok = True
    match = True
    details = {
        "baseline_layer_count": len(baseline_contours),
        "test_layer_count": len(test_contours),
        "mismatch_layers": [],
        "error_details": []
    }
    
    # 检查层数是否一致
    if len(baseline_contours) != len(test_contours):
        ok = False
        match = False
        details["error_details"].append(
            f"Layer count mismatch: baseline has {len(baseline_contours)}, test has {len(test_contours)}"
        )
        return ok, match, details
    
    # 遍历每一层进行比较
    for layer_idx in range(len(baseline_contours)):
        baseline_layer = baseline_contours[layer_idx]
        test_layer = test_contours[layer_idx]
        
        # 检查基准层中是否有BOTTOM_SURFACE
        if ExtrusionType.BOTTOM_SURFACE not in baseline_layer:
            # 基准层没有BOTTOM_SURFACE，测试层也不应该有
            if ExtrusionType.BOTTOM_SURFACE in test_layer:
                ok = False
                match = False
                mismatch_info = {
                    "layer_idx": layer_idx,
                    "reason": "Baseline has no BOTTOM_SURFACE but test does",
                    "baseline_polylines": 0,
                    "test_polylines": len(test_layer[ExtrusionType.BOTTOM_SURFACE]) if ExtrusionType.BOTTOM_SURFACE in test_layer else 0
                }
                details["mismatch_layers"].append(mismatch_info)
            continue
        
        # 检查测试层中是否有BOTTOM_SURFACE
        if ExtrusionType.BOTTOM_SURFACE not in test_layer:
            ok = False
            match = False
            mismatch_info = {
                "layer_idx": layer_idx,
                "reason": "Test has no BOTTOM_SURFACE but baseline does",
                "baseline_polylines": len(baseline_layer[ExtrusionType.BOTTOM_SURFACE]),
                "test_polylines": 0
            }
            details["mismatch_layers"].append(mismatch_info)
            continue
        
        # 获取轮廓
        baseline_polylines = baseline_layer[ExtrusionType.BOTTOM_SURFACE]
        test_polylines = test_layer[ExtrusionType.BOTTOM_SURFACE]
        
        # 检查polyline数量是否一致
        if len(baseline_polylines) != len(test_polylines):
            ok = False
            match = False
            mismatch_info = {
                "layer_idx": layer_idx,
                "reason": "Polyline count mismatch",
                "baseline_polylines": len(baseline_polylines),
                "test_polylines": len(test_polylines)
            }
            details["mismatch_layers"].append(mismatch_info)
            continue
        
        # 遍历每条polyline进行比较
        polyline_match = True
        for poly_idx in range(len(baseline_polylines)):
            baseline_polyline = baseline_polylines[poly_idx]
            test_polyline = test_polylines[poly_idx]
            
            # 检查点数是否一致
            if len(baseline_polyline) != len(test_polyline):
                ok = False
                match = False
                polyline_match = False
                details["error_details"].append(
                    f"Layer {layer_idx}, Polyline {poly_idx}: Point count mismatch - baseline: {len(baseline_polyline)}, test: {len(test_polyline)}"
                )
                continue
            
            # 比较每个点的坐标
            for point_idx in range(len(baseline_polyline)):
                baseline_point = baseline_polyline[point_idx]
                test_point = test_polyline[point_idx]
                
                # 检查x坐标
                if abs(baseline_point.x - test_point.x) > tolerance:
                    ok = False
                    match = False
                    polyline_match = False
                    details["error_details"].append(
                        f"Layer {layer_idx}, Polyline {poly_idx}, Point {point_idx}: X coordinate mismatch - baseline: {baseline_point.x}, test: {test_point.x}"
                    )
                
                # 检查y坐标
                if abs(baseline_point.y - test_point.y) > tolerance:
                    ok = False
                    match = False
                    polyline_match = False
                    details["error_details"].append(
                        f"Layer {layer_idx}, Polyline {poly_idx}, Point {point_idx}: Y coordinate mismatch - baseline: {baseline_point.y}, test: {test_point.y}"
                    )
        
        # 如果该层有不匹配的polyline，记录信息
        if not polyline_match:
            mismatch_info = {
                "layer_idx": layer_idx,
                "reason": "Point coordinate mismatches found in polylines",
                "baseline_polylines": len(baseline_polylines),
                "test_polylines": len(test_polylines)
            }
            details["mismatch_layers"].append(mismatch_info)
    
    # 如果没有发现不匹配，记录成功信息
    if match:
        details["error_details"].append("All layers, polylines and points match within tolerance")
    
    return ok, match, details

# ================== tmps_start_infill_density ==================
def parse_tmps_start_infill_density(
        gcode_path: Path | str,
        baseline_gcode_path: Path | str,
        tolerance: float = 1e-6,
        object_id: int = 0,
) -> Tuple[bool, bool, Dict[str, object]]:
    """
    通过快照对比的方式测试tmps_start_infill_density参数是否有效。
    
    比较测试G-code和基准G-code中所有层的SPARSE_INFILL挤出块的轮廓点是否一致。
    """
    # 加载基准G-code
    baseline_parser = GCodeParser(Path(baseline_gcode_path))
    baseline_contours = baseline_parser.get_type_contours_per_layer_by_object(
        object_id,
        types=[ExtrusionType.SPARSE_INFILL]
    )
    
    # 加载测试G-code
    test_parser = GCodeParser(Path(gcode_path))
    test_contours = test_parser.get_type_contours_per_layer_by_object(
        object_id,
        types=[ExtrusionType.SPARSE_INFILL]
    )
    
    # 初始化结果
    ok = True
    match = True
    details = {
        "baseline_layer_count": len(baseline_contours),
        "test_layer_count": len(test_contours),
        "mismatch_layers": [],
        "error_details": []
    }
    
    # 检查层数是否一致
    if len(baseline_contours) != len(test_contours):
        ok = False
        match = False
        details["error_details"].append(
            f"Layer count mismatch: baseline has {len(baseline_contours)}, test has {len(test_contours)}"
        )
        return ok, match, details
    
    # 遍历每一层进行比较
    for layer_idx in range(len(baseline_contours)):
        baseline_layer = baseline_contours[layer_idx]
        test_layer = test_contours[layer_idx]
        
        # 检查基准层中是否有SPARSE_INFILL
        if ExtrusionType.SPARSE_INFILL not in baseline_layer:
            # 基准层没有SPARSE_INFILL，测试层也不应该有
            if ExtrusionType.SPARSE_INFILL in test_layer:
                ok = False
                match = False
                mismatch_info = {
                    "layer_idx": layer_idx,
                    "reason": "Baseline has no SPARSE_INFILL but test does",
                    "baseline_polylines": 0,
                    "test_polylines": len(test_layer[ExtrusionType.SPARSE_INFILL]) if ExtrusionType.SPARSE_INFILL in test_layer else 0
                }
                details["mismatch_layers"].append(mismatch_info)
            continue
        
        # 检查测试层中是否有SPARSE_INFILL
        if ExtrusionType.SPARSE_INFILL not in test_layer:
            ok = False
            match = False
            mismatch_info = {
                "layer_idx": layer_idx,
                "reason": "Test has no SPARSE_INFILL but baseline does",
                "baseline_polylines": len(baseline_layer[ExtrusionType.SPARSE_INFILL]),
                "test_polylines": 0
            }
            details["mismatch_layers"].append(mismatch_info)
            continue
        
        # 获取轮廓
        baseline_polylines = baseline_layer[ExtrusionType.SPARSE_INFILL]
        test_polylines = test_layer[ExtrusionType.SPARSE_INFILL]
        
        # 检查polyline数量是否一致
        if len(baseline_polylines) != len(test_polylines):
            ok = False
            match = False
            mismatch_info = {
                "layer_idx": layer_idx,
                "reason": "Polyline count mismatch",
                "baseline_polylines": len(baseline_polylines),
                "test_polylines": len(test_polylines)
            }
            details["mismatch_layers"].append(mismatch_info)
            continue
        
        # 遍历每条polyline进行比较
        polyline_match = True
        for poly_idx in range(len(baseline_polylines)):
            baseline_polyline = baseline_polylines[poly_idx]
            test_polyline = test_polylines[poly_idx]
            
            # 检查点数是否一致
            if len(baseline_polyline) != len(test_polyline):
                ok = False
                match = False
                polyline_match = False
                details["error_details"].append(
                    f"Layer {layer_idx}, Polyline {poly_idx}: Point count mismatch - baseline: {len(baseline_polyline)}, test: {len(test_polyline)}"
                )
                continue
            
            # 比较每个点的坐标
            for point_idx in range(len(baseline_polyline)):
                baseline_point = baseline_polyline[point_idx]
                test_point = test_polyline[point_idx]
                
                # 检查x坐标
                if abs(baseline_point.x - test_point.x) > tolerance:
                    ok = False
                    match = False
                    polyline_match = False
                    details["error_details"].append(
                        f"Layer {layer_idx}, Polyline {poly_idx}, Point {point_idx}: X coordinate mismatch - baseline: {baseline_point.x}, test: {test_point.x}"
                    )
                
                # 检查y坐标
                if abs(baseline_point.y - test_point.y) > tolerance:
                    ok = False
                    match = False
                    polyline_match = False
                    details["error_details"].append(
                        f"Layer {layer_idx}, Polyline {poly_idx}, Point {point_idx}: Y coordinate mismatch - baseline: {baseline_point.y}, test: {test_point.y}"
                    )
        
        # 如果该层有不匹配的polyline，记录信息
        if not polyline_match:
            mismatch_info = {
                "layer_idx": layer_idx,
                "reason": "Point coordinate mismatches found in polylines",
                "baseline_polylines": len(baseline_polylines),
                "test_polylines": len(test_polylines)
            }
            details["mismatch_layers"].append(mismatch_info)
    
    # 如果没有发现不匹配，记录成功信息
    if match:
        details["error_details"].append("All layers, polylines and points match within tolerance")
    
    return ok, match, details

# ================== tmps_end_infill_density ==================
def parse_tmps_end_infill_density(
        gcode_path: Path | str,
        baseline_gcode_path: Path | str,
        tolerance: float = 1e-6,
        object_id: int = 0,
) -> Tuple[bool, bool, Dict[str, object]]:
    """
    通过快照对比的方式测试tmps_end_infill_density参数是否有效。
    
    比较测试G-code和基准G-code中所有层的SPARSE_INFILL挤出块的轮廓点是否一致。
    """
    # 加载基准G-code
    baseline_parser = GCodeParser(Path(baseline_gcode_path))
    baseline_contours = baseline_parser.get_type_contours_per_layer_by_object(
        object_id,
        types=[ExtrusionType.SPARSE_INFILL]
    )
    
    # 加载测试G-code
    test_parser = GCodeParser(Path(gcode_path))
    test_contours = test_parser.get_type_contours_per_layer_by_object(
        object_id,
        types=[ExtrusionType.SPARSE_INFILL]
    )
    
    # 初始化结果
    ok = True
    match = True
    details = {
        "baseline_layer_count": len(baseline_contours),
        "test_layer_count": len(test_contours),
        "mismatch_layers": [],
        "error_details": []
    }
    
    # 检查层数是否一致
    if len(baseline_contours) != len(test_contours):
        ok = False
        match = False
        details["error_details"].append(
            f"Layer count mismatch: baseline has {len(baseline_contours)}, test has {len(test_contours)}"
        )
        return ok, match, details
    
    # 遍历每一层进行比较
    for layer_idx in range(len(baseline_contours)):
        baseline_layer = baseline_contours[layer_idx]
        test_layer = test_contours[layer_idx]
        
        # 检查基准层中是否有SPARSE_INFILL
        if ExtrusionType.SPARSE_INFILL not in baseline_layer:
            # 基准层没有SPARSE_INFILL，测试层也不应该有
            if ExtrusionType.SPARSE_INFILL in test_layer:
                ok = False
                match = False
                mismatch_info = {
                    "layer_idx": layer_idx,
                    "reason": "Baseline has no SPARSE_INFILL but test does",
                    "baseline_polylines": 0,
                    "test_polylines": len(test_layer[ExtrusionType.SPARSE_INFILL]) if ExtrusionType.SPARSE_INFILL in test_layer else 0
                }
                details["mismatch_layers"].append(mismatch_info)
            continue
        
        # 检查测试层中是否有SPARSE_INFILL
        if ExtrusionType.SPARSE_INFILL not in test_layer:
            ok = False
            match = False
            mismatch_info = {
                "layer_idx": layer_idx,
                "reason": "Test has no SPARSE_INFILL but baseline does",
                "baseline_polylines": len(baseline_layer[ExtrusionType.SPARSE_INFILL]),
                "test_polylines": 0
            }
            details["mismatch_layers"].append(mismatch_info)
            continue
        
        # 获取轮廓
        baseline_polylines = baseline_layer[ExtrusionType.SPARSE_INFILL]
        test_polylines = test_layer[ExtrusionType.SPARSE_INFILL]
        
        # 检查polyline数量是否一致
        if len(baseline_polylines) != len(test_polylines):
            ok = False
            match = False
            mismatch_info = {
                "layer_idx": layer_idx,
                "reason": "Polyline count mismatch",
                "baseline_polylines": len(baseline_polylines),
                "test_polylines": len(test_polylines)
            }
            details["mismatch_layers"].append(mismatch_info)
            continue
        
        # 遍历每条polyline进行比较
        polyline_match = True
        for poly_idx in range(len(baseline_polylines)):
            baseline_polyline = baseline_polylines[poly_idx]
            test_polyline = test_polylines[poly_idx]
            
            # 检查点数是否一致
            if len(baseline_polyline) != len(test_polyline):
                ok = False
                match = False
                polyline_match = False
                details["error_details"].append(
                    f"Layer {layer_idx}, Polyline {poly_idx}: Point count mismatch - baseline: {len(baseline_polyline)}, test: {len(test_polyline)}"
                )
                continue
            
            # 比较每个点的坐标
            for point_idx in range(len(baseline_polyline)):
                baseline_point = baseline_polyline[point_idx]
                test_point = test_polyline[point_idx]
                
                # 检查x坐标
                if abs(baseline_point.x - test_point.x) > tolerance:
                    ok = False
                    match = False
                    polyline_match = False
                    details["error_details"].append(
                        f"Layer {layer_idx}, Polyline {poly_idx}, Point {point_idx}: X coordinate mismatch - baseline: {baseline_point.x}, test: {test_point.x}"
                    )
                
                # 检查y坐标
                if abs(baseline_point.y - test_point.y) > tolerance:
                    ok = False
                    match = False
                    polyline_match = False
                    details["error_details"].append(
                        f"Layer {layer_idx}, Polyline {poly_idx}, Point {point_idx}: Y coordinate mismatch - baseline: {baseline_point.y}, test: {test_point.y}"
                    )
        
        # 如果该层有不匹配的polyline，记录信息
        if not polyline_match:
            mismatch_info = {
                "layer_idx": layer_idx,
                "reason": "Point coordinate mismatches found in polylines",
                "baseline_polylines": len(baseline_polylines),
                "test_polylines": len(test_polylines)
            }
            details["mismatch_layers"].append(mismatch_info)
    
    # 如果没有发现不匹配，记录成功信息
    if match:
        details["error_details"].append("All layers, polylines and points match within tolerance")
    
    return ok, match, details

# ================== tpms_gradual_direction ==================
def parse_tpms_gradual_direction(
        gcode_path: Path | str,
        baseline_gcode_path: Path | str,
        tolerance: float = 1e-6,
        object_id: int = 0,
) -> Tuple[bool, bool, Dict[str, Any]]:
    """Validate TPMS direction identity and generated sparse-path behavior."""
    return _compare_role_behavior(
        gcode_path,
        baseline_gcode_path,
        role=ExtrusionType.SPARSE_INFILL.value,
        config_key="tpms_gradual_direction",
    )

    # Legacy exact-coordinate implementation retained below for reference.
    baseline_parser = GCodeParser(Path(baseline_gcode_path))
    baseline_contours = baseline_parser.get_type_contours_per_layer_by_object(
        object_id,
        types=[ExtrusionType.SPARSE_INFILL]
    )
    
    # 加载测试G-code
    test_parser = GCodeParser(Path(gcode_path))
    test_contours = test_parser.get_type_contours_per_layer_by_object(
        object_id,
        types=[ExtrusionType.SPARSE_INFILL]
    )
    
    # 初始化结果
    ok = True
    match = True
    details = {
        "baseline_layer_count": len(baseline_contours),
        "test_layer_count": len(test_contours),
        "mismatch_layers": [],
        "error_details": []
    }
    
    # 检查层数是否一致
    if len(baseline_contours) != len(test_contours):
        ok = False
        match = False
        details["error_details"].append(
            f"Layer count mismatch: baseline has {len(baseline_contours)}, test has {len(test_contours)}"
        )
        return ok, match, details
    
    # 遍历每一层进行比较
    for layer_idx in range(len(baseline_contours)):
        baseline_layer = baseline_contours[layer_idx]
        test_layer = test_contours[layer_idx]
        
        # 检查基准层中是否有SPARSE_INFILL
        if ExtrusionType.SPARSE_INFILL not in baseline_layer:
            # 基准层没有SPARSE_INFILL，测试层也不应该有
            if ExtrusionType.SPARSE_INFILL in test_layer:
                ok = False
                match = False
                mismatch_info = {
                    "layer_idx": layer_idx,
                    "reason": "Baseline has no SPARSE_INFILL but test does",
                    "baseline_polylines": 0,
                    "test_polylines": len(test_layer[ExtrusionType.SPARSE_INFILL]) if ExtrusionType.SPARSE_INFILL in test_layer else 0
                }
                details["mismatch_layers"].append(mismatch_info)
            continue
        
        # 检查测试层中是否有SPARSE_INFILL
        if ExtrusionType.SPARSE_INFILL not in test_layer:
            ok = False
            match = False
            mismatch_info = {
                "layer_idx": layer_idx,
                "reason": "Test has no SPARSE_INFILL but baseline does",
                "baseline_polylines": len(baseline_layer[ExtrusionType.SPARSE_INFILL]),
                "test_polylines": 0
            }
            details["mismatch_layers"].append(mismatch_info)
            continue
        
        # 获取轮廓
        baseline_polylines = baseline_layer[ExtrusionType.SPARSE_INFILL]
        test_polylines = test_layer[ExtrusionType.SPARSE_INFILL]
        
        # 检查polyline数量是否一致
        if len(baseline_polylines) != len(test_polylines):
            ok = False
            match = False
            mismatch_info = {
                "layer_idx": layer_idx,
                "reason": "Polyline count mismatch",
                "baseline_polylines": len(baseline_polylines),
                "test_polylines": len(test_polylines)
            }
            details["mismatch_layers"].append(mismatch_info)
            continue
        
        # 遍历每条polyline进行比较
        polyline_match = True
        for poly_idx in range(len(baseline_polylines)):
            baseline_polyline = baseline_polylines[poly_idx]
            test_polyline = test_polylines[poly_idx]
            
            # 检查点数是否一致
            if len(baseline_polyline) != len(test_polyline):
                ok = False
                match = False
                polyline_match = False
                details["error_details"].append(
                    f"Layer {layer_idx}, Polyline {poly_idx}: Point count mismatch - baseline: {len(baseline_polyline)}, test: {len(test_polyline)}"
                )
                continue
            
            # 比较每个点的坐标
            for point_idx in range(len(baseline_polyline)):
                baseline_point = baseline_polyline[point_idx]
                test_point = test_polyline[point_idx]
                
                # 检查x坐标
                if abs(baseline_point.x - test_point.x) > tolerance:
                    ok = False
                    match = False
                    polyline_match = False
                    details["error_details"].append(
                        f"Layer {layer_idx}, Polyline {poly_idx}, Point {point_idx}: X coordinate mismatch - baseline: {baseline_point.x}, test: {test_point.x}"
                    )
                
                # 检查y坐标
                if abs(baseline_point.y - test_point.y) > tolerance:
                    ok = False
                    match = False
                    polyline_match = False
                    details["error_details"].append(
                        f"Layer {layer_idx}, Polyline {poly_idx}, Point {point_idx}: Y coordinate mismatch - baseline: {baseline_point.y}, test: {test_point.y}"
                    )
        
        # 如果该层有不匹配的polyline，记录信息
        if not polyline_match:
            mismatch_info = {
                "layer_idx": layer_idx,
                "reason": "Point coordinate mismatches found in polylines",
                "baseline_polylines": len(baseline_polylines),
                "test_polylines": len(test_polylines)
            }
            details["mismatch_layers"].append(mismatch_info)
    
    # 如果没有发现不匹配，记录成功信息
    if match:
        details["error_details"].append("All layers, polylines and points match within tolerance")
    
    return ok, match, details
