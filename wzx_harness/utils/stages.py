"""Parse the slicer CLI's stdout into an ordered slicing-stage trace.

CrealityPrint's GUI shows the pipeline as progress captions (正在准备 →
生成G-code: 层N → 加载显示数据); the CLI emits the same pipeline as
"[NN%] Stage name" lines plus "[SliceService] ..." markers. This module
turns that stdout into a checkable trace so the stage sequence itself —
including the support stages — is covered by automated tests.
"""

from __future__ import annotations

import re

STAGE_RE = re.compile(r"\[\d+%\]\s*([A-Za-z][^\r\n:]*)")
LAYER_RE = re.compile(r"Generating G-code:\s*layer\s*(\d+)", re.IGNORECASE)
SERVICE_RE = re.compile(r"\[SliceService\]\s*([^,]+)")


def parse_stages(stdout: str) -> list[str]:
    """Distinct stage names in first-appearance order (layer suffix stripped)."""
    seen: list[str] = []
    for match in STAGE_RE.finditer(stdout):
        name = match.group(1).strip()
        if name and name not in seen:
            seen.append(name)
    return seen


def stage_index(stages: list[str], needle: str) -> int:
    """First index whose stage name contains needle (case-insensitive), else -1."""
    low = needle.lower()
    for i, name in enumerate(stages):
        if low in name.lower():
            return i
    return -1


def first_subsequence_index(stages: list[str], expected: list[str]) -> int:
    """First expected stage not found in order; -1 when the whole order holds."""
    cursor = -1
    for needle in expected:
        found = -1
        for i in range(cursor + 1, len(stages)):
            if needle.lower() in stages[i].lower():
                found = i
                break
        if found == -1:
            return len(expected) - len(expected) + expected.index(needle)
        cursor = found
    return -1


def parse_layers(stdout: str) -> list[int]:
    """Layer numbers in emission order from 'Generating G-code: layer N' lines."""
    return [int(m) for m in LAYER_RE.findall(stdout)]


def parse_service_markers(stdout: str) -> list[str]:
    """SliceService markers (slice start / wipe-tower ready / export finished...)."""
    seen: list[str] = []
    for match in SERVICE_RE.finditer(stdout):
        text = match.group(1).strip()
        if text and text not in seen:
            seen.append(text)
    return seen


def service_layers(stdout: str) -> list[int]:
    """Layer counts reported by 'slice finished plate=N ... layers=M' markers."""
    return [int(m) for m in re.findall(r"slice finished[^\r\n]*?layers=(\d+)", stdout)]
