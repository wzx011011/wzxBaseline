#!/usr/bin/env python3
"""
Download a Jenkins build artifact by job/build id and run tests against it.
"""
import argparse
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
    parser.add_argument("--platform", default=os.getenv("PLATFORM", "windows"), help="Platform label used for env injection (e.g., windows/macos_x86/macos_arm64/linux)")
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

    jenkins_base = os.getenv("JENKINS_BASE_URL")
    jenkins_user = os.getenv("JENKINS_USER")
    jenkins_token = os.getenv("JENKINS_TOKEN")
    feishu_webhook = os.getenv("FEISHU_WEBHOOK")

    notifier = FeishuNotifier(feishu_webhook)
    if not all([jenkins_base, jenkins_user, jenkins_token]):
        msg = "[error] JENKINS_BASE_URL / JENKINS_USER / JENKINS_TOKEN are required"
        print(msg, file=sys.stderr)
        notifier.send_text("单平台构建测试失败", [msg])
        return 2

    try:
        build_number = int(args.build_id)
    except ValueError:
        msg = f"[error] invalid build-id: {args.build_id}"
        print(msg, file=sys.stderr)
        notifier.send_text("单平台构建测试失败", [msg])
        return 2

    client = JenkinsClient(jenkins_base, jenkins_user, jenkins_token)
    artifacts_root = repo_root / args.artifacts_dir
    dest_dir = artifacts_root / args.platform

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
    platform_key = args.platform.upper()
    env[f"ARTIFACT_{platform_key}"] = str(downloaded)

    slicer_exe = None
    extracted_dir = extract_artifact_zip(downloaded)
    if extracted_dir:
        maybe_exe = find_slicer_exe(extracted_dir)
        if maybe_exe:
            env[f"SLICER_EXE_{platform_key}"] = str(maybe_exe)
            slicer_exe = maybe_exe

    test_command = args.test_command
    if "{slicer_exe}" in test_command:
        if slicer_exe:
            test_command = test_command.replace("{slicer_exe}", str(slicer_exe))
        else:
            print("[warn] slicer_exe placeholder present but no executable found", file=sys.stderr)

    print(f"[info] running tests with command: {test_command}")
    result = run_tests(test_command, env, repo_root)
    print(f"[info] tests finished with status: {result.status}, rc={result.return_code}")
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
