"""Deposited wipe-tower geometry, independent of tool-change travel paths."""

import math
import re
from collections import defaultdict
from pathlib import Path


_COMMAND = re.compile(r"^([GMT]\d+(?:\.\d+)?)", re.IGNORECASE)
_VALUE = re.compile(r"([XYZEFIJKRP])\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))", re.IGNORECASE)


def _arc_points(start, end, values, clockwise, absolute_center):
    """Return endpoints and XY extrema on an I/J arc, including full circles."""
    if "R" in values or not ({"I", "J"} & values.keys()):
        raise ValueError("Tower arcs require an I/J center; radius-format arcs are unsupported")
    if values.get("P", 1) != 1:
        raise ValueError("Multi-turn deposited tower arcs are unsupported")
    cx = values.get("I", start["X"] if absolute_center else 0)
    cy = values.get("J", start["Y"] if absolute_center else 0)
    if not absolute_center:
        cx, cy = cx + start["X"], cy + start["Y"]
    radius = math.hypot(start["X"] - cx, start["Y"] - cy)
    end_radius = math.hypot(end["X"] - cx, end["Y"] - cy)
    if radius <= 1e-9 or abs(radius - end_radius) > max(0.02, radius * 0.001):
        raise ValueError("Invalid deposited tower arc radius")
    first = math.atan2(start["Y"] - cy, start["X"] - cx)
    last = math.atan2(end["Y"] - cy, end["X"] - cx)
    direction = -1 if clockwise else 1
    sweep = ((last - first) * direction) % math.tau
    if math.hypot(end["X"] - start["X"], end["Y"] - start["Y"]) < 1e-9:
        sweep = math.tau
    points = [(start["X"], start["Y"], start["Z"]), (end["X"], end["Y"], end["Z"])]
    for angle in (0, math.pi / 2, math.pi, 3 * math.pi / 2):
        distance = ((angle - first) * direction) % math.tau
        if distance <= sweep + 1e-9:
            z = start["Z"] + (end["Z"] - start["Z"]) * distance / max(sweep, 1e-9)
            points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle), z))
    return points


def _segment(start, end, values, command, plane, absolute_center):
    if command in {"G2", "G3"}:
        if plane != "G17":
            raise ValueError("Deposited tower arcs must use the XY plane (G17)")
        points = _arc_points(start, end, values, command == "G2", absolute_center)
    else:
        if math.hypot(end["X"] - start["X"], end["Y"] - start["Y"]) < 1e-9:
            return None
        points = [(start["X"], start["Y"], start["Z"]), (end["X"], end["Y"], end["Z"])]
    result = {axis.lower(): end[axis] for axis in "XYZ"}
    result["e"] = end["E"] - start["E"]
    # One record per extrusion, not per sampled arc point: preserve count semantics.
    for index, axis in enumerate("xyz"):
        result[f"min_{axis}"] = min(point[index] for point in points)
        result[f"max_{axis}"] = max(point[index] for point in points)
    return result


class _MotionState:
    def __init__(self):
        self.position = dict.fromkeys("XYZE", 0.0)
        self.relative_xyz = False
        self.relative_e = False
        self.absolute_center = False
        self.plane = "G17"

    def consume(self, command, values, in_tower):
        if command in {"G90", "G91"}:
            self.relative_xyz = command == "G91"
        elif command in {"M82", "M83"}:
            self.relative_e = command == "M83"
        elif command in {"G90.1", "G91.1"}:
            self.absolute_center = command == "G90.1"
        elif command in {"G17", "G18", "G19"}:
            self.plane = command
        elif command == "G20":
            raise ValueError("Tower shape analysis requires millimeter G-code")
        elif command == "G92":
            self.position.update({axis: value for axis, value in values.items() if axis in self.position})
        elif command in {"G0", "G1", "G2", "G3"}:
            start = self.position.copy()
            for axis in "XYZE":
                if axis in values:
                    relative = self.relative_e if axis == "E" else self.relative_xyz
                    self.position[axis] = start[axis] + values[axis] if relative else values[axis]
            if in_tower and command != "G0" and self.position["E"] - start["E"] > 1e-9:
                return _segment(start, self.position, values, command, self.plane, self.absolute_center)
        return None


def extract_tower_paths(gcode_path: Path | str) -> list[dict[str, float]]:
    """Track every move but retain only positive XY tower extrusion geometry."""
    state = _MotionState()
    paths = []
    in_tower = False
    with Path(gcode_path).open(encoding="utf-8") as stream:
        for number, raw in enumerate(stream, 1):
            line = raw.strip()
            if line.startswith(";TYPE:"):
                in_tower = line.partition(":")[2].strip() == "Prime tower"
            elif line == "; WIPE_TOWER_START":
                in_tower = True
            elif line == "; WIPE_TOWER_END":
                in_tower = False
            code = line.split(";", 1)[0].strip()
            match = _COMMAND.match(code)
            if not match:
                continue
            command = match[1].upper()
            # Normalize G01 etc., without conflating G90 with G90.1.
            command = command[0] + str(int(command[1:])) if "." not in command else command
            values = {axis.upper(): float(value) for axis, value in _VALUE.findall(code[match.end():])}
            try:
                path = state.consume(command, values, in_tower)
            except ValueError as exc:
                raise ValueError(f"{gcode_path}:{number}: {exc}") from exc
            if path is not None:
                paths.append(path)
    return paths


def _bounds(paths):
    return {f"{edge}_{axis}": operation(p.get(f"{edge}_{axis}", p[axis]) for p in paths)
            for edge, operation in (("min", min), ("max", max)) for axis in "xyz"}


def _dimensions(bounds):
    return {name: bounds[f"max_{axis}"] - bounds[f"min_{axis}"]
            for name, axis in (("width", "x"), ("depth", "y"), ("height", "z"))}


def _layer_dimensions(paths):
    layers = defaultdict(list)
    for path in paths:
        layers[round(path["z"], 4)].append(path)
    return {z: _dimensions(_bounds(points)) for z, points in layers.items()}


def compare_tower_paths(baseline_paths, test_paths, tolerance=0.1):
    """Compare deposited extents globally and at every actual printing height."""
    count_diff = abs(len(baseline_paths) - len(test_paths))
    ratio = count_diff / max(len(baseline_paths), 1)
    details = {"baseline_path_count": len(baseline_paths), "test_path_count": len(test_paths),
               "tolerance": tolerance, "path_count_diff": count_diff, "path_count_diff_ratio": ratio,
               "geometry": "positive XY extrusion, including arc extrema"}
    if not baseline_paths or not test_paths:
        return False, {**details, "message": "无法计算挤出边界框：擦拭塔挤出路径为空"}
    baseline_bounds, test_bounds = _bounds(baseline_paths), _bounds(test_paths)
    details.update(baseline_bounds=baseline_bounds, test_bounds=test_bounds)
    baseline_size, test_size = _dimensions(baseline_bounds), _dimensions(test_bounds)
    differences = {f"{key}_diff": abs(baseline_size[key] - test_size[key]) for key in baseline_size}
    details.update(differences)
    baseline_layers, test_layers = _layer_dimensions(baseline_paths), _layer_dimensions(test_paths)
    details.update(baseline_layer_count=len(baseline_layers), test_layer_count=len(test_layers))
    if baseline_layers.keys() != test_layers.keys():
        return False, {**details, "message": "擦拭塔挤出层高集合不匹配"}
    mismatches = [{"z": z, "baseline": baseline_layers[z], "test": test_layers[z]}
                  for z in sorted(baseline_layers)
                  if any(abs(baseline_layers[z][key] - test_layers[z][key]) > tolerance
                         for key in ("width", "depth"))]
    details["layer_mismatch_count"] = len(mismatches)
    details["layer_mismatches"] = mismatches[:5]
    if ratio > 0.1:
        return False, {**details, "message": f"挤出路径数量差异过大: {ratio:.2%}"}
    if any(value > tolerance for value in differences.values()) or mismatches:
        return False, {**details, "message": "擦拭塔挤出轮廓尺寸不匹配"}
    return True, {**details, "message": "Prime tower 挤出轮廓匹配"}


def check_cone_angle(config, expected):
    actual = config.get("wipe_tower_cone_angle")
    try:
        matches = math.isfinite(float(actual)) and abs(float(actual) - float(expected)) <= 0.01
    except (TypeError, ValueError):
        matches = False
    return matches, {"expected_cone_angle": expected, "actual_cone_angle": actual,
                     "cone_angle_passed": matches}
