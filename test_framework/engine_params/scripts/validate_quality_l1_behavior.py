"""Slice quality L1 projects with C3DSlicer CLI and execute behavioral assertions.

This is an engine-side regression harness for the normal pytest GUI fixture.
It calls the same ``test_*`` functions after exporting each case project, so a
passing result verifies both the designed 3MF and its public parser assertion.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Direct script execution adds only ``engine_params/scripts`` to sys.path.
# Add the test-framework package root so this harness behaves like pytest.
TEST_FRAMEWORK_ROOT = Path(__file__).resolve().parents[2]
if str(TEST_FRAMEWORK_ROOT) not in sys.path:
    sys.path.insert(0, str(TEST_FRAMEWORK_ROOT))

from engine_params.scripts.design_quality_l1_models import ARCHETYPE_BY_PARAM


MODULES = {
    "bridging": "engine_params.case.params.process.quality.test_bridging",
    "ironing": "engine_params.case.params.process.quality.test_ironing",
    "line_width": "engine_params.case.params.process.quality.test_line_width",
    "overhangs": "engine_params.case.params.process.quality.test_overhangs",
    "precision": "engine_params.case.params.process.quality.test_precision",
    "seam": "engine_params.case.params.process.quality.test_seam",
    "wall_and_surfaces": "engine_params.case.params.process.quality.test_wall_and_surfaces",
    "wall_generator": "engine_params.case.params.process.quality.test_wall_generator",
}


def _slice(executable: Path, project: Path, output: Path, timeout: int) -> tuple[Path | None, str]:
    output.mkdir(parents=True, exist_ok=True)
    process = subprocess.run(
        [str(executable), "--slice", "1", "--outputdir", str(output), str(project)],
        cwd=executable.parent,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=timeout,
    )
    gcode = output / "plate_1.gcode"
    log = (process.stdout or "") + (process.stderr or "")
    return (gcode if process.returncode == 0 and gcode.exists() else None), log


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--slicer", type=Path, default=Path(r"C:\work\C3DSlicer\build\src\CrealityPrint.exe"))
    parser.add_argument("--group", choices=sorted(MODULES))
    parser.add_argument("--parameter")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--keep-output", type=Path)
    parser.add_argument("--fail-fast", action="store_true")
    args = parser.parse_args()

    repo = args.repo.resolve()
    case_root = repo / "test_framework/engine_params/data/case_input/process/quality"
    model_root = repo / "test_framework/engine_params/data/models/process/quality"
    if not args.slicer.exists():
        raise FileNotFoundError(args.slicer)

    temporary = None
    if args.keep_output:
        output_root = args.keep_output.resolve()
        output_root.mkdir(parents=True, exist_ok=True)
    else:
        temporary = tempfile.TemporaryDirectory(prefix="quality_l1_behavior_")
        output_root = Path(temporary.name)

    total = passed = 0
    failures: list[tuple[str, str]] = []
    started = time.monotonic()
    try:
        for case_json in sorted(case_root.rglob("*.json")):
            group, parameter = case_json.parent.name, case_json.stem
            if group not in MODULES or parameter not in ARCHETYPE_BY_PARAM:
                continue
            if args.group and group != args.group:
                continue
            if args.parameter and parameter != args.parameter:
                continue

            module = importlib.import_module(MODULES[group])
            test = getattr(module, f"test_{parameter}")
            signature = inspect.signature(test)
            data = json.loads(case_json.read_text(encoding="utf-8-sig"))
            for index, case in enumerate(data["cases"]):
                total += 1
                case_id = f"{group}/{parameter}[{index}]"
                project = model_root / group / parameter / case["input_3mf"]
                output = output_root / group / parameter / str(index)
                try:
                    gcode, log = _slice(args.slicer, project, output, args.timeout)
                    if gcode is None:
                        raise AssertionError("C3DSlicer did not export plate_1.gcode\n" + log[-4000:])
                    kwargs = {"slice_and_export": gcode}
                    for name in signature.parameters:
                        if name == "slice_and_export":
                            continue
                        if name not in case:
                            raise KeyError(f"case data does not provide {name!r}")
                        kwargs[name] = case[name]
                    test(**kwargs)
                except Exception as exc:  # regression report must continue across parameters
                    failures.append((case_id, f"{type(exc).__name__}: {exc}"))
                    print(f"FAIL {case_id}: {type(exc).__name__}: {exc}", flush=True)
                    if args.fail_fast:
                        break
                else:
                    passed += 1
                    print(f"PASS {case_id}", flush=True)
            if args.fail_fast and failures:
                break
    finally:
        if temporary is not None:
            temporary.cleanup()

    elapsed = time.monotonic() - started
    print(f"RESULT passed={passed} failed={len(failures)} total={total} elapsed={elapsed:.1f}s")
    for case_id, message in failures:
        print(f"  {case_id}: {message}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
