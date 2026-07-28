"""Generate the support L2 metric baseline from trusted exported G-code."""

from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from engine_params.src.gcode.process.support_l2_metrics import (
    BASELINE_FILE,
    analyze_support_gcode,
    canonical_expected,
)


# These are intentional equivalences observed in the trusted ReleaseC G-code,
# not a generic escape hatch.  Any new indistinguishable pair still fails
# baseline generation until it is investigated and documented here.
_ALLOWED_BEHAVIOR_ALIASES = {
    "max_bridge_length": {
        frozenset((canonical_expected("5"), canonical_expected("10"))):
            "both thresholds retain the same bridge contacts after geometric quantization",
    },
    "support_bottom_interface_spacing": {
        frozenset((canonical_expected("0.3"), canonical_expected("0.5"))):
            "support_new/TreeSupport.cpp reuses top interface spacing for the bottom interface",
    },
    "support_interface_pattern": {
        frozenset((canonical_expected("auto"), canonical_expected("rectilinear_interlaced"))):
            "auto resolves to the rectilinear-interlaced interface path for this geometry",
    },
    "support_interface_min_area": {
        frozenset((canonical_expected("0.25"), canonical_expected("5"))):
            "all canonical contact islands exceed both minimum-area thresholds",
    },
    "support_object_first_layer_gap": {
        frozenset((canonical_expected("0.2"), canonical_expected("0.3"))):
            "both clearances quantize to the same first-layer support boundary",
    },
    "support_object_xy_distance": {
        frozenset((canonical_expected("0.35"), canonical_expected("0.2"))):
            "both clearances quantize to the same support boundary for the canonical model",
        frozenset((canonical_expected("0.35"), canonical_expected("0.6"))):
            "both clearances quantize to the same support boundary for the canonical model",
    },
    "support_style": {
        frozenset((canonical_expected("default"), canonical_expected("grid"))):
            "default resolves to the grid normal-support style",
        frozenset((canonical_expected("tree_slim"), canonical_expected("tree_hybrid"))):
            "their aggregate path difference is below ReleaseC tree-layout variance for this geometry",
    },
    "support_type": {
        frozenset((canonical_expected("normal(auto)"), canonical_expected("normal(manual)"))):
            "the painted regions fully constrain the normal-support paths for this geometry",
        frozenset((canonical_expected("tree(auto)"), canonical_expected("tree(manual)"))):
            "the painted regions constrain both tree modes to the same stochastic layout range",
    },
    "raft_contact_distance": {
        frozenset((canonical_expected("0.1"), canonical_expected("0.2"))):
            "both values round to the same printable raft contact layer gap",
    },
    "tree_hybrid_cross_height": {
        frozenset((canonical_expected("0"), canonical_expected("5"))):
            "the compiled support_new path does not consume tree_hybrid_cross_height",
        frozenset((canonical_expected("0"), canonical_expected("10"))):
            "the compiled support_new path does not consume tree_hybrid_cross_height",
        frozenset((canonical_expected("5"), canonical_expected("10"))):
            "the compiled support_new path does not consume tree_hybrid_cross_height",
    },
    "tree_support_tip_diameter": {
        frozenset((canonical_expected("0.6"), canonical_expected("0.8"))):
            "support_new/TreeSupportCommon.hpp currently fixes the tip diameter at 0.8 mm",
        frozenset((canonical_expected("0.6"), canonical_expected("1"))):
            "support_new/TreeSupportCommon.hpp currently fixes the tip diameter at 0.8 mm",
        frozenset((canonical_expected("0.8"), canonical_expected("1"))):
            "support_new/TreeSupportCommon.hpp currently fixes the tip diameter at 0.8 mm",
    },
    "tree_support_branch_distance": {
        frozenset((canonical_expected("0.5"), canonical_expected("1"))):
            "both distances are below the effective branch sampling resolution",
        frozenset((canonical_expected("0.5"), canonical_expected("1.5"))):
            "their aggregate branch-layout difference is below ReleaseC sampling variance",
        frozenset((canonical_expected("1"), canonical_expected("1.5"))):
            "their aggregate branch-layout difference is below ReleaseC sampling variance",
    },
    "tree_support_wall_count": {
        frozenset((canonical_expected("0"), canonical_expected("1"))):
            "support generation clamps the wall count to at least one",
        frozenset((canonical_expected("0"), canonical_expected("2"))):
            "support_new normal support exposes no stable wall-count path difference",
        frozenset((canonical_expected("1"), canonical_expected("2"))):
            "support_new normal support exposes no stable wall-count path difference",
    },
    "tree_support_wall_count_tree": {
        frozenset((canonical_expected(0), canonical_expected(1))):
            "tree support generation clamps the wall count to at least one",
        frozenset((canonical_expected(0), canonical_expected(2))):
            "the extra tree wall is below ReleaseC aggregate layout variance",
        frozenset((canonical_expected(1), canonical_expected(2))):
            "the extra tree wall is below ReleaseC aggregate layout variance",
    },
}

_STOCHASTIC_TREE_PARAMETERS = {
    "support_type",
    "support_style",
    "support_base_pattern_tree",
    "max_bridge_length",
    "tree_hybrid_cross_height",
    "support_interface_min_area",
    "tree_support_branch_diameter",
    "tree_support_branch_angle",
    "tree_support_wall_count_tree",
    "tree_support_branch_distance",
    "tree_support_tip_diameter",
}

_SPEED_UNIQUE_PARAMETERS = {
    "support_interface_speed",
}


def _metric_allowed(parameter: str, key: str) -> bool:
    """Reject metrics that separate samples without matching the parameter."""
    if key.startswith("semantic."):
        return parameter == "support_top_z_distance" and key == "semantic.support_top_z_gap"
    if key.endswith(".speed_unique") and parameter not in _SPEED_UNIQUE_PARAMETERS:
        return False
    if parameter == "support_base_pattern":
        return key.startswith("role.Support") and ".orientation_" in key
    if parameter == "support_on_build_plate_only":
        return key.startswith("role.Support total.") and key.endswith((
            ".block_count",
            ".layer_count",
            ".move_count",
            ".path_length",
        ))
    return True


def _case_files(case_root: Path) -> Iterable[Tuple[str, dict]]:
    seen = set()
    for json_path in sorted(case_root.rglob("*.json")):
        parameter = json_path.stem
        if parameter in seen:
            continue
        seen.add(parameter)
        for case in json.loads(json_path.read_text(encoding="utf-8")).get("cases", []):
            yield parameter, case


def _find_gcode(
    gcode_root: Path,
    parameter: str,
    project_name: str,
    *,
    required: bool = True,
) -> Path | None:
    prefix = f"test_{parameter}_{project_name}__"
    matches = [path for path in gcode_root.rglob("*.gcode") if path.name.startswith(prefix)]
    if not matches and not required:
        return None
    if len(matches) != 1:
        raise RuntimeError(f"expected one G-code for {parameter}/{project_name}, got {matches}")
    return matches[0]


def _feature_priority(key: str) -> Tuple[int, str]:
    if key.startswith("semantic."):
        return 0, key
    if key.startswith("role.Support"):
        return 1, key
    if key.startswith("role.Bridge") or key.startswith("role.Internal Bridge"):
        return 2, key
    if ".tool_" in key or ".speed_" in key or ".z_" in key:
        return 3, key
    if ".orientation_" in key or ".bbox_" in key:
        return 4, key
    if key.startswith("role."):
        return 5, key
    return 6, key


def _metric_range(values: Sequence[float | int]) -> Dict[str, float | int]:
    return {"min": min(values), "max": max(values)}


def _range_padding(
    key: str,
    metric_range: Dict[str, float | int],
    relative_tolerance: float,
) -> float:
    scale = max(abs(float(metric_range["min"])), abs(float(metric_range["max"])))
    absolute_tolerance = (
        1.0
        if relative_tolerance >= 0.1 and key.endswith(".block_count")
        else 0.02
    )
    return max(absolute_tolerance, scale * relative_tolerance)


def _ranges_separate(
    key: str,
    left: Dict[str, float | int],
    right: Dict[str, float | int],
    relative_tolerance: float,
) -> bool:
    left_pad = _range_padding(key, left, relative_tolerance)
    right_pad = _range_padding(key, right, relative_tolerance)
    return (
        float(left["max"]) + left_pad < float(right["min"]) - right_pad
        or float(right["max"]) + right_pad < float(left["min"]) - left_pad
    )


def _select_checks(
    parameter: str,
    entries: List[Dict[str, Any]],
    maximum: int = 8,
) -> Tuple[List[str], List[Dict[str, Any]]]:
    pairs = {
        (left, right)
        for left, right in combinations(range(len(entries)), 2)
        if entries[left]["expected_key"] != entries[right]["expected_key"]
    }
    if not pairs:
        raise RuntimeError("parameter has no distinct expected values")

    allowed_aliases = _ALLOWED_BEHAVIOR_ALIASES.get(parameter, {})
    aliases = []
    behavior_pairs = set()
    for left, right in sorted(pairs):
        alias_key = frozenset((entries[left]["expected_key"], entries[right]["expected_key"]))
        reason = allowed_aliases.get(alias_key)
        if reason is None:
            behavior_pairs.add((left, right))
        else:
            aliases.append({
                "expected_values": [entries[left]["expected_value"], entries[right]["expected_value"]],
                "reason": reason,
            })

    relative_tolerance = 0.12 if parameter in _STOCHASTIC_TREE_PARAMETERS else 0.01

    keys = sorted(set.intersection(*(set(entry["all_metrics"]) for entry in entries)))
    keys = [
        key for key in keys
        if all(
            all(isinstance(value, (int, float)) for value in entry["all_metrics"][key])
            for entry in entries
        )
    ]
    keys = [key for key in keys if _metric_allowed(parameter, key)]
    separates: Dict[str, set] = {}
    for key in keys:
        covered = set()
        for pair in pairs:
            left = _metric_range(entries[pair[0]]["all_metrics"][key])
            right = _metric_range(entries[pair[1]]["all_metrics"][key])
            if pair in behavior_pairs and _ranges_separate(
                key,
                left,
                right,
                relative_tolerance,
            ):
                covered.add(pair)
        if covered:
            separates[key] = covered

    distinguishable = set().union(*separates.values()) if separates else set()
    undocumented = behavior_pairs - distinguishable
    if undocumented:
        left, right = min(undocumented)
        raise RuntimeError(
            "semantic metrics cannot distinguish an undocumented pair: "
            f"{entries[left]['expected_value']!r} / {entries[right]['expected_value']!r}"
        )

    selected: List[str] = []
    uncovered = set(distinguishable)
    while uncovered and len(selected) < maximum:
        choices = [
            (len(covered & uncovered), _feature_priority(key), key)
            for key, covered in separates.items()
            if key not in selected and covered & uncovered
        ]
        if not choices:
            break
        best_score = max(item[0] for item in choices)
        best = min(
            (item[2] for item in choices if item[0] == best_score),
            key=_feature_priority,
        )
        selected.append(best)
        uncovered -= separates[best]
    if uncovered:
        raise RuntimeError(f"semantic metrics cannot distinguish {len(uncovered)} expected-value pairs")

    # A fully aliased parameter still validates real executable behavior. Pick
    # stable support metrics even though they do not distinguish the aliases.
    if not selected:
        preferred = [
            key for key in keys
            if key.startswith("role.Support total.") and key.endswith((
                "move_count", "path_length", "layer_count", "block_count",
                "bbox_x_span", "bbox_y_span", "z_first", "z_last",
            ))
        ]
        selected.extend(sorted(preferred, key=_feature_priority)[:maximum])
    if not selected:
        raise RuntimeError("no executable support metrics are available")
    return selected, aliases


def generate(gcode_roots: Sequence[Path], case_root: Path, output: Path) -> Dict[str, Any]:
    parameters: Dict[str, Dict[str, Any]] = {}
    generated_by = None
    for parameter, case in _case_files(case_root):
        project_name = str(case["project_name"])
        first_gcode = _find_gcode(gcode_roots[0], parameter, project_name)
        gcode_paths = [first_gcode]
        for gcode_root in gcode_roots[1:]:
            replica = _find_gcode(
                gcode_root,
                parameter,
                project_name,
                required=False,
            )
            if replica is not None:
                gcode_paths.append(replica)
        if generated_by is None:
            with gcode_paths[0].open("r", encoding="utf-8", errors="ignore") as stream:
                generated_by = next((line.strip("; \n") for line in stream if "generated by" in line), None)
        expected_value = case.get("expected_value")
        entry = {
            "project_name": project_name,
            "input_3mf": case.get("input_3mf"),
            "expected_value": expected_value,
            "expected_key": canonical_expected(expected_value),
            "replica_count": len(gcode_paths),
            "all_metrics": {},
        }
        replica_metrics = [analyze_support_gcode(path) for path in gcode_paths]
        common_keys = set.intersection(*(set(metrics) for metrics in replica_metrics))
        entry["all_metrics"] = {
            key: [metrics[key] for metrics in replica_metrics]
            for key in common_keys
        }
        parameters.setdefault(parameter, {"entries": []})["entries"].append(entry)

    indistinguishable = []
    for parameter, data in parameters.items():
        try:
            checks, aliases = _select_checks(parameter, data["entries"])
        except RuntimeError as exc:
            indistinguishable.append(f"{parameter}: {exc}")
            continue
        data["checks"] = checks
        data["relative_tolerance"] = (
            0.12 if parameter in _STOCHASTIC_TREE_PARAMETERS else 0.01
        )
        if aliases:
            data["behavior_aliases"] = aliases
        for entry in data["entries"]:
            entry["metrics"] = {
                key: _metric_range(entry["all_metrics"][key])
                for key in checks
            }
            del entry["all_metrics"]

    if indistinguishable:
        raise RuntimeError("indistinguishable L2 behavior:\n" + "\n".join(indistinguishable))

    baseline = {
        "schema_version": 2,
        "generator": {
            "product": generated_by,
            "executable": r"D:\Program Files\Creality\Creality Print 7.1.0.ReleaseC\CrealityPrint.exe",
            "validation_level": "L2 semantic G-code metrics",
            "replica_root_count": len(gcode_roots),
        },
        "parameter_count": len(parameters),
        "case_count": sum(len(data["entries"]) for data in parameters.values()),
        "parameters": dict(sorted(parameters.items())),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(baseline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return baseline


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("gcode_roots", type=Path, nargs="+")
    parser.add_argument(
        "--case-root",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "case_input" / "process" / "support",
    )
    parser.add_argument("--output", type=Path, default=BASELINE_FILE)
    args = parser.parse_args()
    baseline = generate(args.gcode_roots, args.case_root, args.output)
    print(f"generated {baseline['parameter_count']} parameters / {baseline['case_count']} cases: {args.output}")


if __name__ == "__main__":
    main()
