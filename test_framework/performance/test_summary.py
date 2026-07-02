from pathlib import Path

from test_framework.performance.summary import (
    build_efficiency_summary,
    write_summary_files,
    _optimization_rate,
)


def test_build_efficiency_summary_flags_second_slice_regression_only_after_percent_and_absolute_threshold():
    baseline = {
        "slow.3mf": {
            "record_id": "slow.3mf",
            "first_slice_ms": "30000",
            "second_slice_ms": "10000",
            "import_ok": "True",
            "move_ok": "True",
            "slice_ok": "True",
            "export_ok": "True",
            "crashed": "False",
            "error": "",
        },
        "small-jitter.3mf": {
            "record_id": "small-jitter.3mf",
            "first_slice_ms": "30000",
            "second_slice_ms": "10000",
            "import_ok": "True",
            "move_ok": "True",
            "slice_ok": "True",
            "export_ok": "True",
            "crashed": "False",
            "error": "",
        },
        "faster.3mf": {
            "record_id": "faster.3mf",
            "first_slice_ms": "30000",
            "second_slice_ms": "8000",
            "import_ok": "True",
            "move_ok": "True",
            "slice_ok": "True",
            "export_ok": "True",
            "crashed": "False",
            "error": "",
        },
    }
    current = {
        "slow.3mf": {
            "record_id": "slow.3mf",
            "first_slice_ms": "31000",
            "second_slice_ms": "11200",
            "import_ok": "True",
            "move_ok": "True",
            "slice_ok": "True",
            "export_ok": "True",
            "crashed": "False",
            "error": "",
        },
        "small-jitter.3mf": {
            "record_id": "small-jitter.3mf",
            "first_slice_ms": "31000",
            "second_slice_ms": "10700",
            "import_ok": "True",
            "move_ok": "True",
            "slice_ok": "True",
            "export_ok": "True",
            "crashed": "False",
            "error": "",
        },
        "faster.3mf": {
            "record_id": "faster.3mf",
            "first_slice_ms": "31000",
            "second_slice_ms": "7000",
            "import_ok": "True",
            "move_ok": "True",
            "slice_ok": "True",
            "export_ok": "True",
            "crashed": "False",
            "error": "",
        },
    }

    summary = build_efficiency_summary(baseline, current, regression_percent=5.0, min_delta_ms=1000.0)

    assert summary["status"] == "REGRESSION"
    assert summary["threshold"]["regression_percent"] == 5.0
    assert summary["counts"]["comparable"] == 3
    assert summary["counts"]["regressions"] == 1
    assert summary["counts"]["improvements"] == 1
    assert summary["regressions"][0]["record_id"] == "slow.3mf"
    assert summary["regressions"][0]["delta_percent"] == 12.0
    assert summary["improvements"][0]["record_id"] == "faster.3mf"


def test_optimization_rate_is_first_minus_second_over_first():
    # version-internal optimization rate = (first - second) / first
    # reference image: V7.0 first=14.119s second=6.779s -> 51.99%
    rate = _optimization_rate(14119.0, 6779.0)
    assert rate is not None
    assert round(rate, 2) == round((14119.0 - 6779.0) / 14119.0 * 100, 2)

    # reference image: 7.1 first=14.768s second=8.752s -> ~40.7%
    rate2 = _optimization_rate(14768.0, 8752.0)
    assert rate2 is not None
    assert round(rate2, 2) == round((14768.0 - 8752.0) / 14768.0 * 100, 2)


def test_optimization_rate_returns_none_when_inputs_invalid():
    assert _optimization_rate(None, 100.0) is None
    assert _optimization_rate(100.0, None) is None
    assert _optimization_rate(0.0, 100.0) is None
    assert _optimization_rate(100.0, 0.0) is None


def test_build_efficiency_summary_version_comparison_uses_optimization_rate_delta():
    # Reproduce the reference image scenario: two versions, optimization-rate drops by -11.25%
    # V7.0 (baseline): first=14.119s -> 51.99%, 7.1 (current): first=14.768s -> 40.73%
    # rate_change = 40.73 - 51.99 = -11.26 (rounding), overall drop < -5% => REGRESSION
    baseline = {
        "model.3mf": {
            "record_id": "model.3mf",
            "version": "7.0.0.4127",
            "first_slice_ms": "14119.0",
            "second_slice_ms": "6779.0",
            "import_ok": "True",
            "move_ok": "True",
            "slice_ok": "True",
            "export_ok": "True",
            "crashed": "False",
            "error": "",
        },
    }
    current = {
        "model.3mf": {
            "record_id": "model.3mf",
            "version": "7.1.1.4472",
            "first_slice_ms": "14768.0",
            "second_slice_ms": "8752.0",
            "import_ok": "True",
            "move_ok": "True",
            "slice_ok": "True",
            "export_ok": "True",
            "crashed": "False",
            "error": "",
        },
    }

    summary = build_efficiency_summary(baseline, current, regression_percent=5.0, min_delta_ms=1000.0)

    # version comparison populated
    vc = summary["version_comparison"]
    assert len(vc) == 1
    row = vc[0]
    assert row["record_id"] == "model.3mf"
    assert row["baseline_version"] == "7.0.0.4127"
    assert row["current_version"] == "7.1.1.4472"
    assert row["baseline_optimization_rate"] == round((14119.0 - 6779.0) / 14119.0 * 100, 2)
    assert row["current_optimization_rate"] == round((14768.0 - 8752.0) / 14768.0 * 100, 2)
    # rate change negative => efficiency drop
    assert row["rate_change"] < 0
    assert round(row["rate_change"], 2) == round(
        ((14768.0 - 8752.0) / 14768.0 * 100) - ((14119.0 - 6779.0) / 14119.0 * 100), 2
    )

    # overall rate change + REGRESSION status driven by optimization-rate drop > 5%
    assert summary["overall_rate_change"] is not None
    assert summary["overall_rate_change"] < -5.0
    assert summary["status"] == "REGRESSION"


def test_build_efficiency_summary_status_pass_when_optimization_rate_improves():
    baseline = {
        "model.3mf": {
            "record_id": "model.3mf",
            "version": "1.0",
            "first_slice_ms": "10000.0",
            "second_slice_ms": "8000.0",  # 20% optimization
            "import_ok": "True", "move_ok": "True", "slice_ok": "True", "export_ok": "True",
            "crashed": "False", "error": "",
        },
    }
    current = {
        "model.3mf": {
            "record_id": "model.3mf",
            "version": "2.0",
            "first_slice_ms": "10000.0",
            "second_slice_ms": "5000.0",  # 50% optimization, big improvement
            "import_ok": "True", "move_ok": "True", "slice_ok": "True", "export_ok": "True",
            "crashed": "False", "error": "",
        },
    }

    summary = build_efficiency_summary(baseline, current)

    assert summary["status"] == "PASS"
    assert summary["overall_rate_change"] > 0
    assert summary["version_comparison"][0]["rate_change"] > 0


def test_version_comparison_skips_failed_rows():
    baseline = {
        "model.3mf": {
            "record_id": "model.3mf",
            "version": "1.0",
            "first_slice_ms": "10000.0",
            "second_slice_ms": "8000.0",
            "import_ok": "True", "move_ok": "True", "slice_ok": "True", "export_ok": "True",
            "crashed": "False", "error": "",
        },
    }
    current = {
        "model.3mf": {
            "record_id": "model.3mf",
            "version": "2.0",
            "first_slice_ms": "10000.0",
            "second_slice_ms": "",
            "import_ok": "True", "move_ok": "True", "slice_ok": "False", "export_ok": "False",
            "crashed": "False", "error": "boom",
        },
    }

    summary = build_efficiency_summary(baseline, current)

    # current row failed -> no version comparison, no overall rate change
    assert summary["version_comparison"] == []
    assert summary["overall_rate_change"] is None
    # still recorded as a failure
    assert summary["counts"]["failures"] == 1
    assert summary["status"] == "INCONCLUSIVE"


def test_build_efficiency_summary_status_inconclusive_for_new_failed_case():
    current = {
        "model.3mf": {
            "record_id": "model.3mf",
            "version": "2.0",
            "first_slice_ms": "10000.0",
            "second_slice_ms": "",
            "import_ok": "True", "move_ok": "False", "slice_ok": "False", "export_ok": "False",
            "crashed": "False", "error": "COMMAND NOT FAOUND",
        },
    }

    summary = build_efficiency_summary({}, current)

    assert summary["status"] == "INCONCLUSIVE"
    assert summary["counts"]["failures"] == 1
    assert summary["counts"]["comparable"] == 0


def test_write_summary_files_outputs_version_comparison_table(tmp_path: Path):
    summary = build_efficiency_summary(
        {
            "model.3mf": {
                "record_id": "model.3mf",
                "version": "7.0.0.4127",
                "first_slice_ms": "14119.0",
                "second_slice_ms": "6779.0",
                "import_ok": "True", "move_ok": "True", "slice_ok": "True", "export_ok": "True",
                "crashed": "False", "error": "",
            },
        },
        {
            "model.3mf": {
                "record_id": "model.3mf",
                "version": "7.1.1.4472",
                "first_slice_ms": "14768.0",
                "second_slice_ms": "8752.0",
                "import_ok": "True", "move_ok": "True", "slice_ok": "True", "export_ok": "True",
                "crashed": "False", "error": "",
            },
        },
    )

    markdown_path, json_path = write_summary_files(summary, tmp_path)

    markdown = markdown_path.read_text(encoding="utf-8")
    assert markdown_path.name == "second_slice_efficiency_summary.md"
    assert json_path.name == "second_slice_efficiency_summary.json"
    # both version labels appear in the side-by-side report
    assert "7.0.0.4127" in markdown
    assert "7.1.1.4472" in markdown
    # optimization-rate columns present
    assert "优化率" in markdown
    # efficiency-change percentage present (negative => drop)
    assert "11." in markdown  # ~11.26% drop
