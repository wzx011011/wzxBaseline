from pathlib import Path

import pytest

from ci.jenkins_build_tester import (
    prepare_slicer_datadir,
    resolve_run_slicer_datadir,
    should_use_isolated_slicer_datadir,
)


def test_prepare_slicer_datadir_seeds_from_explicit_template(tmp_path: Path):
    template = tmp_path / "Creality" / "Creality Print" / "7.0 Alpha"
    template.mkdir(parents=True)
    (template / "Creality.conf").write_text("printer=config\n", encoding="utf-8")
    (template / "log").mkdir()
    (template / "log" / "old.log").write_text("noise\n", encoding="utf-8")

    target = tmp_path / "run-data"
    seeded_from = prepare_slicer_datadir(
        target,
        env={"SLICER_DATADIR_TEMPLATE": str(template), "APPDATA": str(tmp_path / "empty")},
    )

    assert seeded_from == [template]
    seeded_target = target / "Creality Print" / "7.0 Alpha"
    assert (seeded_target / "Creality.conf").read_text(encoding="utf-8") == "printer=config\n"
    assert not (seeded_target / "log").exists()


def test_prepare_slicer_datadir_uses_empty_dir_when_no_template(tmp_path: Path):
    target = tmp_path / "run-data"
    appdata = tmp_path / "appdata"
    appdata.mkdir()

    seeded_from = prepare_slicer_datadir(target, env={"APPDATA": str(appdata)})

    assert seeded_from == []
    assert target.exists()
    assert list(target.iterdir()) == []


def test_prepare_slicer_datadir_does_not_auto_seed_appdata_by_default(tmp_path: Path):
    target = tmp_path / "run-data"
    appdata = tmp_path / "appdata"
    profile = appdata / "Creality" / "Creality Print" / "7.0 Alpha"
    profile.mkdir(parents=True)
    (profile / "Creality.conf").write_text("printer=config\n", encoding="utf-8")

    seeded_from = prepare_slicer_datadir(target, env={"APPDATA": str(appdata)})

    assert seeded_from == []
    assert target.exists()
    assert list(target.iterdir()) == []


def test_prepare_slicer_datadir_auto_seeds_appdata_when_enabled(tmp_path: Path):
    target = tmp_path / "run-data"
    appdata = tmp_path / "appdata"
    profile = appdata / "Creality" / "Creality Print" / "7.0 Alpha"
    profile.mkdir(parents=True)
    (profile / "Creality.conf").write_text("printer=config\n", encoding="utf-8")

    seeded_from = prepare_slicer_datadir(
        target,
        env={"APPDATA": str(appdata), "SLICER_DATADIR_AUTO_SEED": "1"},
    )

    assert seeded_from == [profile]
    assert (target / "Creality Print" / "7.0 Alpha" / "Creality.conf").exists()


def test_prepare_slicer_datadir_fails_when_old_datadir_is_locked(tmp_path: Path, monkeypatch):
    target = tmp_path / "run-data"
    target.mkdir()

    def fail_rmtree(_path):
        raise PermissionError("locked")

    monkeypatch.setattr("ci.jenkins_build_tester.shutil.rmtree", fail_rmtree)

    with pytest.raises(PermissionError, match="locked"):
        prepare_slicer_datadir(target, env={})


def test_resolve_run_slicer_datadir_uses_jenkins_build_number(tmp_path: Path):
    root = tmp_path / "artifacts"

    datadir = resolve_run_slicer_datadir(
        root,
        platform="windows",
        package_build_number=1793,
        env={"BUILD_NUMBER": "67"},
    )

    assert datadir == root / "slicer_data" / "windows" / "1793" / "jenkins_67"


def test_resolve_run_slicer_datadir_falls_back_to_package_build_number(tmp_path: Path):
    root = tmp_path / "artifacts"

    datadir = resolve_run_slicer_datadir(
        root,
        platform="windows",
        package_build_number=1793,
        env={},
    )

    assert datadir == root / "slicer_data" / "windows" / "1793"


def test_should_use_isolated_slicer_datadir_defaults_to_global_datadir():
    assert should_use_isolated_slicer_datadir({}) is False


def test_should_use_isolated_slicer_datadir_can_be_enabled_explicitly():
    assert should_use_isolated_slicer_datadir({"SLICER_DATADIR_ISOLATED": "1"}) is True


def test_should_use_isolated_slicer_datadir_is_enabled_for_template():
    assert should_use_isolated_slicer_datadir({"SLICER_DATADIR_TEMPLATE": r"D:\profiles\Creality Print\7.0 Alpha"}) is True
