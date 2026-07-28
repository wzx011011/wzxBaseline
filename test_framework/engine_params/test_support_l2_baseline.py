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
