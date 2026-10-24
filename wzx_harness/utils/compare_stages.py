"""Per-stage timing windows from the '[NN%] Stage' line timeline.

The user-defined segmentation (from CrealityPrint's caption chain) is the
canonical row structure for baseline comparison:

    正在准备 → 应用参数 → 网格切片 → 支撑/悬空 → 裙边 → 墙 → 填充 →
    优化路径 → 生成G-code → 导出

Each row's time = window between the first marker of that stage and the
first marker of the NEXT stage (marker-to-marker).  Orca's CLI emits no
stage progress at all, so its side only carries the total; the table
marks that honestly instead of inventing numbers.
"""

from __future__ import annotations

import re

# ordered: (CP caption, regex of the stage's first progress marker)
_STAGE_MARKERS = [
    ("正在准备", r"\[\s*0%\] Preparing slice"),
    ("准备盘模型", r"Preparing current plate model"),
    ("准备切片参数", r"Preparing slice parameters"),
    ("应用参数", r"Applying slice parameters"),
    ("运行切片(入口)", r"Running slice"),
    ("网格切片", r"Slicing mesh"),
    ("墙", r"Generating walls"),
    ("填充", r"Generating infill regions"),
    ("填充路径", r"Generating infill toolpath"),
    ("支撑", r"Generating support|Checking support necessity"),
    ("悬空检测", r"Detect overhangs"),
    ("裙边/边沿", r"Generating skirt"),
    ("优化路径", r"Optimizing toolpath"),
    ("生成G-code", r"Generating G-code\b"),
    ("切片完成", r"\[SliceService\] slice finished"),
    ("导出+收尾", r"\[SliceService\] export finished"),
]


def stage_windows(timeline: list[tuple[float, str]]) -> dict[str, float]:
    """Marker-to-marker windows in ms; last stage closes at total elapsed."""
    if not timeline:
        return {}
    total_ms = timeline[-1][0]
    marks: list[tuple[str, float]] = []
    for caption, pattern in _STAGE_MARKERS:
        for t, line in timeline:
            if re.search(pattern, line, re.IGNORECASE):
                marks.append((caption, t))
                break
    if not marks:
        return {}
    windows: dict[str, float] = {}
    for i, (caption, t0) in enumerate(marks):
        # The first stage owns everything before its marker too (process
        # start, model load, scene prep — CP's 正在准备 covers it).
        prev = 0.0 if i == 0 else marks[i - 1][1]
        t1 = marks[i + 1][1] if i + 1 < len(marks) else total_ms
        windows[caption] = round(max(0.0, t1 - prev), 1)
    return windows


def render_stage_table(model: str, owzx_windows: dict, orca_total_ms: float | None,
                       owzx_total_ms: float) -> str:
    """Markdown table rows for one model, aligned to the user's segmentation."""
    rows = ["| 阶段 | owzx (ms) | Orca (ms) |", "|---|---:|---:|"]
    orca_known = orca_total_ms is not None
    for caption, ms in owzx_windows.items():
        orca_cell = "—¹" if orca_known else "n/a"
        rows.append(f"| {caption} | {ms:.0f} | {orca_cell} |")
    orca_total_cell = f"{orca_total_ms:.0f}" if orca_known else "n/a"
    rows.append(f"| **总计** | **{owzx_total_ms:.0f}** | **{orca_total_cell}** |")
    return f"### {model}\n" + "\n".join(rows) + "\n"
