"""
后处理脚本与备注 (Post-processing Scripts & Notes) 参数校验模块

包含以下参数的校验函数：
- post_process: 特殊 - 无法直接通过G-code校验（脚本执行后效果）
- notes: Level 1 配置对比 - 检测G-code头部注释中的备注内容
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

from engine_params.src.gcode.GCodeParser import GCodeParser


# ================== post_process ==================

def parse_post_process(
        gcode_path: Path | str,
        expected_value: str,
) -> Tuple[bool, str, Dict[str, object]]:
    """
    解析 G-code，特殊处理 post_process。
    
    注意：post_process 参数指定的是外部脚本路径，该脚本在 G-code 生成后执行。
    脚本可能修改 G-code 内容，但无法通过 G-code 内容反向推断脚本路径。
    
    可能的验证方式：
    1. 检测 G-code 中是否有脚本执行的痕迹（如特定注释标记）
    2. 对比脚本执行前后的 G-code 差异（需要基线对比）
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的后处理脚本路径

    返回:
        Tuple[bool, str, Dict[str, object]]:
            - ok: 始终返回 False（无法直接校验）
            - detected_value: "N/A"
            - details: 详细信息字典
    """
    gcode_path = Path(gcode_path)
    
    try:
        # 尝试从 G-code 中搜索后处理脚本的痕迹
        content = gcode_path.read_text(encoding='utf-8')
        config = GCodeParser(gcode_path).load_config() or {}
        raw_config = config.get("post_process", "")
        config_value = str(getattr(raw_config, "value", raw_config) or "").strip()
        
        # 搜索可能的标记（不同切片器可能有不同标记）
        # 例如："; post-processed by <script>"
        post_process_markers = [
            "post-processed by",
            "POST_PROCESS",
        ]
        
        found_markers = []
        for marker in post_process_markers:
            if marker in content:
                found_markers.append(marker)
        
        if not str(expected_value).strip():
            ok = not config_value and not found_markers
            return ok, config_value, {
                "detection_method": "Config + output marker absence",
                "config_value": config_value,
                "found_markers": found_markers,
                "message": "No post-process command configured and no modified-output marker found.",
            }
        if found_markers:
            return (
                False,
                "N/A",
                {
                    "detection_method": "Special - Marker Search",
                    "found_markers": found_markers,
                    "expected_script": expected_value,
                    "message": (
                        f"Found post-process markers: {found_markers}, "
                        "but cannot verify script path through G-code content."
                    ),
                    "note": "后处理脚本需要通过基线对比或外部验证来校验效果。",
                }
            )
        else:
            return (
                False,
                "N/A",
                {
                    "detection_method": "Special - No Markers Found",
                    "expected_script": expected_value,
                    "message": (
                        "post_process parameter cannot be validated through G-code content. "
                        "The script executes after G-code generation and may modify the content, "
                        "but the script path itself is not recorded in G-code."
                    ),
                    "note": "此参数需要通过基线对比或检查脚本执行效果来间接验证。",
                }
            )
    
    except Exception as e:
        return (
            False,
            "N/A",
            {
                "detection_method": "Special - Failed",
                "error": str(e),
                "message": f"Failed to check post_process markers: {e}",
            }
        )


# ================== notes ==================

def parse_notes(
        gcode_path: Path | str,
        expected_value: str,
) -> Tuple[bool, str, Dict[str, object]]:
    """
    解析 G-code，Level 1 配置对比 notes。
    
    验证思路：检测 G-code 头部是否包含备注内容
    - notes 参数的内容通常会以注释形式出现在 G-code 文件头部
    - 搜索 "; notes:" 或直接搜索期望的备注文本
    
    参数:
        gcode_path: G-code 文件路径
        expected_value: 期望的备注内容

    返回:
        Tuple[bool, str, Dict[str, object]]:
            - ok: 检测结果是否与期望一致
            - detected_value: 检测到的备注内容
            - details: 详细信息字典
    """
    gcode_path = Path(gcode_path)
    parser = GCodeParser(gcode_path)
    
    # Level 1: 从配置中读取 notes
    cfg = parser.load_config()
    config_notes = cfg.get("notes")
    
    if config_notes is not None:
        config_notes_str = str(config_notes).strip()
        expected_str = str(expected_value).strip()
        
        # 判断：配置中的 notes 是否包含期望的内容
        # 支持部分匹配（因为 notes 可能包含额外的格式化字符）
        is_match = (expected_str in config_notes_str) or (config_notes_str == expected_str)
        
        return (
            is_match,
            config_notes_str,
            {
                "detection_method": "Level 1 - Config",
                "config_value": config_notes_str,
                "expected": expected_str,
                "match_type": "exact" if config_notes_str == expected_str else "partial",
                "message": f"Config notes: '{config_notes_str}', expected: '{expected_str}'",
            }
        )
    
    # Level 1 备选：直接从 G-code 头部搜索 notes 注释
    try:
        lines = gcode_path.read_text(encoding='utf-8').splitlines()
        
        # 只搜索前 100 行（notes 通常在文件头部）
        header_lines = lines[:100]
        
        found_notes = []
        for line in header_lines:
            line = line.strip()
            
            # 搜索 "; notes:" 或类似标记
            if line.startswith(";") and "notes:" in line.lower():
                # 提取 notes 内容
                notes_content = line.split(":", 1)[1].strip() if ":" in line else ""
                found_notes.append(notes_content)
            
            # 直接搜索期望的备注文本
            elif expected_value and expected_value in line:
                found_notes.append(line.lstrip(";").strip())
        
        if found_notes:
            detected_notes = " ".join(found_notes)
            is_match = expected_value in detected_notes
            
            return (
                is_match,
                detected_notes,
                {
                    "detection_method": "Level 1 - Header Search",
                    "found_notes": found_notes,
                    "expected": expected_value,
                    "message": f"Found notes in header: '{detected_notes}', expected: '{expected_value}'",
                }
            )
        else:
            # 未找到 notes
            return (
                expected_value == "" or expected_value is None,  # 如果期望值为空，则匹配
                "",
                {
                    "detection_method": "Level 1 - No Notes Found",
                    "expected": expected_value,
                    "message": f"No notes found in G-code header, expected: '{expected_value}'",
                }
            )
    
    except Exception as e:
        return (
            False,
            "",
            {
                "detection_method": "Level 1 - Failed",
                "error": str(e),
                "message": f"Failed to detect notes: {e}",
            }
        )
