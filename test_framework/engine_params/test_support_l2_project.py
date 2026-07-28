import json
from pathlib import Path
from zipfile import ZipFile

from engine_params.src.testing_utils.support_l2_project import (
    PROJECT_SETTINGS,
    build_support_l2_project,
)


def _repo() -> Path:
    return Path(__file__).resolve().parents[2]


def test_build_support_l2_project_enables_support_and_sets_value(tmp_path: Path):
    output = build_support_l2_project(
        repo=_repo(),
        output_path=tmp_path / "speed.3mf",
        parameter="support_interface_speed",
        expected_value="60",
    )

    with ZipFile(output) as archive:
        settings = json.loads(archive.read(PROJECT_SETTINGS))
    assert settings["enable_support"] == "1"
    assert settings["support_interface_speed"] == "60"
    assert settings["support_interface_top_layers"] == "2"
    assert "support_interface_speed" in settings["different_settings_to_system"][0].split(";")


def test_build_support_l2_project_uses_tree_prerequisites(tmp_path: Path):
    output = build_support_l2_project(
        repo=_repo(),
        output_path=tmp_path / "tree.3mf",
        parameter="tree_support_branch_diameter",
        expected_value="3",
    )

    with ZipFile(output) as archive:
        settings = json.loads(archive.read(PROJECT_SETTINGS))
    assert settings["support_type"] == "tree(auto)"
    assert settings["support_style"] == "tree_slim"
    assert settings["tree_support_branch_diameter"] == "3"


def test_build_support_l2_project_preserves_painted_support(tmp_path: Path):
    source = (
        _repo()
        / "test_framework"
        / "engine_params"
        / "data"
        / "models"
        / "process"
        / "support"
        / "support_basic"
        / "support_type"
        / "support_type_painted.3mf"
    )
    output = build_support_l2_project(
        repo=_repo(),
        output_path=tmp_path / "painted.3mf",
        parameter="support_type",
        expected_value="normal(manual)",
        source_project=source,
    )

    with ZipFile(source) as source_archive, ZipFile(output) as output_archive:
        painted_models = [
            name
            for name in source_archive.namelist()
            if source_archive.read(name).count(b"paint_supports=")
        ]
        assert painted_models
        for name in painted_models:
            assert output_archive.read(name) == source_archive.read(name)
        settings = json.loads(output_archive.read(PROJECT_SETTINGS))

    assert settings["enable_support"] == "1"
    assert settings["support_type"] == "normal(manual)"
