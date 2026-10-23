"""Human-readable run summary (markdown + json), C3DBaseline-style."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

VERDICT_ORDER = {"regressed": 0, "new": 1, "improved": 2, "ok": 3}


def write_summary(
    artifacts_dir: Path,
    meta: dict,
    entries: list[dict],
) -> tuple[Path, Path]:
    """entries: [{'model','os','verdict','reasons','total_ms','baseline_ms'} ...]"""
    entries = sorted(entries, key=lambda e: (VERDICT_ORDER.get(e["verdict"], 9), e["model"]))
    counts: dict[str, int] = {}
    for e in entries:
        counts[e["verdict"]] = counts.get(e["verdict"], 0) + 1

    artifacts_dir.mkdir(parents=True, exist_ok=True)
    md_path = artifacts_dir / "slice_summary.md"
    json_path = artifacts_dir / "slice_summary.json"

    lines = [
        "# 切片性能冒烟汇总",
        "",
        f"- 时间：{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"- 版本：{meta.get('version', 'unknown')}  平台：{meta.get('platform')}  "
        f"机器：{meta.get('machine')}",
        f"- 结果：回退 {counts.get('regressed', 0)} / 新基线 {counts.get('new', 0)} / "
        f"改善 {counts.get('improved', 0)} / 持平 {counts.get('ok', 0)}",
        "",
        "| 结果 | 模型 | 本次(ms) | 基线(ms) | Orca(ms) | owzx/Orca | 说明 |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for e in entries:
        orca_ms = f"{float(e['orca_ms']):.0f}" if e.get("orca_ms") else "-"
        ratio = e.get("orca_ratio") or "-"
        lines.append(
            f"| {e['verdict']} | {e['model']} | {e['total_ms']:.0f} | "
            f"{e['baseline_ms']:.0f} | {orca_ms} | {ratio} | "
            f"{'; '.join(e['reasons']) or '-'} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    json_path.write_text(
        json.dumps(
            {"meta": meta, "counts": counts, "entries": entries},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return md_path, json_path
