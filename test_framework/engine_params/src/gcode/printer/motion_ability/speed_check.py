"""Speed limitation group validation for motion_ability page"""

from pathlib import Path
from typing import Tuple, Any, Dict

from engine_params.src.gcode.printer.motion_ability.motion_config import parse_motion_limit


def parse_machine_max_speed_x(
    gcode_path: Path,
    expected_value: Any,
) -> Tuple[bool, Any, Dict]:
    """Validate machine_max_speed_x for the first nozzle in Normal mode."""
    return parse_motion_limit(gcode_path, expected_value, "machine_max_speed_x", "mm/s")


def parse_machine_max_speed_y(
    gcode_path: Path,
    expected_value: Any,
) -> Tuple[bool, Any, Dict]:
    """Validate machine_max_speed_y for the first nozzle in Normal mode."""
    return parse_motion_limit(gcode_path, expected_value, "machine_max_speed_y", "mm/s")


def parse_machine_max_speed_z(
    gcode_path: Path,
    expected_value: Any,
) -> Tuple[bool, Any, Dict]:
    """Validate machine_max_speed_z for the first nozzle in Normal mode."""
    return parse_motion_limit(gcode_path, expected_value, "machine_max_speed_z", "mm/s")


def parse_machine_max_speed_e(
    gcode_path: Path,
    expected_value: Any,
) -> Tuple[bool, Any, Dict]:
    """Validate machine_max_speed_e for the first nozzle in Normal mode."""
    return parse_motion_limit(gcode_path, expected_value, "machine_max_speed_e", "mm/s")
