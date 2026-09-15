"""Jerk limitation group validation for motion_ability page"""

from pathlib import Path
from typing import Tuple, Any, Dict

from engine_params.src.gcode.printer.motion_ability.motion_config import parse_motion_limit


def parse_machine_max_jerk_x(
    gcode_path: Path,
    expected_value: Any,
) -> Tuple[bool, Any, Dict]:
    """Validate machine_max_jerk_x for the first nozzle in Normal mode."""
    return parse_motion_limit(gcode_path, expected_value, "machine_max_jerk_x", "mm/s")


def parse_machine_max_jerk_y(
    gcode_path: Path,
    expected_value: Any,
) -> Tuple[bool, Any, Dict]:
    """Validate machine_max_jerk_y for the first nozzle in Normal mode."""
    return parse_motion_limit(gcode_path, expected_value, "machine_max_jerk_y", "mm/s")


def parse_machine_max_jerk_z(
    gcode_path: Path,
    expected_value: Any,
) -> Tuple[bool, Any, Dict]:
    """Validate machine_max_jerk_z for the first nozzle in Normal mode."""
    return parse_motion_limit(gcode_path, expected_value, "machine_max_jerk_z", "mm/s")


def parse_machine_max_jerk_e(
    gcode_path: Path,
    expected_value: Any,
) -> Tuple[bool, Any, Dict]:
    """Validate machine_max_jerk_e for the first nozzle in Normal mode."""
    return parse_motion_limit(gcode_path, expected_value, "machine_max_jerk_e", "mm/s")
