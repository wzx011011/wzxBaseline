"""Layer height comments emitted by current and historical Creality Print versions."""

import re
from typing import Iterable


_LAYER_Z_RE = re.compile(r"^\s*;\s*(?:Z\s*)?:\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*$")


def parse_layer_z(line: str) -> float | None:
    """Read either ;Z:0.2 or the legacy ;:0.2 without matching ;HEIGHT:."""
    match = _LAYER_Z_RE.match(line)
    return float(match.group(1)) if match else None


def read_layer_heights(lines: Iterable[str]) -> list[float | None]:
    """Keep one height per layer, including missing heights as None."""
    heights: list[float | None] = []
    pending = False
    for raw_line in lines:
        line = raw_line.strip()
        if line in ("; EXECUTABLE_BLOCK_END", "; CONFIG_BLOCK_START"):
            break
        if line == ";LAYER_CHANGE":
            heights.append(None)
            pending = True
        elif pending:
            height = parse_layer_z(line)
            if height is not None:
                heights[-1] = height
                pending = False
            elif line and not line.startswith(";"):
                pending = False
    return heights
