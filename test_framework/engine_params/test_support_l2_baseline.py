import pytest

from engine_params.scripts.generate_support_l2_baseline import _select_checks
from engine_params.src.gcode.process.support_l2_metrics import canonical_expected


def _entry(value):
    return {
        "expected_value": value,
        "expected_key": canonical_expected(value),
        "all_metrics": {
            "role.Support total.move_count": [100, 101],
            "role.Support total.path_length": [200.0, 201.0],
        },
    }


def test_documented_behavior_alias_retains_real_l2_checks():
    checks, aliases = _select_checks(
        "support_bottom_interface_spacing",
        [_entry("0.3"), _entry("0.5")],
    )

    assert checks
    assert aliases[0]["expected_values"] == ["0.3", "0.5"]


def test_undocumented_behavior_alias_is_rejected():
    with pytest.raises(RuntimeError, match="undocumented pair"):
        _select_checks("unexpected_parameter", [_entry("a"), _entry("b")])


def test_non_speed_parameter_rejects_speed_unique():
    entries = []
    for value, orientation, speed_count in (("rectilinear", 0.8, 135), ("grid", 0.4, 132)):
        entries.append({
            "expected_value": value,
            "expected_key": canonical_expected(value),
            "all_metrics": {
                "role.Support.orientation_00_ratio": [orientation, orientation],
                "role.Support.speed_unique": [speed_count, speed_count],
            },
        })

    checks, _ = _select_checks("support_base_pattern", entries)

    assert checks == ["role.Support.orientation_00_ratio"]


def test_build_plate_only_rejects_unrelated_role_metrics():
    entries = []
    for value, starts, gap_speeds in ((0, 2, 95), (1, 0, 93)):
        entries.append({
            "expected_value": value,
            "expected_key": canonical_expected(value),
            "all_metrics": {
                "role.Support total.path_length": [1000 + starts * 100, 1000 + starts * 100],
                "role.Gap infill.speed_unique": [gap_speeds, gap_speeds],
                "semantic.support_top_z_gap": [starts, starts],
            },
        })

    checks, _ = _select_checks("support_on_build_plate_only", entries)

    assert checks == ["role.Support total.path_length"]
