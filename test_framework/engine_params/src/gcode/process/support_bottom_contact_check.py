"""Measure the air gap above the platform of the support-bottom fixture."""

import math
from collections import defaultdict
from pathlib import Path

from engine_params.src.gcode.process.quality.behavior import BehaviorGCode
from engine_params.src.gcode.process.support_l2_metrics import _segment_cells


def _footprint(moves):
    cells = set()
    for move in moves:
        cells.update(_segment_cells((move.x0, move.y0), (move.x, move.y), resolution=0.2))
    return cells


def validate_support_bottom_z_distance(gcode_path: Path | str, expected_value):
    """Use physical Z and interface thickness, not baseline move counts or ;Z."""
    details = {"detection_method": "Level 2 - Measured support bottom air gap",
               "parameter": "support_bottom_z_distance", "checks": ["semantic.support_bottom_air_gap"],
               "mismatches": []}
    try:
        expected = float(expected_value)
    except (TypeError, ValueError):
        return False, {**details, "error": "invalid expected gap"}
    if not math.isfinite(expected) or expected < 0:
        return False, {**details, "error": "invalid expected gap"}

    behavior = BehaviorGCode(gcode_path)
    top = behavior.extrusion_moves("Top surface")
    interface = behavior.extrusion_moves("Support interface")
    if not top or not interface:
        return False, {**details, "error": "missing model top or support interface"}
    # The canonical fixture's lowest exposed top is the platform on which a
    # bottom interface starts. Upper interfaces must not vote on this gap.
    model_z = min(m.z for m in top)
    platform = [m for m in top if abs(m.z - model_z) < 1e-6]
    platform_cells = _footprint(platform)
    by_z = defaultdict(list)
    for move in interface:
        if move.z > model_z + 1e-6:
            by_z[round(move.z, 5)].append(move)
    for z, moves in sorted(by_z.items()):
        overlapping = [m for m in moves if _footprint([m]) & platform_cells]
        if not overlapping:
            continue
        if any(not m.height or m.height <= 0 for m in overlapping):
            return False, {**details, "error": "missing interface thickness"}
        gaps = sorted({round(m.z - m.height - model_z, 5) for m in overlapping})
        details.update({"model_top_z": model_z, "interface_z": z,
                        "interface_heights": sorted({m.height for m in overlapping}),
                        "measured_gaps_mm": gaps, "expected_gap_mm": expected,
                        "overlapping_moves": len(overlapping),
                        "evidence_lines": [m.line_no for m in overlapping[:5]]})
        details["mismatches"] = [
            {"metric": "semantic.support_bottom_air_gap", "expected": expected, "actual": gap}
            for gap in gaps if not math.isclose(gap, expected, rel_tol=0, abs_tol=0.015)
        ]
        return not details["mismatches"], details
    return False, {**details, "error": "no interface above the model platform at overlapping XY"}
