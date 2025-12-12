"""Acceleration limitation group validation for motion_ability page"""

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


def parse_machine_max_acceleration_x(
    gcode_path: Path,
    expected_value: Any,
) -> Tuple[bool, Any, Dict]:
    """
    Level 1 - Config: Validate machine_max_acceleration_x (X axis maximum acceleration)
    
    Returns: (success: bool, actual_value, details: dict)
    """
    try:
        parser = GCodeParser(gcode_path)
        cfg = parser.load_config()
        
        actual = _to_int(cfg.get("machine_max_acceleration_x"))
        expected = _to_int(expected_value)
        
        success = actual == expected
        
        return (
            success,
            actual,
            {
                "detection_method": "Level 1 - Config",
                "message": f"machine_max_acceleration_x: expected {expected} mm/s², got {actual} mm/s²",
                "raw_data": {"config_value": actual},
            },
        )
    except Exception as e:
        return (
            False,
            None,
            {
                "detection_method": "Level 1 - Config",
                "message": f"Error parsing machine_max_acceleration_x: {str(e)}",
                "raw_data": {"error": str(e)},
            },
        )


def parse_machine_max_acceleration_y(
    gcode_path: Path,
    expected_value: Any,
) -> Tuple[bool, Any, Dict]:
    """
    Level 1 - Config: Validate machine_max_acceleration_y (Y axis maximum acceleration)
    
    Returns: (success: bool, actual_value, details: dict)
    """
    try:
        parser = GCodeParser(gcode_path)
        cfg = parser.load_config()
        
        actual = _to_int(cfg.get("machine_max_acceleration_y"))
        expected = _to_int(expected_value)
        
        success = actual == expected
        
        return (
            success,
            actual,
            {
                "detection_method": "Level 1 - Config",
                "message": f"machine_max_acceleration_y: expected {expected} mm/s², got {actual} mm/s²",
                "raw_data": {"config_value": actual},
            },
        )
    except Exception as e:
        return (
            False,
            None,
            {
                "detection_method": "Level 1 - Config",
                "message": f"Error parsing machine_max_acceleration_y: {str(e)}",
                "raw_data": {"error": str(e)},
            },
        )


def parse_machine_max_acceleration_z(
    gcode_path: Path,
    expected_value: Any,
) -> Tuple[bool, Any, Dict]:
    """
    Level 1 - Config: Validate machine_max_acceleration_z (Z axis maximum acceleration)
    
    Returns: (success: bool, actual_value, details: dict)
    """
    try:
        parser = GCodeParser(gcode_path)
        cfg = parser.load_config()
        
        actual = _to_int(cfg.get("machine_max_acceleration_z"))
        expected = _to_int(expected_value)
        
        success = actual == expected
        
        return (
            success,
            actual,
            {
                "detection_method": "Level 1 - Config",
                "message": f"machine_max_acceleration_z: expected {expected} mm/s², got {actual} mm/s²",
                "raw_data": {"config_value": actual},
            },
        )
    except Exception as e:
        return (
            False,
            None,
            {
                "detection_method": "Level 1 - Config",
                "message": f"Error parsing machine_max_acceleration_z: {str(e)}",
                "raw_data": {"error": str(e)},
            },
        )


def parse_machine_max_acceleration_e(
    gcode_path: Path,
    expected_value: Any,
) -> Tuple[bool, Any, Dict]:
    """
    Level 1 - Config: Validate machine_max_acceleration_e (E axis maximum acceleration)
    
    Returns: (success: bool, actual_value, details: dict)
    """
    try:
        parser = GCodeParser(gcode_path)
        cfg = parser.load_config()
        
        actual = _to_int(cfg.get("machine_max_acceleration_e"))
        expected = _to_int(expected_value)
        
        success = actual == expected
        
        return (
            success,
            actual,
            {
                "detection_method": "Level 1 - Config",
                "message": f"machine_max_acceleration_e: expected {expected} mm/s², got {actual} mm/s²",
                "raw_data": {"config_value": actual},
            },
        )
    except Exception as e:
        return (
            False,
            None,
            {
                "detection_method": "Level 1 - Config",
                "message": f"Error parsing machine_max_acceleration_e: {str(e)}",
                "raw_data": {"error": str(e)},
            },
        )


def parse_machine_max_acceleration_extruding(
    gcode_path: Path,
    expected_value: Any,
) -> Tuple[bool, Any, Dict]:
    """
    Level 1 - Config: Validate machine_max_acceleration_extruding (Extruding maximum acceleration)
    
    Returns: (success: bool, actual_value, details: dict)
    """
    try:
        parser = GCodeParser(gcode_path)
        cfg = parser.load_config()
        
        actual = _to_int(cfg.get("machine_max_acceleration_extruding"))
        expected = _to_int(expected_value)
        
        success = actual == expected
        
        return (
            success,
            actual,
            {
                "detection_method": "Level 1 - Config",
                "message": f"machine_max_acceleration_extruding: expected {expected} mm/s², got {actual} mm/s²",
                "raw_data": {"config_value": actual},
            },
        )
    except Exception as e:
        return (
            False,
            None,
            {
                "detection_method": "Level 1 - Config",
                "message": f"Error parsing machine_max_acceleration_extruding: {str(e)}",
                "raw_data": {"error": str(e)},
            },
        )


def parse_machine_max_acceleration_retracting(
    gcode_path: Path,
    expected_value: Any,
) -> Tuple[bool, Any, Dict]:
    """
    Level 1 - Config: Validate machine_max_acceleration_retracting (Retracting maximum acceleration)
    
    Returns: (success: bool, actual_value, details: dict)
    """
    try:
        parser = GCodeParser(gcode_path)
        cfg = parser.load_config()
        
        actual = _to_int(cfg.get("machine_max_acceleration_retracting"))
        expected = _to_int(expected_value)
        
        success = actual == expected
        
        return (
            success,
            actual,
            {
                "detection_method": "Level 1 - Config",
                "message": f"machine_max_acceleration_retracting: expected {expected} mm/s², got {actual} mm/s²",
                "raw_data": {"config_value": actual},
            },
        )
    except Exception as e:
        return (
            False,
            None,
            {
                "detection_method": "Level 1 - Config",
                "message": f"Error parsing machine_max_acceleration_retracting: {str(e)}",
                "raw_data": {"error": str(e)},
            },
        )


def parse_machine_max_acceleration_travel(
    gcode_path: Path,
    expected_value: Any,
) -> Tuple[bool, Any, Dict]:
    """
    Level 1 - Config: Validate machine_max_acceleration_travel (Travel maximum acceleration)
    
    Returns: (success: bool, actual_value, details: dict)
    """
    try:
        parser = GCodeParser(gcode_path)
        cfg = parser.load_config()
        
        actual = _to_int(cfg.get("machine_max_acceleration_travel"))
        expected = _to_int(expected_value)
        
        success = actual == expected
        
        return (
            success,
            actual,
            {
                "detection_method": "Level 1 - Config",
                "message": f"machine_max_acceleration_travel: expected {expected} mm/s², got {actual} mm/s²",
                "raw_data": {"config_value": actual},
            },
        )
    except Exception as e:
        return (
            False,
            None,
            {
                "detection_method": "Level 1 - Config",
                "message": f"Error parsing machine_max_acceleration_travel: {str(e)}",
                "raw_data": {"error": str(e)},
            },
        )
