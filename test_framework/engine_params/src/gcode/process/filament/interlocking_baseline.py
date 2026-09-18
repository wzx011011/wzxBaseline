"""Reviewed, per-case geometric references for the interlocking parameter suite."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .interlocking_geometry import compare_contours, read_outer_contours


BASELINE_FILE = Path(__file__).resolve().parents[4] / "data/l2_baselines/interlocking_7_2_2.json"


def reference_layer_indices(count: int) -> list[int]:
    """Eight consecutive middle layers cover beam periods 2, 4 and 6 in this suite."""
    start = max(0, count // 2 - 1)
    return sorted({count // 4, 3 * count // 4, *range(start, min(count, start + 8))})


def make_geometry_reference(gcode_path: Path | str) -> dict:
    """Offline reference creation only; the runtime validator never updates baselines."""
    layers = read_outer_contours(gcode_path)
    selected = reference_layer_indices(len(layers))
    return {
        "layer_heights": [layer["z"] for layer in layers],
        "layers": [{"index": index, "tools": {
            tool: [[round(v, 5) for v in segment] for segment in segments]
            for tool, segments in layers[index]["tools"].items()
        }} for index in selected],
    }


def _resolve_reference(entries, parameter, gcode_path, baseline_id):
    if baseline_id is not None:
        return entries.get(baseline_id), baseline_id
    matches = []
    for key in entries:
        prefix, project = key.split("/", 1)
        if prefix == parameter:
            token = re.sub(r"[^A-Za-z0-9_.-]+", "_", project)
            if re.fullmatch(rf"test_{re.escape(parameter)}_{re.escape(token)}(?:_+\d+)?", Path(gcode_path).stem):
                matches.append(key)
    return (entries[matches[0]], matches[0]) if len(matches) == 1 else (None, None)


def validate_interlocking_geometry(gcode_path, parameter, expected_value, baseline_id=None,
                                   baseline_path=BASELINE_FILE):
    details = {"detection_method": "L2 - per-layer, per-material outer contours"}
    try:
        baseline = json.loads(Path(baseline_path).read_text(encoding="utf-8"))
        if baseline.get("schema_version") != 1:
            raise ValueError("Unsupported interlocking reference schema")
        entry, key = _resolve_reference(baseline["entries"], parameter, gcode_path, baseline_id)
        if entry is None:
            return False, {**details, "error": "Missing or ambiguous interlocking geometry reference",
                           "baseline_id": baseline_id}
        details["baseline_id"] = key
        if entry["parameter"] != parameter or entry["expected_value"] != expected_value:
            return False, {**details, "error": "Reference parameter/value does not match test expectation"}
        layers = read_outer_contours(gcode_path)
        heights = entry["geometry"]["layer_heights"]
        if len(layers) != len(heights) or any(abs(layer["z"] - z) > 0.001 for layer, z in zip(layers, heights)):
            return False, {**details, "error": "Layer count or heights differ from geometry reference",
                           "actual_layer_count": len(layers), "expected_layer_count": len(heights)}
        references = entry["geometry"]["layers"]
        if [layer["index"] for layer in references] != reference_layer_indices(len(layers)):
            return False, {**details, "error": "Incomplete reference layer coverage"}
        tolerance = float(baseline["tolerance_mm"])
        if not 0 < tolerance <= 0.08:
            raise ValueError("Interlocking reference tolerance must be in (0, 0.08] mm")
        mismatches = []
        for reference in references:
            index = reference["index"]
            if len(reference["tools"]) < 2 or any(not segments for segments in reference["tools"].values()):
                raise ValueError("Reference must contain extruded contours from multiple materials")
            mismatch = compare_contours(layers[index]["tools"], reference["tools"], tolerance)
            if mismatch:
                mismatches.append({"layer_index": index, "z": layers[index]["z"], **mismatch})
        details.update({"reference_version": baseline["generator"]["version"],
                        "tolerance_mm": tolerance, "checked_layers": len(references),
                        "mismatches": mismatches})
        return not mismatches, details
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        return False, {**details, "error": str(exc)}
