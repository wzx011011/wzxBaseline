"""Semantic (L2) metrics and baseline validation for support G-code tests."""

from __future__ import annotations

import json
import math
import re
from decimal import Decimal, InvalidOperation
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Sequence, Tuple


BASELINE_FILE = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "l2_baselines"
    / "support_7_1_0_release_c.json"
)

_MOVE_RE = re.compile(r"^G([0123])\b", re.IGNORECASE)
_TOKEN_RE = re.compile(r"\b([XYZEF])([+-]?(?:\d+(?:\.\d*)?|\.\d+))", re.IGNORECASE)
_TYPE_RE = re.compile(r"^;TYPE:(.+)$")
_Z_RE = re.compile(r"^;Z:([+-]?(?:\d+(?:\.\d*)?|\.\d+))")
_TOOL_RE = re.compile(r"^T(\d+)\s*$", re.IGNORECASE)
_FAN_RE = re.compile(r"^M106\b.*(?:\bS(\d+(?:\.\d*)?)\b)?", re.IGNORECASE)

_COMBINED_SUPPORT = "Support total"
_INTEGER_SUFFIXES = (
    ".block_count",
    ".layer_count",
    ".move_count",
    ".speed_unique",
    ".tool_count",
    ".tool_change_count",
)


def canonical_expected(value: Any) -> str:
    """Create a stable JSON key for a parameter's expected value."""
    if not isinstance(value, bool):
        try:
            number = Decimal(str(value).strip())
        except (InvalidOperation, ValueError):
            pass
        else:
            if number.is_finite():
                normalized = format(number.normalize(), "f")
                if "." in normalized:
                    normalized = normalized.rstrip("0").rstrip(".")
                return f"number:{normalized}"
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _percentile(values: Sequence[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _new_role_stats() -> Dict[str, Any]:
    return {
        "blocks": 0,
        "layers": set(),
        "z_values": set(),
        "moves": 0,
        "length": 0.0,
        "extrusion": 0.0,
        "segments": [],
        "speeds": [],
        "points": [],
        "orientation_length": [0.0] * 12,
        "tools": defaultdict(lambda: {"moves": 0, "length": 0.0, "extrusion": 0.0}),
        "fans": [],
        "layer_moves": defaultdict(int),
        "layer_length": defaultdict(float),
    }


def _record_extrusion(
    stats: Dict[str, Any],
    *,
    layer_index: int,
    z_value: float | None,
    start_xy: Tuple[float, float],
    end_xy: Tuple[float, float],
    length: float,
    extrusion: float,
    speed: float,
    tool: int,
    fan: float,
) -> None:
    stats["layers"].add(layer_index)
    if z_value is not None:
        stats["z_values"].add(z_value)
    stats["moves"] += 1
    stats["length"] += length
    stats["extrusion"] += extrusion
    stats["segments"].append(length)
    stats["speeds"].append(speed)
    stats["points"].extend((start_xy, end_xy))
    angle = math.atan2(end_xy[1] - start_xy[1], end_xy[0] - start_xy[0]) % math.pi
    orientation_bin = min(11, int(angle / math.pi * 12))
    stats["orientation_length"][orientation_bin] += length
    stats["tools"][tool]["moves"] += 1
    stats["tools"][tool]["length"] += length
    stats["tools"][tool]["extrusion"] += extrusion
    stats["fans"].append(fan)
    stats["layer_moves"][layer_index] += 1
    stats["layer_length"][layer_index] += length


def _round(value: float) -> float:
    return round(float(value), 5)


def _flatten_role(role: str, stats: Mapping[str, Any], output: Dict[str, float | int]) -> None:
    prefix = f"role.{role}"
    layers = sorted(stats["layers"])
    z_values = sorted(stats["z_values"])
    segments = list(stats["segments"])
    speeds = list(stats["speeds"])
    points = list(stats["points"])
    layer_moves = list(stats["layer_moves"].values())
    layer_lengths = list(stats["layer_length"].values())

    output[f"{prefix}.block_count"] = int(stats["blocks"])
    output[f"{prefix}.layer_count"] = len(layers)
    output[f"{prefix}.move_count"] = int(stats["moves"])
    output[f"{prefix}.path_length"] = _round(stats["length"])
    output[f"{prefix}.extrusion"] = _round(stats["extrusion"])

    if points:
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        width = max(xs) - min(xs)
        height = max(ys) - min(ys)
        output[f"{prefix}.bbox_width"] = _round(width)
        output[f"{prefix}.bbox_height"] = _round(height)
        output[f"{prefix}.bbox_area"] = _round(width * height)
    else:
        output[f"{prefix}.bbox_width"] = 0.0
        output[f"{prefix}.bbox_height"] = 0.0
        output[f"{prefix}.bbox_area"] = 0.0

    output[f"{prefix}.segment_p50"] = _round(_percentile(segments, 0.5))
    output[f"{prefix}.segment_p90"] = _round(_percentile(segments, 0.9))
    output[f"{prefix}.segment_max"] = _round(max(segments, default=0.0))
    output[f"{prefix}.speed_min"] = _round(min(speeds, default=0.0))
    output[f"{prefix}.speed_p50"] = _round(_percentile(speeds, 0.5))
    output[f"{prefix}.speed_max"] = _round(max(speeds, default=0.0))
    output[f"{prefix}.speed_unique"] = len({round(speed, 3) for speed in speeds})
    output[f"{prefix}.fan_p50"] = _round(_percentile(stats["fans"], 0.5))
    output[f"{prefix}.layer_moves_p50"] = _round(_percentile(layer_moves, 0.5))
    output[f"{prefix}.layer_moves_max"] = int(max(layer_moves, default=0))
    output[f"{prefix}.layer_length_p50"] = _round(_percentile(layer_lengths, 0.5))
    output[f"{prefix}.layer_length_max"] = _round(max(layer_lengths, default=0.0))

    if z_values:
        gaps = [right - left for left, right in zip(z_values, z_values[1:])]
        output[f"{prefix}.z_first"] = _round(z_values[0])
        output[f"{prefix}.z_last"] = _round(z_values[-1])
        output[f"{prefix}.z_gap_min"] = _round(min(gaps, default=0.0))
        output[f"{prefix}.z_gap_p50"] = _round(_percentile(gaps, 0.5))
        output[f"{prefix}.z_gap_max"] = _round(max(gaps, default=0.0))
    else:
        for suffix in ("z_first", "z_last", "z_gap_min", "z_gap_p50", "z_gap_max"):
            output[f"{prefix}.{suffix}"] = 0.0

    total_length = float(stats["length"])
    for index, length in enumerate(stats["orientation_length"]):
        ratio = length / total_length if total_length > 0 else 0.0
        output[f"{prefix}.orientation_{index:02d}_ratio"] = _round(ratio)

    output[f"{prefix}.tool_count"] = len(stats["tools"])
    for tool, tool_stats in sorted(stats["tools"].items()):
        output[f"{prefix}.tool_{tool}_moves"] = int(tool_stats["moves"])
        output[f"{prefix}.tool_{tool}_length"] = _round(tool_stats["length"])
        output[f"{prefix}.tool_{tool}_extrusion"] = _round(tool_stats["extrusion"])


def analyze_support_gcode(gcode_path: Path | str) -> Dict[str, float | int]:
    """Extract deterministic behavior metrics from executable G-code only.

    UUIDs, object IDs, timestamps, thumbnails and the CONFIG block are ignored.
    """
    role_stats: Dict[str, Dict[str, Any]] = defaultdict(_new_role_stats)
    combined_stats = role_stats[_COMBINED_SUPPORT]
    current_role = "Unclassified"
    current_tool = 0
    current_fan = 0.0
    current_speed = 0.0
    current_layer = -1
    current_layer_z: float | None = None
    x = y = z = e_position = 0.0
    xyz_relative = False
    extrusion_relative = True
    tool_changes = 0
    in_executable = False

    with Path(gcode_path).open("r", encoding="utf-8", errors="ignore") as stream:
        for raw_line in stream:
            line = raw_line.strip()
            if line == "; EXECUTABLE_BLOCK_START":
                in_executable = True
                continue
            if line == "; EXECUTABLE_BLOCK_END":
                break
            if not in_executable:
                continue
            if line == ";LAYER_CHANGE":
                current_layer += 1
                current_layer_z = None
                continue
            z_match = _Z_RE.match(line)
            if z_match:
                current_layer_z = float(z_match.group(1))
                continue
            type_match = _TYPE_RE.match(line)
            if type_match:
                current_role = type_match.group(1).strip()
                role_stats[current_role]["blocks"] += 1
                if current_role in {"Support", "Support interface", "Support transition"}:
                    combined_stats["blocks"] += 1
                continue
            tool_match = _TOOL_RE.match(line)
            if tool_match:
                new_tool = int(tool_match.group(1))
                if new_tool != current_tool:
                    tool_changes += 1
                current_tool = new_tool
                continue
            if line.startswith("G90"):
                xyz_relative = False
                continue
            if line.startswith("G91"):
                xyz_relative = True
                continue
            if line.startswith("M82"):
                extrusion_relative = False
                continue
            if line.startswith("M83"):
                extrusion_relative = True
                continue
            fan_match = _FAN_RE.match(line)
            if fan_match:
                current_fan = float(fan_match.group(1) or 255.0) / 255.0
                continue
            if line.startswith("M107"):
                current_fan = 0.0
                continue
            move_match = _MOVE_RE.match(line)
            if not move_match:
                continue

            tokens = {key.upper(): float(value) for key, value in _TOKEN_RE.findall(line)}
            if "F" in tokens:
                current_speed = tokens["F"] / 60.0
            new_x = x + tokens.get("X", 0.0) if xyz_relative else tokens.get("X", x)
            new_y = y + tokens.get("Y", 0.0) if xyz_relative else tokens.get("Y", y)
            new_z = z + tokens.get("Z", 0.0) if xyz_relative else tokens.get("Z", z)
            if "E" in tokens:
                extrusion = tokens["E"] if extrusion_relative else tokens["E"] - e_position
                e_position = e_position + tokens["E"] if extrusion_relative else tokens["E"]
            else:
                extrusion = 0.0

            length = math.hypot(new_x - x, new_y - y)
            if extrusion > 1e-9 and length > 1e-9:
                stats = role_stats[current_role]
                kwargs = {
                    "layer_index": current_layer,
                    "z_value": current_layer_z,
                    "start_xy": (x, y),
                    "end_xy": (new_x, new_y),
                    "length": length,
                    "extrusion": extrusion,
                    "speed": current_speed,
                    "tool": current_tool,
                    "fan": current_fan,
                }
                _record_extrusion(stats, **kwargs)
                if current_role in {"Support", "Support interface", "Support transition"}:
                    _record_extrusion(combined_stats, **kwargs)
            x, y, z = new_x, new_y, new_z

    output: Dict[str, float | int] = {
        "global.layer_count": current_layer + 1,
        "global.tool_change_count": tool_changes,
    }
    for role, stats in sorted(role_stats.items()):
        _flatten_role(role, stats, output)
    return output


def metric_matches(
    key: str,
    actual: float | int | None,
    expected: float | int | Mapping[str, float | int] | None,
    relative_tolerance: float = 0.01,
) -> bool:
    if actual is None or expected is None:
        return actual == expected
    if isinstance(expected, Mapping) and "min" in expected and "max" in expected:
        low = float(expected["min"])
        high = float(expected["max"])
        scale = max(abs(low), abs(high))
        absolute_tolerance = 0.05 if ".speed_" in key else 0.02
        if relative_tolerance >= 0.1 and key.endswith(".block_count"):
            absolute_tolerance = 1.0
        padding = max(absolute_tolerance, scale * relative_tolerance)
        return low - padding <= float(actual) <= high + padding
    if key.endswith(_INTEGER_SUFFIXES) or re.search(r"\.tool_\d+_moves$", key):
        return int(actual) == int(expected)
    expected_float = float(expected)
    actual_float = float(actual)
    absolute_tolerance = 0.05 if ".speed_" in key else 0.02
    return math.isclose(actual_float, expected_float, rel_tol=0.01, abs_tol=absolute_tolerance)


def validate_support_l2_behavior(
    gcode_path: Path | str,
    parameter: str,
    expected_value: Any,
    baseline_path: Path | str = BASELINE_FILE,
) -> Tuple[bool, Dict[str, Any]]:
    """Compare semantic metrics with a trusted 7.1.0.ReleaseC baseline."""
    path = Path(baseline_path)
    if not path.is_file():
        return False, {"error": f"L2 baseline not found: {path}"}
    baseline = json.loads(path.read_text(encoding="utf-8"))
    parameter_data = baseline.get("parameters", {}).get(parameter)
    if not parameter_data:
        return False, {"error": f"parameter missing from L2 baseline: {parameter}"}

    expected_key = canonical_expected(expected_value)
    candidates = [
        entry for entry in parameter_data.get("entries", [])
        if entry.get("expected_key") == expected_key
    ]
    if not candidates:
        return False, {
            "error": f"expected value missing from L2 baseline: {parameter}={expected_key}",
        }

    metrics = analyze_support_gcode(gcode_path)
    checks = parameter_data.get("checks", [])
    relative_tolerance = float(parameter_data.get("relative_tolerance", 0.01))
    candidate_results = []
    for candidate in candidates:
        mismatches = []
        for key in checks:
            actual = metrics.get(key)
            expected = candidate.get("metrics", {}).get(key)
            if not metric_matches(key, actual, expected, relative_tolerance):
                mismatches.append({"metric": key, "expected": expected, "actual": actual})
        candidate_results.append((len(mismatches), candidate, mismatches))
    _, best_candidate, best_mismatches = min(candidate_results, key=lambda item: item[0])
    return not best_mismatches, {
        "detection_method": "Level 2 - semantic G-code baseline",
        "baseline_generator": baseline.get("generator", {}),
        "parameter": parameter,
        "expected_key": expected_key,
        "matched_project": best_candidate.get("project_name"),
        "checks": checks,
        "mismatches": best_mismatches,
    }
