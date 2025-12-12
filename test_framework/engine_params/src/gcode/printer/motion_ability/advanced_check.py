"""Advanced group validation for motion_ability page"""

from pathlib import Path
from typing import Tuple, Any, Dict
from engine_params.src.gcode.GCodeParser import GCodeParser


def _to_int(value: Any) -> int:
    """Convert value to int safely"""
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value.strip())
        except (ValueError, AttributeError):
            return None
    return None


def parse_emit_machine_limits_to_gcode(
    gcode_path: Path,
    expected_value: Any,
) -> Tuple[bool, Any, Dict]:
    """
    Level 1 - Config: Validate emit_machine_limits_to_gcode
    
    Returns: (success: bool, actual_value, details: dict)
    """
    try:
        parser = GCodeParser(gcode_path)
        cfg = parser.load_config()
        
        actual = _to_int(cfg.get("emit_machine_limits_to_gcode"))
        expected = _to_int(expected_value)
        
        success = actual == expected
        
        return (
            success,
            actual,
            {
                "detection_method": "Level 1 - Config",
                "message": f"emit_machine_limits_to_gcode: expected {expected}, got {actual}",
                "raw_data": {"config_value": actual},
            },
        )
    except Exception as e:
        return (
            False,
            None,
            {
                "detection_method": "Level 1 - Config",
                "message": f"Error parsing emit_machine_limits_to_gcode: {str(e)}",
                "raw_data": {"error": str(e)},
            },
        )
