from pathlib import Path
from typing import Optional

from .GCodeParser import GCodeParser

def parse_layer_height(gcode_path: str | Path, *, workers: int = 0) -> dict[str, object]:
    """
    返回：
      {
        "config_layer_height": <来自 CONFIG_BLOCK 的 layer_height 或 None>,
        "layers": [(z, height), ...],
      }
    """
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    layers = parser.extract_layers(workers=workers)
    return {
        "config_layer_height": cfg.get("layer_height"),
        "layers": layers,
    }

def parse_initial_layer_print_height(gcode_path: str | Path) -> dict[str, Optional[float]]:
    """
    返回：
      {
        "config_initial_layer_print_height": <CONFIG里的值或None>,
        "first_layer_z": <首层Z或None>,
        "first_layer_height": <首层HEIGHT或None>,
      }
    """
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    z, h = parser.extract_layers()
    return {
        "config_initial_layer_print_height": cfg.get("initial_layer_print_height"),
        "first_layer_z": z,
        "first_layer_height": h,
    }