import os
from pathlib import Path

from ci.jenkins_build_tester import prepare_slicer_datadir


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
