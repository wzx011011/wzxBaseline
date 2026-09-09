"""Distinguish open thin-rib centerlines from rescued closed wall contours."""

import math
from pathlib import Path

from engine_params.src.gcode.GCodeParser import GCodeParser
from engine_params.src.gcode.process.quality.behavior import (
    BehaviorGCode, path_length, path_signed_area,
)


def _closed_rib(path):
    # The rib fixture uses straight walls. A seam leaves a small gap even on
    # a closed perimeter; a retraced centerline has no enclosed area.
    gap = math.hypot(path[0].x0 - path[-1].x, path[0].y0 - path[-1].y)
    width = max((move.width or 0.0 for move in path), default=0.0)
    area_per_length = abs(path_signed_area(path)) / path_length(path)
    return gap <= max(0.05, width / 2) and area_per_length > 0.002


def check_detect_thin_wall(gcode_path: Path | str, expected_value: bool):
    behavior = BehaviorGCode(gcode_path)
    paths = behavior.paths(("Outer wall", "Gap infill"), min_length=5.0)
    widths = [move.width for path in paths for move in path if move.width is not None]
    narrow = [path for path in paths if any(
        move.width is not None and 0.05 < move.width < 0.38 for move in path)]
    centerlines = [path for path in narrow if not _closed_rib(path)]
    closed_narrow = len(narrow) - len(centerlines)
    # The 3 mm control rib must survive even when thin-wall detection is off.
    # Area/perimeter distinguishes it from the legitimate 0.48 mm rib loop.
    controls = [path for path in paths if _closed_rib(path)
                and abs(path_signed_area(path)) / path_length(path) > 0.5]
    configured = GCodeParser(Path(gcode_path)).load_config().get("detect_thin_wall")
    actual = bool(centerlines)
    # The exporter may omit WIDTH on the first-layer control perimeter.
    # Body-layer hints are required to identify variable-width thin ribs.
    valid = bool(controls) and bool(widths) and all(
        move.width is not None for path in paths if path[0].layer > 0 for move in path)
    details = {
        "method": "L2 - Open thin-rib centerlines with closed control contour",
        "all_paths": len(paths), "thin_width_samples": sum(0.05 < width < 0.38 for width in widths),
        "thin_centerline_paths": len(centerlines), "closed_narrow_paths": closed_narrow,
        "control_paths": len(controls), "configured": configured,
        "observed_width_range": (min(widths, default=None), max(widths, default=None)),
        "expected": expected_value,
    }
    return valid and configured == int(expected_value) and actual == expected_value, actual, details
