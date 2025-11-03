from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, Optional, Tuple

from engine_params.src.gcode.GCodeParser import GCodeParser
from engine_params.src.gcode.constants import ExtrusionType


def _extract_last_extrude_e(parser: GCodeParser, type_value: str) -> Optional[float]:
    """Return the last extrude-point E for the given TYPE across all layers."""
    contours = parser.get_type_contours_per_layer(types=[type_value], workers=0)
    if not contours:
        return None

    last_e: Optional[float] = None
    for layer_map in contours:
        if not layer_map:
            continue
        for oid, type_map in (layer_map or {}).items():
            polylines = (type_map or {}).get(type_value) or []
            for poly in polylines or []:
                for pt in poly:
                    if pt.kind == "extrude" and pt.e is not None:
                        last_e = pt.e
    return last_e


def parse_internal_bridge_flow(
        tested_gcode: Path | str,
        baseline_gcode: Path | str,
        expected_ratio: float,
        *,
        tol: float = 1e-3,
) -> Tuple[bool, Optional[float], Dict[str, object]]:
    """
    Compare the last Internal bridge extrude E between tested and baseline G-code.
    """
    tested_path = Path(tested_gcode)
    baseline_path = Path(baseline_gcode)

    tested_parser = GCodeParser(tested_path)
    baseline_parser = GCodeParser(baseline_path)

    tested_e = _extract_last_extrude_e(tested_parser, ExtrusionType.INTERNAL_BRIDGE.value)
    baseline_e = _extract_last_extrude_e(baseline_parser, ExtrusionType.INTERNAL_BRIDGE.value)

    ratio: Optional[float] = None
    ok = False
    if tested_e is not None and baseline_e is not None and abs(baseline_e) > 1e-9:
        ratio = tested_e / baseline_e
        ok = math.isclose(ratio, expected_ratio, rel_tol=tol, abs_tol=tol)

    details: Dict[str, object] = {
        "tested_gcode": str(tested_path),
        "baseline_gcode": str(baseline_path),
        "tested_e": tested_e,
        "baseline_e": baseline_e,
        "ratio": ratio,
        "expected_ratio": expected_ratio,
        "tolerance": tol,
    }

    return ok, ratio, details
