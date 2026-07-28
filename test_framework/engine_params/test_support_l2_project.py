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
