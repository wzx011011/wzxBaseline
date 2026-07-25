import hashlib
from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile

import pytest

from ci.jenkins_build_tester import (
    main,
    prepare_slicer_datadir,
    resolve_manual_package_id,
    resolve_run_slicer_datadir,
    resolve_slicer_log_dir,
    resolve_slicer_stdout_log,
    stage_local_package,
    should_use_isolated_slicer_datadir,
)
from ci.jenkins_release_orchestrator import extract_artifact_zip
from test_framework.performance.case import test_slice


def test_extract_artifact_zip_overlay_preserves_unrelated_files(tmp_path: Path):
    archive = tmp_path / "package.zip"
    with ZipFile(archive, "w") as zf:
        zf.writestr("CrealityPrint/CrealityPrint.exe", "new executable")
        zf.writestr("CrealityPrint/new.dll", "new library")

    target = tmp_path / "extracted"
    target.mkdir()
    (target / "CrealityPrint.exe").write_text("old executable", encoding="utf-8")
    (target / "keep.dll").write_text("keep me", encoding="utf-8")

    extract_artifact_zip(archive, target, preserve_existing=True)

    assert (target / "CrealityPrint.exe").read_text(encoding="utf-8") == "new executable"
    assert (target / "new.dll").read_text(encoding="utf-8") == "new library"
    assert (target / "keep.dll").read_text(encoding="utf-8") == "keep me"


def test_second_slice_model_is_opt_in(tmp_path: Path, monkeypatch):
    cases = [
        {"record_id": "a", "name": "a.3mf", "path": "a.3mf", "title": "a.3mf"},
        {"record_id": "b", "name": "b.3mf", "path": "b.3mf", "title": "b.3mf"},
    ]
    monkeypatch.setattr(test_slice, "_FEISHU_CASES", None)
    monkeypatch.setattr(test_slice, "_download_http_3mf_files", lambda: cases)
    no_fixed_model = SimpleNamespace(getoption=lambda _name: "")

    assert test_slice._collect_feishu_cases(no_fixed_model) == cases

    model = tmp_path / "single.3mf"
    model.write_bytes(b"3mf")
    monkeypatch.setattr(test_slice, "_FEISHU_CASES", None)
    fixed_model = SimpleNamespace(getoption=lambda _name: str(model))

    selected = test_slice._collect_feishu_cases(fixed_model)
    assert [case["path"] for case in selected] == [str(model.resolve())]


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


def test_resolve_slicer_log_dir_uses_isolated_datadir(tmp_path: Path):
    datadir = tmp_path / "run-data"

    log_dir = resolve_slicer_log_dir(datadir)

    assert log_dir == datadir / "Creality Print" / "7.0 Alpha" / "log"


def test_resolve_slicer_stdout_log_uses_jenkins_build_number(tmp_path: Path):
    log_path = resolve_slicer_stdout_log(
        tmp_path,
        platform="windows",
        package_build_number=1793,
        env={"BUILD_NUMBER": "74"},
    )

    assert log_path == tmp_path / "test_framework" / "artifacts" / "slicer_stdout_windows_1793_jenkins_74.log"


def _write_release_zip(path: Path, marker: bytes = b"test") -> None:
    with ZipFile(path, "w") as archive:
        archive.writestr("Creality Print/CrealityPrint.exe", marker)


def test_stage_local_package_copies_zip_without_touching_source(tmp_path: Path):
    source = tmp_path / "CrealityPrint 7.0.zip"
    _write_release_zip(source)

    staged, digest = stage_local_package(str(source), tmp_path / "artifacts" / "windows")

    assert staged != source
    assert staged.is_file()
    assert staged.read_bytes() == source.read_bytes()
    assert digest == hashlib.sha256(staged.read_bytes()).hexdigest()
    staged.unlink()
    assert source.is_file()


def test_stage_local_package_rejects_non_zip_file(tmp_path: Path):
    source = tmp_path / "CrealityPrint.exe"
    source.write_bytes(b"not-a-release-zip")

    with pytest.raises(ValueError, match="must be a .zip"):
        stage_local_package(str(source), tmp_path / "artifacts")


def test_stage_local_package_does_not_replace_a_symlink_target(tmp_path: Path):
    destination = tmp_path / "artifacts" / "windows"
    package_bytes = b"release-package"
    digest = hashlib.sha256(package_bytes).hexdigest()
    original = destination / "manual" / f"source_{digest[:12]}.zip"
    original.parent.mkdir(parents=True)
    original.write_bytes(package_bytes)
    source = tmp_path / "source.zip"
    try:
        source.symlink_to(original)
    except OSError:
        pytest.skip("file symlinks are unavailable on this Windows host")

    staged, _ = stage_local_package(str(source), destination)

    assert source.is_symlink()
    assert staged != original
    assert original.read_bytes() == package_bytes


def test_resolve_manual_package_id_defaults_to_filename_and_hash(tmp_path: Path):
    package = tmp_path / "CrealityPrint.zip"

    assert resolve_manual_package_id("", package, "abcdef0123456789") == "CrealityPrint-abcdef012345"
    assert resolve_manual_package_id("7.0.0.5243", package, "abcdef0123456789") == "7.0.0.5243"


def test_main_runs_local_package_without_jenkins_and_preserves_source(tmp_path: Path, monkeypatch):
    package = tmp_path / "manual-release.zip"
    _write_release_zip(package)
    artifacts_dir = tmp_path / "artifacts"
    calls = []

    def fake_run_tests(command, env, repo_root):
        calls.append((command, env, repo_root))
        return SimpleNamespace(status="SUCCESS", return_code=0, output="ok")

    monkeypatch.setattr("ci.jenkins_build_tester.load_env_file", lambda _root: None)
    monkeypatch.setattr("ci.jenkins_build_tester.run_tests", fake_run_tests)
    monkeypatch.delenv("JENKINS_BASE_URL", raising=False)
    monkeypatch.delenv("JENKINS_URL", raising=False)
    monkeypatch.delenv("SLICER_DATADIR_ISOLATED", raising=False)
    monkeypatch.setattr(
        "sys.argv",
        [
            "jenkins_build_tester.py",
            "--artifact-file",
            str(package),
            "--artifact-id",
            "manual-5243",
            "--artifacts-dir",
            str(artifacts_dir),
            "--platform",
            "windows",
            "--test-command=-q",
        ],
    )

    assert main() == 0
    assert package.is_file()
    assert len(calls) == 1
    assert "CrealityPrint.exe" in calls[0][0]
    assert calls[0][1]["CREALITY_PRINTER_PATH"].endswith("CrealityPrint.exe")
    assert not list((artifacts_dir / "windows" / "manual").glob("*.zip"))
    state = (artifacts_dir / "tested_builds" / "manual_windows.json").read_text(encoding="utf-8")
    assert '"source_kind": "local"' in state


def test_main_does_not_skip_a_changed_manual_package(tmp_path: Path, monkeypatch):
    package = tmp_path / "manual-release.zip"
    artifacts_dir = tmp_path / "artifacts"
    calls = []

    def fake_run_tests(command, env, repo_root):
        calls.append(command)
        return SimpleNamespace(status="SUCCESS", return_code=0, output="ok")

    monkeypatch.setattr("ci.jenkins_build_tester.load_env_file", lambda _root: None)
    monkeypatch.setattr("ci.jenkins_build_tester.run_tests", fake_run_tests)
    monkeypatch.delenv("JENKINS_BASE_URL", raising=False)
    monkeypatch.delenv("JENKINS_URL", raising=False)
    monkeypatch.delenv("SLICER_DATADIR_ISOLATED", raising=False)
    monkeypatch.setattr(
        "sys.argv",
        [
            "jenkins_build_tester.py",
            "--artifact-file",
            str(package),
            "--artifact-id",
            "manual-current",
            "--artifacts-dir",
            str(artifacts_dir),
            "--skip-tested-build",
            "--test-command",
            "performance/case/test_slice.py::test_feishu_slice",
        ],
    )

    _write_release_zip(package, b"first")
    assert main() == 0
    _write_release_zip(package, b"second")
    assert main() == 0

    assert len(calls) == 2


def test_main_removes_staged_zip_when_skipping_an_unchanged_package(tmp_path: Path, monkeypatch):
    package = tmp_path / "manual-release.zip"
    artifacts_dir = tmp_path / "artifacts"
    calls = []

    def fake_run_tests(command, env, repo_root):
        calls.append(command)
        return SimpleNamespace(status="SUCCESS", return_code=0, output="ok")

    monkeypatch.setattr("ci.jenkins_build_tester.load_env_file", lambda _root: None)
    monkeypatch.setattr("ci.jenkins_build_tester.run_tests", fake_run_tests)
    monkeypatch.delenv("JENKINS_BASE_URL", raising=False)
    monkeypatch.delenv("JENKINS_URL", raising=False)
    monkeypatch.delenv("SLICER_DATADIR_ISOLATED", raising=False)
    monkeypatch.setattr(
        "sys.argv",
        [
            "jenkins_build_tester.py",
            "--artifact-file",
            str(package),
            "--artifacts-dir",
            str(artifacts_dir),
            "--skip-tested-build",
            "--test-command",
            "performance/case/test_slice.py::test_feishu_slice",
        ],
    )

    _write_release_zip(package)
    assert main() == 0
    assert main() == 0

    assert len(calls) == 1
    assert not list((artifacts_dir / "windows" / "manual").glob("*.zip"))
