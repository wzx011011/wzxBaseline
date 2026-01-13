"""
Extruder assignment parameter validation functions
"""

from __future__ import annotations

from pathlib import Path
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
    
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Wall filament: {actual}"},
    )
