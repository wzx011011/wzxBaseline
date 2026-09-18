"""Capture reviewed 7.2.2 contours from an existing test run; never runs a slicer."""

import argparse
import hashlib
import json
import re
from pathlib import Path

from engine_params.src.gcode.GCodeParser import GCodeParser
from engine_params.src.gcode.process.filament.interlocking_baseline import BASELINE_FILE, make_geometry_reference
from engine_params.src.testing_utils.caseio import model_or_baseline_path


TRUSTED_DLL_SHA256 = "f5cf68772dd711bc01ab0fe8c2c298dd78fe014dc6a0ff1faf427118769c3805"


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def capture(run_directory: Path, destination: Path):
    manifest = json.loads((run_directory / "manifest.json").read_text(encoding="utf-8"))
    if manifest["dll_sha256"] != TRUSTED_DLL_SHA256:
        raise ValueError("Reference must come from the reviewed Creality Print 7.2.2.5483 DLL")
    repo = Path(__file__).resolve().parents[2]
    inputs = repo / "test_framework/engine_params/data/case_input/process/filament/interlocking"
    entries = {}
    for case_file in sorted(inputs.glob("interlocking_*.json")):
        parameter = case_file.stem
        for case in json.loads(case_file.read_text(encoding="utf-8"))["cases"]:
            name = re.sub(r"[^A-Za-z0-9_.-]+", "_", f"test_{parameter}[{case['project_name']}]")
            gcode = run_directory / "mod_process.filament.test_interlocking" / f"{name}_1.gcode"
            config = GCodeParser(gcode).load_config()
            if config.get(parameter) != case["expected_value"]:
                raise ValueError(f"Reference config mismatch: {gcode}")
            if parameter != "interlocking_beam" and config.get("interlocking_beam") != 1:
                raise ValueError(f"Reference interlocking is disabled: {gcode}")
            source = model_or_baseline_path(repo, "process", "filament", parameter, case["input_3mf"])
            entries[case["geometry_baseline"]] = {
                "parameter": parameter, "expected_value": case["expected_value"],
                "input_3mf": str(source.relative_to(repo)).replace("\\", "/"),
                "input_sha256": _sha256(source), "gcode_sha256": _sha256(gcode),
                "geometry": make_geometry_reference(gcode),
            }
    header = {"schema_version": 1, "generator": {
        "version": "Creality Print 7.2.2.5483 Release", "exe_sha256": manifest["exe_sha256"],
        "dll_sha256": manifest["dll_sha256"], "replicas_per_case": 1,
    }, "tolerance_mm": 0.08}
    # Keep each layer on its own line, rather than one line per coordinate.
    lines = [json.dumps(header, indent=2)[:-2] + ',\n  "entries": {']
    for index, (key, entry) in enumerate(entries.items()):
        metadata = {k: v for k, v in entry.items() if k != "geometry"}
        lines.append("    " + json.dumps(key) + ": {" + json.dumps(metadata)[1:-1] + ",")
        lines.append('      "geometry": {"layer_heights": ' + json.dumps(entry["geometry"]["layer_heights"]) + ', "layers": [')
        layers = entry["geometry"]["layers"]
        lines.extend("        " + json.dumps(layer, separators=(",", ":")) + ("," if i + 1 < len(layers) else "")
                     for i, layer in enumerate(layers))
        lines.append("      ]}}" + ("," if index + 1 < len(entries) else ""))
    lines.append("  }\n}\n")
    destination.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("--output", type=Path, default=BASELINE_FILE)
    args = parser.parse_args()
    capture(args.run_directory, args.output)
