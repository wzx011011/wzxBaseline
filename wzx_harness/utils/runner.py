"""Subprocess driver for the owzx-cli headless slicer.

Cross-platform on purpose: pathlib + subprocess only. Crash detection
covers POSIX signals (negative return codes) and the usual Windows
fault codes when running on nt.
"""

from __future__ import annotations

import re
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

WINDOWS_FAULT_CODES = {0xC0000005, 0xC0000409, 0xC00000FD}  # access-violation / stack overflow


@dataclass
class SliceRun:
    model: Path
    exit_code: int | None = None
    total_ms: float = 0.0
    gcode_path: Path | None = None
    gcode_bytes: int = 0
    timed_out: bool = False
    error: str = ""

    @property
    def crashed(self) -> bool:
        if self.timed_out:
            return True
        if self.exit_code is None:
            return False
        if self.exit_code < 0:  # POSIX: terminated by signal -N
            return True
        return (self.exit_code & 0xFFFFFFFF) in WINDOWS_FAULT_CODES

    @property
    def slice_ok(self) -> bool:
        return self.exit_code == 0 and self.gcode_path is not None and self.gcode_bytes > 0

    @property
    def export_ok(self) -> bool:
        return self.gcode_path is not None and self.gcode_bytes > 0

    def as_dict(self) -> dict:
        return {
            "total_ms": round(self.total_ms, 1),
            "exit_code": self.exit_code,
            "gcode_bytes": self.gcode_bytes,
            "slice_ok": self.slice_ok,
            "export_ok": self.export_ok,
            "crashed": self.crashed,
            "timed_out": self.timed_out,
            "error": self.error,
        }


def slicer_version(exe: Path) -> str:
    try:
        out = subprocess.run(
            [str(exe), "--version"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        ).stdout
    except (OSError, subprocess.SubprocessError) as exc:
        return f"unknown ({exc})"
    match = re.search(r"([\w.-]+-cli\s+)?([\w.+~-]+)", out.strip())
    return match.group(2) if match else out.strip()[:40] or "unknown"


def run_slice(
    exe: Path,
    model: Path,
    out_dir: Path,
    timeout_s: int,
    extra_args: list[str] | None = None,
) -> SliceRun:
    """Slice one model; wall-clock timed; never raises for slicer failures."""
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(exe),
        "--load",
        str(model),
        "--slice",
        "--output-dir",
        str(out_dir),
    ]
    cmd += list(extra_args or [])

    run = SliceRun(model=model)
    start = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout_s, check=False
        )
        run.exit_code = proc.returncode
        if proc.returncode != 0:
            run.error = _brief(proc.stderr or proc.stdout)
    except subprocess.TimeoutExpired:
        run.timed_out = True
        run.error = f"timeout after {timeout_s}s"
    run.total_ms = (time.perf_counter() - start) * 1000.0

    gcodes = sorted(
        (p for p in out_dir.glob("*.gcode") if p.is_file()),
        key=lambda p: p.stat().st_size,
        reverse=True,
    )
    if gcodes:
        run.gcode_path = gcodes[0]
        run.gcode_bytes = gcodes[0].stat().st_size
    return run


def make_case_out_dir(artifacts_dir: Path, case_id: str) -> Path:
    safe = re.sub(r"[^\w.-]+", "_", case_id)[:80]
    return Path(tempfile.mkdtemp(prefix=f"{safe}__", dir=str(artifacts_dir)))


def _brief(text: str, limit: int = 300) -> str:
    text = (text or "").strip().replace("\n", " | ")
    return text[-limit:]


def find_gcode(out_dir: Path) -> Path | None:  # kept for CLI parity/debugging
    gcodes = sorted(out_dir.glob("*.gcode"))
    return gcodes[0] if gcodes else None
