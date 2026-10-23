"""G-code parser for functional checks: layers, extrusion types, header stats.

Orca-lineage G-code carries `;LAYER_CHANGE`, `;TYPE:<NAME>` and `G1 ... E`
moves. Summing positive extrusion deltas per TYPE segment reproduces the
per-type filament table CrealityPrint shows in its G-code preview
(走线类型: 内墙/外墙/支撑/支撑界面/桥接...), which is what the automated
checks assert against.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field

MOVE_RE = re.compile(r"^G1?\s")
E_RE = re.compile(r"(?:^|\s)E([-\d.]+)")
Z_RE = re.compile(r"(?:^|\s)Z([-\d.]+)")
TYPE_RE = re.compile(r";\s*TYPE\s*:\s*(.+)")
LAYER_CHANGE_RE = re.compile(r";\s*LAYER_CHANGE")
HEADER_TOTAL_LAYERS_RE = re.compile(r"total layer(?:s count| number)\s*[:=]\s*(\d+)")


@dataclass
class GcodeInfo:
    layers: int = 0
    max_z: float = 0.0
    total_e: float = 0.0
    header_total_layers: int | None = None  # '; total layer number: N'
    relative_e: bool = False  # M83 / relative extruder addressing
    type_e: dict = field(default_factory=dict)  # TYPE name -> filament mm
    header_lines: list = field(default_factory=list)


def parse_gcode(path) -> GcodeInfo:
    """Single pass; tolerates missing markers (all counters just stay low).

    Orca-lineage files put the estimate block (printing time / filament
    totals) at the END, after the config dump — so the tail is tracked too.
    """
    from collections import deque

    info = GcodeInfo()
    current_type = "UNKNOWN"
    last_e = 0.0
    header_budget = 400  # stats/comments live in the preamble
    tail = deque(maxlen=1500)  # estimate block precedes a long config dump

    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            tail.append(stripped)
            if stripped.startswith(";"):
                if LAYER_CHANGE_RE.search(stripped):
                    info.layers += 1
                if "relative_extruder_addressing = 1" in stripped:
                    info.relative_e = True
                type_match = TYPE_RE.search(stripped)
                if type_match:
                    current_type = type_match.group(1).upper()
                    info.type_e.setdefault(current_type, 0.0)
                    continue
                if header_budget > 0:
                    info.header_lines.append(stripped)
                    if info.header_total_layers is None:
                        total = HEADER_TOTAL_LAYERS_RE.search(stripped)
                        if total:
                            info.header_total_layers = int(total.group(1))
                    header_budget -= 1
                continue

            if not MOVE_RE.match(stripped):
                continue

            z_match = Z_RE.search(stripped)
            if z_match:
                info.max_z = max(info.max_z, float(z_match.group(1)))

            if stripped.startswith("G92") and " E0" in stripped:
                last_e = 0.0  # explicit reset in absolute mode

            if stripped.startswith("M83"):  # relative extrusion switch
                info.relative_e = True

            e_match = E_RE.search(stripped)
            if e_match:
                e = float(e_match.group(1))
                if info.relative_e:
                    delta = e  # E is already per-move extrusion
                else:
                    delta = e - last_e
                    last_e = e
                if delta > 0:
                    info.total_e += delta
                    info.type_e[current_type] = (
                        info.type_e.get(current_type, 0.0) + delta
                    )
    info.header_lines.extend(tail)
    return info


def type_length_mm(info: GcodeInfo, needle: str) -> float:
    """Total filament for types containing needle ('SUPPORT', 'WALL', ...)."""
    low = needle.lower()
    return sum(v for k, v in info.type_e.items() if low in k.lower())
