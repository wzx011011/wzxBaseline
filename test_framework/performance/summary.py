import json
import math
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Tuple


REPORT_MD = "second_slice_efficiency_summary.md"
REPORT_JSON = "second_slice_efficiency_summary.json"


def _parse_float(value) -> Optional[float]:
    if value in (None, "", "None"):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def _truthy(value) -> bool:
    return str(value).strip().lower() == "true"


def _row_failed(row: Mapping[str, object]) -> bool:
    return (
        _truthy(row.get("crashed"))
        or not _truthy(row.get("import_ok"))
        or not _truthy(row.get("move_ok"))
        or not _truthy(row.get("slice_ok"))
        or not _truthy(row.get("export_ok"))
    )


def _optimization_rate(first_ms, second_ms) -> Optional[float]:
    """Version-internal optimization rate (cache benefit of the second slice).

    Returns (first_slice_ms - second_slice_ms) / first_slice_ms * 100, or None when
    either input is missing/invalid. Positive = second slice is faster than first
    (good cache reuse); negative = second slice is slower.
    """
    first = _parse_float(first_ms)
    second = _parse_float(second_ms)
    if first is None or second is None or first <= 0 or second <= 0:
        return None
    return (first - second) / first * 100.0


def _case_delta(record_id: str, baseline: Mapping[str, object], current: Mapping[str, object]) -> Optional[Dict[str, float]]:
    base_slice = _parse_float(baseline.get("second_slice_ms"))
    cur_slice = _parse_float(current.get("second_slice_ms"))
    if base_slice is None or cur_slice is None or base_slice <= 0:
        return None
    delta_ms = cur_slice - base_slice
    return {
        "record_id": record_id,
        "baseline_second_slice_ms": round(base_slice, 2),
        "current_first_slice_ms": round(_parse_float(current.get("first_slice_ms")) or 0.0, 2),
        "current_second_slice_ms": round(cur_slice, 2),
        "delta_ms": round(delta_ms, 2),
        "delta_percent": round((delta_ms / base_slice) * 100.0, 2),
    }


def build_efficiency_summary(
    baseline_rows: Mapping[str, Mapping[str, object]],
    current_rows: Mapping[str, Mapping[str, object]],
    regression_percent: float = 5.0,
    min_delta_ms: float = 1000.0,
) -> Dict[str, object]:
    baseline_keys = set(baseline_rows)
    current_keys = set(current_rows)
    common_keys = sorted(baseline_keys & current_keys)

    regressions: List[Dict[str, object]] = []
    improvements: List[Dict[str, object]] = []
    failures: List[Dict[str, object]] = []

    for key in sorted(current_keys):
        current = current_rows[key]
        if _row_failed(current):
            failures.append(
                {
                    "record_id": current.get("record_id") or key,
                    "error": current.get("error") or "",
                    "crashed": _truthy(current.get("crashed")),
                }
            )

    for key in common_keys:
        baseline = baseline_rows[key]
        current = current_rows[key]
        if _row_failed(baseline) or _row_failed(current):
            continue
        delta = _case_delta(str(current.get("record_id") or key), baseline, current)
        if delta is None:
            continue
        if delta["delta_ms"] >= min_delta_ms and delta["delta_percent"] > regression_percent:
            regressions.append(delta)
        elif delta["delta_ms"] <= -min_delta_ms and delta["delta_percent"] < -regression_percent:
            improvements.append(delta)

    regressions.sort(key=lambda row: (row["delta_percent"], row["delta_ms"]), reverse=True)
    improvements.sort(key=lambda row: (row["delta_percent"], row["delta_ms"]))

    # Cross-version comparison on optimization-rate (first vs second slice cache benefit).
    # rate_change = current_optimization_rate - baseline_optimization_rate; negative = drop.
    version_comparison: List[Dict[str, object]] = []
    for key in common_keys:
        baseline = baseline_rows[key]
        current = current_rows[key]
        if _row_failed(baseline) or _row_failed(current):
            continue
        b_first = _parse_float(baseline.get("first_slice_ms"))
        b_second = _parse_float(baseline.get("second_slice_ms"))
        c_first = _parse_float(current.get("first_slice_ms"))
        c_second = _parse_float(current.get("second_slice_ms"))
        b_rate = _optimization_rate(b_first, b_second)
        c_rate = _optimization_rate(c_first, c_second)
        if b_rate is None or c_rate is None:
            continue
        version_comparison.append(
            {
                "record_id": str(current.get("record_id") or key),
                "baseline_version": str(baseline.get("version") or ""),
                "current_version": str(current.get("version") or ""),
                "baseline_first_ms": round(b_first, 2),
                "baseline_second_ms": round(b_second, 2),
                "current_first_ms": round(c_first, 2),
                "current_second_ms": round(c_second, 2),
                "baseline_optimization_rate": round(b_rate, 2),
                "current_optimization_rate": round(c_rate, 2),
                "rate_change": round(c_rate - b_rate, 2),
            }
        )

    overall_rate_change: Optional[float] = None
    if version_comparison:
        overall_rate_change = round(
            sum(row["rate_change"] for row in version_comparison) / len(version_comparison), 2
        )

    # REGRESSION when the average optimization-rate drops by more than the threshold
    # percentage points (cross-version cache-benefit loss), OR a second-slice absolute
    # regression was detected.
    rate_regression = overall_rate_change is not None and overall_rate_change < -regression_percent
    inconclusive = bool(current_rows) and not version_comparison and (bool(failures) or not baseline_rows)
    if rate_regression or regressions:
        status = "REGRESSION"
    elif inconclusive:
        status = "INCONCLUSIVE"
    else:
        status = "PASS"
    return {
        "status": status,
        "threshold": {
            "regression_percent": float(regression_percent),
            "min_delta_ms": float(min_delta_ms),
        },
        "counts": {
            "baseline": len(baseline_rows),
            "current": len(current_rows),
            "comparable": len(common_keys),
            "regressions": len(regressions),
            "improvements": len(improvements),
            "failures": len(failures),
            "new_cases": len(current_keys - baseline_keys),
            "missing_cases": len(baseline_keys - current_keys),
        },
        "regressions": regressions[:10],
        "improvements": improvements[:10],
        "failures": failures[:10],
        "version_comparison": version_comparison[:20],
        "overall_rate_change": overall_rate_change,
        "new_cases": sorted(current_keys - baseline_keys)[:20],
        "missing_cases": sorted(baseline_keys - current_keys)[:20],
    }


def _format_ms(value: float) -> str:
    return f"{value:.2f}"


def _table(rows: List[Mapping[str, object]]) -> List[str]:
    lines = [
        "| 模型 | 基线二次切片(ms) | 本次首次切片(ms) | 本次二次切片(ms) | 变化(ms) | 变化比例 |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    if not rows:
        lines.append("| 无 | - | - | - | - | - |")
        return lines
    for row in rows:
        lines.append(
            "| {record_id} | {baseline} | {first} | {current} | {delta} | {percent:.2f}% |".format(
                record_id=row["record_id"],
                baseline=_format_ms(float(row["baseline_second_slice_ms"])),
                first=_format_ms(float(row.get("current_first_slice_ms", 0.0))),
                current=_format_ms(float(row["current_second_slice_ms"])),
                delta=_format_ms(float(row["delta_ms"])),
                percent=float(row["delta_percent"]),
            )
        )
    return lines


def _version_comparison_table(rows: List[Mapping[str, object]]) -> List[str]:
    """Side-by-side two-version comparison table (optimization-rate based).

    Columns: 序号 | 模型 | 基线版本 首次切 | 二次切片 | 优化率 | 本次版本 首次切 |
    二次切片 | 优化率 | 效率变化
    """
    lines = [
        "| 序号 | 模型 | 基线版本 首次切(ms) | 基线 二次切片(ms) | 基线 优化率 | "
        "本次版本 首次切(ms) | 本次 二次切片(ms) | 本次 优化率 | 效率变化 |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    if not rows:
        lines.append("| - | 无 | - | - | - | - | - | - | - |")
        return lines
    for idx, row in enumerate(rows, 1):
        b_rate = float(row["baseline_optimization_rate"])
        c_rate = float(row["current_optimization_rate"])
        change = float(row["rate_change"])
        lines.append(
            "| {idx} | {rid} | {bf} | {bs} | {br:.2f}% | {cf} | {cs} | {cr:.2f}% | {ch:+.2f}% |".format(
                idx=idx,
                rid=row["record_id"],
                bf=_format_ms(float(row["baseline_first_ms"])),
                bs=_format_ms(float(row["baseline_second_ms"])),
                br=b_rate,
                cf=_format_ms(float(row["current_first_ms"])),
                cs=_format_ms(float(row["current_second_ms"])),
                cr=c_rate,
                ch=change,
            )
        )
    return lines


def render_markdown(summary: Mapping[str, object]) -> str:
    counts = summary["counts"]
    threshold = summary["threshold"]
    overall_rate_change = summary.get("overall_rate_change")

    # Version labels for the headline (from the first comparable row, if any).
    version_rows = list(summary.get("version_comparison", []))
    baseline_version = version_rows[0]["baseline_version"] if version_rows else ""
    current_version = version_rows[0]["current_version"] if version_rows else ""

    if summary["status"] == "INCONCLUSIVE":
        headline = "本次版本无法判定二次切片效率是否下降：缺少可对比的成功二次切片结果"
    elif summary["status"] == "REGRESSION":
        if overall_rate_change is not None:
            headline = (
                f"{current_version or '本次版本'} vs {baseline_version or '基线版本'}："
                f"切片效率下降{abs(overall_rate_change):.2f}%"
            )
        else:
            headline = "本次版本存在二次切片效率下降"
    else:
        if overall_rate_change is not None and overall_rate_change > 0:
            headline = (
                f"{current_version or '本次版本'} vs {baseline_version or '基线版本'}："
                f"切片效率提升{overall_rate_change:.2f}%"
            )
        else:
            headline = f"{current_version or '本次版本'}：未发现二次切片效率下降"

    lines = [
        "# 二次切片效率总结",
        "",
        f"结论：{headline}",
        "",
        "## 判定阈值",
        "",
        (
            f"- 版本间优化率下降超过 {threshold['regression_percent']:.1f}% 判定为效率下降；"
            f"二次切片耗时增长超过 {threshold['regression_percent']:.1f}% 且至少增加 "
            f"{threshold['min_delta_ms']:.0f}ms 同样判定为效率下降"
        ),
        "- 每个版本二次切片重复多次取均值，优化率 = (首次切片 - 二次切片均值) / 首次切片",
        "",
        "## 汇总",
        "",
        f"- 基线用例数：{counts['baseline']}",
        f"- 本次用例数：{counts['current']}",
        f"- 可对比用例数：{counts['comparable']}",
        f"- 效率下降用例数（二次切片耗时）：{counts['regressions']}",
        f"- 效率改善用例数（二次切片耗时）：{counts['improvements']}",
        f"- 失败/崩溃用例数：{counts['failures']}",
        f"- 新增用例数：{counts['new_cases']}",
        f"- 缺失用例数：{counts['missing_cases']}",
        "",
    ]

    if overall_rate_change is not None:
        lines.extend(
            [
                f"- 整体优化率变化：{overall_rate_change:+.2f}%",
                "",
            ]
        )

    if version_rows:
        lines.extend(
            [
                "## 版本对比明细（优化率）",
                "",
                *_version_comparison_table(version_rows),
                "",
            ]
        )

    if summary.get("regressions"):
        lines.extend(["## 效率下降明细（二次切片耗时）Top 10", "", *_table(list(summary["regressions"])), ""])
    if summary.get("improvements"):
        lines.extend(["## 效率改善明细（二次切片耗时）Top 10", "", *_table(list(summary["improvements"])), ""])

    failures = list(summary.get("failures", []))
    if failures:
        lines.extend(["## 失败/崩溃 Top 10", ""])
        lines.extend(["| 模型 | crashed | 错误 |", "| --- | --- | --- |"])
        for row in failures:
            lines.append(f"| {row['record_id']} | {row['crashed']} | {row['error']} |")
        lines.append("")
    return "\n".join(lines)


def write_summary_files(summary: Mapping[str, object], output_dir: Path) -> Tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = output_dir / REPORT_MD
    json_path = output_dir / REPORT_JSON
    markdown_path.write_text(render_markdown(summary), encoding="utf-8")
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return markdown_path, json_path
