"""Acceleration limitation group validation for motion_ability page"""

from pathlib import Path
from typing import Tuple, Any, Dict

from engine_params.src.gcode.printer.motion_ability.motion_config import parse_motion_limit


def parse_machine_max_acceleration_x(
    gcode_path: Path,
    expected_value: Any,
) -> Tuple[bool, Any, Dict]:
    """Validate machine_max_acceleration_x for the first nozzle in Normal mode."""
    return parse_motion_limit(gcode_path, expected_value, "machine_max_acceleration_x", "mm/s²")


def parse_machine_max_acceleration_y(
    gcode_path: Path,
    expected_value: Any,
) -> Tuple[bool, Any, Dict]:
    """Validate machine_max_acceleration_y for the first nozzle in Normal mode."""
    return parse_motion_limit(gcode_path, expected_value, "machine_max_acceleration_y", "mm/s²")


def parse_machine_max_acceleration_z(
    gcode_path: Path,
    expected_value: Any,
) -> Tuple[bool, Any, Dict]:
    """Validate machine_max_acceleration_z for the first nozzle in Normal mode."""
    return parse_motion_limit(gcode_path, expected_value, "machine_max_acceleration_z", "mm/s²")


def parse_machine_max_acceleration_e(
    gcode_path: Path,
    expected_value: Any,
) -> Tuple[bool, Any, Dict]:
    """Validate machine_max_acceleration_e for the first nozzle in Normal mode."""
    return parse_motion_limit(gcode_path, expected_value, "machine_max_acceleration_e", "mm/s²")


def parse_machine_max_acceleration_extruding(
    gcode_path: Path,
    expected_value: Any,
) -> Tuple[bool, Any, Dict]:
    """Validate machine_max_acceleration_extruding for the first nozzle in Normal mode."""
    return parse_motion_limit(gcode_path, expected_value, "machine_max_acceleration_extruding", "mm/s²")


def parse_machine_max_acceleration_retracting(
    gcode_path: Path,
    expected_value: Any,
) -> Tuple[bool, Any, Dict]:
    """Validate machine_max_acceleration_retracting for the first nozzle in Normal mode."""
    return parse_motion_limit(gcode_path, expected_value, "machine_max_acceleration_retracting", "mm/s²")


def parse_machine_max_acceleration_travel(
    gcode_path: Path,
    expected_value: Any,
) -> Tuple[bool, Any, Dict]:
    """Validate machine_max_acceleration_travel for the first nozzle in Normal mode."""
    return parse_motion_limit(gcode_path, expected_value, "machine_max_acceleration_travel", "mm/s²")
