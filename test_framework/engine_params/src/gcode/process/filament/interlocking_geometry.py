"""Read extruded, tool-labelled outer contours for interlocking regression checks."""

from __future__ import annotations

import math
import re
from pathlib import Path

from engine_params.src.gcode.layer_comments import parse_layer_z


_TOKEN = re.compile(r"\b([XYZEFIJR])([+-]?(?:\d+(?:\.\d*)?|\.\d+))", re.I)


def _arc_segments(start, end, tokens, clockwise):
    if "R" in tokens or not ({"I", "J"} & tokens.keys()):
        raise ValueError("Outer-wall arc requires I/J centre offsets")
    cx, cy = start[0] + tokens.get("I", 0), start[1] + tokens.get("J", 0)
    radius = math.hypot(start[0] - cx, start[1] - cy)
    if radius <= 0 or abs(math.hypot(end[0] - cx, end[1] - cy) - radius) > 0.02:
        raise ValueError("Invalid outer-wall arc radius")
    angle = math.atan2(start[1] - cy, start[0] - cx)
    sweep = (math.atan2(end[1] - cy, end[0] - cx) - angle) % math.tau
    if clockwise:
        sweep -= math.tau
    elif sweep == 0:
        sweep = math.tau
    # Chords no longer than 0.05 mm, well below the contour comparison tolerance.
    count = max(2, math.ceil(abs(sweep) * radius / 0.05))
    previous = start
    for index in range(1, count + 1):
        theta = angle + sweep * index / count
        point = end if index == count else (cx + radius * math.cos(theta), cy + radius * math.sin(theta))
        yield [*previous, *point]
        previous = point


class _Motion:
    def __init__(self):
        self.x = self.y = self.e = 0.0
        self.relative_xyz = False
        self.relative_e = False

    def consume(self, command, tokens, keep):
        if command == "G92":
            self.x, self.y, self.e = (tokens.get(k, v) for k, v in zip("XYE", (self.x, self.y, self.e)))
            return []
        if command not in ("G0", "G1", "G2", "G3"):
            return []
        start = (self.x, self.y)
        end = tuple(v + tokens.get(k, 0) if self.relative_xyz else tokens.get(k, v)
                    for k, v in zip("XY", start))
        extrusion = tokens.get("E", 0) if self.relative_e else tokens.get("E", self.e) - self.e
        self.e = self.e + tokens.get("E", 0) if self.relative_e else tokens.get("E", self.e)
        self.x, self.y = end
        if not keep or extrusion <= 0:
            return []
        if command in ("G2", "G3"):
            return list(_arc_segments(start, end, tokens, command == "G2"))
        return [[*start, *end]] if start != end else []


def read_outer_contours(gcode_path: Path | str) -> list[dict]:
    """Preserve layer indices and tools; omit travel, infill, supports and prime tower."""
    motion = _Motion()
    layers = []
    role, tool = "", 0
    with Path(gcode_path).open(encoding="utf-8", errors="strict") as stream:
        for raw in stream:
            line = raw.strip()
            if line in ("; CONFIG_BLOCK_START", "; EXECUTABLE_BLOCK_END"):
                break
            if line == ";LAYER_CHANGE":
                layers.append({"z": None, "tools": {}})
                role = ""
            elif (height := parse_layer_z(line)) is not None and layers:
                layers[-1]["z"] = height
            elif line.startswith(";TYPE:"):
                role = line[6:].strip()
            elif re.fullmatch(r"T\d+(?:\s*;.*)?", line):
                tool = int(line.split(";")[0][1:])
            elif line and not line.startswith(";"):
                code = line.split(";")[0]
                command = code.split()[0].upper()
                if command in ("M82", "M83"):
                    motion.relative_e = command == "M83"
                elif command in ("G90", "G91"):
                    motion.relative_xyz = command == "G91"
                else:
                    tokens = {k.upper(): float(v) for k, v in _TOKEN.findall(code)}
                    segments = motion.consume(command, tokens, bool(layers) and role == "Outer wall")
                    if segments:
                        layers[-1]["tools"].setdefault(str(tool), []).extend(segments)
    if not layers or any(layer["z"] is None for layer in layers):
        raise ValueError("Missing layer heights or layer markers in interlocking G-code")
    if not any(layer["tools"] for layer in layers):
        raise ValueError("No extruded outer contours in interlocking G-code")
    return layers


def _samples(segment, spacing):
    x, y, end_x, end_y = segment
    count = max(1, math.ceil(math.hypot(end_x - x, end_y - y) / spacing))
    for index in range(count + 1):
        yield x + (end_x - x) * index / count, y + (end_y - y) * index / count


def _distance_squared(point, segment):
    x, y, end_x, end_y = segment
    dx, dy = end_x - x, end_y - y
    denominator = dx * dx + dy * dy
    fraction = max(0, min(1, ((point[0] - x) * dx + (point[1] - y) * dy) / denominator)) if denominator else 0
    return (point[0] - x - fraction * dx) ** 2 + (point[1] - y - fraction * dy) ** 2


def contour_mismatch(source, target, tolerance=0.08, sample_spacing=0.1):
    """Sample source against target segments; independent of seam or segment order."""
    cell_size = max(1.0, tolerance * 2)
    grid = {}
    for index, segment in enumerate(target):
        cells = {(math.floor(x / cell_size), math.floor(y / cell_size))
                 for x, y in _samples(segment, cell_size / 2)}
        for cell in cells:
            grid.setdefault(cell, []).append(index)
    for segment in source:
        for point in _samples(segment, sample_spacing):
            cx, cy = (math.floor(v / cell_size) for v in point)
            indices = {index for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                       for index in grid.get((cx + dx, cy + dy), [])}
            if not any(_distance_squared(point, target[index]) <= tolerance ** 2 for index in indices):
                return {"point": [round(v, 4) for v in point], "tolerance_mm": tolerance}
    return None


def compare_contours(actual, reference, tolerance=0.08):
    """Both directions matter: reject missing teeth as well as extra contours."""
    if set(actual) != set(reference):
        return {"error": "outer-wall tools differ", "actual_tools": sorted(actual),
                "expected_tools": sorted(reference)}
    for tool in sorted(reference):
        for direction, source, target in (
            ("missing_reference_contour", reference[tool], actual[tool]),
            ("unexpected_actual_contour", actual[tool], reference[tool]),
        ):
            if mismatch := contour_mismatch(source, target, tolerance):
                return {"tool": tool, "direction": direction, **mismatch}
    return None
