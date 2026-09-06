"""Local toolpath checks for the four-channel top-width fixture."""

import math
from pathlib import Path

from engine_params.src.gcode.GCodeParser import GCodeParser
from engine_params.src.gcode.process.quality.behavior import BehaviorGCode, median


def _section_intervals(moves, y):
    intervals = []
    for move in moves:
        if move.command not in {"G0", "G1"}:
            continue
        if abs(move.y - move.y0) < 1e-8:
            if abs(y - move.y) < 1e-6:
                intervals.append((min(move.x0, move.x), max(move.x0, move.x)))
        elif min(move.y0, move.y) <= y <= max(move.y0, move.y):
            x = move.x0 + (y - move.y0) * (move.x - move.x0) / (move.y - move.y0)
            intervals.append((x, x))
    return intervals


def _channel_evidence(moves, xmin, ymin, ymax, threshold, wall_width):
    inner = [move for move in moves if move.role == "Inner wall"]
    top = [move for move in moves if move.role == "Top surface"]
    cursor = xmin
    channels = []
    for gap in (0.36, 0.48, 0.60, 0.78):
        left, right = cursor + 7.0, cursor + 7.0 + gap
        samples = []
        for fraction in (0.3, 0.5, 0.7):
            y = ymin + fraction * (ymax - ymin)
            walls = _section_intervals(inner, y)
            surface = _section_intervals(top, y)
            # The fixture requests four walls. Retained channels have inner
            # walls on BOTH sides; filtered channels lose those local walls.
            reach = 4 * wall_width
            left_wall = any(left - reach <= a <= left for a, _ in walls)
            right_wall = any(right <= a <= right + reach for a, _ in walls)
            covered = any(b >= left - wall_width / 2 and a <= right + wall_width / 2
                          for a, b in surface)
            samples.append({"y": y, "left_wall": left_wall, "right_wall": right_wall,
                            "top_surface": covered})
        filtered = all(not s["left_wall"] and not s["right_wall"] for s in samples)
        retained = all(s["left_wall"] and s["right_wall"] for s in samples)
        expected_filtered = gap <= threshold
        channels.append({
            "gap_mm": gap, "x_range": [left, right], "samples": samples,
            "filtered": filtered, "expected_filtered": expected_filtered,
            "matches": all(s["top_surface"] for s in samples)
            and (filtered if expected_filtered else retained),
        })
        cursor = right
    return channels


def check_min_width_top_surface(gcode_path: Path | str, expected_value: str):
    """Check each known channel, independent of fill segmentation/role blocks."""
    details = {"method": "L2 - Local top-surface channel walls", "expected_setting": expected_value}
    config = GCodeParser(str(gcode_path)).load_config()
    details["config_value"] = config.get("min_width_top_surface")
    try:
        percent = float(str(expected_value).rstrip("%"))
        configured = float(str(details["config_value"]).rstrip("%"))
    except (TypeError, ValueError):
        return False, None, {**details, "error": "missing or invalid percentage"}
    if not math.isfinite(percent) or percent < 0 or configured != percent:
        return False, None, {**details, "error": "percentage does not match configuration"}

    behavior = BehaviorGCode(gcode_path)
    layers = sorted(behavior.role_layers("Top surface"))
    if len(layers) < 2:
        return False, None, {**details, "error": "missing intermediate/final top layers"}
    moves = [move for move in behavior.extrusion_moves() if move.layer == layers[0]]
    outer = [move for move in moves if move.role == "Outer wall"]
    outer_width = median(move.width for move in outer if move.width)
    wall_width = median(move.width for move in moves if move.role == "Inner wall" and move.width)
    if not outer or not outer_width or not wall_width:
        return False, None, {**details, "error": "missing wall geometry/width"}
    xmin = min(min(m.x0, m.x) for m in outer) - outer_width / 2
    xmax = max(max(m.x0, m.x) for m in outer) + outer_width / 2
    ymin = min(min(m.y0, m.y) for m in outer) - outer_width / 2
    ymax = max(max(m.y0, m.y) for m in outer) + outer_width / 2
    if abs(xmax - xmin - 40) > 0.1 or abs(ymax - ymin - 24) > 0.1:
        return False, None, {**details, "error": "expected 40 x 24 mm width-ladder fixture"}
    # Arachne removes regions narrower than twice its perimeter_width*pct/400
    # erosion radius. perimeter_width is the INNER-wall flow, not the outer one.
    threshold = wall_width * percent / 200
    channels = _channel_evidence(moves, xmin, ymin, ymax, threshold, wall_width)
    actual = sum(channel["filtered"] for channel in channels)
    details.update({"representative_layer": layers[0], "channels": channels,
                    "filtered_channel_count": actual,
                    "expected_filtered_channels": sum(c["expected_filtered"] for c in channels),
                    "effective_width_limit_mm": threshold, "observed_wall_width_mm": wall_width})
    return all(channel["matches"] for channel in channels), str(actual), details
