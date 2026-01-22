from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple
from functools import lru_cache

from engine_params.src.gcode.GCodeParser import GCodeParser


@lru_cache(maxsize=128)
def _load_gcode_config(gcode_path: Path) -> Dict[str, Any]:
    """Cached config loading to avoid repeated parsing of same file."""
    parser = GCodeParser(gcode_path)
    return parser.load_config()


def _parse_config_value(
    gcode_path: Path,
    key: str,
    expected_value: Any,
) -> Tuple[bool, Any, Dict[str, Any]]:
    """
    Generic config parameter parser for Level 1 - Config parameters.
    
    Args:
        gcode_path: Path to the G-code file
        key: Configuration key to extract
        expected_value: Expected parameter value
        
    Returns:
        Tuple of (validation_passed, actual_value, details)
    """
    cfg = _load_gcode_config(gcode_path)

    actual = cfg.get(key)
    if actual is None and key not in cfg:
        return (
            False,
            None,
            {
                "detection_method": "Level 1 - Config",
                "message": f"Config key '{key}' not found.",
                "raw_data": {"available_keys_sample": list(cfg.keys())[:50]},
            },
        )

    ok = actual == expected_value
    return (
        ok,
        actual,
        {
            "detection_method": "Level 1 - Config",
            "message": f"Config '{key}' expected {expected_value}, got {actual}.",
            "raw_data": {"key": key, "expected": expected_value, "actual": actual},
        },
    )


def parse_nozzle_diameter(gcode_path: Path, expected_value: float):
    return _parse_config_value(gcode_path, "nozzle_diameter", expected_value)


def parse_min_layer_height(gcode_path: Path, expected_value: float):
    return _parse_config_value(gcode_path, "min_layer_height", expected_value)


def parse_max_layer_height(gcode_path: Path, expected_value: float):
    return _parse_config_value(gcode_path, "max_layer_height", expected_value)


def parse_extruder_offset(gcode_path: Path, expected_value: str):
    return _parse_config_value(gcode_path, "extruder_offset", expected_value)


def parse_retraction_length(gcode_path: Path, expected_value: float):
    return _parse_config_value(gcode_path, "retraction_length", expected_value)


def parse_retract_restart_extra(gcode_path: Path, expected_value: float | int):
    return _parse_config_value(gcode_path, "retract_restart_extra", expected_value)


def parse_z_hop(gcode_path: Path, expected_value: float):
    return _parse_config_value(gcode_path, "z_hop", expected_value)


def parse_z_hop_types(gcode_path: Path, expected_value: str):
    return _parse_config_value(gcode_path, "z_hop_types", expected_value)


def parse_travel_slope(gcode_path: Path, expected_value: float | int):
    return _parse_config_value(gcode_path, "travel_slope", expected_value)


def parse_retraction_speed(gcode_path: Path, expected_value: float | int):
    return _parse_config_value(gcode_path, "retraction_speed", expected_value)


def parse_deretraction_speed(gcode_path: Path, expected_value: float | int):
    return _parse_config_value(gcode_path, "deretraction_speed", expected_value)


def parse_retraction_minimum_travel(gcode_path: Path, expected_value: float | int):
    return _parse_config_value(gcode_path, "retraction_minimum_travel", expected_value)


def parse_retract_when_changing_layer(gcode_path: Path, expected_value: int):
    return _parse_config_value(gcode_path, "retract_when_changing_layer", expected_value)


def parse_retract_when_changing_layer_behavior(gcode_path: Path, expected_value: int) -> Tuple[bool, Any, Dict[str, Any]]:
    """Test retract_when_changing_layer G-code behavior (Level 2 - G-code Analysis)"""
    import re
    
    try:
        with open(gcode_path, 'r', encoding='utf-8') as f:
            gcode_content = f.read()
        
        # 查找Z轴移动和回抽的配合模式
        z_moves = list(re.finditer(r'G[01]\s+.*Z([0-9.]+)', gcode_content, re.IGNORECASE))
        
        z_move_retracts = 0
        total_z_moves = 0
        
        for z_match in z_moves:
            z_value = float(z_match.group(1))
            # 检查Z移动前50行内是否有回抽命令
            start_search = max(0, z_match.start() - 1000)
            search_region = gcode_content[start_search:z_match.start()]
            
            # 查找回抽命令
            retract_patterns = [
                r'G1\s+.*E-[0-9.]+',
                r'G10',
                r'G1\s+F[0-9]+\s+E-[0-9.]+'
            ]
            
            found_retract = False
            for pattern in retract_patterns:
                if re.search(pattern, search_region, re.IGNORECASE):
                    found_retract = True
                    break
            
            if found_retract:
                z_move_retracts += 1
            total_z_moves += 1
        
        # 判断行为
        config_enabled = expected_value == 1
        
        if config_enabled:
            behavior_correct = z_move_retracts > total_z_moves * 0.5 if total_z_moves else False
            message = f"Enabled: {z_move_retracts}/{total_z_moves} Z-moves with retraction"
        else:
            behavior_correct = z_move_retracts <= total_z_moves * 0.5 if total_z_moves else True
            message = f"Disabled: {z_move_retracts}/{total_z_moves} Z-moves with retraction"
        
        return (
            behavior_correct,
            f"{z_move_retracts}/{total_z_moves}",
            {
                "detection_method": "Level 2 - G-code Analysis",
                "message": message,
                "raw_data": {
                    "z_moves": total_z_moves,
                    "retract_count": z_move_retracts,
                    "expected_enabled": config_enabled
                }
            }
        )
        
    except Exception as e:
        return (
            False,
            None,
            {
                "detection_method": "Level 2 - G-code Analysis",
                "message": f"G-code analysis failed: {str(e)}",
                "raw_data": {"error": str(e)}
            }
        )


def parse_wipe(gcode_path: Path, expected_value: int):
    return _parse_config_value(gcode_path, "wipe", expected_value)


def parse_wipe_distance(gcode_path: Path, expected_value: float | int):
    return _parse_config_value(gcode_path, "wipe_distance", expected_value)


def parse_retract_before_wipe(gcode_path: Path, expected_value: str):
    return _parse_config_value(gcode_path, "retract_before_wipe", expected_value)


def parse_retract_lift_above(gcode_path: Path, expected_value: float | int):
    return _parse_config_value(gcode_path, "retract_lift_above", expected_value)


def parse_retract_lift_below(gcode_path: Path, expected_value: float | int):
    return _parse_config_value(gcode_path, "retract_lift_below", expected_value)


def parse_retract_lift_enforce(gcode_path: Path, expected_value: str):
    return _parse_config_value(gcode_path, "retract_lift_enforce", expected_value)


def parse_retract_length_toolchange(gcode_path: Path, expected_value: float | int):
    return _parse_config_value(gcode_path, "retract_length_toolchange", expected_value)


def parse_retract_restart_extra_toolchange(gcode_path: Path, expected_value: float | int):
    return _parse_config_value(gcode_path, "retract_restart_extra_toolchange", expected_value)


def parse_long_retractions_when_cut(gcode_path: Path, expected_value: int):
    return _parse_config_value(gcode_path, "long_retractions_when_cut", expected_value)


def parse_retraction_distances_when_cut(gcode_path: Path, expected_value: float | int):
    return _parse_config_value(gcode_path, "retraction_distances_when_cut", expected_value)
