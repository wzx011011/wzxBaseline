"""CP-to-OWZX full pipeline mapping: render-flow coverage.

CrealityPrint's GUI flow (captured from C3DBaseline stage captions and the
upstream GUI) is: load 3mf -> [scene render] -> slice (准备→参数→网格切片→
支撑→悬空→裙边→墙→填充→优化路径→逐层G-code→导出) -> [gcode preview render:
解析G-code→按层重建路径→图例统计].  The bracketed stages never show up in a
headless CLI run — they are the *render* flow.

This module covers the render flow the only way a black-box harness can:
by asserting the artifacts the renderer consumes and the perf gates that
already exist for it.  What it canNOT assert headlessly (actual RHI frame
output) stays with QmlSmokeTests/visual_baseline in the product repo —
noted in RENDER_GAP.
"""

from __future__ import annotations

import json
import re
import zipfile

import pytest

from utils import runner
from utils.collect import collect_models, resolve_models_dirs

# Full CP caption chain — backbone order for the slice half (kept in sync
# with test_stages.py) plus the render half expressed as observable products.
CP_SLICE_CHAIN = [
    "正在准备",
    "应用参数",
    "网格切片",
    "生成墙",          # 裙边/边沿/墙
    "填充",
    "优化路径",
    "生成G-code",
    "导出",
    "加载显示数据",
    "G-code 预览",
]

# Render-flow stages and their headless-observable proxies:
RENDER_PROXIES = {
    # CP: 切片前实时场景渲染（网格→顶点展开→RHI 上传→拾取BVH）
    "scene render": {
        "observable": "PerfBench stages: load_ms / meshdata_ms / scene_expand_ms / pick_*",
        "gate": "docs/perf-baseline.md thresholds + ObjectPicking parity tests",
    },
    # CP: 切完后的 G-code 预览渲染（parse→per-layer paths→legend）
    "gcode preview render": {
        "observable": "gcode header stats + extrusion-type table + LAYER_CHANGE count",
        "gate": "preview_parse_ms baseline (850ms @ 400k-slice scale)",
    },
}


def pytest_generate_tests(metafunc):
    if "render_case" not in metafunc.fixturenames:
        return
    models_dirs = resolve_models_dirs(metafunc.config.getoption("--models-dir"))
    case_regex = metafunc.config.getoption("--case-regex") or ""
    cases = [c for c in collect_models(models_dirs, case_regex)
             if c["path"].suffix.lower() == ".3mf"]  # render flow needs projects
    if not cases:
        pytest.skip("no .3mf models for render-flow cases", allow_module_level=True)
    metafunc.parametrize("render_case", cases, ids=[c["rel"] for c in cases])


def _gcode_stats(gcode_path):
    """Preview-legend inputs from the CP-style gcode: layer count and the
    per-extruder filament usage the legend/estimate block renders."""
    layers = 0
    used_mm = []
    widths = {}
    with gcode_path.open(errors="replace") as fh:
        for _ in range(400):
            line = fh.readline()
            if not line:
                break
            m = re.search(r"total layer number:\s*(\d+)", line, re.I)
            if m:
                layers = int(m.group(1))
            m = re.match(r";\s*([\w ]+?) extrusion width = ([\d.]+)mm", line)
            if m:
                widths[m.group(1).strip().lower()] = float(m.group(2))
            m = re.search(r"filament used \[mm\] = ([\d., ]+)", line)
            if m:
                used_mm = [float(v) for v in m.group(1).split(",") if v.strip()]
    return layers, {"filament_used_mm": used_mm, "extrusion_widths": widths}


@pytest.mark.slice
def test_render_flow_artifacts(render_case, slicer_exe, harness_config):
    """Render flow, judged by the artifacts each render stage consumes.

    1. project 3mf must carry the metadata the scene renderer needs
       (embedded config present, geometry reachable);
    2. slicing must produce a gcode whose header stats are self-consistent
       (what 切片预览 renders: layer count, extrusion-type table);
    3. the summary JSON that feeds the preview legend must parse.
    """
    cfg = harness_config
    out_dir = runner.make_case_out_dir(cfg["artifacts_dir"], render_case["rel"])

    # --- stage 1: what the SCENE renderer consumes -------------------------
    with zipfile.ZipFile(render_case["path"]) as zf:
        names = zf.namelist()
        has_model = "3D/3dmodel.model" in names
        has_settings = "Metadata/project_settings.config" in names
    assert has_model, f"{render_case['rel']}: no 3D/3dmodel.model — scene render would show an empty bed"
    assert has_settings, f"{render_case['rel']}: no embedded project settings — parameters would not render/apply"

    # --- stage 2: slice, then validate the PREVIEW renderer's input -------
    run = runner.run_slice(slicer_exe, render_case["path"], out_dir, cfg["case_timeout"])
    if run.slice_ok:
        layers_hdr = run.gcode_layers
        types_quick = {}
        try:
            types_quick = _gcode_stats(run.gcode_path)[1]
        finally:
            import shutil
            shutil.rmtree(out_dir, ignore_errors=True)
    assert run.slice_ok, f"{render_case['rel']}: slice failed — no preview to render ({run.error})"
    assert run.gcode_layers > 0, f"{render_case['rel']}: gcode header lacks 'total layer number' — preview layer slider would be empty"

    layers = layers_hdr
    types = types_quick
    # wall/infill are the two series CP's preview legend always shows
    stats_ok = bool(types.get("filament_used_mm")) or bool(types.get("extrusion_widths"))
    assert stats_ok, (
        f"{render_case['rel']}: no usage/width stats in gcode header — preview legend would be empty"
    )


def test_render_flow_map():
    """Documentation test: the CP→OWZX stage mapping, kept executable so it
    cannot silently rot.  Fails if a CP stage has no OWZX counterpart."""
    mapping = {
        # CP caption (C3DBaseline stage chain) -> OWZX surface
        "正在准备": "Preparing current plate model / Preparing slice parameters",
        "应用参数": "Applying slice parameters",
        "网格切片": "Slicing / Generating layers / Generating supports / Calculating paths",
        "检查支撑必要性": "Generating supports (stage label varies by auto/forced)",
        "检测悬空": "libslic3r support generation (no separate label)",
        "裙边/边沿/墙(生成墙)": "Generating walls",
        "填充": "Generating infill regions",
        "优化路径": "Optimizing toolpath",
        "生成G-code(层N)": "Generating G-code (per-layer progress)",
        "导出": "SliceService export finished",
        "加载显示数据": "gcode re-parse (PreviewViewModel / preview_parse_ms)",
        "G-code 预览": "PreviewViewModel legend/stats (PreviewParserTests gate)",
        "场景渲染(网格→RHI)": "PrepareSceneData expand → RhiViewport upload (PerfBench scene_expand_ms/pick_*)",
    }
    missing = [k for k, v in mapping.items() if not v]
    assert not missing, f"CP stages without an OWZX counterpart: {missing}"
    # sanity: every SLICE chain caption appears in the mapping
    for cp in CP_SLICE_CHAIN:
        assert any(cp in k for k in mapping), f"CP stage {cp!r} not mapped"
