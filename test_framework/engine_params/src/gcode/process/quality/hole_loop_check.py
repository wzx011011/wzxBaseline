"""Arc-aware geometry for the printable-overhang blind-hole fixture only."""

import math
import re
from collections import defaultdict

from engine_params.src.gcode.GCodeParser import GCodeParser
from engine_params.src.gcode.process.quality.behavior import BehaviorGCode


def _path_geometry(moves, lines):
    points, length = [], 0.0
    for move in moves:
        points.extend(((move.x0, move.y0), (move.x, move.y)))
        if move.command not in {"G2", "G3"}:
            length += move.xy_length
            continue
        body = lines[move.line_no - 1].split(";", 1)[0]
        offsets = {k: float(v) for k, v in re.findall(
            r"\b([IJR])([-+]?(?:\d+(?:\.\d*)?|\.\d+))", body, re.I)}
        offsets = {k.upper(): v for k, v in offsets.items()}
        if "R" in offsets or not {"I", "J"} & offsets.keys():
            raise ValueError("Expected relative I/J arc centers in hole fixture")
        i, j = offsets.get("I", 0.0), offsets.get("J", 0.0)
        cx, cy = move.x0 + i, move.y0 + j
        radius = math.hypot(i, j)
        if radius <= 0 or abs(math.hypot(move.x - cx, move.y - cy) - radius) > 0.01:
            raise ValueError("Invalid hole arc radius/end point")
        start = math.atan2(move.y0 - cy, move.x0 - cx)
        end = math.atan2(move.y - cy, move.x - cx)
        direction = 1 if move.command == "G3" else -1
        sweep = ((end - start) * direction) % math.tau
        if move.xy_length <= 1e-9:
            sweep = math.tau
        for angle in (0, math.pi / 2, math.pi, 3 * math.pi / 2):
            if ((angle - start) * direction) % math.tau <= sweep + 1e-9:
                points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
        length += radius * sweep
    xs, ys = zip(*points)
    return (min(xs), max(xs), min(ys), max(ys)), length


def check_printable_hole_loops(gcode_path, expected_value, tolerance=0.01):
    details = {"method": "L2 - Arc-aware retained hole-loop count", "area_threshold": expected_value}
    try:
        config = GCodeParser(str(gcode_path)).load_config()
        expected = float(expected_value)
        configured = float(config.get("make_overhang_printable_hole_size"))
    except (TypeError, ValueError):
        return False, None, {**details, "error": "Missing or invalid hole area threshold"}
    if not math.isfinite(expected) or expected < 0 or configured != expected:
        return False, None, {**details, "error": "Hole area threshold configuration mismatch"}
    behavior = BehaviorGCode(gcode_path)
    if not behavior.layers:
        return False, None, {**details, "error": "Missing printable layers"}
    lines = behavior.path.read_text(encoding="utf-8", errors="replace").splitlines()
    if any(re.match(r"^\s*G90\.1(?:\s|$)", line, re.I) for line in lines):
        return False, None, {**details, "error": "Absolute arc centers are unsupported by this fixture check"}
    middle = len(behavior.layers) // 2
    paths = defaultdict(list)
    # Do not use chord-based is_extrusion/min_length: a full circle has a zero
    # chord, and an almost-full circle can have a very short chord.
    for move in behavior.moves:
        if (move.layer == middle and move.role == "Outer wall" and move.e > 1e-9
                and not move.wipe and (move.xy_length > 1e-9 or move.command in {"G2", "G3"})):
            paths[move.path].append(move)
    diameters, evidence, body_count = [], [], 0
    try:
        for moves in paths.values():
            bbox, length = _path_geometry(moves, lines)
            diameter = min(bbox[1] - bbox[0], bbox[3] - bbox[2])
            if length < 1.0:
                continue
            if 1.0 <= diameter <= 5.5:
                # The fixture leaves a small seam gap, not an open arc/line.
                if math.hypot(moves[-1].x - moves[0].x0, moves[-1].y - moves[0].y0) > 0.1:
                    continue
                diameters.append(diameter)
                evidence.append({"line": moves[0].line_no, "bounds": bbox,
                                 "diameter": diameter, "length": length})
            elif diameter > 5.5:
                body_count += 1
    except ValueError as error:
        return False, None, {**details, "error": str(error)}
    expected_count = sum(area < expected - tolerance for area in (math.pi, math.pi * 2.25, math.pi * 4))
    observed = len(diameters)
    details.update({"observed_hole_count": observed, "observed_diameters": diameters,
                    "expected_hole_count": expected_count, "representative_layer": middle,
                    "body_loop_count": body_count, "hole_evidence": evidence})
    return observed == expected_count and body_count == 3, float(observed), details
