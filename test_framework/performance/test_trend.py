import csv
import json
from pathlib import Path

from test_framework.performance.trend import (
    build_run_rows,
    load_history,
    update_history,
    write_performance_artifacts,
    write_run_files,
)


def _result(record_id: str, first_slice_ms: float, *, error: str = ""):
    return {
        "record_id": record_id,
        "version": "7.1.0",
        "import_ms": "1000",
        "first_slice_ms": str(first_slice_ms),
        "move_ms": None,
        "second_slice_ms": None,
        "slice_ms": str(first_slice_ms),
        "export_ms": "500",
        "import_ok": "True",
        "slice_ok": "True" if not error else "False",
        "export_ok": "True" if not error else "False",
        "move_ok": "True",
        "crashed": "False",
        "error": error,
    }


def _metadata(build_id: str, run_id: str):
    return {
        "run_id": run_id,
        "timestamp": f"2026-08-02T00:00:{int(build_id):02d}+00:00",
        "source_kind": "jenkins",
        "source_job": "CrealityPrint_Release_Package_pipeline",
        "source_build_id": build_id,
        "source_url": f"http://jenkins/job/release/{build_id}/",
        "tester_build_id": str(600 + int(build_id)),
        "tester_build_url": "http://jenkins/job/tester/",
        "agent": "tester2",
        "platform": "windows",
    }


def test_build_run_rows_keeps_build_metadata_and_stage_total():
    rows = build_run_rows(
        {"case": _result("folder/model.3mf", 3000)},
        metadata=_metadata("1", "run-1"),
    )

    assert len(rows) == 1
    assert rows[0]["source_build_id"] == "1"
    assert rows[0]["record_id"] == "folder/model.3mf"
    assert rows[0]["first_slice_ms"] == 3000.0
    # import + first slice + export; compatibility slice_ms is not double-counted.
    assert rows[0]["total_ms"] == 4500.0
    assert rows[0]["status"] == "PASS"


def test_run_csv_uses_real_csv_quoting(tmp_path: Path):
    rows = build_run_rows(
        {"case": _result('folder/model, "quoted".3mf', 3000)},
        metadata=_metadata("1", "run-1"),
    )

    outputs = write_run_files(rows, tmp_path)

    with outputs["run_csv"].open("r", encoding="utf-8-sig", newline="") as stream:
        parsed = list(csv.DictReader(stream))
    assert parsed[0]["record_id"] == 'folder/model, "quoted".3mf'


def test_update_history_replaces_same_run_and_retains_newest_runs(tmp_path: Path):
    history_path = tmp_path / "history.json"
    first = build_run_rows({"case": _result("model.3mf", 1000)}, metadata=_metadata("1", "run-1"))
    replacement = build_run_rows({"case": _result("model.3mf", 1100)}, metadata=_metadata("1", "run-1"))
    second = build_run_rows({"case": _result("model.3mf", 1200)}, metadata=_metadata("2", "run-2"))
    third = build_run_rows({"case": _result("model.3mf", 1300)}, metadata=_metadata("3", "run-3"))

    update_history(history_path, first, max_runs=2)
    update_history(history_path, replacement, max_runs=2)
    update_history(history_path, second, max_runs=2)
    rows = update_history(history_path, third, max_runs=2)

    assert {row["run_id"] for row in rows} == {"run-2", "run-3"}
    assert len(load_history(history_path)) == 2


def test_write_performance_artifacts_generates_history_html_and_case_svg(tmp_path: Path):
    history_path = tmp_path / "state" / "history.json"
    report_dir = tmp_path / "report"
    env1 = {
        "PERFORMANCE_RUN_ID": "run-1",
        "PERFORMANCE_RUN_TIMESTAMP": "2026-08-02T00:00:01+00:00",
        "PERFORMANCE_SOURCE_KIND": "jenkins",
        "PERFORMANCE_SOURCE_BUILD_ID": "100",
        "PERFORMANCE_HISTORY_PATH": str(history_path),
    }
    env2 = dict(env1, PERFORMANCE_RUN_ID="run-2", PERFORMANCE_SOURCE_BUILD_ID="101")

    write_performance_artifacts({"case": _result("目录/模型 & A.3mf", 10_000)}, report_dir, env1)
    outputs = write_performance_artifacts({"case": _result("目录/模型 & A.3mf", 13_000)}, report_dir, env2)

    assert outputs["run_csv"].is_file()
    assert outputs["run_json"].is_file()
    assert outputs["history_json"].is_file()
    assert outputs["trend_html"].is_file()
    history = json.loads(outputs["history_json"].read_text(encoding="utf-8"))
    assert [row["source_build_id"] for row in history] == ["100", "101"]
    report = outputs["trend_html"].read_text(encoding="utf-8")
    assert 'data-status="REGRESSION"' in report
    assert "目录/模型 &amp; A.3mf" in report
    charts = list(outputs["chart_dir"].glob("*.svg"))
    assert len(charts) == 1
    svg = charts[0].read_text(encoding="utf-8")
    assert "100" in svg and "101" in svg
    assert "目录/模型 &amp; A.3mf" in svg
    assert "BUILD_ID 101" in svg
    assert "阶段合计" in svg
