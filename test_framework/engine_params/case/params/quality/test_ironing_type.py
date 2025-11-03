from pathlib import Path

import pytest
from engine_params.src.gcode.quality.ironing_type_check import parse_ironing_type


@pytest.mark.engine_params
def test_ironing_type(slice_and_export: Path,
                      expected_ironing_type: bool):
    gcode_path: Path = slice_and_export
    assert gcode_path.exists()
    result:list[dict[int, list[bytes | str]]] = parse_ironing_type(gcode_path)
    has_ironing_type = False
    for layer in result:
        for obj_id,blocks in layer.items():
            has_ironing_type = any(blocks)
        if has_ironing_type:
            break
    assert has_ironing_type

    # return any(bool(layer_blocks) for layer_blocks in blocks_per_layer)
    # assert result == expected_ironing_type,f"result={result},but expected {expected_ironing_type}!"
