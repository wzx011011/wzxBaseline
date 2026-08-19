#!/usr/bin/env python3
"""
Download a Jenkins build artifact by job/build id and run tests against it.
"""
import argparse
import ctypes
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import uuid
from ctypes import wintypes
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from jenkins_release_orchestrator import (
    JenkinsClient,
    FeishuNotifier,
    load_env_file,
    run_tests,
    extract_artifact_zip,
    find_slicer_exe,
)


def _truthy(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _write_package_metadata(downloaded: Path, source_kind: str, job_name: str, build_number: object) -> None:
    """Expose the selected package to opt-in wrappers without changing test reports."""
    output_value = str(os.getenv("PERFORMANCE_PACKAGE_METADATA_PATH") or "").strip()
    if not output_value:
        return

    output_path = Path(output_value).expanduser()
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(
                {
                    "package_name": downloaded.name,
                    "source_kind": source_kind,
                    "job_name": str(job_name or ""),
                    "build_number": str(build_number),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    except OSError as exc:
        print(f"[warn] unable to write package metadata: {exc}", file=sys.stderr)


def split_test_command_args(command: str) -> List[str]:
    """Split pytest arguments without losing Windows regex backslashes."""
    value = str(command or "").strip()
    if not value:
        return []
    if os.name != "nt":
        return shlex.split(value)

    # CommandLineToArgvW follows the same quoting rules used by Windows Python.
    # Prefix a dummy executable because argv[0] has special parsing semantics.
    argc = ctypes.c_int()
    command_line_to_argv = ctypes.windll.shell32.CommandLineToArgvW
    command_line_to_argv.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_int)]
    command_line_to_argv.restype = ctypes.POINTER(wintypes.LPWSTR)
    argv = command_line_to_argv(f"pytest {value}", ctypes.byref(argc))
    if not argv:
        raise ctypes.WinError()
    try:
        return [argv[index] for index in range(1, argc.value)]
    finally:
        ctypes.windll.kernel32.LocalFree(argv)


def _template_relative_target(source: Path) -> Path:
    if source.parent.name in {"Creality Print", "CrealityPrint"}:
        return Path(source.parent.name) / source.name
    if source.name in {"Creality Print", "CrealityPrint"}:
        return Path(source.name)
    return Path()


def _candidate_slicer_datadir_templates(env: Optional[Dict[str, str]] = None) -> List[Tuple[Path, Path]]:
    env = env or os.environ
    candidates: List[Tuple[Path, Path]] = []
    explicit = str(env.get("SLICER_DATADIR_TEMPLATE", "")).strip()
    if explicit:
        explicit_path = Path(explicit)
        candidates.append((explicit_path, _template_relative_target(explicit_path)))

    if not _truthy(str(env.get("SLICER_DATADIR_AUTO_SEED", ""))):
        return candidates

    appdata = str(env.get("APPDATA", "")).strip()
    if appdata:
        appdata_path = Path(appdata)
        candidates.extend(
            [
                (appdata_path / "Creality" / "Creality Print" / "7.0 Alpha", Path("Creality Print") / "7.0 Alpha"),
                (appdata_path / "Creality" / "Creality Print" / "7.0", Path("Creality Print") / "7.0"),
                (appdata_path / "CrealityPrint" / "7.0 Alpha", Path("CrealityPrint") / "7.0 Alpha"),
                (appdata_path / "CrealityPrint" / "7.0", Path("CrealityPrint") / "7.0"),
            ]
        )
    return candidates


def _copy_slicer_datadir_template(source: Path, target: Path) -> None:
    ignore_names = {
        "log",
        "logs",
        "applock.data",
        "cache",
        "caches",
        "thumbnail_cache",
        "cloud_download_data",
        "Network",
        "GPUCache",
        "Code Cache",
    }

    ignore_keys = {name.lower() for name in ignore_names}

    def ignore(_dir: str, names: List[str]) -> Set[str]:
        return {name for name in names if name.lower() in ignore_keys}

    shutil.copytree(source, target, dirs_exist_ok=True, ignore=ignore)


def prepare_slicer_datadir(target: Path, env: Optional[Dict[str, str]] = None) -> List[Path]:
    """Create an isolated CrealityPrint datadir, seeded from a known-good profile if present."""
    env = env or os.environ
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)

    if _truthy(str(env.get("SLICER_DATADIR_EMPTY", ""))):
        return []

    seeded: List[Path] = []
    for candidate, relative_target in _candidate_slicer_datadir_templates(env):
        candidate = candidate.expanduser()
        if candidate.exists() and candidate.is_dir():
            dest = target / relative_target if str(relative_target) else target
            dest.parent.mkdir(parents=True, exist_ok=True)
            _copy_slicer_datadir_template(candidate, dest)
            seeded.append(candidate)
    return seeded


def resolve_run_slicer_datadir(
    artifacts_root: Path,
    platform: str,
    package_build_number: int,
    env: Optional[Dict[str, str]] = None,
) -> Path:
    env = env or os.environ
    datadir = artifacts_root / "slicer_data" / platform / str(package_build_number)
    jenkins_build_number = str(env.get("BUILD_NUMBER", "")).strip()
    if jenkins_build_number:
        datadir = datadir / f"jenkins_{jenkins_build_number}"
    return datadir.resolve()


def should_use_isolated_slicer_datadir(env: Optional[Dict[str, str]] = None) -> bool:
    env = env or os.environ
    return (
        _truthy(str(env.get("SLICER_DATADIR_ISOLATED", "")))
        or bool(str(env.get("SLICER_DATADIR_TEMPLATE", "")).strip())
        or _truthy(str(env.get("SLICER_DATADIR_EMPTY", "")))
    )


def _safe_filename_part(value: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in str(value).strip())
    return safe.strip("_") or "unknown"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stage_local_package(source_value: str, dest_dir: Path) -> Tuple[Path, str]:
    """Copy a manually selected release ZIP into the run workspace.

    The pipeline cleans managed artifacts after a run. Copying first keeps the
    original package (including one on a shared drive) untouched.
    """
    source = Path(str(source_value).strip()).expanduser()
    if not source.is_file():
        raise ValueError(f"local package file does not exist: {source}")
    if source.suffix.lower() != ".zip":
        raise ValueError(f"local package must be a .zip file: {source}")

    staging_dir = dest_dir / "manual"
    staging_dir.mkdir(parents=True, exist_ok=True)
    temporary = staging_dir / f".{_safe_filename_part(source.stem)}.{uuid.uuid4().hex}.tmp"
    try:
        shutil.copy2(source, temporary)
        # Hash the staged copy so skip state always describes the bytes tested.
        digest = _sha256_file(temporary)
        target = staging_dir / f"{_safe_filename_part(source.stem)}_{digest[:12]}.zip"
        if source.resolve() == target.resolve():
            target = staging_dir / f"{_safe_filename_part(source.stem)}_{digest[:12]}_{uuid.uuid4().hex[:8]}.zip"
        temporary.replace(target)
    finally:
        if temporary.exists():
            temporary.unlink()
    return target, digest


def resolve_manual_package_id(requested_id: str, package_path: Path, digest: str) -> str:
    value = str(requested_id or "").strip()
    return value or f"{package_path.stem}-{digest[:12]}"


def resolve_slicer_stdout_log(
    repo_root: Path,
    platform: str,
    package_build_number: int,
    env: Optional[Dict[str, str]] = None,
) -> Path:
    env = env or os.environ
    parts = ["slicer_stdout", _safe_filename_part(platform), str(package_build_number)]
    jenkins_build_number = str(env.get("BUILD_NUMBER", "")).strip()
    if jenkins_build_number:
        parts.append(f"jenkins_{_safe_filename_part(jenkins_build_number)}")
    return (repo_root / "test_framework" / "artifacts" / ("_".join(parts) + ".log")).resolve()


def resolve_slicer_log_dir(slicer_datadir: Path) -> Path:
    return (slicer_datadir / "Creality Print" / "7.0 Alpha" / "log").resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run tests against a selected local package or Jenkins artifact.")
    parser.add_argument("--artifact-file", default=os.getenv("PACKAGE_FILE", ""), help="Local release ZIP path; bypasses Jenkins artifact download")
    parser.add_argument("--artifact-id", default=os.getenv("PACKAGE_ID", ""), help="Optional display identifier for a local package")
    parser.add_argument("--job-name", help="Jenkins job name (required when --artifact-file is omitted)")
    parser.add_argument("--build-id", help="Jenkins build number (required when --artifact-file is omitted)")
    parser.add_argument("--artifact-path", help="Desired artifact relativePath or filename (optional)")
    parser.add_argument("--artifacts-dir", default=os.getenv("ARTIFACTS_DIR", "artifacts"), help="Where to store downloaded artifacts")
    parser.add_argument("--allure-results-dir", default=os.getenv("ALLURE_RESULTS_DIR", "allure-results"), help="Directory for pytest Allure result files, relative to the repository unless absolute")
    parser.add_argument("--gcode-root", default=os.getenv("GCODE_ROOT", ""), help="Root directory for pytest --gcode-root; auto-generated when omitted")
    parser.add_argument("--platform", default=os.getenv("PLATFORM", "windows"), help="Platform label used for env injection (e.g., windows/macos_x86/macos_arm64/linux)")
    parser.add_argument("--baseline-build-id", default=os.getenv("BASELINE_BUILD_ID", "1793"), help="Fixed Jenkins build number used as the second-slice baseline")
    parser.add_argument("--second-slice-model", default=os.getenv("SECOND_SLICE_MODEL", ""), help="Optional 3MF path used as the only second-slice case")
    parser.add_argument("--enable-second-slice", action="store_true", default=_truthy(os.getenv("ENABLE_SECOND_SLICE", "0")), help="Enable moved-model second-slice performance checks")
    parser.add_argument("--update-baseline", action="store_true", default=os.getenv("UPDATE_BASELINE", "").lower() in {"1", "true", "yes", "on"}, help="Allow updating the persistent second-slice baseline CSV")
    parser.add_argument("--skip-tested-build", action="store_true", default=os.getenv("SKIP_TESTED_BUILD", "").lower() in {"1", "true", "yes", "on"}, help="Skip when the resolved build was already tested")
    parser.add_argument("--preserve-extracted-files", action="store_true", default=_truthy(os.getenv("PRESERVE_EXTRACTED_FILES", "1")), help="Overlay ZIP contents onto the extraction directory without removing existing files")
    parser.add_argument(
        "--test-command",
        default=os.getenv("TEST_COMMAND", "pytest -q"),
        help='Test command to execute; supports "{slicer_exe}" placeholder',
    )
    return parser.parse_args()


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    load_env_file(repo_root)
    args = parse_args()

    feishu_webhook = os.getenv("FEISHU_WEBHOOK")
    notifier = FeishuNotifier(feishu_webhook)

    artifact_file = str(args.artifact_file or "").strip()
    has_jenkins_fields = bool(str(args.job_name or "").strip() or str(args.build_id or "").strip())
    if artifact_file and has_jenkins_fields:
        msg = "[error] --artifact-file cannot be combined with --job-name or --build-id"
        print(msg, file=sys.stderr)
        notifier.send_text("单平台构建测试失败", [msg])
        return 2

    if not artifact_file and (not str(args.job_name or "").strip() or not str(args.build_id or "").strip()):
        msg = "[error] provide --artifact-file, or both --job-name and --build-id"
        print(msg, file=sys.stderr)
        notifier.send_text("单平台构建测试失败", [msg])
        return 2

    artifacts_root = repo_root / args.artifacts_dir
    dest_dir = artifacts_root / args.platform
    state_dir = artifacts_root / "tested_builds"
    state_dir.mkdir(parents=True, exist_ok=True)

    source_kind = "local" if artifact_file else "jenkins"
    artifact_sha256 = ""
    artifact_url = None
    artifacts_meta: List[Dict] = []
    jenkins_base = None
    package_id = ""
    package_run_key = ""
    state_key = ""
    source_label = ""
    build_number = ""

    if source_kind == "local":
        try:
            downloaded, artifact_sha256 = stage_local_package(artifact_file, dest_dir)
        except (OSError, ValueError) as exc:
            msg = f"[error] {exc}"
            print(msg, file=sys.stderr)
            notifier.send_text("单平台构建测试失败", [msg])
            return 2
        package_id = resolve_manual_package_id(args.artifact_id, Path(artifact_file), artifact_sha256)
        package_run_key = _safe_filename_part(package_id)
        state_key = "manual"
        source_label = f"local package {package_id}"
        build_number = package_run_key
        print(f"[info] staged {source_label}: {downloaded}")
    else:
        jenkins_base = os.getenv("JENKINS_BASE_URL") or os.getenv("JENKINS_URL")
        jenkins_user = os.getenv("JENKINS_USER")
        jenkins_token = os.getenv("JENKINS_TOKEN")
        if not jenkins_base:
            msg = "[error] JENKINS_BASE_URL or JENKINS_URL is required for Jenkins artifact mode"
            print(msg, file=sys.stderr)
            notifier.send_text("单平台构建测试失败", [msg])
            return 2

        client = JenkinsClient(jenkins_base, jenkins_user, jenkins_token)
        build_id_text = str(args.build_id).strip()
        if build_id_text == "lastSuccessfulBuild":
            resp = client.session.get(f"{client.base_url}/job/{args.job_name}/lastSuccessfulBuild/api/json", timeout=client.timeout)
            resp.raise_for_status()
            build_number = int(resp.json()["number"])
        else:
            try:
                build_number = int(args.build_id)
            except ValueError:
                msg = f"[error] invalid build-id: {args.build_id}"
                print(msg, file=sys.stderr)
                notifier.send_text("单平台构建测试失败", [msg])
                return 2

        print(f"[info] downloading artifact for {args.job_name} #{build_number}")
        downloaded, artifact_url, artifacts_meta = client.download_artifact(args.job_name, build_number, args.artifact_path, dest_dir)
        if not downloaded:
            msg = f"[error] no artifact found for {args.job_name} #{build_number}"
            print(msg, file=sys.stderr)
            notifier.send_text("单平台构建测试失败", [msg])
            return 1

        package_id = str(build_number)
        package_run_key = _safe_filename_part(package_id)
        state_key = str(args.job_name)
        source_label = f"Jenkins {args.job_name} #{build_number}"
        print(f"[info] artifact saved to: {downloaded}")
        if artifact_url:
            print(f"[info] artifact URL: {artifact_url}")

    _write_package_metadata(downloaded, source_kind, str(args.job_name or ""), build_number)

    state_file_key = _safe_filename_part(state_key)
    platform_file_key = _safe_filename_part(args.platform)
    state_path = state_dir / f"{state_file_key}_{platform_file_key}.json"
    baseline_csv = state_dir / f"{state_file_key}_{platform_file_key}_second_slice_baseline.csv"
    baseline_build_text = str(args.baseline_build_id).strip()
    try:
        baseline_build_number = int(baseline_build_text)
    except ValueError:
        baseline_build_number = -1
    test_args = (args.test_command or "").strip()
    if not test_args:
        test_args = "-q"
    if len(test_args) >= 2 and test_args[0] == test_args[-1] and test_args[0] in {"'", '"'}:
        test_args = test_args[1:-1].strip()
    # Undo optional cmd-layer escaping from Jenkins bat when needed.
    test_args = test_args.replace('\\"', '"')

    if args.skip_tested_build and state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            state = {}
        if source_kind == "local":
            same_source = (
                state.get("source_kind") == "local"
                and state.get("artifact_sha256") == artifact_sha256
            )
        else:
            same_source = (
                state.get("source_kind") in {None, "jenkins"}
                and str(state.get("build_number") or "") == str(build_number)
            )
        same_mode = bool(state.get("enable_second_slice", False)) == bool(args.enable_second_slice)
        if same_source and same_mode and str(state.get("test_command") or "").strip() == test_args:
            print(f"[info] {source_label} was already tested, skipping")
            if source_kind == "local" and downloaded.exists():
                try:
                    downloaded.unlink()
                except OSError as exc:
                    print(f"[warn] cleanup failed: {exc}", file=sys.stderr)
            return 0

    env = os.environ.copy()
    env["ARTIFACTS_DIR"] = str(artifacts_root)
    env["PYTHONUNBUFFERED"] = "1"
    existing_pythonpath = env.get("PYTHONPATH", "")
    python_paths = [str(repo_root), str(repo_root / "test_framework")]
    if existing_pythonpath:
        python_paths.append(existing_pythonpath)
    env["PYTHONPATH"] = os.pathsep.join(python_paths)
    env["ENABLE_SECOND_SLICE"] = "1" if args.enable_second_slice else "0"
    env["PERFORMANCE_SOURCE_KIND"] = source_kind
    env["PERFORMANCE_SOURCE_JOB"] = str(args.job_name or "")
    env["PERFORMANCE_SOURCE_BUILD_ID"] = str(build_number)
    env["PERFORMANCE_TESTER_BUILD_ID"] = str(env.get("BUILD_NUMBER") or "")
    env["PERFORMANCE_TESTER_BUILD_URL"] = str(env.get("BUILD_URL") or "")
    env["PERFORMANCE_AGENT"] = str(env.get("NODE_NAME") or env.get("COMPUTERNAME") or "")
    env["PERFORMANCE_PLATFORM"] = str(args.platform)
    env["PERFORMANCE_RUN_TIMESTAMP"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    env["PERFORMANCE_RUN_ID"] = str(env.get("BUILD_TAG") or f"{state_file_key}:{platform_file_key}:{build_number}")
    env["PERFORMANCE_HISTORY_PATH"] = str(
        state_dir / f"{state_file_key}_{platform_file_key}_performance_history.json"
    )
    if source_kind == "jenkins" and jenkins_base:
        env["PERFORMANCE_SOURCE_URL"] = f"{jenkins_base}/job/{args.job_name}/{build_number}/"
    else:
        env["PERFORMANCE_SOURCE_URL"] = str(artifact_file)
    env["SECOND_SLICE_BASELINE_CSV"] = str(baseline_csv)
    env["SECOND_SLICE_BASELINE_BUILD_ID"] = str(args.baseline_build_id if source_kind == "jenkins" else package_id)
    allow_update_baseline = args.enable_second_slice and (
        args.update_baseline
        or (source_kind == "jenkins" and build_number == baseline_build_number and not baseline_csv.exists())
    )
    env["SECOND_SLICE_UPDATE_BASELINE"] = "1" if allow_update_baseline else "0"
    print(f"[info] second slice: {'enabled' if args.enable_second_slice else 'disabled'}")
    print(
        f"[info] second-slice baseline: scope={state_key}, "
        f"csv={baseline_csv}, update={'on' if allow_update_baseline else 'off'}"
    )
    if source_kind == "local" and not baseline_csv.exists() and not allow_update_baseline:
        print(
            "[warn] no manual baseline exists; rerun an approved reference package with "
            "--update-baseline to initialize performance comparison"
        )
    platform_key = args.platform.upper()
    env[f"ARTIFACT_{platform_key}"] = str(downloaded)

    slicer_exe = None
    extract_root = artifacts_root / "extracted" / args.platform
    extracted_dir = extract_artifact_zip(downloaded, extract_root, preserve_existing=args.preserve_extracted_files)
    if extracted_dir:
        maybe_exe = find_slicer_exe(extracted_dir)
        if maybe_exe:
            env[f"CREALITY_PRINTER_PATH"] = str(maybe_exe)
            slicer_exe = maybe_exe
    if source_kind == "local" and not slicer_exe:
        msg = f"[error] local package does not contain CrealityPrint.exe: {downloaded}"
        print(msg, file=sys.stderr)
        notifier.send_text("单平台构建测试失败", [msg])
        try:
            if extracted_dir and extracted_dir.exists():
                print(f"[info] preserving extracted package directory: {extracted_dir}")
            if downloaded.exists():
                downloaded.unlink()
        except OSError as exc:
            print(f"[warn] cleanup failed: {exc}", file=sys.stderr)
        return 1

    if "{slicer_exe}" in test_args:
        if slicer_exe:
            test_args = test_args.replace("{slicer_exe}", str(slicer_exe))
        else:
            print("[warn] slicer_exe placeholder present but no executable found", file=sys.stderr)

    gcode_root = Path(args.gcode_root).resolve() if args.gcode_root else (artifacts_root / "gcode" / args.platform / package_run_key).resolve()
    gcode_root.mkdir(parents=True, exist_ok=True)
    slicer_datadir = None
    if should_use_isolated_slicer_datadir(env):
        slicer_datadir = resolve_run_slicer_datadir(artifacts_root, args.platform, build_number, env)
        seeded_from = prepare_slicer_datadir(slicer_datadir, env)
        slicer_log_dir = resolve_slicer_log_dir(slicer_datadir)
        slicer_log_dir.mkdir(parents=True, exist_ok=True)
        env["CREALITY_PRINTER_LOG_PATH"] = str(slicer_log_dir)
        slicer_stdout_log = resolve_slicer_stdout_log(repo_root, args.platform, build_number, env)
        slicer_stdout_log.parent.mkdir(parents=True, exist_ok=True)
        try:
            slicer_stdout_log.unlink()
        except FileNotFoundError:
            pass
        env["SLICER_STDOUT_LOG"] = str(slicer_stdout_log)
        print(f"[info] using isolated slicer datadir: {slicer_datadir}")
        print(f"[info] using isolated slicer log dir: {slicer_log_dir}")
        print(f"[info] slicer stdout log: {slicer_stdout_log}")
        if seeded_from:
            for source in seeded_from:
                print(f"[info] seeded slicer datadir from: {source}")
        else:
            print("[warn] no slicer datadir template found; starting with an empty datadir")
    else:
        print("[info] using Jenkins user CrealityPrint datadir")

    test_command = [sys.executable, "-u", "-m", "pytest", *split_test_command_args(test_args)]
    if slicer_exe:
        test_command.extend(["--slicer-exe", str(slicer_exe)])
    if "--gcode-root" not in test_args:
        test_command.extend(["--gcode-root", str(gcode_root)])
    if slicer_datadir and "--slicer-datadir" not in test_args:
        test_command.extend(["--slicer-datadir", str(slicer_datadir)])
    allure_results_dir = Path(args.allure_results_dir).expanduser()
    if not allure_results_dir.is_absolute():
        allure_results_dir = repo_root / allure_results_dir
    allure_results_dir = allure_results_dir.resolve()
    test_command.extend(["-v", "--alluredir", str(allure_results_dir), "--capture=tee-sys"])
    if args.second_slice_model and "--second-slice-model" not in test_args:
        requested_model = Path(args.second_slice_model).expanduser()
        if not requested_model.is_absolute():
            requested_model = repo_root / requested_model
        test_command.extend(["--second-slice-model", str(requested_model.resolve())])

    print(f"[info] running tests with command: {subprocess.list2cmdline(test_command)}")
    result = run_tests(test_command, env, repo_root / "test_framework")
    print(f"[info] tests finished with status: {result.status}, rc={result.return_code}")
    if result.status == "SUCCESS":
        state_path.write_text(
            json.dumps(
                {
                    "source_kind": source_kind,
                    "source_label": source_label,
                    "job_name": args.job_name if source_kind == "jenkins" else None,
                    "platform": args.platform,
                    "build_number": build_number,
                    "package_id": package_id,
                    "artifact_sha256": artifact_sha256 or None,
                    "test_command": test_args,
                    "enable_second_slice": bool(args.enable_second_slice),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    # Prefer exe URL for Windows notifications when available
    preferred_url = None
    if source_kind == "jenkins" and artifacts_meta:
        if args.platform.lower().startswith("windows"):
            for a in artifacts_meta:
                rel = a.get("relativePath") or ""
                if rel.lower().endswith(".exe"):
                    preferred_url = f"{jenkins_base}/job/{args.job_name}/{build_number}/artifact/{rel}"
                    break
        if not preferred_url and artifact_url:
            preferred_url = artifact_url
    if not preferred_url:
        preferred_url = artifact_url or artifact_file or downloaded
    lines = [
        f"Source: {source_label}",
        f"Artifact: {preferred_url}",
        f"Test: {result.status} (rc={result.return_code})",
    ]
    tail = (result.output or "")[-1200:]
    if tail:
        lines.append("")
        lines.append("输出片段:")
        lines.append(tail)

    title = "单平台构建测试通过" if result.status == "SUCCESS" else "单平台构建测试失败"
    notifier.send_text(title, lines)

    # Cleanup downloaded/extracted artifacts
    try:
        if downloaded and downloaded.exists():
            if downloaded.is_file():
                downloaded.unlink()
        if extracted_dir and extracted_dir.exists():
            print(f"[info] preserving extracted package directory: {extracted_dir}")
    except Exception as exc:
        print(f"[warn] cleanup failed: {exc}", file=sys.stderr)

    return 0 if result.status == "SUCCESS" else 1


if __name__ == "__main__":
    sys.exit(main())
