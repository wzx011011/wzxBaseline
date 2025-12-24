from __future__ import annotations

import json
import re
import shutil
from pathlib import Path


def _slug(s: str) -> str:
    # Keep filenames stable across Windows; mirror test framework sanitizer but preserve intent.
    s = str(s)
    s = s.replace("%", "pct")
    s = s.replace(",", "_")
    s = s.replace("(", "_").replace(")", "")
    s = s.replace(" ", "_")
    s = re.sub(r"[^A-Za-z0-9_.-]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "value"


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]

    template_3mf = repo_root / "engine_params" / "data" / "models" / "template_model.3mf"
    if not template_3mf.exists():
        # fallback: top-level template
        template_3mf = repo_root / "template_model.3mf"
    if not template_3mf.exists():
        raise FileNotFoundError(f"Template 3MF not found: {template_3mf}")

    json_root = repo_root / "engine_params" / "data" / "case_input" / "process" / "support" / "support_advanced"
    models_root = repo_root / "engine_params" / "data" / "models" / "process" / "support" / "support_advanced"

    # Advanced (30) parameters per doc section 7 -> 6.4 expansion.
    # expected_value MUST match G-code config output format.
    params: dict[str, list[object]] = {
        "raft_first_layer_density": ["90%", "50%", "100%"],
        "raft_first_layer_expansion": ["2", "0", "5"],
        "support_top_z_distance": ["0.2", "0.1", "0.3"],
        "support_base_pattern": ["rectilinear", "grid"],
        "support_base_pattern_spacing": ["2.5", "1.5", "3.5"],
        "support_angle": ["0", "30", "45"],
        # existing 8 interface params are also part of Advanced group but are generated elsewhere
        # we still generate the remaining ones here.
        "support_expansion": ["0", "2"],
        "support_object_xy_distance": ["0.35", "0.2", "0.6"],
        "support_object_first_layer_gap": ["0.2", "0", "0.3"],
        # note: actual config value is a string like "xy_overrides_z"
        "support_xy_overrides_z": ["xy_overrides_z", "z_overrides_xy"],
        "bridge_no_support": [0, 1],
        "max_bridge_length": ["10", "5", "20"],
        "independent_support_layer_height": [0, 1],
        "ironing_support_layer": [0, 1],
        "tree_hybrid_cross_height": ["0", "5", "10"],
        "support_bottom_z_distance": ["0.2", "0.1", "0.3"],
        "support_line_width": ["0.42", "0.4", "0.5"],
        "support_speed": ["150", "60", "200"],
        "minimum_support_area": ["5", "1", "10"],
        # doc name mapped to actual config key `support_material_interface_fan_speed`
        "support_material_interface_fan_speed": ["-1,-1", "0,0", "100,100"],
        "support_base_pattern_tree": ["default", "grid"],
    }

    for param, values in params.items():
        cases = []
        model_dir = models_root / param
        model_dir.mkdir(parents=True, exist_ok=True)

        for v in values:
            slug = _slug(str(v))
            input_3mf = f"{param}_{slug}.3mf"
            dst = model_dir / input_3mf
            if not dst.exists():
                shutil.copy2(template_3mf, dst)

            cases.append(
                {
                    "project_name": f"{param}_{slug}",
                    "input_3mf": input_3mf,
                    "expected_value": v,
                }
            )

        _write_json(json_root / f"{param}.json", {"cases": cases})

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
