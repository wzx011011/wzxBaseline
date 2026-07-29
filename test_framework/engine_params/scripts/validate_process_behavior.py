"""Slice process parameter projects and execute their public G-code assertions.

The normal suite drives the GUI fixture.  This regression harness uses the
same 3MF inputs and ``test_*`` functions but exports with CrealityPrint CLI,
which makes behavior-parser development deterministic and batch friendly.
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


TEST_FRAMEWORK_ROOT = Path(__file__).resolve().parents[2]
if str(TEST_FRAMEWORK_ROOT) not in sys.path:
    sys.path.insert(0, str(TEST_FRAMEWORK_ROOT))


GROUP_MODULES = {
    "strength": (
        "engine_params.case.params.process.strength.test_advance",
        "engine_params.case.params.process.strength.test_fill",
        "engine_params.case.params.process.strength.test_top_or_bottom_shells",
        "engine_params.case.params.process.strength.test_walls",
    ),
    "others": (
        "engine_params.case.params.process.others.test_brim",
        "engine_params.case.params.process.others.test_gcode_output",
        "engine_params.case.params.process.others.test_post_process_notes",
        "engine_params.case.params.process.others.test_skirt",
        "engine_params.case.params.process.others.test_special_mode",
    ),
    "filament": (
        "engine_params.case.params.process.filament.test_extruder_assignment",
        "engine_params.case.params.process.filament.test_flush_options",
        "engine_params.case.params.process.filament.test_interlocking",
        "engine_params.case.params.process.filament.test_prime_tower",
        "engine_params.case.params.process.filament.test_prime_tower_gcode",
    ),
}


def _message(exc: Exception, limit: int = 1200) -> str:
    message = f"{type(exc).__name__}: {exc}"
    if len(message) <= limit:
        return message
    return message[:limit] + f" ... <truncated {len(message) - limit} chars>"


def _tests(group: str) -> dict[str, object]:
    result = {}
    for module_name in GROUP_MODULES[group]:
        module = importlib.import_module(module_name)
        for name in dir(module):
            if name.startswith("test_") and callable(getattr(module, name)):
                result[name[5:]] = getattr(module, name)
    return result


def _slice(executable: Path, project: Path, output: Path, timeout: int) -> tuple[Path | None, str]:
    output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
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
    # On Windows the GUI entry process may return while its single-instance
    # worker is still finishing the export.  Wait for two stable size samples
    # so the following parser never observes a missing or half-written file.
    last_size = -1
    stable_samples = 0
    while process.returncode == 0 and time.monotonic() - started < timeout:
        if gcode.exists():
            size = gcode.stat().st_size
            if size > 0 and size == last_size:
                stable_samples += 1
                if stable_samples >= 2:
                    return gcode, log
            else:
                stable_samples = 0
                last_size = size
        time.sleep(0.2)
    return None, log


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--slicer", type=Path, default=Path(r"C:\work\C3DSlicer\build\src\CrealityPrint.exe"))
    parser.add_argument("--group", choices=sorted(GROUP_MODULES), required=True)
    parser.add_argument("--parameter")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--keep-output", type=Path)
    parser.add_argument("--fail-fast", action="store_true")
    args = parser.parse_args()

    repo = args.repo.resolve()
    case_root = repo / "test_framework/engine_params/data/case_input/process" / args.group
    model_root = repo / "test_framework/engine_params/data/models/process" / args.group
    tests = _tests(args.group)
    if not args.slicer.exists():
        raise FileNotFoundError(args.slicer)

    temporary = None
    if args.keep_output:
        output_root = args.keep_output.resolve()
        output_root.mkdir(parents=True, exist_ok=True)
    else:
        temporary = tempfile.TemporaryDirectory(prefix=f"{args.group}_behavior_")
        output_root = Path(temporary.name)

    total = passed = 0
    failures: list[tuple[str, str]] = []
    started = time.monotonic()
    try:
        for case_json in sorted(case_root.rglob("*.json")):
            parameter = case_json.stem
            if args.parameter and parameter != args.parameter:
                continue
            test = tests.get(parameter)
            if test is None:
                failures.append((parameter, "no matching public test function"))
                continue
            signature = inspect.signature(test)
            data = json.loads(case_json.read_text(encoding="utf-8-sig"))
            relative = case_json.parent.relative_to(case_root)
            for index, case in enumerate(data["cases"]):
                total += 1
                case_id = f"{args.group}/{relative}/{parameter}[{index}]"
                project = model_root / relative / parameter / case["input_3mf"]
                output = output_root / args.group / relative / parameter / str(index)
                try:
                    gcode, log = _slice(args.slicer, project, output, args.timeout)
                    if gcode is None:
                        raise AssertionError("CrealityPrint did not export plate_1.gcode\n" + log[-4000:])
                    kwargs = {"slice_and_export": gcode}
                    for name in signature.parameters:
                        if name == "slice_and_export":
                            continue
                        if name == "baseline_gcode":
                            raw = case.get(name)
                            kwargs[name] = None if raw is None else model_root / relative / parameter / str(raw)
                        elif name in case:
                            kwargs[name] = case[name]
                        else:
                            raise KeyError(f"case data does not provide {name!r}")
                    test(**kwargs)
                except Exception as exc:
                    message = _message(exc)
                    failures.append((case_id, message))
                    print(f"FAIL {case_id}: {message}", flush=True)
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
