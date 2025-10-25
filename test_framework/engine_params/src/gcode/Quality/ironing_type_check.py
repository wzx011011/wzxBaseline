from __future__ import annotations

from pathlib import Path

from engine_params.src.gcode.GCodeParser import GCodeParser


def parse_ironing_type(gcode_path: str | Path, *, workers: int = 0) -> list[dict[int, list[bytes | str]]]:
    '''
        现在只能检查存在性，TODO，类型还不能检查
    '''
    parser = GCodeParser(gcode_path)
    blocks_per_layer = parser.get_extrusion_blocks_per_layer(
        "Ironing", include_wipe=True, decode=False, workers=4
    )
    # 只要某一层非空，就说明存在 Ironing 段
    # return any(bool(layer_blocks) for layer_blocks in blocks_per_layer)
    return blocks_per_layer
