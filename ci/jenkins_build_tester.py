#!/usr/bin/env python3
"""
Download a Jenkins build artifact by job/build id and run tests against it.
"""
import argparse
import json
import os
import sys
from pathlib import Path

from jenkins_release_orchestrator import (
    JenkinsClient,
    FeishuNotifier,
    load_env_file,
    run_tests,
    extract_artifact_zip,
    find_slicer_exe,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download a Jenkins build artifact and run tests.")
    parser.add_argument("--job-name", required=True, help="Jenkins job name")
    parser.add_argument("--build-id", required=True, help="Jenkins build number")
    parser.add_argument("--artifact-path", help="Desired artifact relativePath or filename (optional)")
    parser.add_argument("--artifacts-dir", default=os.getenv("ARTIFACTS_DIR", "artifacts"), help="Where to store downloaded artifacts")
    parser.add_argument("--gcode-root", default=os.getenv("GCODE_ROOT", ""), help="Root directory for pytest --gcode-root; auto-generated when omitted")
    parser.add_argument("--platform", default=os.getenv("PLATFORM", "windows"), help="Platform label used for env injection (e.g., windows/macos_x86/macos_arm64/linux)")
    parser.add_argument("--skip-tested-build", action="store_true", default=os.getenv("SKIP_TESTED_BUILD", "").lower() in {"1", "true", "yes", "on"}, help="Skip when the resolved build was already tested")
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

    jenkins_base = os.getenv("JENKINS_BASE_URL") or os.getenv("JENKINS_URL")
    jenkins_user = os.getenv("JENKINS_USER")
    jenkins_token = os.getenv("JENKINS_TOKEN")
    feishu_webhook = os.getenv("FEISHU_WEBHOOK")

    notifier = FeishuNotifier(feishu_webhook)
    if not jenkins_base:
        msg = "[error] JENKINS_BASE_URL or JENKINS_URL is required"
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
    artifacts_root = repo_root / args.artifacts_dir
    dest_dir = artifacts_root / args.platform
    state_dir = artifacts_root / "tested_builds"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / f"{args.job_name.replace('/', '_')}_{args.platform}.json"
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
        if (
            int(state.get("build_number") or -1) == build_number
            and str(state.get("test_command") or "").strip() == test_args
        ):
            print(f"[info] {args.job_name} #{build_number} was already tested, skipping")
            return 0

    print(f"[info] downloading artifact for {args.job_name} #{build_number}")
    downloaded, artifact_url, artifacts_meta = client.download_artifact(args.job_name, build_number, args.artifact_path, dest_dir)
    if not downloaded:
        msg = f"[error] no artifact found for {args.job_name} #{build_number}"
        print(msg, file=sys.stderr)
        notifier.send_text("单平台构建测试失败", [msg])
        return 1

    print(f"[info] artifact saved to: {downloaded}")
    if artifact_url:
        print(f"[info] artifact URL: {artifact_url}")

    env = os.environ.copy()
    env["ARTIFACTS_DIR"] = str(artifacts_root)
    env["PYTHONUNBUFFERED"] = "1"
    existing_pythonpath = env.get("PYTHONPATH", "")
    python_paths = [str(repo_root), str(repo_root / "test_framework")]
    if existing_pythonpath:
        python_paths.append(existing_pythonpath)
    env["PYTHONPATH"] = os.pathsep.join(python_paths)
    env["SECOND_SLICE_BASELINE_CSV"] = str(state_dir / f"{args.job_name.replace('/', '_')}_{args.platform}_second_slice_baseline.csv")
    platform_key = args.platform.upper()
    env[f"ARTIFACT_{platform_key}"] = str(downloaded)

    slicer_exe = None
    extract_root = artifacts_root / "extracted" / args.platform
    extracted_dir = extract_artifact_zip(downloaded, extract_root)
    if extracted_dir:
        maybe_exe = find_slicer_exe(extracted_dir)
        if maybe_exe:
            env[f"CREALITY_PRINTER_PATH"] = str(maybe_exe)
            slicer_exe = maybe_exe

    if "{slicer_exe}" in test_args:
        if slicer_exe:
            test_args = test_args.replace("{slicer_exe}", str(slicer_exe))
        else:
            print("[warn] slicer_exe placeholder present but no executable found", file=sys.stderr)

    gcode_root = Path(args.gcode_root).resolve() if args.gcode_root else (artifacts_root / "gcode" / args.platform / str(build_number)).resolve()
    gcode_root.mkdir(parents=True, exist_ok=True)

    slicer_arg = f' --slicer-exe="{slicer_exe}"' if slicer_exe else ""
    gcode_root_arg = "" if "--gcode-root" in test_args else f' --gcode-root="{gcode_root}"'
    test_command = (
        f"cd .\\test_framework\\&&python -u -m pytest {test_args}{slicer_arg}{gcode_root_arg}"
        " -v --alluredir=../allure-results --capture=tee-sys"
    )

    print(f"[info] running tests with command: {test_command}")
    result = run_tests(test_command, env, repo_root)
    print(f"[info] tests finished with status: {result.status}, rc={result.return_code}")
    if result.status == "SUCCESS":
        state_path.write_text(
            json.dumps(
                {
                    "job_name": args.job_name,
                    "platform": args.platform,
                    "build_number": build_number,
                    "test_command": test_args,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    # Prefer exe URL for Windows notifications when available
    preferred_url = None
    if artifacts_meta:
        if args.platform.lower().startswith("windows"):
            for a in artifacts_meta:
                rel = a.get("relativePath") or ""
                if rel.lower().endswith(".exe"):
                    preferred_url = f"{jenkins_base}/job/{args.job_name}/{build_number}/artifact/{rel}"
                    break
        if not preferred_url and artifact_url:
            preferred_url = artifact_url
    if not preferred_url:
        preferred_url = artifact_url or downloaded
    lines = [
        f"Job: {args.job_name}",
        f"Build: #{build_number}",
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
            import shutil
            shutil.rmtree(extracted_dir, ignore_errors=True)
    except Exception as exc:
        print(f"[warn] cleanup failed: {exc}", file=sys.stderr)

    return 0 if result.status == "SUCCESS" else 1


if __name__ == "__main__":
    sys.exit(main())
