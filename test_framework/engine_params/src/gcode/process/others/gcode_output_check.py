"""
G代码输出 (G-code output) 参数校验模块

包含以下参数的校验函数：
- reduce_infill_retraction: Level 2 特征检测（统计填充区域回抽次数）
- gcode_add_line_number: Level 2 特征检测（检测行号格式）
- gcode_comments: Level 2 特征检测（统计注释行占比）
- gcode_label_objects: Level 2 特征检测（检测EXCLUDE_OBJECT标记）
- exclude_object: Level 2 特征检测（同 gcode_label_objects）
- filename_format: 特殊 - 无法通过G-code校验（文件名相关）
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple
import re

from engine_params.src.gcode.GCodeParser import GCodeParser


def _normalize_to_bool(val: object) -> bool:
    """将配置值规范化为 bool"""
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    if isinstance(val, str):
        return val.lower() in ("1", "true", "yes", "on")
    return False


# ================== reduce_infill_retraction ==================

def parse_reduce_infill_retraction(
        gcode_path: Path | str,
        expected_value: bool,
) -> Tuple[bool, bool, Dict[str, object]]:
    """
    解析 G-code，Level 2 特征检测 reduce_infill_retraction。
    
    验证思路：统计填充区域的回抽命令次数
    - 启用特征：填充区域内的 G10（回抽）命令显著减少
    - 禁用特征：填充区域内仍有较多回抽命令
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 reduce_infill_retraction 值 (True/False)

    返回:
        Tuple[bool, bool, Dict[str, object]]:
            - ok: 检测结果是否与期望一致
            - detected_value: 检测出的值
            - details: 详细信息字典
    """
    gcode_path = Path(gcode_path)
    parser = GCodeParser(gcode_path)
    
    # 从配置中读取（Level 1 快速预检）
    cfg = parser.load_config()
    config_value = cfg.get("reduce_infill_retraction")
    
    if config_value is not None:
        config_bool = _normalize_to_bool(config_value)
        is_match = (config_bool == expected_value)
        
        return (
            is_match,
            config_bool,
            {
                "detection_method": "Level 1 - Config",
                "config_value": config_value,
                "expected": expected_value,
                "message": f"Config value: {config_value}, expected: {expected_value}",
            }
        )
    
    # Level 2: 统计填充区域回抽次数（如果配置不可用）
    try:
        lines = gcode_path.read_text(encoding='utf-8').splitlines()
        
        in_infill = False
        infill_lines = 0
        infill_retractions = 0
        total_retractions = 0
        
        for line in lines:
            line = line.strip()
            
            # 检测填充类型标记
            if ";TYPE:Sparse infill" in line or ";TYPE:Internal solid infill" in line:
                in_infill = True
                continue
            elif line.startswith(";TYPE:") and in_infill:
                in_infill = False
                continue
            
            # 统计回抽命令
            if line.startswith("G10"):  # 回抽命令
                total_retractions += 1
                if in_infill:
                    infill_retractions += 1
            
            if in_infill:
                infill_lines += 1
        
        # 判断：如果填充区域回抽率低，则启用了 reduce_infill_retraction
        infill_retraction_rate = infill_retractions / infill_lines if infill_lines > 0 else 0
        detected_enabled = infill_retraction_rate < 0.01  # 阈值：低于1%认为已减少
        
        is_match = (detected_enabled == expected_value)
        
        return (
            is_match,
            detected_enabled,
            {
                "detection_method": "Level 2 - Retraction Counting",
                "infill_lines": infill_lines,
                "infill_retractions": infill_retractions,
                "total_retractions": total_retractions,
                "infill_retraction_rate": f"{infill_retraction_rate:.2%}",
                "threshold": "< 1%",
                "expected": expected_value,
                "message": f"Infill retraction rate: {infill_retraction_rate:.2%}, expected enabled: {expected_value}",
            }
        )
    
    except Exception as e:
        return (
            False,
            False,
            {
                "detection_method": "Level 2 - Failed",
                "error": str(e),
                "message": f"Failed to detect reduce_infill_retraction: {e}",
            }
        )


# ================== gcode_add_line_number ==================

def parse_gcode_add_line_number(
        gcode_path: Path | str,
        expected_value: bool,
) -> Tuple[bool, bool, Dict[str, object]]:
    """
    解析 G-code，Level 2 特征检测 gcode_add_line_number。
    
    验证思路：检测 G-code 行是否有 N 开头的行号
    - 启用特征：大部分非注释行以 N1, N2, N3 ... 开头
    - 禁用特征：行首直接是 G/M 命令或注释
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 gcode_add_line_number 值 (True/False)

    返回:
        Tuple[bool, bool, Dict[str, object]]:
            - ok: 检测结果是否与期望一致
            - detected_value: 检测出的值
            - details: 详细信息字典
    """
    gcode_path = Path(gcode_path)
    
    try:
        lines = gcode_path.read_text(encoding='utf-8').splitlines()
        
        line_number_pattern = re.compile(r'^N\d+')
        
        total_lines = 0
        lines_with_number = 0
        
        for line in lines:
            line = line.strip()
            
            # 跳过空行和纯注释行
            if not line or line.startswith(';'):
                continue
            
            total_lines += 1
            
            # 检测行号
            if line_number_pattern.match(line):
                lines_with_number += 1
        
        # 判断：如果超过 90% 的行有行号，则启用了 gcode_add_line_number
        line_number_rate = lines_with_number / total_lines if total_lines > 0 else 0
        detected_enabled = line_number_rate > 0.9  # 阈值：超过 90%
        
        is_match = (detected_enabled == expected_value)
        
        return (
            is_match,
            detected_enabled,
            {
                "detection_method": "Level 2 - Line Number Detection",
                "total_lines": total_lines,
                "lines_with_number": lines_with_number,
                "line_number_rate": f"{line_number_rate:.2%}",
                "threshold": "> 90%",
                "expected": expected_value,
                "message": f"Line number rate: {line_number_rate:.2%}, expected enabled: {expected_value}",
            }
        )
    
    except Exception as e:
        return (
            False,
            False,
            {
                "detection_method": "Level 2 - Failed",
                "error": str(e),
                "message": f"Failed to detect gcode_add_line_number: {e}",
            }
        )


# ================== gcode_comments ==================

def parse_gcode_comments(
        gcode_path: Path | str,
        expected_value: bool,
) -> Tuple[bool, bool, Dict[str, object]]:
    """
    解析 G-code，Level 2 特征检测 gcode_comments。
    
    验证思路：统计注释行占比
    - 启用特征：注释行（以 ; 开头）占比较高（> 5%）
    - 禁用特征：注释行很少，仅有必要的配置注释
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 gcode_comments 值 (True/False)

    返回:
        Tuple[bool, bool, Dict[str, object]]:
            - ok: 检测结果是否与期望一致
            - detected_value: 检测出的值
            - details: 详细信息字典
    """
    gcode_path = Path(gcode_path)
    
    try:
        lines = gcode_path.read_text(encoding='utf-8').splitlines()
        
        total_gcode_lines = 0  # 执行块内 G-code 命令行总数
        inline_comment_lines = 0  # 执行块内行尾注释行数
        in_executable_block = False  # 是否在执行块内
        
        for line in lines:
            line = line.strip()
            
            # 检测执行块标记
            if '; EXECUTABLE_BLOCK_START' in line:
                in_executable_block = True
                continue
            elif '; EXECUTABLE_BLOCK_END' in line:
                in_executable_block = False
                continue
            
            # 只处理执行块内的代码
            if not in_executable_block:
                continue
            
            # 跳过空行和纯注释行（单独成行的注释）
            if not line or line.startswith(';'):
                continue
            
            total_gcode_lines += 1
            
            # 检查是否有行尾注释（G-code 命令后跟 ;）
            if ';' in line:
                inline_comment_lines += 1
        
        # 判断：如果行尾注释占比 > 5%，则启用了 G-code comments
        inline_comment_rate = inline_comment_lines / total_gcode_lines if total_gcode_lines > 0 else 0
        detected_enabled = inline_comment_rate > 0.05  # 阈值：> 5%
        
        is_match = (detected_enabled == expected_value)
        
        return (
            is_match,
            detected_enabled,
            {
                "detection_method": "Level 2 - Inline Comment Detection",
                "total_gcode_lines": total_gcode_lines,
                "inline_comment_lines": inline_comment_lines,
                "inline_comment_rate": f"{inline_comment_rate:.2%}",
                "threshold": "> 5%",
                "expected": expected_value,
                "message": f"Inline comment rate: {inline_comment_rate:.2%}, expected enabled: {expected_value}",
            }
        )
    
    except Exception as e:
        return (
            False,
            False,
            {
                "detection_method": "Level 2 - Failed",
                "error": str(e),
                "message": f"Failed to detect gcode_comments: {e}",
            }
        )


# ================== gcode_label_objects ==================

def parse_gcode_label_objects(
        gcode_path: Path | str,
        expected_value: bool,
) -> Tuple[bool, bool, Dict[str, object]]:
    """
    解析 G-code，Level 2 特征检测 gcode_label_objects。
    
    验证思路：搜索对象打印控制注释
    - 启用特征：存在 "; printing object" 和 "; stop printing object" 标记
    - 禁用特征：不存在上述标记
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 gcode_label_objects 值 (True/False)

    返回:
        Tuple[bool, bool, Dict[str, object]]:
            - ok: 检测结果是否与期望一致
            - detected_value: 检测出的值
            - details: 详细信息字典
    """
    gcode_path = Path(gcode_path)
    
    try:
        content = gcode_path.read_text(encoding='utf-8')
        
        # 搜索对象打印控制注释
        has_printing_object = "; printing object" in content
        has_stop_printing = "; stop printing object" in content
        
        # 判断：必须同时存在两个标记才认为启用了对象标签
        detected_enabled = has_printing_object and has_stop_printing
        
        is_match = (detected_enabled == expected_value)
        
        return (
            is_match,
            detected_enabled,
            {
                "detection_method": "Level 2 - Object Print Control Comments",
                "has_printing_object": has_printing_object,
                "has_stop_printing": has_stop_printing,
                "expected": expected_value,
                "message": f"'; printing object' / '; stop printing object' found: {detected_enabled}, expected enabled: {expected_value}",
            }
        )
    
    except Exception as e:
        return (
            False,
            False,
            {
                "detection_method": "Level 2 - Failed",
                "error": str(e),
                "message": f"Failed to detect gcode_label_objects: {e}",
            }
        )


# ================== exclude_object ==================

def parse_exclude_object(
        gcode_path: Path | str,
        expected_value: bool,
) -> Tuple[bool, bool, Dict[str, object]]:
    """
    解析 G-code，Level 2 特征检测 exclude_object。
    
    验证思路：搜索对象排除标记
    - 启用特征：存在 EXCLUDE_OBJECT_START 和 EXCLUDE_OBJECT_END 标记
    - 禁用特征：不存在上述标记
    
    注意：这与 gcode_label_objects 不同
    - gcode_label_objects: 检测 "; printing object" / "; stop printing object"（注释标记）
    - exclude_object: 检测 EXCLUDE_OBJECT_START/END（Klipper对象排除命令）
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的 exclude_object 值 (True/False)

    返回:
        Tuple[bool, bool, Dict[str, object]]:
            - ok: 检测结果是否与期望一致
            - detected_value: 检测出的值
            - details: 详细信息字典
    """
    gcode_path = Path(gcode_path)
    
    try:
        content = gcode_path.read_text(encoding='utf-8')
        
        # 搜索 EXCLUDE_OBJECT 边界标记
        has_start = "EXCLUDE_OBJECT_START" in content
        has_end = "EXCLUDE_OBJECT_END" in content
        
        # 判断：必须同时存在两个标记才认为启用了对象排除
        detected_enabled = has_start and has_end
        
        is_match = (detected_enabled == expected_value)
        
        return (
            is_match,
            detected_enabled,
            {
                "detection_method": "Level 2 - EXCLUDE_OBJECT Boundary Markers",
                "has_start": has_start,
                "has_end": has_end,
                "expected": expected_value,
                "message": f"EXCLUDE_OBJECT_START/END found: {detected_enabled}, expected enabled: {expected_value}",
            }
        )
    
    except Exception as e:
        return (
            False,
            False,
            {
                "detection_method": "Level 2 - Failed",
                "error": str(e),
                "message": f"Failed to detect exclude_object: {e}",
            }
        )


# ================== filename_format ==================

def parse_filename_format(
        gcode_path: Path | str,
        expected_value: str,
) -> Tuple[bool, str, Dict[str, object]]:
    """
    解析 G-code，特殊处理 filename_format。
    
    注意：filename_format 参数影响输出文件名，无法通过 G-code 内容校验。
    此函数仅作占位，实际校验需要在文件系统层面检查文件名格式。
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的文件名格式模板

    返回:
        Tuple[bool, str, Dict[str, object]]:
            - ok: 始终返回 False（无法通过 G-code 校验）
            - detected_value: "N/A"
            - details: 详细信息字典
    """
    gcode_path = Path(gcode_path)
    
    # 提取实际文件名
    actual_filename = gcode_path.name
    
    return (
        False,
        "N/A",
        {
            "detection_method": "Special - Filename Validation",
            "actual_filename": actual_filename,
            "expected_format": expected_value,
            "message": (
                "filename_format cannot be validated through G-code content. "
                "It requires filesystem-level validation of output filename pattern."
            ),
            "note": "此参数需要在文件系统层面校验输出文件名格式，无法通过 G-code 内容检测。",
        }
    )
