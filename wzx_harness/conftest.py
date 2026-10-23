"""Shared fixtures for the wzx slicing performance harness.

Black-box driver for the 3DPrinter_Qt6 headless slicer CLI (owzx-cli).
All knobs come from pytest options or OWZX_* env vars; nothing in here
is Windows-specific (pathlib + subprocess only).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

HARNESS_ROOT = Path(__file__).resolve().parent
if str(HARNESS_ROOT) not in sys.path:
    sys.path.insert(0, str(HARNESS_ROOT))

from utils.baseline import FIELDS  # noqa: E402
from utils.collect import resolve_models_dirs  # noqa: E402

DEFAULT_BASELINE = HARNESS_ROOT / "data" / "baseline.csv"
DEFAULT_ARTIFACTS = HARNESS_ROOT / "artifacts"

# Session ledger: cases append result rows here; pytest_sessionfinish turns
# it into artifacts/run_report.csv + slice_summary.md/json.
LEDGER = {"meta": {}, "entries": []}


def pytest_addoption(parser):
    group = parser.getgroup("wzx-harness")
    group.addoption(
        "--slicer-exe",
        action="store",
        default=None,
        help="Path to the slicer CLI (owzx-cli). Defaults to OWZX_SLICER_EXE "
        "or <repo>/../3DPrinter_Qt6/build/owzx-cli when it exists.",
    )
    group.addoption(
        "--models-dir",
        action="append",
        nargs="+",
        default=None,
        help="One or more directories to scan for .3mf/.stl models. "
        "Repeat the flag for several dirs. Defaults to OWZX_MODELS_DIR "
        "(several paths separated by the OS path separator).",
    )
    group.addoption(
        "--case-regex",
        action="store",
        default="",
        help="Only keep models whose relative path matches this regex "
        "(same idea as C3DBaseline's FEISHU_CASE_REGEX).",
    )
    group.addoption(
        "--repeats",
        action="store",
        type=int,
        default=int(os.environ.get("OWZX_HARNESS_REPEATS", "1")),
        help="Repeat each model N times and keep the fastest run "
        "(default 1; use >=3 for timing-sensitive comparisons).",
    )
    group.addoption(
        "--case-timeout",
        action="store",
        type=int,
        default=int(os.environ.get("OWZX_HARNESS_TIMEOUT", "900")),
        help="Per-run wall clock timeout in seconds (default 900).",
    )
    group.addoption(
        "--baseline-csv",
        action="store",
        default=str(DEFAULT_BASELINE),
        help="Persistent baseline CSV to compare against (default: %(default)s).",
    )
    group.addoption(
        "--artifacts-dir",
        action="store",
        default=str(DEFAULT_ARTIFACTS),
        help="Where run reports and gcode outputs are written (default: %(default)s).",
    )
    group.addoption(
        "--update-baseline",
        action="store_true",
        default=False,
        help="Write/overwrite baseline entries instead of asserting against them.",
    )


@pytest.fixture(scope="session")
def slicer_exe(request) -> Path:
    exe = _resolve_slicer_exe(request.config.getoption("--slicer-exe"))
    if exe is None or not exe.is_file():
        pytest.exit(
            f"slicer CLI not found: {exe}\n"
            "Pass --slicer-exe / OWZX_SLICER_EXE pointing at owzx-cli.",
            returncode=4,
        )
    return exe.resolve()


@pytest.fixture(scope="session")
def harness_config(request) -> dict:
    models_dirs = resolve_models_dirs(request.config.getoption("--models-dir"))
    if not models_dirs:
        pytest.exit(
            "No model directories. Pass --models-dir <dir> [...] "
            "or set OWZX_MODELS_DIR.",
            returncode=4,
        )
    missing = [str(p) for p in models_dirs if not p.is_dir()]
    if missing:
        pytest.exit(f"model directories not found: {missing}", returncode=4)

    artifacts = Path(request.config.getoption("--artifacts-dir"))
    artifacts.mkdir(parents=True, exist_ok=True)
    return {
        "models_dirs": models_dirs,
        "case_regex": request.config.getoption("--case-regex"),
        "repeats": max(1, int(request.config.getoption("--repeats"))),
        "case_timeout": max(30, int(request.config.getoption("--case-timeout"))),
        "baseline_csv": Path(request.config.getoption("--baseline-csv")),
        "artifacts_dir": artifacts,
        "update_baseline": bool(request.config.getoption("--update-baseline")),
        "platform": "windows" if os.name == "nt" else "linux",
        "machine": os.uname().nodename if hasattr(os, "uname") else "unknown",
    }


def _resolve_slicer_exe(explicit) -> Path | None:
    if explicit:
        return Path(explicit)
    env = os.environ.get("OWZX_SLICER_EXE")
    if env:
        return Path(env)
    guess = HARNESS_ROOT.parent.parent / "3DPrinter_Qt6" / "build" / _cli_name()
    return guess if guess.is_file() else None


def _cli_name() -> str:
    return "owzx-cli.exe" if os.name == "nt" else "owzx-cli"


def pytest_sessionfinish(session, exitstatus):
    """Write the run report and summary when at least one case ran."""
    entries = LEDGER["entries"]
    if not entries:
        return
    import csv

    artifacts = Path(session.config.getoption("--artifacts-dir"))
    artifacts.mkdir(parents=True, exist_ok=True)

    report_csv = artifacts / "run_report.csv"
    with report_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(entries)

    try:
        from summary import write_summary

        write_summary(
            artifacts,
            LEDGER["meta"],
            [
                {
                    "model": e["model"],
                    "os": e["os"],
                    "verdict": e.get("verdict", "ok"),
                    "reasons": e.get("reasons", []),
                    "total_ms": float(e.get("total_ms") or 0),
                    "baseline_ms": float(e.get("baseline_ms") or 0),
                }
                for e in entries
            ],
        )
    except Exception as exc:  # summary is best-effort; never mask test results
        print(f"[wzx-harness] summary generation failed: {exc}")
    print(f"\n[wzx-harness] report: {report_csv}")
