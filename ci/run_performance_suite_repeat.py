"""Repeat the QA performance suite in fresh pytest/CrealityPrint sessions.

This wrapper is intentionally separate from the shared performance test.  Each
round invokes the existing Jenkins runner unchanged, preserves that round's
CSV/Allure output, and writes an aggregate report after all rounds complete.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import statistics
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


REPORT_FIELDS = (
    "record_id",
    "version",
    "import_ms",
    "first_slice_ms",
    "move_ms",
    "second_slice_trials",
    "second_slice_ms",
    "slice_ms",
    "export_ms",
    "import_ok",
    "move_ok",
    "slice_ok",
    "export_ok",
    "crashed",
    "error",
)

METRIC_FIELDS = (
    "import_ms",
    "first_slice_ms",
    "move_ms",
    "second_slice_ms",
    "slice_ms",
    "export_ms",
)

SUMMARY_FIELDS = (
    "record_id",
    "rounds_planned",
    "rounds_recorded",
    "passed_rounds",
    "failed_rounds",
    "import_trials_ms",
    "import_avg_ms",
    "first_slice_trials_ms",
    "first_slice_avg_ms",
    "second_slice_trials_ms",
    "second_slice_avg_ms",
    "export_trials_ms",
    "export_avg_ms",
    "errors",
)

RAW_FIELDS = (
    "round",
    "result_status",
    *REPORT_FIELDS,
)

STATISTICS_FIELDS = (
    "record_id",
    "stage",
    "metric",
    "rounds_planned",
    "valid_samples",
    "missing_rounds",
    "raw_values_ms",
    "mean_ms",
    "median_ms",
    "min_ms",
    "max_ms",
    "range_ms",
    "sample_variance_ms2",
    "sample_stddev_ms",
    "cv_percent",
)

COMBINED_REPORT_FIELDS = (
    "row_type",
    "record_id",
    "round",
    "result_status",
    "version",
    "stage",
    "metric",
    "import_ms",
    "first_slice_ms",
    "move_ms",
    "second_slice_trials",
    "second_slice_ms",
    "slice_ms",
    "export_ms",
    "import_ok",
    "move_ok",
    "slice_ok",
    "export_ok",
    "crashed",
    "error",
    "rounds_planned",
    "rounds_recorded",
    "passed_rounds",
    "failed_rounds",
    "import_trials_ms",
    "import_avg_ms",
    "first_slice_trials_ms",
    "first_slice_avg_ms",
    "second_slice_trials_ms",
    "second_slice_avg_ms",
    "export_trials_ms",
    "export_avg_ms",
    "errors",
    "valid_samples",
    "missing_rounds",
    "raw_values_ms",
    "mean_ms",
    "median_ms",
    "min_ms",
    "max_ms",
    "range_ms",
    "sample_variance_ms2",
    "sample_stddev_ms",
    "cv_percent",
)

STATISTIC_METRICS = (
    ("open", "打开", "import_ms", True),
    ("first_slice", "切片", "first_slice_ms", True),
    ("move", "移动模型", "move_ms", False),
    ("second_slice", "二次切片", "second_slice_ms", False),
    ("export", "导出", "export_ms", True),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Repeat the complete QA performance model set.")
    parser.add_argument(
        "--repeat",
        type=int,
        default=os.getenv("PERFORMANCE_SUITE_REPEAT", "1"),
        help="Number of complete suite rounds (1-10)",
    )
    parser.add_argument(
        "--runner",
        default="ci/jenkins_build_tester.py",
        help="Existing single-run Jenkins test runner",
    )
    parser.add_argument(
        "--report-path",
        default="test_framework/performance/data/feishu_slice_report.csv",
        help="CSV written by the existing performance test",
    )
    parser.add_argument(
        "runner_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to jenkins_build_tester.py after --",
    )
    args = parser.parse_args()
    if args.runner_args and args.runner_args[0] == "--":
        args.runner_args = args.runner_args[1:]
    if not 1 <= args.repeat <= 10:
        parser.error("--repeat must be between 1 and 10")
    if not args.runner_args:
        parser.error("runner arguments are required after --")
    return args


def _option_value(args: Sequence[str], name: str, default: str) -> str:
    for index, value in enumerate(args):
        if value == name and index + 1 < len(args):
            return args[index + 1]
        prefix = name + "="
        if value.startswith(prefix):
            return value[len(prefix) :]
    return default


def _replace_option(args: Sequence[str], name: str, value: str) -> List[str]:
    result: List[str] = []
    index = 0
    replaced = False
    while index < len(args):
        current = args[index]
        if current == name:
            result.extend((name, value))
            replaced = True
            index += 2
            continue
        if current.startswith(name + "="):
            result.append(f"{name}={value}")
            replaced = True
            index += 1
            continue
        result.append(current)
        index += 1
    if not replaced:
        result.extend((name, value))
    return result


def _resolve_from_repo(repo_root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve()


def _read_report(path: Path) -> List[Dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return [dict(row) for row in csv.DictReader(stream)]


def _write_csv(path: Path, fieldnames: Sequence[str], rows: Iterable[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _number(value: object) -> Optional[float]:
    try:
        if value is None or str(value).strip() in {"", "None", "null"}:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _truthy(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _row_passed(row: Mapping[str, str]) -> bool:
    return (
        _truthy(row.get("import_ok"))
        and _truthy(row.get("slice_ok"))
        and _truthy(row.get("export_ok"))
        and not _truthy(row.get("crashed"))
        and not str(row.get("error") or "").strip()
    )


def _average(values: Sequence[float]) -> str:
    if not values:
        return ""
    return f"{sum(values) / len(values):.2f}"


def _round_values(entries: Sequence[Tuple[int, Mapping[str, str]]], field: str) -> List[Tuple[int, float]]:
    values = []
    for round_index, row in entries:
        value = _number(row.get(field))
        if value is not None:
            values.append((round_index, value))
    return values


def _trials_text(values: Sequence[Tuple[int, float]]) -> str:
    return "; ".join(f"{round_index}:{value:.2f}" for round_index, value in values)


def aggregate_reports(
    reports: Sequence[Tuple[int, Sequence[Mapping[str, str]]]],
    rounds_planned: int,
) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    grouped: Dict[str, List[Tuple[int, Mapping[str, str]]]] = defaultdict(list)
    for round_index, rows in reports:
        for row in rows:
            record_id = str(row.get("record_id") or "").strip()
            if record_id:
                grouped[record_id].append((round_index, row))

    aggregate_rows: List[Dict[str, object]] = []
    summary_rows: List[Dict[str, object]] = []
    for record_id in sorted(grouped):
        entries = sorted(grouped[record_id], key=lambda item: item[0])
        by_round = {round_index: row for round_index, row in entries}
        passed_rounds = [index for index, row in entries if _row_passed(row)]
        failed_rounds = [index for index in range(1, rounds_planned + 1) if index not in passed_rounds]

        errors = []
        for index in failed_rounds:
            row = by_round.get(index)
            detail = str((row or {}).get("error") or "").strip()
            if not detail and row and _truthy(row.get("crashed")):
                detail = "CrealityPrint crashed"
            errors.append(f"round {index}: {detail or 'no successful result'}")

        successful_entries = [(index, row) for index, row in entries if _row_passed(row)]
        metric_values = {field: _round_values(successful_entries, field) for field in METRIC_FIELDS}
        first_row = entries[0][1]
        aggregate_row: Dict[str, object] = {
            "record_id": record_id,
            "version": str(first_row.get("version") or ""),
            "second_slice_trials": " | ".join(
                f"round {index}:{row.get('second_slice_trials')}"
                for index, row in entries
                if str(row.get("second_slice_trials") or "").strip()
            ),
            "import_ok": str(
                len(entries) == rounds_planned
                and all(_truthy(row.get("import_ok")) for _, row in entries)
            ),
            "move_ok": str(len(entries) == rounds_planned and all(_truthy(row.get("move_ok")) for _, row in entries)),
            "slice_ok": str(len(entries) == rounds_planned and all(_truthy(row.get("slice_ok")) for _, row in entries)),
            "export_ok": str(
                len(entries) == rounds_planned
                and all(_truthy(row.get("export_ok")) for _, row in entries)
            ),
            "crashed": str(any(_truthy(row.get("crashed")) for _, row in entries)),
            "error": " | ".join(errors),
        }
        for field in METRIC_FIELDS:
            aggregate_row[field] = _average([value for _, value in metric_values[field]])
        aggregate_rows.append(aggregate_row)

        summary_rows.append(
            {
                "record_id": record_id,
                "rounds_planned": rounds_planned,
                "rounds_recorded": len(entries),
                "passed_rounds": ",".join(str(index) for index in passed_rounds),
                "failed_rounds": ",".join(str(index) for index in failed_rounds),
                "import_trials_ms": _trials_text(metric_values["import_ms"]),
                "import_avg_ms": aggregate_row["import_ms"],
                "first_slice_trials_ms": _trials_text(metric_values["first_slice_ms"]),
                "first_slice_avg_ms": aggregate_row["first_slice_ms"],
                "second_slice_trials_ms": _trials_text(metric_values["second_slice_ms"]),
                "second_slice_avg_ms": aggregate_row["second_slice_ms"],
                "export_trials_ms": _trials_text(metric_values["export_ms"]),
                "export_avg_ms": aggregate_row["export_ms"],
                "errors": " | ".join(errors),
            }
        )
    return aggregate_rows, summary_rows


def build_raw_rows(
    reports: Sequence[Tuple[int, Sequence[Mapping[str, str]]]],
    rounds_planned: int,
) -> List[Dict[str, object]]:
    """Flatten every model/round result and make missing rounds explicit."""
    rows_by_round: Dict[int, Dict[str, Mapping[str, str]]] = {}
    record_ids = set()
    for round_index, rows in reports:
        current_round: Dict[str, Mapping[str, str]] = {}
        for row in rows:
            record_id = str(row.get("record_id") or "").strip()
            if not record_id:
                continue
            current_round[record_id] = row
            record_ids.add(record_id)
        rows_by_round[round_index] = current_round

    raw_rows: List[Dict[str, object]] = []
    for round_index in range(1, rounds_planned + 1):
        current_round = rows_by_round.get(round_index, {})
        for record_id in sorted(record_ids):
            source = current_round.get(record_id)
            if source is None:
                raw_row: Dict[str, object] = {
                    "round": round_index,
                    "result_status": "missing",
                    "record_id": record_id,
                    "error": "no result in this round",
                }
            else:
                raw_row = {
                    "round": round_index,
                    "result_status": "passed" if _row_passed(source) else "failed",
                    **source,
                }
            raw_rows.append(raw_row)
    return raw_rows


def build_statistics_rows(
    reports: Sequence[Tuple[int, Sequence[Mapping[str, str]]]],
    rounds_planned: int,
) -> List[Dict[str, object]]:
    """Calculate stage statistics from valid numeric measurements only."""
    grouped: Dict[str, List[Tuple[int, Mapping[str, str]]]] = defaultdict(list)
    for round_index, rows in reports:
        for row in rows:
            record_id = str(row.get("record_id") or "").strip()
            if record_id:
                grouped[record_id].append((round_index, row))

    result: List[Dict[str, object]] = []
    for record_id in sorted(grouped):
        entries = sorted(grouped[record_id], key=lambda item: item[0])
        for stage, _stage_label, metric, always_include in STATISTIC_METRICS:
            values = _round_values(entries, metric)
            if not always_include and not values:
                continue

            numbers = [value for _, value in values]
            measured_rounds = {round_index for round_index, _ in values}
            missing_rounds = [
                round_index
                for round_index in range(1, rounds_planned + 1)
                if round_index not in measured_rounds
            ]
            mean_value = statistics.mean(numbers) if numbers else None
            median_value = statistics.median(numbers) if numbers else None
            min_value = min(numbers) if numbers else None
            max_value = max(numbers) if numbers else None
            variance_value = statistics.variance(numbers) if len(numbers) >= 2 else None
            stddev_value = statistics.stdev(numbers) if len(numbers) >= 2 else None
            cv_value = (
                stddev_value / mean_value * 100
                if stddev_value is not None and mean_value not in {None, 0}
                else None
            )
            result.append(
                {
                    "record_id": record_id,
                    "stage": stage,
                    "metric": metric,
                    "rounds_planned": rounds_planned,
                    "valid_samples": len(numbers),
                    "missing_rounds": ",".join(str(index) for index in missing_rounds),
                    "raw_values_ms": _trials_text(values),
                    "mean_ms": _format_number(mean_value),
                    "median_ms": _format_number(median_value),
                    "min_ms": _format_number(min_value),
                    "max_ms": _format_number(max_value),
                    "range_ms": _format_number(
                        max_value - min_value
                        if max_value is not None and min_value is not None
                        else None
                    ),
                    "sample_variance_ms2": _format_number(variance_value),
                    "sample_stddev_ms": _format_number(stddev_value),
                    "cv_percent": _format_number(cv_value),
                }
            )
    return result


def build_combined_report_rows(
    raw_rows: Sequence[Mapping[str, object]],
    summary_rows: Sequence[Mapping[str, object]],
    statistics_rows: Sequence[Mapping[str, object]],
) -> List[Dict[str, object]]:
    """Combine all new QA report views into one filterable CSV table."""
    rows_by_record: Dict[str, Dict[str, List[Mapping[str, object]]]] = defaultdict(
        lambda: {"summary": [], "statistics": [], "raw": []}
    )
    for row_type, rows in (
        ("summary", summary_rows),
        ("statistics", statistics_rows),
        ("raw", raw_rows),
    ):
        for row in rows:
            record_id = str(row.get("record_id") or "").strip()
            if record_id:
                rows_by_record[record_id][row_type].append(row)

    combined: List[Dict[str, object]] = []
    for record_id in sorted(rows_by_record):
        grouped = rows_by_record[record_id]
        for row_type in ("summary", "statistics", "raw"):
            for row in grouped[row_type]:
                combined.append({"row_type": row_type, **row})
    return combined


def _format_number(value: Optional[float]) -> str:
    return "" if value is None else f"{value:.2f}"


def _seconds(value: object) -> str:
    number = _number(value)
    return "-" if number is None else f"{number / 1000:.2f}s"


def _variance_seconds(value: object) -> str:
    number = _number(value)
    return "-" if number is None else f"{number / 1_000_000:.4f}"


def _raw_seconds(value: object) -> str:
    output = []
    for item in str(value or "").split(";"):
        item = item.strip()
        if not item or ":" not in item:
            continue
        round_index, raw_number = item.split(":", 1)
        number = _number(raw_number)
        if number is not None:
            output.append(f"第{round_index}轮:{number / 1000:.2f}s")
    return "；".join(output) or "-"


def _write_summary_markdown(
    path: Path,
    summary_rows: Sequence[Mapping[str, object]],
    round_return_codes: Sequence[int],
) -> None:
    lines = [
        "# QA性能多轮测试汇总",
        "",
        f"- 计划轮次：{len(round_return_codes)}",
        f"- 成功轮次：{sum(code == 0 for code in round_return_codes)}",
        f"- 失败轮次：{sum(code != 0 for code in round_return_codes)}",
        "- 执行方式：每轮完整执行全部模型；轮次之间重新启动CrealityPrint并使用新的隔离数据目录。",
        "",
        "| 模型 | 通过轮次 | 失败轮次 | 打开平均 | 切片平均 | 导出平均 |",
        "|---|---|---|---:|---:|---:|",
    ]
    for row in summary_rows:
        lines.append(
            "| {record_id} | {passed} | {failed} | {opened} | {sliced} | {exported} |".format(
                record_id=str(row.get("record_id") or "").replace("|", "\\|"),
                passed=row.get("passed_rounds") or "-",
                failed=row.get("failed_rounds") or "-",
                opened=_seconds(row.get("import_avg_ms")),
                sliced=_seconds(row.get("first_slice_avg_ms")),
                exported=_seconds(row.get("export_avg_ms")),
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_statistics_markdown(
    path: Path,
    statistics_rows: Sequence[Mapping[str, object]],
) -> None:
    stage_labels = {stage: label for stage, label, _metric, _required in STATISTIC_METRICS}
    lines = [
        "# QA性能多轮测试统计",
        "",
        "- 原始耗时和统计值均来自各阶段已成功产生的有效计时；失败或缺失轮次不计入耗时统计。",
        "- 方差和标准差使用样本统计口径；有效样本少于2个时不计算。",
        "",
        "| 模型 | 阶段 | 原始耗时 | 有效/计划 | 缺失轮次 | 平均 | 中位数 | 最小 | 最大 | 极差 | 方差(s²) | 标准差 | 波动率 |",
        "|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in statistics_rows:
        stage = str(row.get("stage") or "")
        cv_number = _number(row.get("cv_percent"))
        lines.append(
            "| {record_id} | {stage} | {raw} | {valid}/{planned} | {missing} | "
            "{mean} | {median} | {minimum} | {maximum} | {value_range} | "
            "{variance} | {stddev} | {cv} |".format(
                record_id=str(row.get("record_id") or "").replace("|", "\\|"),
                stage=stage_labels.get(stage, stage).replace("|", "\\|"),
                raw=_raw_seconds(row.get("raw_values_ms")),
                valid=row.get("valid_samples") or 0,
                planned=row.get("rounds_planned") or 0,
                missing=row.get("missing_rounds") or "-",
                mean=_seconds(row.get("mean_ms")),
                median=_seconds(row.get("median_ms")),
                minimum=_seconds(row.get("min_ms")),
                maximum=_seconds(row.get("max_ms")),
                value_range=_seconds(row.get("range_ms")),
                variance=_variance_seconds(row.get("sample_variance_ms2")),
                stddev=_seconds(row.get("sample_stddev_ms")),
                cv="-" if cv_number is None else f"{cv_number:.2f}%",
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _annotate_allure_round(result_path: Path, round_index: int, rounds_total: int) -> None:
    try:
        data = json.loads(result_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    suffix = f" [轮次 {round_index}/{rounds_total}]"
    original_name = str(data.get("name") or "")
    original_full_name = str(data.get("fullName") or original_name)
    data["name"] = original_name + suffix
    data["fullName"] = original_full_name + suffix
    parameters = data.get("parameters")
    if not isinstance(parameters, list):
        parameters = []
    parameters.append({"name": "suite_round", "value": f"{round_index}/{rounds_total}"})
    data["parameters"] = parameters
    identity = str(data.get("historyId") or data.get("testCaseId") or data["fullName"])
    round_identity = hashlib.md5(f"{identity}|suite_round={round_index}".encode("utf-8")).hexdigest()
    data["historyId"] = round_identity
    data["testCaseId"] = round_identity
    result_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def _merge_allure_round(round_dir: Path, target_dir: Path, round_index: int, rounds_total: int) -> None:
    if not round_dir.is_dir():
        return
    target_dir.mkdir(parents=True, exist_ok=True)
    for result_path in round_dir.glob("*-result.json"):
        _annotate_allure_round(result_path, round_index, rounds_total)
    for source in list(round_dir.iterdir()):
        if not source.is_file():
            continue
        destination = target_dir / source.name
        if destination.exists():
            destination = target_dir / f"round-{round_index:02d}-{source.name}"
        shutil.move(str(source), str(destination))
    shutil.rmtree(round_dir, ignore_errors=True)


def _clean_previous_outputs(data_dir: Path) -> None:
    for path in data_dir.glob("qa_performance_repeat_round_*.csv"):
        if path.is_file():
            path.unlink()
    for name in (
        "qa_performance_repeat_report.csv",
        "qa_performance_repeat_raw.csv",
        "qa_performance_repeat_summary.csv",
        "qa_performance_repeat_summary.md",
        "qa_performance_repeat_statistics.csv",
        "qa_performance_repeat_statistics.md",
    ):
        path = data_dir / name
        if path.is_file():
            path.unlink()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    runner = _resolve_from_repo(repo_root, args.runner)
    report_path = _resolve_from_repo(repo_root, args.report_path)
    data_dir = report_path.parent
    data_dir.mkdir(parents=True, exist_ok=True)
    _clean_previous_outputs(data_dir)

    original_runner_args = list(args.runner_args)
    allure_value = _option_value(
        original_runner_args,
        "--allure-results-dir",
        os.getenv("ALLURE_RESULTS_DIR", "allure-results-performance-qa"),
    )
    allure_root = _resolve_from_repo(repo_root, allure_value)
    allure_root.mkdir(parents=True, exist_ok=True)

    artifacts_value = _option_value(
        original_runner_args,
        "--artifacts-dir",
        os.getenv("ARTIFACTS_DIR", "artifacts-performance-qa"),
    )
    artifacts_root = _resolve_from_repo(repo_root, artifacts_value)

    reports: List[Tuple[int, Sequence[Mapping[str, str]]]] = []
    round_return_codes: List[int] = []
    original_build_number = str(os.getenv("BUILD_NUMBER") or "").strip()

    for round_index in range(1, args.repeat + 1):
        print(f"\n=== QA performance suite round {round_index}/{args.repeat} ===", flush=True)
        if report_path.exists():
            report_path.unlink()

        round_allure_dir = allure_root / f"_round_{round_index:02d}"
        if round_allure_dir.exists():
            shutil.rmtree(round_allure_dir)
        round_runner_args = _replace_option(
            original_runner_args,
            "--allure-results-dir",
            str(round_allure_dir),
        )
        round_gcode_root = artifacts_root / "gcode" / f"repeat_round_{round_index:02d}"
        round_runner_args = _replace_option(round_runner_args, "--gcode-root", str(round_gcode_root))

        round_env = os.environ.copy()
        round_env["PERFORMANCE_SUITE_ROUND"] = str(round_index)
        round_env["PERFORMANCE_SUITE_REPEAT"] = str(args.repeat)
        if original_build_number:
            round_env["QA_REPEAT_ORIGINAL_BUILD_NUMBER"] = original_build_number
            round_env["BUILD_NUMBER"] = f"{original_build_number}_round_{round_index:02d}"

        command = [sys.executable, "-u", str(runner), *round_runner_args]
        print(f"[qa-repeat] command: {subprocess.list2cmdline(command)}", flush=True)
        completed = subprocess.run(command, cwd=repo_root, env=round_env, check=False)
        round_return_codes.append(completed.returncode)

        rows = _read_report(report_path)
        reports.append((round_index, rows))
        round_report = data_dir / f"qa_performance_repeat_round_{round_index:02d}.csv"
        _write_csv(round_report, REPORT_FIELDS, rows)
        _merge_allure_round(round_allure_dir, allure_root, round_index, args.repeat)
        print(
            f"[qa-repeat] round {round_index}/{args.repeat} finished: "
            f"rc={completed.returncode}, records={len(rows)}",
            flush=True,
        )

    aggregate_rows, summary_rows = aggregate_reports(reports, args.repeat)
    raw_rows = build_raw_rows(reports, args.repeat)
    statistics_rows = build_statistics_rows(reports, args.repeat)
    combined_rows = build_combined_report_rows(raw_rows, summary_rows, statistics_rows)
    _write_csv(report_path, REPORT_FIELDS, aggregate_rows)
    combined_csv = data_dir / "qa_performance_repeat_report.csv"
    raw_csv = data_dir / "qa_performance_repeat_raw.csv"
    summary_csv = data_dir / "qa_performance_repeat_summary.csv"
    summary_md = data_dir / "qa_performance_repeat_summary.md"
    statistics_csv = data_dir / "qa_performance_repeat_statistics.csv"
    statistics_md = data_dir / "qa_performance_repeat_statistics.md"
    _write_csv(combined_csv, COMBINED_REPORT_FIELDS, combined_rows)
    _write_csv(raw_csv, RAW_FIELDS, raw_rows)
    _write_csv(summary_csv, SUMMARY_FIELDS, summary_rows)
    _write_summary_markdown(summary_md, summary_rows, round_return_codes)
    _write_csv(statistics_csv, STATISTICS_FIELDS, statistics_rows)
    _write_statistics_markdown(statistics_md, statistics_rows)
    print(f"[qa-repeat] aggregate report: {report_path}", flush=True)
    print(f"[qa-repeat] combined CSV: {combined_csv}", flush=True)
    print(f"[qa-repeat] raw CSV: {raw_csv}", flush=True)
    print(f"[qa-repeat] summary CSV: {summary_csv}", flush=True)
    print(f"[qa-repeat] summary Markdown: {summary_md}", flush=True)
    print(f"[qa-repeat] statistics CSV: {statistics_csv}", flush=True)
    print(f"[qa-repeat] statistics Markdown: {statistics_md}", flush=True)

    failed_rounds = [index for index, code in enumerate(round_return_codes, 1) if code != 0]
    if failed_rounds:
        print(f"[qa-repeat] failed rounds: {failed_rounds}", file=sys.stderr, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
