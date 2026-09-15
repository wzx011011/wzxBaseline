"""
TC-WT-007: 回抽量和装填量计算校验

验证不同耗材类型和场景下回抽/装填量的正确性
"""
from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
import json
import math
import re

from .prime_tower_gcode_check import (
    WipeTowerGCodeParser,
    GCodeMove,
    GCodeMoveType,
)


# 独立 E 指令的输出精度远小于 0.01 mm；此容差能识别漏加 0.2 mm 的回填。
UNRETRACT_TOLERANCE = 0.01


def _within_tolerance(actual: float, expected: float, tolerance: float) -> bool:
    """包含容差边界，只吸收浮点运算噪声，不扩大业务容差。"""
    if not all(math.isfinite(value) for value in (actual, expected, tolerance)):
        return False
    difference = abs(actual - expected)
    return difference <= tolerance or math.isclose(
        difference, tolerance, rel_tol=0.0, abs_tol=1e-9
    )


def _restart_extra(params: Dict[str, Any]) -> float:
    """extra 兼容旧输入，仅表示毫米；擦拭比例使用 retract_before_wipe。"""
    return params.get("retract_restart_extra", params.get("extra", 0.0))


def _check_infill_retraction(
    parser: WipeTowerGCodeParser, tool_change_line: int, params: Dict[str, Any]
) -> List[str]:
    """校验当前擦拭塔尾部回抽，支持用例声明的单段和三段模式。"""
    unretract = find_first_unretraction_after(parser.moves, tool_change_line)
    if unretract is None:
        return ["未找到填充前装填，无法校验填充后回抽"]
    end = None
    for i in range(unretract.line_num, len(parser.lines)):
        line = parser.lines[i].strip()
        if re.match(r'^T\d+\b', line) or 'WIPE_TOWER_START' in line:
            break
        if 'WIPE_TOWER_END' in line:
            end = i
            break
    if end is None:
        return ["未找到当前换料对应的 WIPE_TOWER_END"]

    # 只收集最后一次正向挤出之后的回抽，避免包含填充过程中的其他回抽。
    retractions = []
    for line in parser.lines[unretract.line_num:end]:
        code = line.split(';', 1)[0].strip()
        if not re.match(r'^G1\s', code):
            continue
        match = re.search(r'E([+-]?(?:\d+(?:\.\d*)?|\.\d+))', code)
        if match:
            amount = float(match.group(1))
            if amount > 0:
                retractions.clear()
            elif amount < 0:
                retractions.append(-amount)
    if not retractions:
        return ["未找到填充后回抽"]

    failures = []
    length = params["retraction_length"]
    if not _within_tolerance(sum(retractions), length, 0.3):
        failures.append(f"填充后回抽总量{sum(retractions):.4f}mm，期望{length:.4f}mm")
    phases = params.get("after_infill_retract", {})
    names = ["single"] if "single" in phases else ["first", "second", "third"]
    if phases:
        if len(retractions) != len(names):
            failures.append(f"填充后回抽段数{len(retractions)}，期望{len(names)}")
        else:
            for name, actual in zip(names, retractions):
                if name in phases and not _within_tolerance(actual, phases[name], UNRETRACT_TOLERANCE):
                    failures.append(f"填充后回抽{name}={actual:.4f}mm，期望{phases[name]:.4f}mm")
    if "retract_before_wipe" in params:
        expected_tail = length * (1.0 - params["retract_before_wipe"])
        actual_tail = sum(retractions[1:])
        if not _within_tolerance(actual_tail, expected_tail, 0.1):
            failures.append(
                f"擦拭回抽比例不符：后续回抽{actual_tail:.4f}mm，"
                f"期望 retraction_length × (1 - retract_before_wipe)={expected_tail:.4f}mm"
            )
    return failures


def parse_tc_wt_007(
    gcode_path: Path,
    expected_value: str
) -> Tuple[bool, Any, Dict[str, Any]]:
    """
    TC-WT-007: 验证不同耗材类型的回抽/装填量
    
    校验级别: L2 (参数验证 + 工具追踪)
    
    校验点：
    1. before_change: 换料前回抽（三段式）- Bug 11460
    2. after_change: 擦拭塔填充装填 - Bug 11462  
    3. purge_line: 擦嘴线装填 - Bug 11463
    4. after_infill_retract: 打完擦拭塔填充后的回抽（三段式）- Bug 13303 & 13379
       验证公式: (second + third) = retraction_length × (1 - retract_before_wipe)
       以及: first + (second + third) = retraction_length
       其中 retract_before_wipe 是比例，retract_restart_extra 是额外回填长度（毫米）
    5. infill_perimeter: 填充和外墙装填 - Bug 13309
    6. layer_change: 层间换色装填 - Bug 13534-13555
    
    Args:
        gcode_path: GCode 文件路径
        expected_value: 期望值（JSON字符串）
            {
                "tool_params": {
                    "T0": {"retraction_length": 5.0, "retract_restart_extra": 0.0},
                    "T1": {"retraction_length": 8.0, "retract_restart_extra": 0.5}
                },
                "from_tool": "T0",
                "to_tool": "T1",
                "check_points": ["before_change", "after_change", "purge_line", 
                               "after_infill", "infill_perimeter", "layer_change"]
            }
    
    Returns:
        (是否通过, 实际值, 详细信息)
    """
    parser = WipeTowerGCodeParser(gcode_path)
    expected = json.loads(expected_value)
    
    tool_params = expected.get("tool_params", {})
    from_tool = expected.get("from_tool", "T0")
    to_tool = expected.get("to_tool", "T1")
    check_points = expected.get("check_points", ["before_change", "after_change"])
    
    # 查找所有换料点
    tool_changes = find_tool_changes(parser, from_tool, to_tool)
    
    if not tool_changes:
        return False, None, {"error": f"未找到从{from_tool}到{to_tool}的换料"}
    
    failures = []
    checked_count = 0
    
    for idx, tc in enumerate(tool_changes):
        # 检查换料前的回抽（如果需要）
        if "before_change" in check_points:
            # 解析三阶段回抽（擦拭前+擦拭时+擦拭后）
            retract_phases = parse_retraction_phases(parser.lines, parser.moves, tc['line'])
            
            if retract_phases:
                expected_retract = tool_params[from_tool]["retraction_length"]
                
                # 提取三个阶段的回抽量
                before_wipe = retract_phases.get('before_wipe', 0.0)
                during_wipe = retract_phases.get('during_wipe', 0.0)
                after_wipe = retract_phases.get('after_wipe', 0.0)
                total_retract = before_wipe + during_wipe + after_wipe
                
                # 打印第一个换料点的调试信息
                if idx == 0:
                    # 优先使用用例中明确给出的三阶段期望值。
                    retract_before_wipe_ratio = tool_params[from_tool].get("retract_before_wipe", 0.7)
                    expected_phases = tool_params[from_tool].get("before_change", {})
                    print(f"\n=== 参数信息 ===")
                    print(f"{from_tool} retract_before_wipe: {retract_before_wipe_ratio}")
                    print(f"{from_tool} retraction_length: {expected_retract}")
                    
                    expected_before = expected_phases.get(
                        "before_wipe", expected_retract * retract_before_wipe_ratio
                    )
                    expected_after = expected_phases.get("after_wipe", 0.05)
                    expected_during = expected_phases.get(
                        "during_wipe", expected_retract - expected_before - expected_after
                    )
                    
                    print(f"\n=== Bug 11460 换料前三阶段回抽 (换料点0 行{tc['line']}) ===")
                    print(f"期望值 (基于{from_tool}参数 {expected_retract}mm):")
                    print(f"  擦拭前回抽: {expected_before:.2f}mm")
                    print(f"  擦拭时回抽: {expected_during:.2f}mm")
                    print(f"  擦拭后回抽: {expected_after:.2f}mm")
                    print(f"实际值:")
                    print(f"  擦拭前回抽: {before_wipe:.2f}mm")
                    print(f"  擦拭时回抽: {during_wipe:.2f}mm")
                    print(f"  擦拭后回抽: {after_wipe:.2f}mm")
                
                # 验证总量
                if not _within_tolerance(total_retract, expected_retract, 0.2):
                    failures.append(
                        f"换料点{idx} 行{tc['line']}: "
                        f"换料前回抽分解 - 擦拭前:{before_wipe:.2f}mm, "
                        f"擦拭时:{during_wipe:.2f}mm, 擦拭后:{after_wipe:.2f}mm, "
                        f"总计:{total_retract:.2f}mm，"
                        f"期望{from_tool}参数{expected_retract:.2f}mm，"
                        f"差值{abs(total_retract - expected_retract):.2f}mm"
                    )
                
                # 验证擦拭前回抽（应该使用当前工具参数计算）
                # retract_before_wipe 比例验证
                if before_wipe > 0:
                    # 期望擦拭前回抽应该接近总量的某个比例（如70%）
                    # 这里简化处理，主要验证是否使用了正确的基数
                    pass
                
                checked_count += 1
        
        # 检查换料后的装填（如果需要）
        # Bug 11462: 装填量应该使用from_tool（当前工具）的retraction_length，与回抽保持一致
        # Bug 17817: 单喷嘴多耗材共用回抽状态，回填包含换料前工具的额外回填长度。
        if "after_change" in check_points:
            unretract_after = find_first_unretraction_after(parser.moves, tc['line'])
            if unretract_after:
                expected_base = tool_params[from_tool]["retraction_length"]
                expected_extra = _restart_extra(tool_params[from_tool])
                expected_unretract = expected_base + expected_extra
                actual_unretract = unretract_after.e
                
                if not _within_tolerance(actual_unretract, expected_unretract, UNRETRACT_TOLERANCE):
                    failures.append(
                        f"换料点{idx} 行{tc['line']}: "
                        f"换料后装填量{actual_unretract:.4f}mm，"
                        f"期望{from_tool}参数{expected_unretract:.4f}mm "
                        f"(retraction_length={expected_base} + retract_restart_extra={expected_extra})，"
                        f"差值{abs(actual_unretract - expected_unretract):.4f}mm"
                    )
                checked_count += 1
            else:
                failures.append(f"换料点{idx} 行{tc['line']}: 未找到换料后装填")

        # Bug 11463: 检查擦嘴线装填
        # 擦嘴线是在换料后、返回模型前的清理动作，应该使用to_tool（T1）的参数
        if "purge_line" in check_points:
            # 在Skirt/Brim段落中查找装填
            unretract_purge = find_unretraction_in_section(
                parser.lines, parser.moves, tc['line'],
                section_marker=";TYPE:Skirt/Brim"
            )
            if unretract_purge:
                expected_base = tool_params[to_tool]["retraction_length"]
                expected_extra = _restart_extra(tool_params[to_tool])
                expected_unretract = expected_base + expected_extra
                actual_unretract = unretract_purge.e
                
                if not _within_tolerance(actual_unretract, expected_unretract, 0.2):
                    failures.append(
                        f"换料点{idx} 行{tc['line']}: "
                        f"擦嘴线装填量{actual_unretract:.2f}mm，"
                        f"期望{to_tool}参数{expected_unretract:.2f}mm "
                        f"(base={expected_base:.2f} + extra={expected_extra:.2f})，"
                        f"差值{abs(actual_unretract - expected_unretract):.2f}mm"
                    )
                checked_count += 1
        
        # Bug 13303: 检查填充完成后装填
        if "after_infill" in check_points:
            # 在AFTER_LAYER_CHANGE标记后查找装填
            unretract_infill = find_unretraction_after_marker(
                parser.lines, parser.moves, tc['line'],
                marker=";AFTER_LAYER_CHANGE"
            )
            if unretract_infill:
                expected_base = tool_params[from_tool]["retraction_length"]
                expected_unretract = expected_base
                actual_unretract = unretract_infill.e
                
                if not _within_tolerance(actual_unretract, expected_unretract, 0.2):
                    failures.append(
                        f"换料点{idx} 行{tc['line']}: "
                        f"填充完成后装填量{actual_unretract:.2f}mm，"
                        f"期望{from_tool}参数{expected_unretract:.2f}mm，"
                        f"差值{abs(actual_unretract - expected_unretract):.2f}mm"
                    )
                checked_count += 1
        
        # 填充后使用新耗材的回抽长度和擦拭比例，额外回填不参与比例计算。
        if "after_infill_retract" in check_points:
            infill_failures = _check_infill_retraction(parser, tc['line'], tool_params[to_tool])
            failures.extend(f"换料点{idx} 行{tc['line']}: {failure}" for failure in infill_failures)
            checked_count += 1

        # Bug 13309: 检查填充和外墙装填
        if "infill_perimeter" in check_points:
            # 在Internal infill或Perimeter段落中查找装填
            unretract_ip = find_unretraction_in_section(
                parser.lines, parser.moves, tc['line'],
                section_marker=";TYPE:Internal infill"
            )
            if not unretract_ip:
                unretract_ip = find_unretraction_in_section(
                    parser.lines, parser.moves, tc['line'],
                    section_marker=";TYPE:Outer wall"
                )
            
            if unretract_ip:
                expected_base = tool_params[from_tool]["retraction_length"]
                expected_unretract = expected_base
                actual_unretract = unretract_ip.e
                
                if not _within_tolerance(actual_unretract, expected_unretract, 0.2):
                    failures.append(
                        f"换料点{idx} 行{tc['line']}: "
                        f"填充/外墙装填量{actual_unretract:.2f}mm，"
                        f"期望{from_tool}参数{expected_unretract:.2f}mm，"
                        f"差值{abs(actual_unretract - expected_unretract):.2f}mm"
                    )
                checked_count += 1
        
        # Bug 13534-13555: 检查层间换色装填
        if "layer_change" in check_points:
            # 在LAYER_CHANGE标记后查找装填
            unretract_layer = find_unretraction_after_marker(
                parser.lines, parser.moves, tc['line'],
                marker=";LAYER_CHANGE"
            )
            if unretract_layer:
                expected_base = tool_params[from_tool]["retraction_length"]
                expected_unretract = expected_base
                actual_unretract = unretract_layer.e
                
                if not _within_tolerance(actual_unretract, expected_unretract, 0.2):
                    failures.append(
                        f"换料点{idx} 行{tc['line']}: "
                        f"层间换色装填量{actual_unretract:.2f}mm，"
                        f"期望{from_tool}参数{expected_unretract:.2f}mm，"
                        f"差值{abs(actual_unretract - expected_unretract):.2f}mm"
                    )
                checked_count += 1
    
    if failures:
        return False, tool_changes, {
            "failures": failures,
            "tool_change_count": len(tool_changes),
            "checked_count": checked_count
        }
    
    return True, tool_changes, {
        "tool_change_count": len(tool_changes),
        "checked_count": checked_count,
        "from_tool": from_tool,
        "to_tool": to_tool
    }


def parse_retraction_phases(
    lines: List[str],
    moves: List[GCodeMove],
    tool_change_line: int
) -> Dict[str, float]:
    """
    解析换料前的三阶段回抽
    
    回抽分为三个阶段：
    1. 擦拭前回抽（before_wipe）: ;WIPE_START 之前的主回抽 G1 E-X
    2. 擦拭时回抽（during_wipe）: ;WIPE_START 和 ;WIPE_END 之间的回抽
    3. 擦拭后回抽（after_wipe）: ;WIPE_END 之后到换料命令之间的小回抽
    
    Args:
        lines: GCode所有行
        moves: 所有移动指令列表
        tool_change_line: 换料指令行号
    
    Returns:
        {
            'before_wipe': 擦拭前回抽量,
            'during_wipe': 擦拭时回抽量,
            'after_wipe': 擦拭后回抽量
        }
    """
    result = {
        'before_wipe': 0.0,
        'during_wipe': 0.0,
        'after_wipe': 0.0
    }
    
    # 以最近一次独立装填（G1 E<positive>）作为当前回抽序列的起点。
    # 固定 50 行窗口可能同时覆盖擦拭塔上一段完整回抽，导致重复累计。
    tool_change_idx = min(len(lines), max(0, tool_change_line - 1))
    standalone_unretract_re = re.compile(
        r'^G1\s+E\+?([\d.]+)(?:\s+F[\d.]+)?\s*(?:;.*)?$',
        re.IGNORECASE,
    )
    search_start = max(0, tool_change_idx - 500)
    for line_idx in range(tool_change_idx - 1, search_start - 1, -1):
        if standalone_unretract_re.match(lines[line_idx].strip()):
            search_start = line_idx
            break
    search_lines = lines[search_start:tool_change_idx]
    
    # 查找标记位置
    wipe_start_idx = None
    wipe_end_idx = None
    
    for i, line in enumerate(search_lines):
        if ';WIPE_START' in line:
            wipe_start_idx = i
        elif ';WIPE_END' in line:
            wipe_end_idx = i
    
    # 如果没有找到擦拭标记，使用简单模式
    if wipe_start_idx is None or wipe_end_idx is None:
        # 收集当前装填之后到换料前的所有回抽
        for move in reversed(moves):
            if move.line_num >= tool_change_line:
                continue
            if move.line_num < search_start + 1:
                break
            if move.move_type == GCodeMoveType.RETRACTION:
                result['before_wipe'] += abs(move.e)
        return result
    
    # 分阶段提取回抽
    # 1. 擦拭前回抽：WIPE_START之前
    for i in range(wipe_start_idx):
        line = search_lines[i].strip()
        if line.startswith('G1') and 'E-' in line:
            # 提取回抽量
            match = re.search(r'E(-?[\d.]+)', line)
            if match:
                e_val = float(match.group(1))
                if e_val < 0:
                    result['before_wipe'] += abs(e_val)
    
    # 2. 擦拭时回抽：WIPE_START 和 WIPE_END 之间
    for i in range(wipe_start_idx, wipe_end_idx + 1):
        line = search_lines[i].strip()
        if line.startswith('G1') and 'E-' in line:
            match = re.search(r'E(-?[\d.]+)', line)
            if match:
                e_val = float(match.group(1))
                if e_val < 0:
                    result['during_wipe'] += abs(e_val)
    
    # 3. 擦拭后回抽：WIPE_END 之后到换料命令
    for i in range(wipe_end_idx + 1, len(search_lines)):
        line = search_lines[i].strip()
        if line.startswith('G1') and 'E-' in line:
            match = re.search(r'E(-?[\d.]+)', line)
            if match:
                e_val = float(match.group(1))
                if e_val < 0:
                    result['after_wipe'] += abs(e_val)
    
    return result


def find_tool_changes(
    parser: WipeTowerGCodeParser,
    from_tool: str,
    to_tool: str
) -> List[Dict[str, Any]]:
    """
    查找从from_tool到to_tool的所有换料点
    
    Returns:
        List of {
            'line': 换料指令行号,
            'from': 原工具,
            'to': 目标工具
        }
    """
    tool_changes = []
    current_tool = "T0"  # 默认起始工具
    
    for i, line in enumerate(parser.lines, start=1):
        stripped = line.strip()
        
        # 检测T指令
        match = re.match(r'^T(\d+)', stripped)
        if match:
            new_tool = f"T{match.group(1)}"
            
            # 检查是否是我们关心的换料
            if current_tool == from_tool and new_tool == to_tool:
                tool_changes.append({
                    'line': i,
                    'from': current_tool,
                    'to': new_tool
                })
            
            current_tool = new_tool
    
    return tool_changes


def find_all_retractions_before(
    moves: List[GCodeMove],
    line_num: int
) -> List[GCodeMove]:
    """
    查找指定行号之前的所有回抽动作（擦拭前+擦拭时+擦拭后）
    
    Args:
        moves: 所有移动指令列表
        line_num: 参考行号
    
    Returns:
        所有回抽动作的列表
    """
    retractions = []
    # 从指定行号向前查找，最多查找50行以覆盖所有回抽组件
    for move in reversed(moves):
        if move.line_num >= line_num:
            continue
        if move.line_num < line_num - 50:
            break
        
        if move.move_type == GCodeMoveType.RETRACTION:
            retractions.insert(0, move)  # 保持时间顺序
    
    return retractions


def find_first_unretraction_after(
    moves: List[GCodeMove],
    line_num: int,
    max_lines: int = 30
) -> Optional[GCodeMove]:
    """
    查找指定行号之后的第一次装填动作
    
    Args:
        moves: 所有移动指令列表
        line_num: 参考行号
        max_lines: 最多向后查找的行数
    
    Returns:
        第一次装填动作，如果没有则返回None
        """
    # 从指定行号向后查找，最多查找max_lines行
    for move in moves:
        if move.line_num <= line_num:
            continue
        if move.line_num > line_num + max_lines:
            break
        
        if move.move_type == GCodeMoveType.UNRETRACTION:
            return move
    
    return None


def find_unretraction_in_section(
    lines: List[str],
    moves: List[GCodeMove],
    start_line: int,
    section_marker: str,
    max_search_lines: int = 200
) -> Optional[GCodeMove]:
    """
    在特定GCode段落中查找装填动作
    
    Args:
        lines: GCode所有行
        moves: 所有移动指令列表
        start_line: 开始搜索的行号
        section_marker: 段落标记（如";TYPE:Skirt/Brim", ";TYPE:Prime tower"）
        max_search_lines: 最多搜索的行数
    
    Returns:
        找到的第一个装填动作，如果没有则返回None
    """
    # 先找到section_marker所在的行
    section_start = None
    for i in range(start_line, min(start_line + max_search_lines, len(lines))):
        if section_marker in lines[i]:
            section_start = i + 1
            break
    
    if section_start is None:
        return None
    
    # 在该section中查找装填
    for move in moves:
        if move.line_num < section_start:
            continue
        if move.line_num > section_start + 50:  # section内最多查50行
            break
        
        if move.move_type == GCodeMoveType.UNRETRACTION:
            return move
    
    return None


def find_unretraction_after_marker(
    lines: List[str],
    moves: List[GCodeMove],
    start_line: int,
    marker: str,
    max_search_lines: int = 100
) -> Optional[GCodeMove]:
    """
    查找特定标记之后的装填动作
    
    Args:
        lines: GCode所有行
        moves: 所有移动指令列表
        start_line: 开始搜索的行号
        marker: 标记字符串（如";AFTER_LAYER_CHANGE"）
        max_search_lines: 最多搜索的行数
    
    Returns:
        找到的第一个装填动作，如果没有则返回None
    """
    # 先找到marker所在的行
    marker_line = None
    for i in range(start_line, min(start_line + max_search_lines, len(lines))):
        if marker in lines[i]:
            marker_line = i + 1
            break
    
    if marker_line is None:
        return None
    
    # 在marker之后查找装填
    return find_first_unretraction_after(moves, marker_line, max_lines=30)


def find_retraction_after_unretraction(
    moves: List[GCodeMove],
    unretract_line: int,
    max_lines: int = 50
) -> Optional[GCodeMove]:
    """
    查找装填之后的第一次回抽
    
    用于验证Bug 13303：打完擦拭塔填充后的回抽应该使用当前工具参数
    
    Args:
        moves: 所有移动指令列表
        unretract_line: 装填动作所在行号
        max_lines: 最多向后查找的行数
    
    Returns:
        第一次回抽动作，如果没有则返回None
    """
    for move in moves:
        if move.line_num <= unretract_line:
            continue
        if move.line_num > unretract_line + max_lines:
            break
        
        if move.move_type == GCodeMoveType.RETRACTION:
            return move
    
    return None


def get_tool_params_from_config(
    config: Dict[str, str]
) -> Dict[str, Dict[str, float]]:
    """
    从CONFIG_BLOCK提取工具参数
    
    Args:
        config: 配置字典
    
    Returns:
        {
            "T0": {"retraction_length": 5.0, "extra": 0.0},
            "T1": {"retraction_length": 8.0, "extra": 0.5}
        }
    """
    tool_params = {}
    
    # 提取T0参数
    if "retraction_length[0]" in config:
        tool_params["T0"] = {
            "retraction_length": float(config["retraction_length[0]"]),
            "extra": float(config.get("retract_restart_extra_toolchange[0]", 
                                     config.get("retract_restart_extra[0]", "0")))
        }
    
    # 提取T1参数
    if "retraction_length[1]" in config:
        tool_params["T1"] = {
            "retraction_length": float(config["retraction_length[1]"]),
            "extra": float(config.get("retract_restart_extra_toolchange[1]", 
                                     config.get("retract_restart_extra[1]", "0")))
        }
    
    return tool_params


def parse_retraction_phases_after_infill(
    lines: List[str],
    moves: List[GCodeMove],
    unretract_line: int
) -> Optional[Dict[str, float]]:
    """
    解析打完填充后的三阶段回抽（与parse_retraction_phases类似，但是向后查找）
    
    Args:
        lines: GCode所有行
        moves: 所有移动指令列表
        unretract_line: 装填指令行号
    
    Returns:
        {
            'before_wipe': 擦拭前回抽量,
            'during_wipe': 擦拭时回抽量,
            'after_wipe': 擦拭后回抽量
        }
        如果未找到返回None
    """
    result = {
        'before_wipe': 0.0,
        'during_wipe': 0.0,
        'after_wipe': 0.0
    }
    
    # 向后搜索50行范围
    search_end = min(len(lines), unretract_line + 50)
    search_lines = lines[unretract_line:search_end]
    
    # 查找标记位置
    wipe_start_idx = None
    wipe_end_idx = None
    
    for i, line in enumerate(search_lines):
        if ';WIPE_START' in line:
            wipe_start_idx = i
        elif ';WIPE_END' in line:
            wipe_end_idx = i
    
    # 如果没有找到擦拭标记，返回None
    if wipe_start_idx is None or wipe_end_idx is None:
        return None
    
    # 分阶段提取回抽
    # 1. 擦拭前回抽：WIPE_START之前
    for i in range(wipe_start_idx):
        line = search_lines[i].strip()
        if line.startswith('G1') and 'E-' in line:
            match = re.search(r'E(-?[\d.]+)', line)
            if match:
                e_val = float(match.group(1))
                if e_val < 0:
                    result['before_wipe'] += abs(e_val)
    
    # 2. 擦拭时回抽：WIPE_START 和 WIPE_END 之间
    for i in range(wipe_start_idx, wipe_end_idx + 1):
        line = search_lines[i].strip()
        if line.startswith('G1') and 'E-' in line:
            match = re.search(r'E(-?[\d.]+)', line)
            if match:
                e_val = float(match.group(1))
                if e_val < 0:
                    result['during_wipe'] += abs(e_val)
    
    # 3. 擦拭后回抽：WIPE_END 之后
    for i in range(wipe_end_idx + 1, len(search_lines)):
        line = search_lines[i].strip()
        if line.startswith('G1') and 'E-' in line:
            match = re.search(r'E(-?[\d.]+)', line)
            if match:
                e_val = float(match.group(1))
                if e_val < 0:
                    result['after_wipe'] += abs(e_val)
    
    return result

    return tool_params
