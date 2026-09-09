"""Keep reviewed snapshot updates narrow and regression-sensitive."""

import json
from pathlib import Path

import pytest

from engine_params.case.params.process.strength import test_fill as fill_cases
from engine_params.src.gcode.process import support_l2_metrics as support_metrics
from engine_params.test_coordinate_precision_regressions import _shift_xy


FILL_MODELS = Path(__file__).parent / "data/models/process/strength/fill"
SNAPSHOTS = [
    ("internal_solid_infill_pattern/baseline_sip_monotonic.gcode",
     fill_cases.test_internal_solid_infill_pattern, "Internal solid infill"),
    ("sparse_infill_density/baseline_50%_noai_grid.gcode",
     fill_cases.test_sparse_infill_density, "Sparse infill"),
    ("sparse_infill_density/baseline_50%_noai_hilbert_curve.gcode",
     fill_cases.test_sparse_infill_density, "Sparse infill"),
    ("infill_wall_overlap/baseline_infill_wall_overlap_100percentage.gcode",
     fill_cases.test_infill_wall_overlap, "Internal solid infill"),
]
SUPPORT_PARAMETER = "support_bottom_interface_spacing"
TREE_STRONG_PARAMETER = "support_style"
TREE_STRONG_VALUE = "tree_strong"


def _assert_snapshot(function, actual, baseline):
    if function is fill_cases.test_infill_wall_overlap:
        function(actual, baseline)
    else:
        function(actual, True, baseline)


@pytest.mark.parametrize("relative,function,role", SNAPSHOTS, ids=[s[0] for s in SNAPSHOTS])
@pytest.mark.parametrize("delta", [-.002, -.001, .001, .002])
def test_refreshed_snapshots_keep_one_quantum_tolerance(tmp_path, relative, function, role, delta):
    baseline = FILL_MODELS / relative
    actual = tmp_path / "shifted.gcode"
    _shift_xy(baseline, actual, delta)
    if abs(delta) <= .001:
        _assert_snapshot(function, actual, baseline)
    else:
        with pytest.raises(AssertionError):
            _assert_snapshot(function, actual, baseline)


@pytest.mark.parametrize("relative,function,role", SNAPSHOTS, ids=[s[0] for s in SNAPSHOTS])
def test_refreshed_snapshots_reject_missing_role(tmp_path, relative, function, role):
    baseline = FILL_MODELS / relative
    original = baseline.read_text(encoding="utf-8")
    changed = original.replace(f";TYPE:{role}", ";TYPE:Removed test role")
    assert changed != original
    actual = tmp_path / "missing-role.gcode"
    actual.write_text(changed, encoding="utf-8")
    with pytest.raises(AssertionError):
        _assert_snapshot(function, actual, baseline)


def _support_reference(value):
    data = json.loads(support_metrics.BASELINE_FILE.read_text(encoding="utf-8"))
    parameter = data["parameters"][SUPPORT_PARAMETER]
    entry = next(e for e in parameter["entries"]
                 if e["expected_key"] == support_metrics.canonical_expected(value))
    return {key: entry["metrics"][key]["max"] for key in parameter["checks"]}


@pytest.mark.parametrize("value", ["0.3", "0.5"])
@pytest.mark.parametrize("move_count", [6576, 6633, 6680])
def test_reviewed_support_connector_counts_pass(monkeypatch, value, move_count):
    metrics = _support_reference(value)
    metrics["role.Support total.move_count"] = move_count
    monkeypatch.setattr(support_metrics, "analyze_support_gcode", lambda _: metrics)
    ok, details = support_metrics.validate_support_l2_behavior("unused.gcode", SUPPORT_PARAMETER, value)
    assert ok, details


@pytest.mark.parametrize("value", ["0.3", "0.5"])
@pytest.mark.parametrize("metric,actual", [
    ("role.Support total.move_count", 6500),
    ("role.Support total.move_count", 6800),
    ("role.Support total.block_count", 79),
    ("role.Support total.layer_count", 67),
    ("role.Support total.path_length", 66000),
    ("role.Support interface.layer_count", 14),
    ("role.Support interface.path_length", 10000),
    ("role.Support interface.extrusion", 390),
    ("role.Support interface.extrusion", None),
    ("role.Support interface.bbox_width", 70),
    ("role.Support interface.bbox_height", 49),
])
def test_support_geometry_and_out_of_range_counts_still_fail(monkeypatch, value, metric, actual):
    metrics = _support_reference(value)
    metrics[metric] = actual
    monkeypatch.setattr(support_metrics, "analyze_support_gcode", lambda _: metrics)
    ok, details = support_metrics.validate_support_l2_behavior("unused.gcode", SUPPORT_PARAMETER, value)
    assert not ok
    assert [m["metric"] for m in details["mismatches"]] == [metric]


@pytest.mark.parametrize("parameter,value,metric,actual", [
    ("ironing_support_layer", "0", "role.Support total.block_count", 94),
    ("ironing_support_layer", "1", "role.Support total.block_count", 94),
    ("support_filament", "0", "role.Support interface.extrusion", None),
    ("support_filament", "2", "role.Support interface.extrusion", None),
    ("support_interface_filament", "2", "role.Support interface.extrusion", None),
    ("support_interface_not_for_body", "1", "role.Support total.tool_0_extrusion", 366.02836),
])
def test_unresolved_multimaterial_support_failures_are_not_relaxed(monkeypatch, parameter, value, metric, actual):
    monkeypatch.setattr(support_metrics, "analyze_support_gcode", lambda _: {metric: actual})
    assert not support_metrics.validate_support_l2_behavior("unused.gcode", parameter, value)[0]


def _tree_strong_metrics(layer_length_max, path_length, extrusion):
    return {
        "role.Support total.layer_length_max": layer_length_max,
        "role.Support total.block_count": 208,
        "role.Support total.layer_count": 141,
        "role.Support total.path_length": path_length,
        "role.Support total.extrusion": extrusion,
        "role.Support total.tool_count": 1,
    }


@pytest.mark.parametrize("metrics", [
    _tree_strong_metrics(861.60175, 43177.0743, 1623.01365),
    _tree_strong_metrics(965.12513, 43838.39809, 1650.55353),
])
def test_tree_strong_observed_topologies_pass(monkeypatch, metrics):
    monkeypatch.setattr(support_metrics, "analyze_support_gcode", lambda _: metrics)
    ok, details = support_metrics.validate_support_l2_behavior(
        "unused.gcode", TREE_STRONG_PARAMETER, TREE_STRONG_VALUE
    )
    assert ok, details
    assert len(details["checks"]) == 6


@pytest.mark.parametrize("metric,actual", [
    ("role.Support total.layer_length_max", 840),
    ("role.Support total.block_count", 207),
    ("role.Support total.layer_count", 140),
    ("role.Support total.path_length", 40000),
    ("role.Support total.extrusion", 1500),
    ("role.Support total.tool_count", 2),
])
def test_tree_strong_still_rejects_geometry_degradation(monkeypatch, metric, actual):
    metrics = _tree_strong_metrics(861.60175, 43177.0743, 1623.01365)
    metrics[metric] = actual
    monkeypatch.setattr(support_metrics, "analyze_support_gcode", lambda _: metrics)
    ok, details = support_metrics.validate_support_l2_behavior(
        "unused.gcode", TREE_STRONG_PARAMETER, TREE_STRONG_VALUE
    )
    assert not ok
    assert [m["metric"] for m in details["mismatches"]] == [metric]


def test_support_style_entry_checks_do_not_change_other_styles(monkeypatch):
    metrics = {"role.Support total.layer_length_max": 2108.604}
    monkeypatch.setattr(support_metrics, "analyze_support_gcode", lambda _: metrics)
    ok, details = support_metrics.validate_support_l2_behavior(
        "unused.gcode", TREE_STRONG_PARAMETER, "default"
    )
    assert ok, details
    assert details["checks"] == ["role.Support total.layer_length_max"]
