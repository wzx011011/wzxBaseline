import mmap
from pathlib import Path
from typing import List, Tuple, Literal, Optional

from engine_params.src.gcode.GCodeParser import GCodeParser, WallStyle


def parse_wall_sequence(gcode_path: str | Path, *, expected_sequence: WallStyle, workers: int = 0) \
        -> Tuple[bool, WallStyle, List[Tuple[int, WallStyle, List[str]]]]:
    parser = GCodeParser(gcode_path)
    cfg = parser.load_config()
    ret = parser.validate_wall_sequence()
    return ret

