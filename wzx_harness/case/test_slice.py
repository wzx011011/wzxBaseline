"""P0 black-box slicing performance cases.

One parametrized test drives the headless slicer CLI once per model
(best of N repeats), then either records a new baseline row or asserts
the fresh run does not regress against the persistent baseline.

Same shape as C3DBaseline's test_feishu_slice, minus the Feishu
downloader and the Windows-only plumbing.
"""

from __future__ import annotations

import re

import pytest

from conftest import LEDGER
from utils import runner
from utils.baseline import judge, load_baseline, now_iso, upsert
from utils.collect import collect_models, resolve_models_dirs


def pytest_generate_tests(metafunc):
    if "wzx_case" not in metafunc.fixturenames:
        return
    models_dirs = resolve_models_dirs(metafunc.config.getoption("--models-dir"))
    case_regex = metafunc.config.getoption("--case-regex") or ""
    cases = collect_models(models_dirs, case_regex)
    if not cases:
        pytest.skip(
            f"no models under {models_dirs} matching {case_regex!r}",
            allow_module_level=True,
        )
    ids = [c["rel"] for c in cases]
    metafunc.parametrize("wzx_case", cases, ids=ids)


@pytest.mark.slice
def test_slice_model(wzx_case, slicer_exe, harness_config):
    cfg = harness_config
    model: str = wzx_case["rel"]

    best = None
    for _ in range(cfg["repeats"]):
        out_dir = runner.make_case_out_dir(cfg["artifacts_dir"], model)
        run = runner.run_slice(
            slicer_exe, wzx_case["path"], out_dir, cfg["case_timeout"]
        )
        if best is None:
            best = run
        elif run.slice_ok and run.total_ms < best.total_ms:
            best = run

    assert best is not None
    row = {
        "model": model,
        "os": cfg["platform"],
        "machine": cfg["machine"],
        "version": runner.slicer_version(slicer_exe),
        "total_ms": f"{best.total_ms:.1f}",
        "exit_code": best.exit_code,
        "gcode_bytes": best.gcode_bytes,
        "slice_ok": best.slice_ok,
        "export_ok": best.export_ok,
        "crashed": best.crashed,
        "measured_at": now_iso(),
        "error": best.error,
    }

    baseline = load_baseline(cfg["baseline_csv"])
    baseline_row = baseline.get((model, cfg["platform"]))
    LEDGER["meta"] = {
        "version": row["version"],
        "platform": cfg["platform"],
        "machine": cfg["machine"],
    }

    if cfg["update_baseline"] or baseline_row is None:
        if not best.slice_ok:
            pytest.fail(
                f"{model}: cannot record baseline, run failed "
                f"(exit={best.exit_code}, {best.error})"
            )
        upsert(cfg["baseline_csv"], row)
        verdict, reasons = "new", ["first run; baseline recorded"]
    else:
        verdict = judge(row, baseline_row)
        reasons = verdict.reasons
        if verdict.failed:
            pytest.fail(
                f"{model}: performance regression — {'; '.join(reasons)}"
            )
        if verdict.status == "improved":
            # Keep the faster number so future comparisons stay honest.
            upsert(cfg["baseline_csv"], row)

    row["verdict"] = verdict
    row["reasons"] = reasons
    row["baseline_ms"] = float(baseline_row["total_ms"]) if baseline_row else 0.0
    LEDGER["entries"].append(row)

    assert best.slice_ok, f"{model}: slicing failed (exit={best.exit_code}, {best.error})"
