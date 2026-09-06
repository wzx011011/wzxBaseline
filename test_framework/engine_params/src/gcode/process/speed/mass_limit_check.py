"""Validate mass limits over observable in-curve extrusion, not role blocks."""

import ast
import math
import re
from collections import defaultdict
from pathlib import Path

from engine_params.src.gcode.GCodeParser import GCodeParser
from engine_params.src.gcode.process.quality.behavior import BehaviorGCode


def _curve(raw):
    try:
        rows = ast.literal_eval(str(raw))
        if not isinstance(rows, list) or not rows:
            return []
        result = [tuple(float(v) for v in row) for row in rows if isinstance(row, (list, tuple))]
        if len(result) != len(rows) or any(len(r) not in (4, 5) for r in result):
            return []
        if any(not all(math.isfinite(v) for v in r) or r[0] < 0 or r[1] <= r[0]
               or r[2] <= 0 or r[3] <= 0 for r in result):
            return []
        if any(right[0] < left[1] for left, right in zip(result, result[1:])):
            return []
        return result
    except (TypeError, ValueError, SyntaxError):
        return []


def _number(config, key, default=0.0):
    value = config.get(key, default)
    if isinstance(value, (list, tuple)):
        value = value[0] if len(value) == 1 else None
    try:
        number = float(value)
        return number if math.isfinite(number) else default
    except (TypeError, ValueError):
        return default


def _acceleration_by_line(path):
    current = None
    values = {}
    for line_no, raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        body = raw.split(";", 1)[0].strip()
        if body.startswith("SET_VELOCITY_LIMIT "):
            match = re.search(r"\bACCEL=([\d.]+)", body)
            if match:
                current = float(match.group(1))
        elif body.startswith("M204 "):
            match = re.search(r"\bP([\d.]+)", body) or re.search(r"\bS([\d.]+)", body)
            if match:
                current = float(match.group(1))
        if current is not None:
            values[line_no] = current
    return values


def _endpoint(value):
    # SmoothSpeedAndAcc.cpp stores _MM2INT's result in double, without int().
    return value * 1000 + (0.5 if value > 0 else 0)


def _cap(rows, mass, initial, column):
    cap, previous = initial, initial
    for row in rows:
        lo, hi = _endpoint(row[0]), _endpoint(row[1])
        if mass >= lo:
            interpolated = previous + (row[column] - previous) * (min(mass, hi) - lo) / (hi - lo)
            cap = min(cap, previous, interpolated)
        previous = row[column]
    return cap


def check_mass_limit(gcode_path, expected_enabled, curve, diameter, density,
                     speed_tolerance=0.1, acc_tolerance=2.0):
    config = GCodeParser(str(gcode_path)).load_config()
    rows = _curve(curve)
    actual_enabled = str(config.get("acceleration_limit_mess_enable", "")).lower() in {"1", "true"}
    config_ok = ("acceleration_limit_mess_enable" in config
                 and actual_enabled == expected_enabled and bool(rows)
                 and _curve(config.get("acceleration_limit_mess")) == rows
                 and math.isclose(_number(config, "filament_diameter"), diameter, abs_tol=1e-6)
                 and math.isclose(_number(config, "filament_density"), density, abs_tol=1e-6)
                 and diameter > 0 and density > 0)
    details = {"expected_enabled": expected_enabled, "actual_enabled": actual_enabled,
               "config_match": config_ok, "sample_count": 0, "checked_layers": [],
               "mismatches_speed": [], "mismatches_acc": [], "missing_accel": [],
               "speed_limit_observed": False, "acceleration_limit_observed": False,
               "method": "L2 - Mass interval speed/acceleration bounds"}
    if not config_ok:
        return False, actual_enabled, {**details, "match": False, "note": "Configuration/curve/material mismatch."}
    if str(config.get("speed_limit_to_height_enable", "0")).lower() in {"1", "true"}:
        return False, actual_enabled, {**details, "match": False, "note": "Mass fixture must isolate height limiting."}

    behavior = BehaviorGCode(gcode_path)
    layers = defaultdict(list)
    for move in behavior.extrusion_moves():
        # Start/filament custom G-code is passed through, not charged to the
        # slicer's Extruder::used_filament() counter used by this feature.
        if move.role and move.role != "Custom":
            layers[move.layer].append(move)
    accelerations = _acceleration_by_line(gcode_path)
    grams_per_mm = math.pi * diameter ** 2 / 4 * density / 1000
    initial_speed = max(_number(config, key) for key in ("outer_wall_speed", "inner_wall_speed"))
    initial_acc = max(_number(config, key) for key in
                      ("default_acceleration", "inner_wall_acceleration", "outer_wall_acceleration"))
    mass = 0.0
    for layer, moves in sorted(layers.items()):
        start_mass = mass
        mass += sum(m.e for m in moves) * grams_per_mm
        # Only whole layers within an interpolation interval are sampled.
        # This bounds every possible path-start weight without inventing path
        # boundaries from ;TYPE or assuming a post-curve endpoint was visited.
        in_curve = any(_endpoint(r[0]) <= start_mass <= mass <= _endpoint(r[1]) for r in rows)
        if layer == 0 or (expected_enabled and not in_curve):
            continue
        for move in moves:
            prefix = {"Outer wall": "outer_wall", "Inner wall": "inner_wall"}.get(move.role)
            if not prefix:
                continue
            raw_speed = _number(config, prefix + "_speed")
            raw_acc = _number(config, prefix + "_acceleration") or _number(config, "default_acceleration")
            upper_speed, lower_acc, upper_acc = raw_speed, raw_acc, raw_acc
            if expected_enabled:
                upper_speed = min(raw_speed, _cap(rows, start_mass, initial_speed, 2))
                lower_acc = min(raw_acc, _cap(rows, mass, initial_acc, 3))
                upper_acc = min(raw_acc, _cap(rows, start_mass, initial_acc, 3))
            evidence = {"layer": layer, "line": move.line_no, "type": move.role,
                        "mass_range_g": [start_mass, mass]}
            details["sample_count"] += 1
            if layer not in details["checked_layers"]:
                details["checked_layers"].append(layer)
            if move.speed is None or not 0 < move.speed <= upper_speed + speed_tolerance:
                details["mismatches_speed"].append({**evidence, "actual": move.speed, "maximum": upper_speed})
            accel = accelerations.get(move.line_no)
            if accel is None:
                details["missing_accel"].append(evidence)
            elif not max(0, lower_acc - acc_tolerance) <= accel <= upper_acc + acc_tolerance or accel <= 0:
                details["mismatches_acc"].append({**evidence, "actual": accel, "expected_range": [lower_acc, upper_acc]})
            details["speed_limit_observed"] |= upper_speed < raw_speed - speed_tolerance
            details["acceleration_limit_observed"] |= upper_acc < raw_acc - acc_tolerance
    details["final_total_weight"] = mass
    ok = (details["sample_count"] > 0 and not details["mismatches_speed"]
          and not details["mismatches_acc"] and not details["missing_accel"]
          and (not expected_enabled or (details["speed_limit_observed"] and details["acceleration_limit_observed"])))
    details.update({"match": ok, "note": None if ok else "Missing effective in-curve samples or out-of-bound motion."})
    return ok, actual_enabled, details
