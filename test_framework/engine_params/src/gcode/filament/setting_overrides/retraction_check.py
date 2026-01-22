"""
Setting Overrides parameter validation functions.

This module contains parsing and validation functions for filament setting overrides.
Total: 16 parameters
"""

from pathlib import Path
from typing import Tuple, Dict, Any
from functools import lru_cache
from engine_params.src.gcode.GCodeParserEx import GCodeParserEx

# Alias for backward compatibility
GCodeParser = GCodeParserEx


def _str_norm(v: Any) -> str | None:
    """Normalize value for comparison. Treats None and 'nil' as equivalent."""
    if v is None:
        return None
    s = str(v).strip()
    # Treat 'nil' as None for comparison
    if s.lower() == 'nil':
        return None
    return s


def _values_equal(actual: Any, expected: Any) -> bool:
    """Compare values, treating None and 'nil' as equivalent."""
    norm_actual = _str_norm(actual)
    norm_expected = _str_norm(expected)
    return norm_actual == norm_expected


@lru_cache(maxsize=128)
def _load_gcode_config(gcode_path: Path) -> Dict[str, Any]:
    """Cached config loading to avoid repeated parsing of same file."""
    parser = GCodeParser(gcode_path)
    return parser.load_config()


def _parse_config_parameter(gcode_path: Path, param_name: str, expected_value: str, 
                          display_name: str = None) -> Tuple[bool, Any, Dict]:
    """
    Generic config parameter parser for Level 1 - Config parameters.
    
    Args:
        gcode_path: Path to the G-code file
        param_name: Parameter name to extract from config
        expected_value: Expected parameter value
        display_name: Human-readable parameter name for messages
    
    Returns:
        Tuple of (validation_passed, actual_value, details)
    """
    cfg = _load_gcode_config(gcode_path)
    actual = cfg.get(param_name)
    display = display_name or param_name.replace('_', ' ').title()
    
    return (
        _values_equal(actual.value, expected_value),
        actual,
        {"detection_method": "Level 1 - Config", "message": f"{display}: {actual}"},
    )


# Optimized parameter parsing functions using the generic helper
def parse_filament_retraction_length(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_retraction_length parameter (Level 1 - Config)"""
    return _parse_config_parameter(gcode_path, "filament_retraction_length", expected_value, 
                                 "Filament retraction length")


def parse_filament_z_hop(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_z_hop parameter (Level 1 - Config)"""
    return _parse_config_parameter(gcode_path, "filament_z_hop", expected_value, 
                                 "Filament Z hop")


def parse_filament_z_hop_types(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_z_hop_types parameter (Level 1 - Config)"""
    return _parse_config_parameter(gcode_path, "filament_z_hop_types", expected_value, 
                                 "Filament Z hop types")


def parse_filament_retract_lift_above(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_retract_lift_above parameter (Level 1 - Config)"""
    return _parse_config_parameter(gcode_path, "filament_retract_lift_above", expected_value, 
                                 "Filament retract lift above")


def parse_filament_retract_lift_below(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_retract_lift_below parameter (Level 1 - Config)"""
    return _parse_config_parameter(gcode_path, "filament_retract_lift_below", expected_value, 
                                 "Filament retract lift below")


def parse_filament_retract_lift_enforce(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_retract_lift_enforce parameter (Level 1 - Config)"""
    return _parse_config_parameter(gcode_path, "filament_retract_lift_enforce", expected_value, 
                                 "Filament retract lift enforce")


def parse_filament_retraction_speed(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_retraction_speed parameter (Level 1 - Config)"""
    return _parse_config_parameter(gcode_path, "filament_retraction_speed", expected_value, 
                                 "Filament retraction speed")


def parse_filament_deretraction_speed(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_deretraction_speed parameter (Level 1 - Config)"""
    return _parse_config_parameter(gcode_path, "filament_deretraction_speed", expected_value, 
                                 "Filament deretraction speed")


def parse_filament_retract_restart_extra(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_retract_restart_extra parameter (Level 1 - Config)"""
    return _parse_config_parameter(gcode_path, "filament_retract_restart_extra", expected_value, 
                                 "Filament retract restart extra")


def parse_filament_retraction_minimum_travel(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_retraction_minimum_travel parameter (Level 1 - Config)"""
    return _parse_config_parameter(gcode_path, "filament_retraction_minimum_travel", expected_value, 
                                 "Filament retraction minimum travel")


def parse_filament_retract_when_changing_layer(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """
    Test filament_retract_when_changing_layer parameter (Level 1 - Config)
    
    基于C3D源码分析的参数覆盖机制:
    - filament_retract_when_changing_layer (ConfigOptionBoolsNullable) 覆盖 retract_when_changing_layer (ConfigOptionBools)
    - EXTRUDER_CONFIG(retract_when_changing_layer) 最终调用覆盖后的配置
    - G-code中显示 retract_when_changing_layer=1，但实际值可能来自filament覆盖
    """
    cfg = _load_gcode_config(gcode_path)
    
    # 检查filament级别的覆盖参数 (ConfigOptionBoolsNullable - 可覆盖)
    filament_override = cfg.get("filament_retract_when_changing_layer")
    # 检查printer级别的基础参数 (ConfigOptionBools - 被覆盖)
    printer_base = cfg.get("retract_when_changing_layer")
    
    # 标准化值处理函数
    def normalize_value(val):
        if val is None:
            return None
        if hasattr(val, 'value'):
            val = val.value
        if isinstance(val, str):
            if val.lower() == 'true':
                return 1
            elif val.lower() == 'false':
                return 0
        try:
            return int(val)
        except (ValueError, TypeError):
            return val
    
    filament_normalized = normalize_value(filament_override)
    printer_normalized = normalize_value(printer_base)
    
    # 根据C3D覆盖机制确定最终有效值
    # nullable配置(filament)存在且有效时覆盖非nullable配置(printer)
    if filament_normalized is not None:
        effective_value = filament_normalized
        param_source = "filament_retract_when_changing_layer (override applied)"
        override_detected = True
    else:
        effective_value = printer_normalized
        param_source = "retract_when_changing_layer (printer default)"
        override_detected = False
    
    # 标准化期望值
    expected_normalized = normalize_value(expected_value)
    
    values_match = effective_value == expected_normalized
    
    return (
        values_match,
        effective_value,
        {
            "detection_method": "Level 1 - Config (Override Analysis)",
            "message": f"Filament retract when changing layer ({param_source}): {effective_value} (expected: {expected_value})",
            "override_mechanism": {
                "filament_override": filament_override,
                "printer_base": printer_base,
                "effective_value": effective_value,
                "override_applied": override_detected,
                "parameter_source": param_source,
                "mechanism_note": "filament_retract_when_changing_layer (nullable) can override retract_when_changing_layer (printer)"
            },
            "raw_data": {
                "filament_param": filament_override,
                "printer_param": printer_base,
                "expected": expected_value
            }
        },
    )


def parse_filament_retract_when_changing_layer_behavior(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_retract_when_changing_layer G-code behavior (Level 2 - G-code Analysis)"""
    import re
    
    try:
        with open(gcode_path, 'r', encoding='utf-8') as f:
            gcode_content = f.read()
        
        # 获取retraction_minimum_travel参数值用于区分空驶触发回抽
        cfg = _load_gcode_config(gcode_path)
        min_travel = float(cfg.get('filament_retraction_minimum_travel', 1.75))
        
        # 查找层变化标记和对应的位置信息
        layer_pattern = r';LAYER_CHANGE\s*\n|;BEFORE_LAYER_CHANGE\s*\n|;LAYER:(\d+)\s*\n'
        layer_matches = list(re.finditer(layer_pattern, gcode_content))
        
        forced_retracts = 0  # 强制换层回抽
        travel_retracts = 0  # 空驶距离触发回抽
        total_layers = len(layer_matches)
        
        for i, layer_match in enumerate(layer_matches):
            if i == 0:  # 跳过第一层
                continue
                
            # 分析层变化前后的代码段
            start_pos = max(0, layer_match.start() - 1500)
            end_pos = min(len(gcode_content), layer_match.end() + 1500)
            region = gcode_content[start_pos:end_pos]
            
            lines = region.split('\n')
            layer_line_idx = -1
            
            # 找到层变化标记的位置
            for j, line in enumerate(lines):
                if 'LAYER_CHANGE' in line or 'LAYER:' in line:
                    layer_line_idx = j
                    break
            
            if layer_line_idx < 0:
                continue
                
            # 检查层变化后的代码（接下来50行）
            after_lines = lines[layer_line_idx+1:min(len(lines), layer_line_idx+50)]
            
            # 分析这个区域的移动和回抽模式
            found_retract = False
            travel_distance = 0
            last_pos = None
            
            for line in after_lines:
                line = line.strip()
                if not line or line.startswith(';'):
                    continue
                    
                # 先检查XY移动距离，然后再判断回抽
                xy_match = re.search(r'G[01]\s+.*X([0-9.-]+).*Y([0-9.-]+)', line, re.IGNORECASE)
                if xy_match:
                    try:
                        x, y = float(xy_match.group(1)), float(xy_match.group(2))
                        if last_pos:
                            dx = x - last_pos[0]
                            dy = y - last_pos[1]
                            travel_distance += (dx*dx + dy*dy)**0.5
                        last_pos = (x, y)
                    except ValueError:
                        pass
                
                # 检查是否有回抽命令
                if (re.search(r'G1\s+.*E-[0-9.]+', line, re.IGNORECASE) or 
                    re.search(r'G10\s*$', line, re.IGNORECASE)):
                    found_retract = True
                    
                    # 关键修正：正确判断回抽类型并增加调试信息
                    # 在层变化后，如果累计空驶距离 >= min_travel，则是空驶触发的回抽
                    # 如果距离很短但仍然回抽，才是真正的强制换层回抽
                    if travel_distance >= min_travel:
                        travel_retracts += 1  # 空驶距离触发
                        retract_type = "travel"
                    else:
                        forced_retracts += 1  # 强制换层回抽
                        retract_type = "forced"
                    
                    # 调试：前几个层的详细信息
                    if i <= 5:
                        # DEBUG: print(f"Layer {i}: {retract_type} retract, travel_distance={travel_distance:.2f}, threshold={min_travel}")
                        pass
                    
                    break
        
        # 判断行为是否符合期望 - 基于正确的优先级逻辑
        if expected_value.lower() in ['nil', 'none', 'null']:
            expected_enabled = False
        else:
            expected_enabled = expected_value.lower() in ['true', '1']

        if expected_enabled:
            # 如果明确启用换层回抽，预期在大部分层变化时都会回抽
            # (包括强制换层回抽 + 空驶触发回抽)
            total_retracts = forced_retracts + travel_retracts
            behavior_correct = total_retracts > total_layers * 0.8 if total_layers > 1 else True
            message = f"Enabled: {forced_retracts} forced + {travel_retracts} travel retracts in {total_layers} layers (total: {total_retracts})"
        else:
            # 对于disabled情况，应用优先级逻辑分析  
            if expected_value.lower() == 'false':
                total_retracts = forced_retracts + travel_retracts
                
                if total_layers > 1:
                    # 基于调试发现的模式分析：
                    # - travel_distance=0但仍回抽 → 说明换层回抽未被正确禁用
                    # - travel_distance>threshold的回抽 → 正常的空驶回抽
                    
                    forced_ratio = forced_retracts / total_layers
                    travel_ratio = travel_retracts / total_layers
                    
                    # 如果大部分是forced retract (0距离但仍回抽)，说明换层回抽设置未生效
                    if forced_ratio > 0.9:  # 超过90%是forced
                        behavior_correct = False
                        message = f"Disabled (not effective): {forced_retracts} forced + {travel_retracts} travel retracts - layer change retraction setting appears not effective"
                    elif travel_ratio > 0.8:  # 主要是travel触发
                        behavior_correct = True
                        message = f"Disabled (correct priority): {forced_retracts} forced + {travel_retracts} travel retracts - mostly travel-distance triggered"
                    else:  # 混合情况
                        behavior_correct = forced_ratio <= 0.3  # 容忍一定比例的forced
                        status = "acceptable" if behavior_correct else "problematic"
                        message = f"Disabled ({status}): {forced_retracts} forced + {travel_retracts} travel retracts - mixed triggers"
                else:
                    behavior_correct = True
                    message = f"Disabled (single layer): cannot analyze priority logic"
            else:  # nil情况
                behavior_correct = True
                message = f"Default(nil): {forced_retracts} forced + {travel_retracts} travel retracts in {total_layers} layers (influenced by other settings)"
        
        return (
            behavior_correct,
            f"{forced_retracts}+{travel_retracts}/{total_layers}",
            {
                "detection_method": "Level 2 - G-code Analysis",
                "message": message,
                "raw_data": {
                    "total_layers": total_layers,
                    "forced_retracts": forced_retracts,
                    "travel_retracts": travel_retracts,
                    "min_travel_threshold": min_travel,
                    "expected_enabled": expected_enabled
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


def parse_filament_wipe(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_wipe parameter (Level 1 - Config)"""
    return _parse_config_parameter(gcode_path, "filament_wipe", expected_value, 
                                 "Filament wipe")


def parse_filament_wipe_distance(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_wipe_distance parameter (Level 1 - Config)"""
    return _parse_config_parameter(gcode_path, "filament_wipe_distance", expected_value, 
                                 "Filament wipe distance")


def parse_filament_retract_before_wipe(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_retract_before_wipe parameter (Level 1 - Config)"""
    return _parse_config_parameter(gcode_path, "filament_retract_before_wipe", expected_value, 
                                 "Filament retract before wipe")


def parse_filament_long_retractions_when_cut(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_long_retractions_when_cut parameter (Level 1 - Config)"""
    return _parse_config_parameter(gcode_path, "filament_long_retractions_when_cut", expected_value, 
                                 "Filament long retractions when cut")


def parse_filament_retraction_distances_when_cut(gcode_path: Path, expected_value: str) -> Tuple[bool, Any, Dict]:
    """Test filament_retraction_distances_when_cut parameter (Level 1 - Config)"""
    return _parse_config_parameter(gcode_path, "filament_retraction_distances_when_cut", expected_value, 
                                 "Filament retraction distances when cut")

