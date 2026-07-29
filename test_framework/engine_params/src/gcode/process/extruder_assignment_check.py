"""
Extruder assignment parameter validation functions
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Dict, Tuple

from engine_params.src.gcode.GCodeParser import GCodeParser


def _str_norm(v: Any) -> str:
    """Normalize value to string for comparison"""
    if v is None:
        return ""
    return str(v).strip()


def parse_wall_filament(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """
    Test wall_filament parameter (Level 1 - Config)
    
    Note: This parameter specifies which extruder to use for printing walls (perimeters).
    For single-extruder printers, it should always be 1.
    For multi-extruder printers, it can be 1, 2, 3, etc.
    """
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("wall_filament")
    current_tool = 0
    current_type = ""
    extrusion_by_tool: Dict[int, float] = {}
    with Path(gcode_path).open("r", encoding="utf-8", errors="ignore") as stream:
        for raw in stream:
            line = raw.strip()
            if re.fullmatch(r"T\d+", line):
                current_tool = int(line[1:])
            elif line.startswith(";TYPE:"):
                current_type = line[6:]
            elif current_type in {"Inner wall", "Outer wall", "Overhang wall"} and line.startswith("G1"):
                match = re.search(r"\bE([+]?(?:\d+(?:\.\d*)?|\.\d+))\b", line)
                if match and float(match.group(1)) > 0 and (" X" in f" {line}" or " Y" in f" {line}"):
                    extrusion_by_tool[current_tool] = extrusion_by_tool.get(current_tool, 0.0) + float(match.group(1))

    expected_tool = max(int(float(expected_value)) - 1, 0)
    total = sum(extrusion_by_tool.values())
    expected_ratio = extrusion_by_tool.get(expected_tool, 0.0) / total if total else 0.0
    behavior_ok = total > 0 and expected_ratio >= 0.95
    config_ok = _str_norm(actual) == _str_norm(expected_value)
    return (
        config_ok and behavior_ok,
        actual,
        {
            "detection_method": "配置值 + Wall 正向挤出工具占比",
            "wall_extrusion_by_tool": {f"T{k}": round(v, 6) for k, v in sorted(extrusion_by_tool.items())},
            "expected_tool": f"T{expected_tool}",
            "expected_tool_ratio": expected_ratio,
            "message": f"Wall filament: {actual}, T{expected_tool} ratio={expected_ratio:.1%}",
        },
    )
