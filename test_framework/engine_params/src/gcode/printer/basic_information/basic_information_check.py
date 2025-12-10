from pathlib import Path
from typing import Any, Dict, Tuple

from engine_params.src.gcode.GCodeParser import GCodeParser


def _to_float(val):
    """将值转换为浮点数"""
    try:
        return float(val)
    except Exception:
        return None


def _to_bool(val):
    """将值转换为布尔值"""
    if isinstance(val, bool):
        return val
    if val is None:
        return None
    s = str(val).strip().lower()
    if s in ("true", "1", "yes"):
        return True
    if s in ("false", "0", "no"):
        return False
    return None


def _norm_raw(val):
    """规范化原始值为小写字符串"""
    return None if val is None else str(val).strip().lower()


def parse_printable_area(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Level 1 - Config: 从 G-code 的配置块读取 printable_area 并与期望值对比"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()

    if not cfg:
        return False, None, {
            "detection_method": "Level 1 - Config",
            "message": "no CONFIG block found in G-code",
            "raw_data": None,
        }

    actual_raw = cfg.get("printable_area")
    actual = _norm_raw(actual_raw)

    if actual is None:
        return False, None, {
            "detection_method": "Level 1 - Config",
            "message": "printable_area not found in config",
            "raw_data": cfg,
        }

    exp = _norm_raw(expected_value)
    ok = actual == exp
    
    return ok, actual, {
        "detection_method": "Level 1 - Config",
        "message": "raw string compare for printable_area",
        "raw_data": cfg,
    }


def parse_printable_height(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Level 1 - Config: 从 G-code 的配置块读取 printable_height 并与期望值对比"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    
    if not cfg:
        return False, None, {
            "detection_method": "Level 1 - Config",
            "message": "no CONFIG block found",
            "raw_data": None
        }

    actual_raw = cfg.get("printable_height")
    actual = _to_float(actual_raw)
    
    if actual is None:
        return False, actual_raw, {
            "detection_method": "Level 1 - Config",
            "message": "printable_height missing or not numeric",
            "raw_data": cfg
        }

    exp = _to_float(expected_value)
    if exp is None:
        return False, actual, {
            "detection_method": "Level 1 - Config",
            "message": "expected_value not numeric",
            "raw_data": cfg
        }

    ok = abs(actual - exp) < 1e-6
    return ok, actual, {
        "detection_method": "Level 1 - Config",
        "message": "numeric compare",
        "raw_data": cfg
    }


def parse_bed_exclude_area(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Level 1 - Config: 从 G-code 的配置块读取 bed_exclude_area 并与期望值对比"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    
    if not cfg:
        return False, None, {
            "detection_method": "Level 1 - Config",
            "message": "no CONFIG block found",
            "raw_data": None
        }

    actual_raw = cfg.get("bed_exclude_area")
    actual = _norm_raw(actual_raw)
    exp = _norm_raw(expected_value)
    ok = actual == exp
    
    return ok, actual_raw, {
        "detection_method": "Level 1 - Config",
        "message": "raw string compare for bed_exclude_area",
        "raw_data": cfg
    }


def parse_support_multi_bed_types(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Level 1 - Config: 从 G-code 的配置块读取 support_multi_bed_types 并与期望值对比"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    
    if not cfg:
        return False, None, {
            "detection_method": "Level 1 - Config",
            "message": "no CONFIG block found",
            "raw_data": None
        }

    actual_raw = cfg.get("support_multi_bed_types")
    actual = _to_bool(actual_raw)
    exp = _to_bool(expected_value)
    
    ok = actual == exp
    return ok, actual_raw, {
        "detection_method": "Level 1 - Config",
        "message": "boolean compare for support_multi_bed_types",
        "raw_data": cfg
    }


def parse_nozzle_volume(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Level 1 - Config: 从 G-code 的配置块读取 nozzle_volume 并与期望值对比"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    
    if not cfg:
        return False, None, {
            "detection_method": "Level 1 - Config",
            "message": "no CONFIG block found",
            "raw_data": None
        }

    actual_raw = cfg.get("nozzle_volume")
    actual = _to_float(actual_raw)
    exp = _to_float(expected_value)
    
    if actual is None or exp is None:
        return False, actual_raw, {
            "detection_method": "Level 1 - Config",
            "message": "nozzle_volume missing or expected not numeric",
            "raw_data": cfg
        }

    ok = abs(actual - exp) < 1e-6
    return ok, actual, {
        "detection_method": "Level 1 - Config",
        "message": "numeric compare for nozzle_volume",
        "raw_data": cfg
    }


def parse_best_object_pos(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Level 1 - Config: 从 G-code 的配置块读取 best_object_pos 并与期望值对比"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    
    if not cfg:
        return False, None, {
            "detection_method": "Level 1 - Config",
            "message": "no CONFIG block found",
            "raw_data": None
        }

    actual_raw = cfg.get("best_object_pos")
    actual = _norm_raw(actual_raw)
    exp = _norm_raw(expected_value)
    ok = actual == exp
    
    return ok, actual_raw, {
        "detection_method": "Level 1 - Config",
        "message": "raw compare for best_object_pos",
        "raw_data": cfg
    }


def parse_z_offset(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Level 1 - Config: 从 G-code 的配置块读取 z_offset 并与期望值对比"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    
    if not cfg:
        return False, None, {
            "detection_method": "Level 1 - Config",
            "message": "no CONFIG block found",
            "raw_data": None
        }

    actual_raw = cfg.get("z_offset")
    actual = _to_float(actual_raw)
    exp = _to_float(expected_value)
    
    if actual is None or exp is None:
        return False, actual_raw, {
            "detection_method": "Level 1 - Config",
            "message": "z_offset missing or expected not numeric",
            "raw_data": cfg
        }

    ok = abs(actual - exp) < 1e-6
    return ok, actual, {
        "detection_method": "Level 1 - Config",
        "message": "numeric compare for z_offset",
        "raw_data": cfg
    }


def parse_preferred_orientation(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Level 1 - Config: 从 G-code 的配置块读取 preferred_orientation 并与期望值对比"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    
    if not cfg:
        return False, None, {
            "detection_method": "Level 1 - Config",
            "message": "no CONFIG block found",
            "raw_data": None
        }

    actual_raw = cfg.get("preferred_orientation")
    actual = _to_float(actual_raw)
    exp = _to_float(expected_value)
    
    if actual is None or exp is None:
        return False, actual_raw, {
            "detection_method": "Level 1 - Config",
            "message": "preferred_orientation missing or expected not numeric",
            "raw_data": cfg
        }

    ok = abs(actual - exp) < 1e-6
    return ok, actual, {
        "detection_method": "Level 1 - Config",
        "message": "numeric compare for preferred_orientation",
        "raw_data": cfg
    }


# ===== Advanced 分组（13个参数）=====

def parse_printer_structure(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Level 1 - Config: 从 G-code 的配置块读取 printer_structure 并与期望值对比"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    
    if not cfg:
        return False, None, {
            "detection_method": "Level 1 - Config",
            "message": "no CONFIG block found",
            "raw_data": None
        }

    actual_raw = cfg.get("printer_structure")
    actual = _norm_raw(actual_raw)
    exp = _norm_raw(expected_value)
    ok = actual == exp
    
    return ok, actual_raw, {
        "detection_method": "Level 1 - Config",
        "message": "raw string compare for printer_structure",
        "raw_data": cfg
    }


def parse_gcode_flavor(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Level 1 - Config: 从 G-code 的配置块读取 gcode_flavor 并与期望值对比"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    
    if not cfg:
        return False, None, {
            "detection_method": "Level 1 - Config",
            "message": "no CONFIG block found",
            "raw_data": None
        }

    actual_raw = cfg.get("gcode_flavor")
    actual = _norm_raw(actual_raw)
    exp = _norm_raw(expected_value)
    ok = actual == exp
    
    return ok, actual_raw, {
        "detection_method": "Level 1 - Config",
        "message": "raw string compare for gcode_flavor",
        "raw_data": cfg
    }


def parse_pellet_modded_printer(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Level 1 - Config: 从 G-code 的配置块读取 pellet_modded_printer 并与期望值对比"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    
    if not cfg:
        return False, None, {
            "detection_method": "Level 1 - Config",
            "message": "no CONFIG block found",
            "raw_data": None
        }

    actual_raw = cfg.get("pellet_modded_printer")
    actual = _to_bool(actual_raw)
    exp = _to_bool(expected_value)
    
    ok = actual == exp
    return ok, actual_raw, {
        "detection_method": "Level 1 - Config",
        "message": "boolean compare for pellet_modded_printer",
        "raw_data": cfg
    }


def parse_bbl_use_printhost(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Level 1 - Config: 从 G-code 的配置块读取 bbl_use_printhost 并与期望值对比"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    
    if not cfg:
        return False, None, {
            "detection_method": "Level 1 - Config",
            "message": "no CONFIG block found",
            "raw_data": None
        }

    actual_raw = cfg.get("bbl_use_printhost")
    actual = _to_bool(actual_raw)
    exp = _to_bool(expected_value)
    
    ok = actual == exp
    return ok, actual_raw, {
        "detection_method": "Level 1 - Config",
        "message": "boolean compare for bbl_use_printhost",
        "raw_data": cfg
    }


def parse_disable_m73(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Level 1 - Config: 从 G-code 的配置块读取 disable_m73 并与期望值对比"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    
    if not cfg:
        return False, None, {
            "detection_method": "Level 1 - Config",
            "message": "no CONFIG block found",
            "raw_data": None
        }

    actual_raw = cfg.get("disable_m73")
    actual = _to_bool(actual_raw)
    exp = _to_bool(expected_value)
    
    ok = actual == exp
    return ok, actual_raw, {
        "detection_method": "Level 1 - Config",
        "message": "boolean compare for disable_m73",
        "raw_data": cfg
    }


def parse_thumbnails(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Level 1 - Config: 从 G-code 的配置块读取 thumbnails 并与期望值对比"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    
    if not cfg:
        return False, None, {
            "detection_method": "Level 1 - Config",
            "message": "no CONFIG block found",
            "raw_data": None
        }

    actual_raw = cfg.get("thumbnails")
    actual = _norm_raw(actual_raw)
    exp = _norm_raw(expected_value)
    ok = actual == exp
    
    return ok, actual_raw, {
        "detection_method": "Level 1 - Config",
        "message": "raw string compare for thumbnails",
        "raw_data": cfg
    }


def parse_use_relative_e_distances(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Level 1 - Config: 从 G-code 的配置块读取 use_relative_e_distances 并与期望值对比"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    
    if not cfg:
        return False, None, {
            "detection_method": "Level 1 - Config",
            "message": "no CONFIG block found",
            "raw_data": None
        }

    actual_raw = cfg.get("use_relative_e_distances")
    actual = _to_bool(actual_raw)
    exp = _to_bool(expected_value)
    
    ok = actual == exp
    return ok, actual_raw, {
        "detection_method": "Level 1 - Config",
        "message": "boolean compare for use_relative_e_distances",
        "raw_data": cfg
    }


def parse_use_firmware_retraction(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Level 1 - Config: 从 G-code 的配置块读取 use_firmware_retraction 并与期望值对比"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    
    if not cfg:
        return False, None, {
            "detection_method": "Level 1 - Config",
            "message": "no CONFIG block found",
            "raw_data": None
        }

    actual_raw = cfg.get("use_firmware_retraction")
    actual = _to_bool(actual_raw)
    exp = _to_bool(expected_value)
    
    ok = actual == exp
    return ok, actual_raw, {
        "detection_method": "Level 1 - Config",
        "message": "boolean compare for use_firmware_retraction",
        "raw_data": cfg
    }


def parse_machine_load_filament_time(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Level 1 - Config: 从 G-code 的配置块读取 machine_load_filament_time 并与期望值对比"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    
    if not cfg:
        return False, None, {
            "detection_method": "Level 1 - Config",
            "message": "no CONFIG block found",
            "raw_data": None
        }

    actual_raw = cfg.get("machine_load_filament_time")
    actual = _to_float(actual_raw)
    exp = _to_float(expected_value)
    
    if actual is None or exp is None:
        return False, actual_raw, {
            "detection_method": "Level 1 - Config",
            "message": "machine_load_filament_time missing or expected not numeric",
            "raw_data": cfg
        }

    ok = abs(actual - exp) < 1e-6
    return ok, actual, {
        "detection_method": "Level 1 - Config",
        "message": "numeric compare for machine_load_filament_time",
        "raw_data": cfg
    }


def parse_machine_unload_filament_time(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Level 1 - Config: 从 G-code 的配置块读取 machine_unload_filament_time 并与期望值对比"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    
    if not cfg:
        return False, None, {
            "detection_method": "Level 1 - Config",
            "message": "no CONFIG block found",
            "raw_data": None
        }

    actual_raw = cfg.get("machine_unload_filament_time")
    actual = _to_float(actual_raw)
    exp = _to_float(expected_value)
    
    if actual is None or exp is None:
        return False, actual_raw, {
            "detection_method": "Level 1 - Config",
            "message": "machine_unload_filament_time missing or expected not numeric",
            "raw_data": cfg
        }

    ok = abs(actual - exp) < 1e-6
    return ok, actual, {
        "detection_method": "Level 1 - Config",
        "message": "numeric compare for machine_unload_filament_time",
        "raw_data": cfg
    }


def parse_time_cost(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Level 1 - Config: 从 G-code 的配置块读取 time_cost 并与期望值对比"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    
    if not cfg:
        return False, None, {
            "detection_method": "Level 1 - Config",
            "message": "no CONFIG block found",
            "raw_data": None
        }

    actual_raw = cfg.get("time_cost")
    actual = _to_float(actual_raw)
    exp = _to_float(expected_value)
    
    if actual is None or exp is None:
        return False, actual_raw, {
            "detection_method": "Level 1 - Config",
            "message": "time_cost missing or expected not numeric",
            "raw_data": cfg
        }

    ok = abs(actual - exp) < 1e-6
    return ok, actual, {
        "detection_method": "Level 1 - Config",
        "message": "numeric compare for time_cost",
        "raw_data": cfg
    }


def parse_machine_is_belt(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Level 1 - Config: 从 G-code 的配置块读取 machine_is_belt 并与期望值对比"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    
    if not cfg:
        return False, None, {
            "detection_method": "Level 1 - Config",
            "message": "no CONFIG block found",
            "raw_data": None
        }

    actual_raw = cfg.get("machine_is_belt")
    actual = _to_bool(actual_raw)
    exp = _to_bool(expected_value)
    
    ok = actual == exp
    return ok, actual_raw, {
        "detection_method": "Level 1 - Config",
        "message": "boolean compare for machine_is_belt",
        "raw_data": cfg
    }


def parse_multicolor_method(gcode_path: Path, expected_value: Any) -> Tuple[bool, Any, Dict]:
    """Level 1 - Config: 从 G-code 的配置块读取 multicolor_method 并与期望值对比"""
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    
    if not cfg:
        return False, None, {
            "detection_method": "Level 1 - Config",
            "message": "no CONFIG block found",
            "raw_data": None
        }

    actual_raw = cfg.get("multicolor_method")
    actual = _to_bool(actual_raw)
    exp = _to_bool(expected_value)
    
    ok = actual == exp
    return ok, actual_raw, {
        "detection_method": "Level 1 - Config",
        "message": "boolean compare for multicolor_method",
        "raw_data": cfg
    }
