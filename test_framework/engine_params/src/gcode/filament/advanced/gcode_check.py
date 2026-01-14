"""
Advanced parameter validation functions.

This module contains parsing and validation functions for advanced filament parameters.
Total: 3 parameters
"""

from pathlib import Path
from typing import Tuple, Dict, Any
from engine_params.src.gcode.GCodeParserEx import GCodeParserEx


def _str_norm(v: Any) -> str | None:
    """Normalize string value, removing surrounding quotes and whitespace."""
    if v is None:
        return None
    s = str(v).strip()
    # Remove surrounding quotes if present (e.g., '""' -> '')
    if len(s) >= 2 and s.startswith('"') and s.endswith('"'):
        s = s[1:-1]
    return s


def parse_filament_start_gcode(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_start_gcode parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_start_gcode")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament start gcode: {actual}"},
    )


def parse_filament_end_gcode(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_end_gcode parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_end_gcode")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament end gcode: {actual}"},
    )


def parse_filament_notes(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_notes parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("filament_notes")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Filament notes: {actual}"},
    )

