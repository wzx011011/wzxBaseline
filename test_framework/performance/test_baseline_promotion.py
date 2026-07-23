import pytest

from test_framework.performance.case import test_slice as slice_case


def _healthy_row(record_id="case.3mf"):
    return {
        "record_id": record_id,
        "version": "7.0.0",
        "import_ms": "1000",
        "first_slice_ms": "5000",
        "move_ms": "100",
        "second_slice_trials": "3000",
        "second_slice_ms": "3000",
        "slice_ms": "3000",
        "export_ms": "100",
        "import_ok": "True",
        "move_ok": "True",
        "slice_ok": "True",
        "export_ok": "True",
        "crashed": "False",
        "error": "",
    }


def _complete_report_fixture(baseline_data, baseline_snapshot, current_results):
    fixture = slice_case.write_report_to_feishu_after_tests.__wrapped__(
        baseline_data,
        baseline_snapshot,
        current_results,
        None,
    )
    next(fixture)
    with pytest.raises(StopIteration):
        next(fixture)


def test_empty_session_rewrites_report_but_does_not_promote_legacy_baseline(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    report_path = tmp_path / "performance" / "data" / "feishu_slice_report.csv"
    report_path.parent.mkdir(parents=True)
    report_path.write_text("legacy-report\n", encoding="utf-8")
    persistent_baseline = tmp_path / "persistent-baseline.csv"
    persistent_baseline.write_text("keep-baseline\n", encoding="utf-8")
    monkeypatch.setenv("SECOND_SLICE_BASELINE_CSV", str(persistent_baseline))
    monkeypatch.setenv("SECOND_SLICE_UPDATE_BASELINE", "true")

    _complete_report_fixture({}, {}, {})

    assert report_path.read_text(encoding="utf-8").startswith("record_id,version,")
    assert persistent_baseline.read_text(encoding="utf-8") == "keep-baseline\n"


def test_setup_failure_with_loaded_baseline_does_not_promote_it(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    persistent_baseline = tmp_path / "persistent-baseline.csv"
    persistent_baseline.write_text("keep-baseline\n", encoding="utf-8")
    monkeypatch.setenv("SECOND_SLICE_BASELINE_CSV", str(persistent_baseline))
    monkeypatch.setenv("SECOND_SLICE_UPDATE_BASELINE", "true")
    loaded_row = _healthy_row()

    _complete_report_fixture({loaded_row["record_id"]: loaded_row}, {loaded_row["record_id"]: dict(loaded_row)}, {})

    assert persistent_baseline.read_text(encoding="utf-8") == "keep-baseline\n"


def test_healthy_current_result_promotes_the_report(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    persistent_baseline = tmp_path / "persistent-baseline.csv"
    persistent_baseline.write_text("old-baseline\n", encoding="utf-8")
    monkeypatch.setenv("SECOND_SLICE_BASELINE_CSV", str(persistent_baseline))
    monkeypatch.setenv("SECOND_SLICE_UPDATE_BASELINE", "true")
    current_row = _healthy_row()
    current = {current_row["record_id"]: current_row}

    _complete_report_fixture(dict(current), {}, current)

    report = (tmp_path / "performance" / "data" / "feishu_slice_report.csv").read_text(encoding="utf-8")
    assert persistent_baseline.read_text(encoding="utf-8") == report
    assert current_row["record_id"] in report


def test_failed_current_result_does_not_promote_the_report(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    persistent_baseline = tmp_path / "persistent-baseline.csv"
    persistent_baseline.write_text("keep-baseline\n", encoding="utf-8")
    monkeypatch.setenv("SECOND_SLICE_BASELINE_CSV", str(persistent_baseline))
    monkeypatch.setenv("SECOND_SLICE_UPDATE_BASELINE", "true")
    failed_row = _healthy_row()
    failed_row.update({"move_ok": "False", "slice_ok": "False", "export_ok": "False", "error": "move failed"})
    current = {failed_row["record_id"]: failed_row}

    _complete_report_fixture(dict(current), {}, current)

    assert persistent_baseline.read_text(encoding="utf-8") == "keep-baseline\n"
