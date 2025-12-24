"""
Support parameter validation functions.

This module contains parsing and validation functions for support-related parameters.
"""

from pathlib import Path
from typing import Tuple, Dict, Any, List
import re
from engine_params.src.gcode.GCodeParser import GCodeParser
from engine_params.src.gcode.constants import ExtrusionType


def _to_int_maybe(v: Any) -> int | None:
    try:
        return int(str(v).strip())
    except Exception:
        return None


def _to_float_maybe(v: Any) -> float | None:
    try:
        s = str(v).strip()
        if s.endswith("%"):
            s = s[:-1]
        return float(s)
    except Exception:
        return None


def _str_norm(v: Any) -> str | None:
    if v is None:
        return None
    return str(v).strip()


def parse_enable_support(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """
    Test enable_support parameter (Level 2 - Feature Detection)
    
    Verification: Detect ;TYPE:Support or ;TYPE:Support interface markers
    """
    parser = GCodeParser(gcode_path)
    # Handle both string and int types for expected_value
    if isinstance(expected_value, bool):
        expected = expected_value
    elif isinstance(expected_value, int):
        expected = expected_value != 0
    else:
        expected = str(expected_value).lower() in ["true", "1", "yes"]
    
    # Check for support markers
    support_blocks = parser.get_extrusion_blocks_per_layer(ExtrusionType.SUPPORT.value)
    support_present = any(blocks for blocks in support_blocks if blocks)
    
    # Also check for support interface
    interface_blocks = parser.get_extrusion_blocks_per_layer(ExtrusionType.SUPPORT_INTERFACE.value)
    interface_present = any(blocks for blocks in interface_blocks if blocks)
    
    actual = support_present or interface_present
    
    return (
        actual == expected,
        actual,
        {
            "detection_method": "Level 2 - Feature Detection",
            "message": f"Support markers {'found' if actual else 'not found'} in G-code",
            "support_present": support_present,
            "interface_present": interface_present,
        }
    )


def parse_support_type(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """
    Test support_type parameter (Level 1 - Config)
    
    Values: stNormal/stNormalAuto/stTree/stTreeAuto/stNormalManual/stTreeManual
    """
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("support_type")
    
    return (
        actual == expected_value,
        actual,
        {
            "detection_method": "Level 1 - Config",
            "message": f"Support type from config: {actual}",
        }
    )


def parse_support_style(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """
    Test support_style parameter (Level 1 - Config)
    
    Values: smsDefault/smsGrid/smsSnug/smsTreeSlim/smsTreeStrong/smsTreeHybrid/smsTreeOrganic
    """
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("support_style")
    
    return (
        actual == expected_value,
        actual,
        {
            "detection_method": "Level 1 - Config",
            "message": f"Support style from config: {actual}",
        }
    )


def parse_support_threshold_angle(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """
    Test support_threshold_angle parameter (Level 1 - Config)
    
    Default: 30 degrees
    """
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("support_threshold_angle")
    
    try:
        expected = float(expected_value)
        actual_float = float(actual) if actual is not None else None
        match = abs(actual_float - expected) < 0.1 if actual_float is not None else False
    except (ValueError, TypeError):
        match = str(actual) == str(expected_value)
        expected = expected_value
    
    return (
        match,
        actual,
        {
            "detection_method": "Level 1 - Config",
            "message": f"Support threshold angle: {actual}°",
            "expected": expected,
        }
    )


def parse_support_on_build_plate_only(gcode_path: Path, expected_value) -> Tuple[bool, Any, Dict]:
    """
    Test support_on_build_plate_only parameter (Level 1 - Config)
    
    Verification: Read from G-code config block
    """
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("support_on_build_plate_only")
    
    # Normalize expected value to int for comparison
    if isinstance(expected_value, bool):
        expected_int = 1 if expected_value else 0
    elif isinstance(expected_value, int):
        expected_int = expected_value
    else:
        expected_int = 1 if str(expected_value).lower() in ["true", "1", "yes"] else 0
    
    actual_int = _to_int_maybe(actual)
    if actual_int is not None:
        match = actual_int == expected_int
    else:
        match = _str_norm(actual) == _str_norm(expected_value)
    
    return (
        match,
        actual,
        {
            "detection_method": "Level 1 - Config",
            "message": f"Support on build plate only: {actual}",
        }
    )


def parse_support_critical_regions_only(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """
    Test support_critical_regions_only parameter (Level 2 - Feature Detection)
    
    Verification: Check if support volume is minimal (only critical areas)
    """
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual_cfg = cfg.get("support_critical_regions_only")
    
    # Convert to int for comparison (G-code uses 0/1)
    actual_value = int(actual_cfg) if actual_cfg is not None else None
    expected_int = int(expected_value) if isinstance(expected_value, (str, int)) else expected_value
    
    return (
        actual_value == expected_int,
        actual_value,
        {
            "detection_method": "Level 1 - Config",
            "message": f"Support critical regions only: {actual_value}",
        }
    )


def parse_support_remove_small_overhang(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """
    Test support_remove_small_overhang parameter (Level 1 - Config)
    """
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual_cfg = cfg.get("support_remove_small_overhang")
    
    # Convert to int for comparison (G-code uses 0/1)
    actual_value = int(actual_cfg) if actual_cfg is not None else None
    expected_int = int(expected_value) if isinstance(expected_value, (str, int)) else expected_value
    
    return (
        actual_value == expected_int,
        actual_value,
        {
            "detection_method": "Level 1 - Config",
            "message": f"Remove small overhang: {actual_value}",
        }
    )


def parse_raft_layers(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """
    Test raft_layers parameter (Level 2 - Layer Counting)
    
    Verification: Count support layers below model's first layer
    """
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    
    try:
        expected = int(expected_value)
    except (TypeError, ValueError):
        expected = 0
    
    # Try to get from config first
    cfg_value = cfg.get("raft_layers")
    if cfg_value is not None:
        try:
            actual = int(cfg_value)
        except ValueError:
            actual = 0
    else:
        # Count layers below first model layer
        layer_height = float(cfg.get("layer_height", "0.2"))
        support_blocks = parser.get_extrusion_blocks_per_layer(ExtrusionType.SUPPORT.value)
        
        actual = 0
        for layer_idx, blocks in enumerate(support_blocks):
            z_value = parser.get_layer_z_values()[layer_idx] if layer_idx < len(parser.get_layer_z_values()) else layer_height * (layer_idx + 1)
            if z_value < layer_height and blocks:
                actual += 1
    
    return (
        actual == expected,
        actual,
        {
            "detection_method": "Level 2 - Layer Counting",
            "message": f"Raft layers: {actual}",
            "expected": expected,
        }
    )


def parse_raft_contact_distance(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """
    Test raft_contact_distance parameter (Level 1 - Config)
    """
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("raft_contact_distance")
    
    try:
        expected = float(expected_value)
        actual_float = float(actual) if actual is not None else None
        match = abs(actual_float - expected) < 0.01 if actual_float is not None else False
    except (ValueError, TypeError):
        match = str(actual) == str(expected_value)
        expected = expected_value
    
    return (
        match,
        actual,
        {
            "detection_method": "Level 1 - Config",
            "message": f"Raft contact distance: {actual}mm",
        }
    )


def parse_raft_first_layer_density(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Test raft_first_layer_density parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("raft_first_layer_density")
    match = _str_norm(actual) == _str_norm(expected_value)
    return (
        match,
        actual,
        {
            "detection_method": "Level 1 - Config",
            "message": f"Raft first layer density: {actual}",
        },
    )


def parse_raft_first_layer_expansion(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Test raft_first_layer_expansion parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("raft_first_layer_expansion")
    expected_f = _to_float_maybe(expected_value)
    actual_f = _to_float_maybe(actual)
    if expected_f is not None and actual_f is not None:
        match = abs(actual_f - expected_f) < 0.01
    else:
        match = _str_norm(actual) == _str_norm(expected_value)
    return (
        match,
        actual,
        {
            "detection_method": "Level 1 - Config",
            "message": f"Raft first layer expansion: {actual}",
        },
    )


def parse_support_top_z_distance(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Test support_top_z_distance parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("support_top_z_distance")
    expected_f = _to_float_maybe(expected_value)
    actual_f = _to_float_maybe(actual)
    if expected_f is not None and actual_f is not None:
        match = abs(actual_f - expected_f) < 0.01
    else:
        match = _str_norm(actual) == _str_norm(expected_value)
    return (
        match,
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Support top Z distance: {actual}"},
    )


def parse_support_bottom_z_distance(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Test support_bottom_z_distance parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("support_bottom_z_distance")
    expected_f = _to_float_maybe(expected_value)
    actual_f = _to_float_maybe(actual)
    if expected_f is not None and actual_f is not None:
        match = abs(actual_f - expected_f) < 0.01
    else:
        match = _str_norm(actual) == _str_norm(expected_value)
    return (
        match,
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Support bottom Z distance: {actual}"},
    )


def parse_support_base_pattern(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Test support_base_pattern parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("support_base_pattern")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Support base pattern: {actual}"},
    )


def parse_support_base_pattern_tree(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Test support_base_pattern_tree parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("support_base_pattern_tree")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Support base pattern tree: {actual}"},
    )


def parse_support_base_pattern_spacing(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Test support_base_pattern_spacing parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("support_base_pattern_spacing")
    expected_f = _to_float_maybe(expected_value)
    actual_f = _to_float_maybe(actual)
    if expected_f is not None and actual_f is not None:
        match = abs(actual_f - expected_f) < 0.01
    else:
        match = _str_norm(actual) == _str_norm(expected_value)
    return (
        match,
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Support base pattern spacing: {actual}"},
    )


def parse_support_angle(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Test support_angle parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("support_angle")
    expected_f = _to_float_maybe(expected_value)
    actual_f = _to_float_maybe(actual)
    if expected_f is not None and actual_f is not None:
        match = abs(actual_f - expected_f) < 0.01
    else:
        match = _str_norm(actual) == _str_norm(expected_value)
    return (
        match,
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Support angle: {actual}"},
    )


def parse_support_expansion(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Test support_expansion parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("support_expansion")
    expected_f = _to_float_maybe(expected_value)
    actual_f = _to_float_maybe(actual)
    if expected_f is not None and actual_f is not None:
        match = abs(actual_f - expected_f) < 0.01
    else:
        match = _str_norm(actual) == _str_norm(expected_value)
    return (
        match,
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Support expansion: {actual}"},
    )


def parse_support_object_xy_distance(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Test support_object_xy_distance parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("support_object_xy_distance")
    expected_f = _to_float_maybe(expected_value)
    actual_f = _to_float_maybe(actual)
    if expected_f is not None and actual_f is not None:
        match = abs(actual_f - expected_f) < 0.01
    else:
        match = _str_norm(actual) == _str_norm(expected_value)
    return (
        match,
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Support object XY distance: {actual}"},
    )


def parse_support_object_first_layer_gap(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Test support_object_first_layer_gap parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("support_object_first_layer_gap")
    expected_f = _to_float_maybe(expected_value)
    actual_f = _to_float_maybe(actual)
    if expected_f is not None and actual_f is not None:
        match = abs(actual_f - expected_f) < 0.01
    else:
        match = _str_norm(actual) == _str_norm(expected_value)
    return (
        match,
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Support object first layer gap: {actual}"},
    )


def parse_support_xy_overrides_z(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Test support_xy_overrides_z parameter (Level 1 - Config)

    Note: G-code may serialize this as a string like `xy_overrides_z`.
    """
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("support_xy_overrides_z")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Support XY overrides Z: {actual}"},
    )


def parse_bridge_no_support(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Test bridge_no_support parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("bridge_no_support")
    ai = _to_int_maybe(actual)
    ei = _to_int_maybe(expected_value)
    if ai is not None and ei is not None:
        match = ai == ei
    else:
        match = _str_norm(actual) == _str_norm(expected_value)
    return (
        match,
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Bridge no support: {actual}"},
    )


def parse_max_bridge_length(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Test max_bridge_length parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("max_bridge_length")
    expected_f = _to_float_maybe(expected_value)
    actual_f = _to_float_maybe(actual)
    if expected_f is not None and actual_f is not None:
        match = abs(actual_f - expected_f) < 0.01
    else:
        match = _str_norm(actual) == _str_norm(expected_value)
    return (
        match,
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Max bridge length: {actual}"},
    )


def parse_independent_support_layer_height(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Test independent_support_layer_height parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("independent_support_layer_height")
    ai = _to_int_maybe(actual)
    ei = _to_int_maybe(expected_value)
    if ai is not None and ei is not None:
        match = ai == ei
    else:
        match = _str_norm(actual) == _str_norm(expected_value)
    return (
        match,
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Independent support layer height: {actual}"},
    )


def parse_ironing_support_layer(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Test ironing_support_layer parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("ironing_support_layer")
    ai = _to_int_maybe(actual)
    ei = _to_int_maybe(expected_value)
    if ai is not None and ei is not None:
        match = ai == ei
    else:
        match = _str_norm(actual) == _str_norm(expected_value)
    return (
        match,
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Ironing support layer: {actual}"},
    )


def parse_tree_hybrid_cross_height(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Test tree_hybrid_cross_height parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("tree_hybrid_cross_height")
    expected_f = _to_float_maybe(expected_value)
    actual_f = _to_float_maybe(actual)
    if expected_f is not None and actual_f is not None:
        match = abs(actual_f - expected_f) < 0.01
    else:
        match = _str_norm(actual) == _str_norm(expected_value)
    return (
        match,
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Tree hybrid cross height: {actual}"},
    )


def parse_support_line_width(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Test support_line_width parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("support_line_width")
    expected_f = _to_float_maybe(expected_value)
    actual_f = _to_float_maybe(actual)
    if expected_f is not None and actual_f is not None:
        match = abs(actual_f - expected_f) < 0.01
    else:
        match = _str_norm(actual) == _str_norm(expected_value)
    return (
        match,
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Support line width: {actual}"},
    )


def parse_support_speed(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Test support_speed parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("support_speed")
    expected_f = _to_float_maybe(expected_value)
    actual_f = _to_float_maybe(actual)
    if expected_f is not None and actual_f is not None:
        match = abs(actual_f - expected_f) < 0.01
    else:
        match = _str_norm(actual) == _str_norm(expected_value)
    return (
        match,
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Support speed: {actual}"},
    )


def parse_minimum_support_area(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Test minimum_support_area parameter (Level 1 - Config)"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("minimum_support_area")
    expected_f = _to_float_maybe(expected_value)
    actual_f = _to_float_maybe(actual)
    if expected_f is not None and actual_f is not None:
        match = abs(actual_f - expected_f) < 0.01
    else:
        match = _str_norm(actual) == _str_norm(expected_value)
    return (
        match,
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Minimum support area: {actual}"},
    )


def parse_support_material_interface_fan_speed(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Test support_material_interface_fan_speed parameter (Level 1 - Config)

    Note: serialized as a comma-separated list (e.g. "-1,-1").
    """
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("support_material_interface_fan_speed")
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Support material interface fan speed: {actual}"},
    )


def parse_support_filament(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """
    Test support_filament parameter (Level 1 - Config)
    
    Note: This parameter only has effect on multi-extruder printers.
    For single-extruder, it's stored in config but actual printing uses T0.
    """
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("support_filament")
    
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Support filament: {actual}"},
    )


def parse_support_interface_filament(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """
    Test support_interface_filament parameter (Level 1 - Config)
    
    Note: This parameter only has effect on multi-extruder printers.
    """
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("support_interface_filament")
    
    return (
        _str_norm(actual) == _str_norm(expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"Support interface filament: {actual}"},
    )


def parse_support_interface_not_for_body(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """
    Test support_interface_not_for_body parameter (Level 1 - Config)
    """
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual_cfg = cfg.get("support_interface_not_for_body")
    
    # Convert to int for comparison (G-code uses 0/1)
    actual_value = int(actual_cfg) if actual_cfg is not None else None
    expected_int = int(expected_value) if isinstance(expected_value, (str, int)) else expected_value
    
    return (
        actual_value == expected_int,
        actual_value,
        {
            "detection_method": "Level 1 - Config",
            "message": f"Support interface not for body: {actual_value}",
        }
    )


def parse_support_interface_top_layers(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """
    Test support_interface_top_layers parameter (Level 1 - Config)
    """
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("support_interface_top_layers")
    
    try:
        expected = int(expected_value)
        actual_int = int(actual) if actual is not None else None
        match = actual_int == expected if actual_int is not None else False
    except (ValueError, TypeError):
        match = str(actual) == str(expected_value)
        expected = expected_value
    
    return (
        match,
        actual,
        {
            "detection_method": "Level 1 - Config",
            "message": f"Support interface top layers: {actual}",
        }
    )


def parse_support_interface_bottom_layers(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """
    Test support_interface_bottom_layers parameter (Level 1 - Config)
    """
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("support_interface_bottom_layers")
    
    try:
        expected = int(expected_value)
        actual_int = int(actual) if actual is not None else None
        match = actual_int == expected if actual_int is not None else False
    except (ValueError, TypeError):
        match = str(actual) == str(expected_value)
        expected = expected_value
    
    return (
        match,
        actual,
        {
            "detection_method": "Level 1 - Config",
            "message": f"Support interface bottom layers: {actual}",
        }
    )


def parse_support_interface_pattern(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """
    Test support_interface_pattern parameter (Level 1 - Config)
    
    Values: smipRectilinear/smipConcentric/smipGrid/smipRectilinearInterlaced/smipMonotonicLine/smipAuto
    """
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("support_interface_pattern")
    
    return (
        actual == expected_value,
        actual,
        {
            "detection_method": "Level 1 - Config",
            "message": f"Support interface pattern: {actual}",
        }
    )


def parse_support_interface_spacing(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """
    Test support_interface_spacing parameter (Level 1 - Config)
    """
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("support_interface_spacing")
    
    try:
        expected = float(expected_value)
        actual_float = float(actual) if actual is not None else None
        match = abs(actual_float - expected) < 0.01 if actual_float is not None else False
    except (ValueError, TypeError):
        match = str(actual) == str(expected_value)
        expected = expected_value
    
    return (
        match,
        actual,
        {
            "detection_method": "Level 1 - Config",
            "message": f"Support interface spacing: {actual}mm",
        }
    )


def parse_support_bottom_interface_spacing(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """
    Test support_bottom_interface_spacing parameter (Level 1 - Config)
    """
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("support_bottom_interface_spacing")
    
    try:
        expected = float(expected_value)
        actual_float = float(actual) if actual is not None else None
        match = abs(actual_float - expected) < 0.01 if actual_float is not None else False
    except (ValueError, TypeError):
        match = str(actual) == str(expected_value)
        expected = expected_value
    
    return (
        match,
        actual,
        {
            "detection_method": "Level 1 - Config",
            "message": f"Support interface bottom spacing: {actual}mm",
        }
    )


def parse_support_interface_loop_pattern(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """
    Test support_interface_loop_pattern parameter (Level 1 - Config)
    """
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual_cfg = cfg.get("support_interface_loop_pattern")
    
    # Convert to int for comparison (G-code uses 0/1)
    actual_value = int(actual_cfg) if actual_cfg is not None else None
    expected_int = int(expected_value) if isinstance(expected_value, (str, int)) else expected_value
    
    return (
        actual_value == expected_int,
        actual_value,
        {
            "detection_method": "Level 1 - Config",
            "message": f"Support interface loop pattern: {actual_value}",
        }
    )


def parse_support_interface_speed(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """
    Test support_interface_speed parameter (Level 1 - Config)
    """
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("support_interface_speed")
    
    try:
        expected = float(expected_value)
        actual_float = float(actual) if actual is not None else None
        match = abs(actual_float - expected) < 0.1 if actual_float is not None else False
    except (ValueError, TypeError):
        match = str(actual) == str(expected_value)
        expected = expected_value
    
    return (
        match,
        actual,
        {
            "detection_method": "Level 1 - Config",
            "message": f"Support interface speed: {actual}mm/s",
        }
    )


def parse_support_interface_min_area(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """
    Test support_interface_min_area parameter (Level 1 - Config)
    """
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("support_interface_min_area")
    
    try:
        expected = float(expected_value)
        actual_float = float(actual) if actual is not None else None
        match = abs(actual_float - expected) < 0.1 if actual_float is not None else False
    except (ValueError, TypeError):
        match = str(actual) == str(expected_value)
        expected = expected_value
    
    return (
        match,
        actual,
        {
            "detection_method": "Level 1 - Config",
            "message": f"Support interface min area: {actual}mm²",
        }
    )


def parse_tree_support_branch_diameter(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """
    Test tree_support_branch_diameter parameter (Level 1 - Config)
    """
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("tree_support_branch_diameter")
    
    try:
        expected = float(expected_value)
        actual_float = float(actual) if actual is not None else None
        match = abs(actual_float - expected) < 0.01 if actual_float is not None else False
    except (ValueError, TypeError):
        match = str(actual) == str(expected_value)
        expected = expected_value
    
    return (
        match,
        actual,
        {
            "detection_method": "Level 1 - Config",
            "message": f"Tree support branch diameter: {actual}mm",
        }
    )


def parse_tree_support_branch_angle(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """
    Test tree_support_branch_angle parameter (Level 1 - Config)
    """
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("tree_support_branch_angle")
    
    try:
        expected = float(expected_value)
        actual_float = float(actual) if actual is not None else None
        match = abs(actual_float - expected) < 0.1 if actual_float is not None else False
    except (ValueError, TypeError):
        match = str(actual) == str(expected_value)
        expected = expected_value
    
    return (
        match,
        actual,
        {
            "detection_method": "Level 1 - Config",
            "message": f"Tree support branch angle: {actual}°",
        }
    )


def parse_tree_support_wall_count(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """
    Test tree_support_wall_count parameter (Level 1 - Config)
    """
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("tree_support_wall_count")
    
    try:
        expected = int(expected_value)
        actual_int = int(actual) if actual is not None else None
        match = actual_int == expected if actual_int is not None else False
    except (ValueError, TypeError):
        match = str(actual) == str(expected_value)
        expected = expected_value
    
    return (
        match,
        actual,
        {
            "detection_method": "Level 1 - Config",
            "message": f"Tree support wall count: {actual}",
        }
    )


def parse_tree_support_branch_distance(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """
    Test tree_support_branch_distance parameter (Level 1 - Config)
    """
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("tree_support_branch_distance")
    
    try:
        expected = float(expected_value)
        actual_float = float(actual) if actual is not None else None
        match = abs(actual_float - expected) < 0.01 if actual_float is not None else False
    except (ValueError, TypeError):
        match = str(actual) == str(expected_value)
        expected = expected_value
    
    return (
        match,
        actual,
        {
            "detection_method": "Level 1 - Config",
            "message": f"Tree support branch distance: {actual}mm",
        }
    )


def parse_tree_support_wall_count_tree(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """
    Test tree_support_wall_count_tree parameter (Level 1 - Config)
    树状支撑的外壁圈数
    """
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("tree_support_wall_count_tree")
    
    try:
        expected = int(expected_value)
        actual_int = int(actual) if actual is not None else None
        match = actual_int == expected if actual_int is not None else False
    except (ValueError, TypeError):
        match = str(actual) == str(expected_value)
        expected = expected_value
    
    return (
        match,
        actual,
        {
            "detection_method": "Level 1 - Config",
            "message": f"Tree support wall count (tree mode): {actual}",
        }
    )


def parse_tree_support_tip_diameter(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """
    Test tree_support_tip_diameter parameter (Level 1 - Config)
    """
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    actual = cfg.get("tree_support_tip_diameter")
    
    try:
        expected = float(expected_value)
        actual_float = float(actual) if actual is not None else None
        match = abs(actual_float - expected) < 0.01 if actual_float is not None else False
    except (ValueError, TypeError):
        match = str(actual) == str(expected_value)
        expected = expected_value
    
    return (
        match,
        actual,
        {
            "detection_method": "Level 1 - Config",
            "message": f"Tree support tip diameter: {actual}mm",
        }
    )
