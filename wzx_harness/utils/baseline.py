"""Persistent baseline CSV plus the version-to-version regression verdict.

CSV schema (one row per model per platform):

    model,os,machine,version,total_ms,exit_code,gcode_bytes,
    slice_ok,export_ok,crashed,measured_at,error

Verdict rule mirrors C3DBaseline's second-slice policy, applied to the
P0 wall-clock metric: a run regresses when a status bit flips for the
worse, or the best-of-N time grows by more than 5% AND at least 1000 ms
against the baseline row of the same model on the same OS.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

FIELDS = [
    "model",
    "os",
    "machine",
    "version",
    "total_ms",
    "exit_code",
    "gcode_bytes",
    "gcode_layers",
    "slice_ok",
    "export_ok",
    "crashed",
    "measured_at",
    "error",
    # informational only — recorded when --orca-exe is passed, never judged
    "orca_ms",
    "orca_ok",
    "orca_layers",
    "orca_ratio",
]

REGRESS_RATIO = 0.05
REGRESS_MIN_MS = 1000.0


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class Verdict:
    status: str  # "new" | "ok" | "regressed" | "improved"
    reasons: list[str] = field(default_factory=list)

    @property
    def failed(self) -> bool:
        return self.status == "regressed"


def load_baseline(path: Path) -> dict[tuple[str, str], dict]:
    """Keyed by (relative model path, os). Missing file -> empty baseline."""
    if not path.is_file():
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return {(r["model"], r["os"]): r for r in rows if r.get("model")}


def upsert(path: Path, row: dict) -> None:
    """Insert or replace one baseline row, keeping the file sorted by model."""
    path.parent.mkdir(parents=True, exist_ok=True)
    baseline = load_baseline(path)
    baseline[(row["model"], row["os"])] = row
    rows = sorted(baseline.values(), key=lambda r: (r["model"], r["os"]))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def judge(row: dict, baseline_row: dict) -> Verdict:
    """Compare one fresh run row against its baseline row."""
    for bit in ("crashed", "slice_ok", "export_ok"):
        now = row[bit] == "True"
        was = baseline_row.get(bit) == "True"
        if now != was:
            return Verdict(
                "regressed",
                [f"{bit}: baseline={was} now={now} ({row.get('error', '')[:120]})"],
            )

    now_ms = float(row["total_ms"])
    was_ms = float(baseline_row.get("total_ms") or 0)
    if was_ms <= 0:
        return Verdict("new", ["baseline had no timing; keeping current row"])

    growth = now_ms - was_ms
    if growth > was_ms * REGRESS_RATIO and growth >= REGRESS_MIN_MS:
        return Verdict(
            "regressed",
            [
                f"total_ms {was_ms:.0f} -> {now_ms:.0f} "
                f"(+{growth / was_ms * 100:.1f}% , +{growth:.0f} ms)"
            ],
        )
    if growth < -was_ms * REGRESS_RATIO and -growth >= REGRESS_MIN_MS:
        return Verdict(
            "improved",
            [f"total_ms {was_ms:.0f} -> {now_ms:.0f} (-{-growth / was_ms * 100:.1f}%)"],
        )
    return Verdict("ok", [f"total_ms {was_ms:.0f} -> {now_ms:.0f} (within tolerance)"])
