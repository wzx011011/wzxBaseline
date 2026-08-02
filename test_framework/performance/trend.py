"""Build-level performance history and dependency-free HTML/SVG trend reports."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence


RUN_CSV = "performance_run.csv"
RUN_JSON = "performance_run.json"
HISTORY_JSON = "performance_history.json"
TREND_HTML = "performance_trend.html"
CHART_DIR = "performance_charts"

METRICS = (
    ("total_ms", "阶段合计", "#111827"),
    ("import_ms", "导入", "#2563eb"),
    ("first_slice_ms", "首次切片", "#dc2626"),
    ("second_slice_ms", "二次切片", "#7c3aed"),
    ("export_ms", "导出", "#059669"),
)

RUN_FIELDS = (
    "run_id",
    "timestamp",
    "source_kind",
    "source_job",
    "source_build_id",
    "source_url",
    "tester_build_id",
    "tester_build_url",
    "agent",
    "platform",
    "record_id",
    "version",
    "import_ms",
    "first_slice_ms",
    "move_ms",
    "second_slice_ms",
    "slice_ms",
    "export_ms",
    "total_ms",
    "status",
    "crashed",
    "error",
)


def _number(value) -> Optional[float]:
    if value in (None, "", "None"):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _truthy(value) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _metadata_from_env(env: Mapping[str, str]) -> Dict[str, str]:
    timestamp = str(env.get("PERFORMANCE_RUN_TIMESTAMP") or "").strip()
    if not timestamp:
        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    source_build_id = str(env.get("PERFORMANCE_SOURCE_BUILD_ID") or "local").strip()
    tester_build_id = str(env.get("PERFORMANCE_TESTER_BUILD_ID") or "").strip()
    run_id = str(env.get("PERFORMANCE_RUN_ID") or "").strip()
    if not run_id:
        run_id = ":".join(part for part in (source_build_id, tester_build_id, timestamp) if part)
    return {
        "run_id": run_id,
        "timestamp": timestamp,
        "source_kind": str(env.get("PERFORMANCE_SOURCE_KIND") or "local"),
        "source_job": str(env.get("PERFORMANCE_SOURCE_JOB") or ""),
        "source_build_id": source_build_id,
        "source_url": str(env.get("PERFORMANCE_SOURCE_URL") or ""),
        "tester_build_id": tester_build_id,
        "tester_build_url": str(env.get("PERFORMANCE_TESTER_BUILD_URL") or ""),
        "agent": str(env.get("PERFORMANCE_AGENT") or ""),
        "platform": str(env.get("PERFORMANCE_PLATFORM") or ""),
    }


def build_run_rows(
    current_results: Mapping[str, Mapping[str, object]],
    metadata: Optional[Mapping[str, str]] = None,
    env: Optional[Mapping[str, str]] = None,
) -> List[Dict[str, object]]:
    """Convert this pytest session's result rows into immutable build rows."""
    meta = dict(metadata or _metadata_from_env(env or os.environ))
    rows: List[Dict[str, object]] = []
    for key in sorted(current_results):
        source = current_results[key]
        crashed = _truthy(source.get("crashed"))
        successful = (
            not crashed
            and _truthy(source.get("import_ok"))
            and _truthy(source.get("move_ok"))
            and _truthy(source.get("slice_ok"))
            and _truthy(source.get("export_ok"))
        )
        timings = {
            field: _number(source.get(field))
            for field in ("import_ms", "first_slice_ms", "move_ms", "second_slice_ms", "slice_ms", "export_ms")
        }
        # This is the sum of measured stages, not pytest wall-clock duration.
        total_ms = round(
            sum(
                timings[field]
                for field in ("import_ms", "first_slice_ms", "move_ms", "second_slice_ms", "export_ms")
                if timings[field] is not None
            ),
            2,
        )
        row: Dict[str, object] = {field: meta.get(field, "") for field in RUN_FIELDS}
        row.update(timings)
        row.update(
            {
                "record_id": str(source.get("record_id") or key),
                "version": str(source.get("version") or ""),
                "total_ms": total_ms,
                "status": "PASS" if successful else ("CRASHED" if crashed else "FAILED"),
                "crashed": crashed,
                "error": str(source.get("error") or ""),
            }
        )
        rows.append(row)
    return rows


def _write_json_atomic(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def write_run_files(rows: Sequence[Mapping[str, object]], output_dir: Path) -> Dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / RUN_CSV
    with csv_path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=RUN_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    json_path = output_dir / RUN_JSON
    _write_json_atomic(json_path, list(rows))
    return {"run_csv": csv_path, "run_json": json_path}


def load_history(path: Path) -> List[Dict[str, object]]:
    if not path.is_file():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(value, list):
        return []
    return [dict(row) for row in value if isinstance(row, dict)]


def update_history(
    history_path: Path,
    current_rows: Sequence[Mapping[str, object]],
    max_runs: int = 50,
) -> List[Dict[str, object]]:
    """Replace a repeated run atomically and retain the newest N complete runs."""
    rows = load_history(history_path)
    current_run_ids = {str(row.get("run_id") or "") for row in current_rows}
    if current_run_ids:
        rows = [row for row in rows if str(row.get("run_id") or "") not in current_run_ids]
    rows.extend(dict(row) for row in current_rows)

    run_order: List[str] = []
    for row in rows:
        run_id = str(row.get("run_id") or "")
        if run_id and run_id not in run_order:
            run_order.append(run_id)
    keep = set(run_order[-max(1, int(max_runs)):])
    rows = [row for row in rows if str(row.get("run_id") or "") in keep]
    _write_json_atomic(history_path, rows)
    return rows


def _chart_name(record_id: str) -> str:
    return hashlib.sha1(record_id.encode("utf-8", errors="replace")).hexdigest()[:16] + ".svg"


def _points(values: Sequence[Optional[float]], left: float, top: float, width: float, height: float, y_max: float):
    count = len(values)
    for index, value in enumerate(values):
        x = left + (width / max(1, count - 1)) * index
        y = None if value is None else top + height - (value / y_max) * height
        yield x, y


def _polyline_segments(points: Iterable[tuple]) -> List[List[tuple]]:
    segments: List[List[tuple]] = []
    current: List[tuple] = []
    for x, y in points:
        if y is None:
            if current:
                segments.append(current)
                current = []
        else:
            current.append((x, y))
    if current:
        segments.append(current)
    return segments


def render_case_svg(record_id: str, rows: Sequence[Mapping[str, object]]) -> str:
    width, height = 980, 360
    left, top, plot_width, plot_height = 75, 45, 860, 245
    metric_values = {
        key: [_number(row.get(key)) for row in rows]
        for key, _label, _color in METRICS
    }
    all_values = [value for values in metric_values.values() for value in values if value is not None]
    y_max = max(all_values, default=1000.0) * 1.1
    if y_max <= 0:
        y_max = 1000.0

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{left}" y="24" font-family="sans-serif" font-size="16" font-weight="600">{html.escape(record_id)}</text>',
    ]
    for tick in range(6):
        value = y_max * tick / 5
        y = top + plot_height - plot_height * tick / 5
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_width}" y2="{y:.1f}" stroke="#e5e7eb"/>')
        parts.append(f'<text x="{left - 8}" y="{y + 4:.1f}" text-anchor="end" font-family="sans-serif" font-size="11" fill="#6b7280">{value / 1000:.1f}s</text>')

    for key, label, color in METRICS:
        points = list(_points(metric_values[key], left, top, plot_width, plot_height, y_max))
        for segment in _polyline_segments(points):
            coords = " ".join(f"{x:.1f},{y:.1f}" for x, y in segment)
            parts.append(f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="2"/>')
        for index, (x, y) in enumerate(points):
            if y is not None:
                build_id = html.escape(str(rows[index].get("source_build_id") or "?"))
                value = metric_values[key][index]
                parts.append(
                    f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{color}">'
                    f'<title>BUILD_ID {build_id} · {html.escape(label)} · {value / 1000:.3f}s</title></circle>'
                )

    label_step = max(1, len(rows) // 10)
    for index, row in enumerate(rows):
        if index % label_step and index != len(rows) - 1:
            continue
        x = left + (plot_width / max(1, len(rows) - 1)) * index
        label = html.escape(str(row.get("source_build_id") or "?"))
        parts.append(f'<text x="{x:.1f}" y="{top + plot_height + 18}" text-anchor="end" transform="rotate(-35 {x:.1f} {top + plot_height + 18})" font-family="sans-serif" font-size="10" fill="#4b5563">{label}</text>')

    legend_x = left
    for _key, label, color in METRICS:
        parts.append(f'<line x1="{legend_x}" y1="338" x2="{legend_x + 20}" y2="338" stroke="{color}" stroke-width="3"/>')
        parts.append(f'<text x="{legend_x + 26}" y="342" font-family="sans-serif" font-size="12">{html.escape(label)}</text>')
        legend_x += 130
    parts.append("</svg>")
    return "\n".join(parts)


def _case_summary(rows: Sequence[Mapping[str, object]], regression_percent: float, min_delta_ms: float) -> Dict[str, object]:
    latest = rows[-1]
    latest_value = _number(latest.get("first_slice_ms"))
    previous_value = None
    if latest.get("status") == "PASS" and latest_value is not None:
        latest_build = str(latest.get("source_build_id") or "")
        for candidate in reversed(rows[:-1]):
            if str(candidate.get("source_build_id") or "") == latest_build:
                continue
            candidate_value = _number(candidate.get("first_slice_ms"))
            if candidate.get("status") == "PASS" and candidate_value is not None:
                previous_value = candidate_value
                break
    delta_ms = None if latest_value is None or previous_value is None else latest_value - previous_value
    delta_percent = None if delta_ms is None or not previous_value else delta_ms / previous_value * 100.0
    if latest.get("status") != "PASS":
        status = "INVALID"
    elif delta_ms is not None and delta_percent is not None and delta_ms >= min_delta_ms and delta_percent >= regression_percent:
        status = "REGRESSION"
    elif delta_ms is not None and delta_percent is not None and delta_ms <= -min_delta_ms and delta_percent <= -regression_percent:
        status = "IMPROVED"
    else:
        status = "PASS"
    return {
        "record_id": str(latest.get("record_id") or ""),
        "source_build_id": str(latest.get("source_build_id") or ""),
        "source_url": str(latest.get("source_url") or ""),
        "latest_ms": latest_value,
        "previous_ms": previous_value,
        "delta_ms": delta_ms,
        "delta_percent": delta_percent,
        "status": status,
        "error": str(latest.get("error") or ""),
        "chart": _chart_name(str(latest.get("record_id") or "")),
    }


def write_trend_report(
    history_rows: Sequence[Mapping[str, object]],
    output_dir: Path,
    regression_percent: float = 10.0,
    min_delta_ms: float = 2000.0,
) -> Dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    chart_dir = output_dir / CHART_DIR
    chart_dir.mkdir(parents=True, exist_ok=True)
    grouped: Dict[str, List[Mapping[str, object]]] = {}
    for row in history_rows:
        grouped.setdefault(str(row.get("record_id") or ""), []).append(row)

    summaries = []
    for record_id, rows in grouped.items():
        chart_path = chart_dir / _chart_name(record_id)
        chart_path.write_text(render_case_svg(record_id, rows), encoding="utf-8")
        summaries.append(_case_summary(rows, regression_percent, min_delta_ms))
    rank = {"REGRESSION": 0, "INVALID": 1, "PASS": 2, "IMPROVED": 3}
    summaries.sort(key=lambda row: (rank.get(str(row["status"]), 9), -(row["delta_percent"] or -10_000)))

    def ms(value) -> str:
        return "-" if value is None else f"{float(value) / 1000:.2f}s"

    def percent(value) -> str:
        return "-" if value is None else f"{float(value):+.2f}%"

    table_rows = []
    for row in summaries:
        record = html.escape(str(row["record_id"]))
        error = html.escape(str(row["error"]))
        source_url = html.escape(str(row["source_url"]), quote=True)
        build_text = html.escape(str(row["source_build_id"]))
        build_cell = f'<a href="{source_url}">{build_text}</a>' if source_url else build_text
        table_rows.append(
            "<tr data-search=\"{search}\" data-status=\"{status}\">"
            "<td><a href=\"{chart}\">{record}</a></td><td>{build}</td><td>{latest}</td>"
            "<td>{previous}</td><td>{delta}</td><td class=\"status {status}\">{status}</td><td>{error}</td></tr>".format(
                search=html.escape(str(row["record_id"]).lower(), quote=True),
                status=row["status"],
                chart=f"{CHART_DIR}/{row['chart']}",
                record=record,
                build=build_cell,
                latest=ms(row["latest_ms"]),
                previous=ms(row["previous_ms"]),
                delta=percent(row["delta_percent"]),
                error=error,
            )
        )

    run_count = len({str(row.get("run_id") or "") for row in history_rows})
    document = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>CrealityPrint 性能趋势</title>
<style>
body{{font-family:Arial,"Microsoft YaHei",sans-serif;margin:24px;color:#111827}} h1{{margin-bottom:8px}}
.meta{{color:#6b7280;margin-bottom:18px}} input,select{{padding:8px;margin:0 8px 14px 0}}
table{{border-collapse:collapse;width:100%;font-size:13px}} th,td{{border-bottom:1px solid #e5e7eb;padding:8px;text-align:left}}
th{{background:#f9fafb;position:sticky;top:0}} .status{{font-weight:700}} .REGRESSION{{color:#b91c1c}}
.INVALID{{color:#c2410c}} .IMPROVED{{color:#047857}} a{{color:#1d4ed8;text-decoration:none}}
</style></head><body>
<h1>CrealityPrint 用例性能趋势</h1>
<div class="meta">历史构建：{run_count}；用例：{len(summaries)}；下降阈值：+{regression_percent:.1f}% 且至少 +{min_delta_ms / 1000:.1f}s。点击模型名称查看折线图。</div>
<input id="search" placeholder="搜索模型" oninput="filterRows()"><select id="status" onchange="filterRows()">
<option value="">全部状态</option><option>REGRESSION</option><option>INVALID</option><option>PASS</option><option>IMPROVED</option></select>
<table><thead><tr><th>模型</th><th>BUILD_ID</th><th>当前首次切片</th><th>上一构建</th><th>变化</th><th>状态</th><th>错误</th></tr></thead>
<tbody>{''.join(table_rows)}</tbody></table>
<script>function filterRows(){{const q=document.getElementById('search').value.toLowerCase();const s=document.getElementById('status').value;document.querySelectorAll('tbody tr').forEach(r=>r.hidden=!r.dataset.search.includes(q)||(s&&r.dataset.status!==s));}}</script>
</body></html>"""
    html_path = output_dir / TREND_HTML
    html_path.write_text(document, encoding="utf-8")
    return {"trend_html": html_path, "chart_dir": chart_dir}


def write_performance_artifacts(
    current_results: Mapping[str, Mapping[str, object]],
    output_dir: Path,
    env: Optional[Mapping[str, str]] = None,
) -> Dict[str, Path]:
    env = env or os.environ
    rows = build_run_rows(current_results, env=env)
    if not rows:
        return {}
    outputs = write_run_files(rows, output_dir)
    history_value = str(env.get("PERFORMANCE_HISTORY_PATH") or "").strip()
    history_path = Path(history_value) if history_value else output_dir / HISTORY_JSON
    max_runs = int(env.get("PERFORMANCE_HISTORY_BUILDS", "50"))
    history = update_history(history_path, rows, max_runs=max_runs)
    history_snapshot = output_dir / HISTORY_JSON
    if history_snapshot.resolve() != history_path.resolve():
        _write_json_atomic(history_snapshot, history)
    outputs["history_json"] = history_snapshot
    outputs.update(
        write_trend_report(
            history,
            output_dir,
            regression_percent=float(env.get("PERFORMANCE_REGRESSION_PERCENT", "10")),
            min_delta_ms=float(env.get("PERFORMANCE_MIN_DELTA_MS", "2000")),
        )
    )
    return outputs
