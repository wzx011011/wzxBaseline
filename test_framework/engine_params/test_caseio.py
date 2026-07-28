from pathlib import Path

from engine_params.src.testing_utils.caseio import model_or_baseline_path


def _model_root(repo: Path) -> Path:
    return repo / "test_framework" / "engine_params" / "data" / "models"


def test_model_path_prefers_module_group_scope(tmp_path: Path):
    root = _model_root(tmp_path)
    quality = root / "process" / "quality" / "wall_and_surfaces" / "detect_thin_wall" / "same.3mf"
    strength = root / "process" / "strength" / "walls" / "detect_thin_wall" / "same.3mf"
    quality.parent.mkdir(parents=True)
    strength.parent.mkdir(parents=True)
    quality.write_bytes(b"quality")
    strength.write_bytes(b"strength")

    resolved = model_or_baseline_path(tmp_path, "process", "strength", "detect_thin_wall", "same.3mf")

    assert resolved == strength.resolve()


def test_model_path_uses_parameter_directory_to_disambiguate_group(tmp_path: Path):
    root = _model_root(tmp_path) / "process" / "quality" / "wall_and_surfaces"
    top = root / "top_flow" / "baseline.gcode"
    bottom = root / "bottom_flow" / "baseline.gcode"
    top.parent.mkdir(parents=True)
    bottom.parent.mkdir(parents=True)
    top.write_bytes(b"top")
    bottom.write_bytes(b"bottom")

    resolved = model_or_baseline_path(tmp_path, "process", "quality", "top_flow", "baseline.gcode")

    assert resolved == top.resolve()
