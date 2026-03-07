#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from git import Repo


@dataclass
class PlatformJob:
    platform: str
    job_name: str
    artifact_path: Optional[str] = None
    parameters: Optional[Dict[str, str]] = None


@dataclass
class BuildOutcome:
    platform: str
    job_name: str
    build_number: Optional[int] = None
    status: str = "UNKNOWN"
    url: Optional[str] = None
    artifact_path: Optional[str] = None
    artifact_url: Optional[str] = None
    artifact_local_path: Optional[Path] = None
    artifact_urls: List[str] = field(default_factory=list)
    console_excerpt: str = ""


@dataclass
class TestOutcome:
    status: str
    output: str
    return_code: int


class JenkinsClient:
    def __init__(self, base_url: str, username: str, token: str, timeout: int = 15):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.auth = (username, token)
        self.timeout = timeout
        self.crumb: Optional[Dict[str, str]] = None

    def _headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {}
        if self.crumb:
            headers[self.crumb["crumbRequestField"]] = self.crumb["crumb"]
        return headers

    def _ensure_crumb(self) -> None:
        if self.crumb is not None:
            return
        crumb_url = f"{self.base_url}/crumbIssuer/api/json"
        resp = self.session.get(crumb_url, timeout=self.timeout)
        if resp.ok:
            try:
                payload = resp.json()
                self.crumb = {
                    "crumbRequestField": payload["crumbRequestField"],
                    "crumb": payload["crumb"],
                }
            except Exception:
                self.crumb = None

    def trigger_job(self, job_name: str, parameters: Optional[Dict[str, str]] = None) -> str:
        self._ensure_crumb()
        endpoint = "buildWithParameters" if parameters else "build"
        url = f"{self.base_url}/job/{job_name}/{endpoint}"
        resp = self.session.post(url, params=parameters or {}, headers=self._headers(), timeout=self.timeout)
        resp.raise_for_status()
        queue_url = resp.headers.get("Location")
        if not queue_url:
            raise RuntimeError(f"Jenkins did not return queue location for job {job_name}")
        return queue_url.rstrip("/") + "/api/json"

    def wait_for_build_number(self, queue_api: str, poll: int = 5, max_wait: int = 600) -> int:
        elapsed = 0
        while elapsed <= max_wait:
            resp = self.session.get(queue_api, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            executable = data.get("executable")
            if executable and "number" in executable:
                return int(executable["number"])
            if data.get("cancelled"):
                raise RuntimeError("Jenkins queue item was cancelled")
            time.sleep(poll)
            elapsed += poll
        raise TimeoutError("Timed out waiting for Jenkins to assign a build number")

    def wait_for_result(self, job_name: str, build_number: int, poll: int = 10, max_wait: int = 3600) -> Dict:
        api_url = f"{self.base_url}/job/{job_name}/{build_number}/api/json"
        elapsed = 0
        while elapsed <= max_wait:
            resp = self.session.get(api_url, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            if not data.get("building", True):
                return data
            time.sleep(poll)
            elapsed += poll
        raise TimeoutError(f"Timed out waiting for job {job_name} build #{build_number} to finish")

    def fetch_console(self, job_name: str, build_number: int) -> str:
        url = f"{self.base_url}/job/{job_name}/{build_number}/consoleText"
        resp = self.session.get(url, timeout=self.timeout)
        if resp.ok:
            return resp.text
        return ""

    def download_artifact(self, job_name: str, build_number: int, desired_path: Optional[str], dest_dir: Path) -> Tuple[Optional[Path], Optional[str], List[Dict]]:
        dest_dir.mkdir(parents=True, exist_ok=True)
        api_url = f"{self.base_url}/job/{job_name}/{build_number}/api/json"
        resp = self.session.get(api_url, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        artifacts = data.get("artifacts") or []
        if not artifacts:
            return None, None, []
        artifact = None
        if desired_path:
            for candidate in artifacts:
                if candidate.get("relativePath") == desired_path or candidate.get("fileName") == desired_path:
                    artifact = candidate
                    break
        if artifact is None:
            zip_candidates = [
                a for a in artifacts if str(a.get("relativePath", "")).lower().endswith(".zip") or str(a.get("fileName", "")).lower().endswith(".zip")
            ]
            artifact = zip_candidates[0] if zip_candidates else artifacts[0]

        artifact_url = f"{self.base_url}/job/{job_name}/{build_number}/artifact/{artifact['relativePath']}"
        file_name = Path(artifact["fileName"]).name
        target = dest_dir / file_name
        with self.session.get(artifact_url, timeout=self.timeout, stream=True) as r:
            r.raise_for_status()
            with open(target, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
        return target, artifact_url, artifacts


class FeishuNotifier:
    def __init__(self, webhook: Optional[str]):
        self.webhook = webhook

    def send_text(self, title: str, lines: List[str]) -> None:
        if not self.webhook:
            return
        text = title + "\n" + "\n".join(lines)
        payload = {"msg_type": "text", "content": {"text": text}}
        try:
            resp = requests.post(self.webhook, json=payload, timeout=10)
            resp.raise_for_status()
        except Exception as exc:
            print(f"[warn] Feishu notify failed: {exc}", file=sys.stderr)


class LlmSummarizer:
    def __init__(self, api_key: Optional[str], base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    def summarize(self, prompt: str, max_tokens: int = 400) -> str:
        if not self.api_key:
            return prompt[:600]
        url = f"{self.base_url}/chat/completions" if "/chat/completions" not in self.base_url else self.base_url
        headers = {"Authorization": f"Bearer {self.api_key}"}
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Summarize CI build logs and highlight root causes in Chinese."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": max_tokens,
        }
        try:
            resp = requests.post(url, json=body, headers=headers, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            choice = data.get("choices", [{}])[0]
            msg = choice.get("message", {}).get("content")
            return msg or prompt[:600]
        except Exception as exc:
            print(f"[warn] LLM summary failed: {exc}", file=sys.stderr)
            return prompt[:600]


class ZentaoClient:
    def __init__(self, base_url: Optional[str], account: Optional[str], password: Optional[str], token: Optional[str] = None):
        self.base_url = base_url.rstrip("/") if base_url else None
        self.account = account
        self.password = password
        self.session = requests.Session()
        self.token: Optional[str] = token
        self.timeout = 15

    def active(self) -> bool:
        return bool(self.base_url and self.account and (self.password or self.token))

    def _candidate_bases(self) -> List[str]:
        if not self.base_url:
            return []
        raw = self.base_url.rstrip("/")
        candidates: List[str] = []
        for base in (raw, f"{raw}/zentao"):
            if base and base not in candidates:
                candidates.append(base)
        swapped = None
        if raw.startswith("https://"):
            swapped = "http://" + raw[len("https://") :]
        elif raw.startswith("http://"):
            swapped = "https://" + raw[len("http://") :]
        if swapped:
            for base in (swapped, f"{swapped}/zentao"):
                if base not in candidates:
                    candidates.append(base)
        return candidates

    def _request_with_fallback(self, method: str, paths: List[str], **kwargs) -> requests.Response:
        errors: List[Exception] = []
        for path in paths:
            for base in self._candidate_bases():
                url = f"{base}{path}"
                try:
                    resp = self.session.request(method, url, timeout=self.timeout, **kwargs)
                    if resp.status_code == 404:
                        raise requests.HTTPError(f"404 {url}", response=resp)
                    if resp.status_code == 401:
                        raise requests.HTTPError(f"401 {url}", response=resp)
                    resp.raise_for_status()
                    self.base_url = base
                    return resp
                except Exception as exc:
                    errors.append(exc)
                    continue
        if errors:
            raise errors[-1]
        raise RuntimeError("No Zentao endpoints available")

    def login(self) -> None:
        if not self.active():
            return
        if self.token:
            self.session.headers["token"] = self.token
            return
        
        errors: List[Exception] = []
        payloads = [
            {"json": {"account": self.account, "password": self.password}}
        ]
        paths_order = [
            "/tokens"
        ]
        for payload in payloads:
            try:
                resp = self._request_with_fallback("post", paths_order, **payload)
                print(f"[info] zentao list builds by execution:{resp.content} ")
                data = resp.json()
                token = data.get("token") or data.get("data", {}).get("token")
                if token:
                    self.token = token
                    self.session.headers["token"] = token
                    return
            except Exception as exc:
                errors.append(exc)
                continue
        if errors:
            raise errors[-1]
        raise RuntimeError("Zentao login did not return token")

    def post_build_summary(self, build_id: str, title: str, content: str) -> None:
        if not self.active():
            return
        if not self.token:
            self.login()
        payload = {"title": title, "desc": content}
        resp = self._request_with_fallback("put", [f"/api.php/v1/builds/{build_id}"], json=payload)

    def attach_comment(self, object_type: str, object_id: str, content: str) -> None:
        if not self.active():
            return
        if not self.token:
            self.login()
        payload = {"objectType": object_type, "objectID": object_id, "comment": content}
        self._request_with_fallback("post", ["/api.php/v1/actions"], json=payload)

    def list_builds_by_execution(self, execution_id: str, limit: int = 200) -> List[Dict]:
        """List builds under a Zentao execution; tries both execution-scoped and global filter endpoints."""
        print(f"[info] zentao list builds by execution: {execution_id}")
        if not self.active():
            return []
        if not self.token:
            self.login()
        paths = [
            f"/api.php/v1/executions/{execution_id}/builds?limit={limit}",
            f"/api.php/v1/builds?execution={execution_id}&limit={limit}",
        ]
        
        resp = self._request_with_fallback("get", paths)
        data = resp.json()
        items = data.get("builds") or data.get("data") or data.get("list") or []
        if isinstance(items, dict):
            items = list(items.values())
        return items

    def find_build_by_name(self, execution_id: str, name: str) -> Optional[Dict]:
        """Find an existing build under a Zentao execution by name."""
        for item in self.list_builds_by_execution(execution_id):
            if item.get("name") == name:
                return item
        return None

    def get_execution(self, execution_id: str) -> Optional[Dict]:
        """Fetch execution info to help fill required fields (e.g., product)."""
        if not self.active():
            return None
        if not self.token:
            self.login()
        resp = self._request_with_fallback("get", [f"/api.php/v1/executions/{execution_id}"])
        if not resp.ok:
            return None
        return resp.json()

    def create_build(self, execution_id: str, name: str, desc: str = "", product_id: Optional[str] = None, project_id: Optional[str] = None) -> Optional[str]:
        """Create a build/version under the specified Zentao execution and return its ID."""
        if not self.active():
            return None
        if not self.token:
            self.login()
        if not product_id or not project_id:
            exec_info = self.get_execution(execution_id)
            if exec_info:
                product_id = product_id or str(exec_info.get("product") or exec_info.get("products", [{}])[0].get("id") if exec_info.get("products") else "" or "")
                project_id = project_id or str(exec_info.get("project") or exec_info.get("id") or "")
        payload = {
            "name": name,
            "builder": self.account,
            "date": time.strftime("%Y-%m-%d"),
            "desc": desc,
        }
        if execution_id:
            payload["execution"] = execution_id
        if product_id:
            payload["product"] = product_id
        if project_id:
            payload["project"] = project_id
        # Per REST API doc, prefer /builds then fall back to execution-scoped endpoint.
        paths = ["/api.php/v1/builds"]
        if execution_id:
            paths.append(f"/api.php/v1/executions/{execution_id}/builds")
        resp = self._request_with_fallback("post", paths, json=payload)
        data = resp.json()
        build_id = data.get("id") or data.get("build") or data.get("data", {}).get("id")
        return str(build_id) if build_id else None


def collect_change_scope(repo_root: Path, previous_ref: Optional[str], current_ref: Optional[str]) -> Dict[str, str]:
    repo = Repo(repo_root)
    prev = previous_ref
    curr = current_ref or "HEAD"
    try:
        try:
            for remote in repo.remotes:
                remote.fetch()
        except Exception as exc:
            print(f"[warn] change scope fetch failed: {exc}", file=sys.stderr)
        if not prev:
            tags = sorted(repo.tags, key=lambda t: t.commit.committed_datetime)
            if len(tags) >= 2:
                prev = str(tags[-1])
                #curr = str(tags[-1])
            else:
                prev = f"{repo.head.commit.hexsha}~1"
        shortlog = repo.git.log(f"{prev}..{curr}", "--no-merges", "--pretty=format:%h %an %s")
        diffstat = repo.git.diff(f"{prev}..{curr}", "--stat")
    except Exception as exc:
        print(f"[warn] change scope collection failed: {exc}", file=sys.stderr)
        prev = prev or "unknown"
        shortlog = ""
        diffstat = ""
    return {"previous_ref": prev or "unknown", "current_ref": curr, "shortlog": shortlog, "diffstat": diffstat}


def run_tests(command: str, env: Dict[str, str], cwd: Path) -> TestOutcome:
    print(f"[info] running tests: {command}")
    proc = subprocess.run(command, shell=True, cwd=str(cwd), env=env, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    status = "SUCCESS" if proc.returncode == 0 else "FAILURE"
    output = proc.stdout + "\n" + proc.stderr
    return TestOutcome(status=status, output=output, return_code=proc.returncode)


def extract_revision_from_build(build_info: Dict) -> Optional[str]:
    """Try to pull the commit SHA from Jenkins build metadata."""
    
    for action in build_info.get("actions", []):
        bFoundRepo = False
        remotes = action.get("remoteUrls")
        if remotes:
            if len(remotes)>0:
                if(remotes[0].find("C3DSlicer")!=-1):
                    print(f"[info] found remoteUrl: {remotes[0]}")
                    bFoundRepo = True
        if not bFoundRepo:
            continue

        revision = action.get("lastBuiltRevision") or action.get("revision")
        
        if revision:
            sha = revision.get("SHA1") or revision.get("sha1")
            if sha:
                return sha
            branches = revision.get("branch") or revision.get("branches") or []
            for branch in branches:
                sha = branch.get("SHA1") or branch.get("sha1")
                if sha:
                    return sha
        builds_by_branch = action.get("buildsByBranchName")
        print(builds_by_branch)
        if builds_by_branch:
            for data in builds_by_branch.values():
                sha = data.get("revision", {}).get("SHA1") or data.get("revision", {}).get("sha1")
                if sha:
                    return sha
    for change_set in build_info.get("changeSets", []):
        
        for item in change_set.get("items", []):
            commit_id = item.get("commitId")
            if commit_id:
                return commit_id
    return None


def build_feishu_lines(builds: List[BuildOutcome], tests: Optional[TestOutcome]) -> List[str]:
    lines = []
    for build in builds:
        status = build.status
        num = f"#{build.build_number}" if build.build_number is not None else "#?"
        lines.append(f"{build.platform}: {status} {num}")
    if tests:
        lines.append(f"测试: {tests.status} (rc={tests.return_code})")
    return lines


def preferred_artifact_url(build: BuildOutcome) -> Optional[str]:
    if build.platform.lower().startswith("windows") and build.artifact_urls:
        for url_candidate in build.artifact_urls:
            if url_candidate.lower().endswith(".exe"):
                return url_candidate
    if build.artifact_url:
        return build.artifact_url
    if build.artifact_local_path:
        return str(build.artifact_local_path)
    return None


def write_result_json(
    repo_root: Path,
    output_path: str,
    changes: Dict[str, str],
    resolved_current_ref: Optional[str],
    previous_ref: Optional[str],
    builds: List[BuildOutcome],
) -> None:
    target = Path(output_path)
    if not target.is_absolute():
        target = repo_root / target
    target.parent.mkdir(parents=True, exist_ok=True)

    platform_list = [b.platform for b in builds]
    artifact_url_list = [preferred_artifact_url(b) or "" for b in builds]
    payload = {
        "changes": changes,
        "resolved_current_ref": resolved_current_ref,
        "previous_ref": previous_ref,
        "platform": platform_list,
        "artifact_url": artifact_url_list,
    }
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[info] wrote build result json: {target}")


def render_zentao_body(builds: List[BuildOutcome], tests: Optional[TestOutcome], changes: Dict[str, str], focus: str) -> str:
    lines = [
        f"版本范围: {changes.get('previous_ref')} -> {changes.get('current_ref')}",
        "",
        "构建结果:",
    ]
    for build in builds:
        lines.append(f"- {build.platform}: {build.status} #{build.build_number} {build.url or ''}")
    if tests:
        lines.append("")
        lines.append(f"测试: {tests.status} (rc={tests.return_code})")
    if changes.get("shortlog"):
        lines.append("")
        lines.append("变更短日志:")
        lines.append(changes["shortlog"])
    if changes.get("diffstat"):
        lines.append("")
        lines.append("DiffStat:")
        lines.append(changes["diffstat"])
    if focus:
        lines.append("")
        lines.append("测试关注点:")
        lines.append(focus)
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Trigger cross-platform Jenkins builds, run tests, notify Feishu, and update Zentao.")
    parser.add_argument("--platforms", nargs="+", default=["windows", "macos_x86", "macos_arm64", "linux"], help="Platforms to build")
    parser.add_argument("--artifacts-dir", default="artifacts", help="Where to store downloaded artifacts")
    parser.add_argument("--test-command", default=os.getenv("TEST_COMMAND", "pytest -q"), help="Command to run tests after builds succeed")
    parser.add_argument("--run-tests", default=os.getenv("RUN_TESTS"), choices=["true", "false", "1", "0", "yes", "no", "on", "off"], help="Explicitly control test execution; overrides --skip-tests when provided")
    parser.add_argument("--previous-ref", default=os.getenv("PREVIOUS_REF"), help="Git ref to diff from; defaults to previous tag or HEAD~1")
    parser.add_argument("--current-ref", default=os.getenv("CURRENT_REF", "HEAD"), help="Git ref treated as current version")
    parser.add_argument("--changes-repo", default=os.getenv("CHANGES_REPO"), help="Path or git URL to collect change scope; default current repo")
    parser.add_argument("--result-json", default=os.getenv("RESULT_JSON", "artifacts/release_result.json"), help="Path to write build result json")
    parser.add_argument("--zentao-build-id", default=os.getenv("ZENTAO_BUILD_ID"), help="Zentao build/version ID to update")
    parser.add_argument("--zentao-token", default=os.getenv("ZENTAO_TOKEN"), help="Preset Zentao API token; skips login when provided")
    parser.add_argument("--zentao-execution", default=os.getenv("ZENTAO_EXECUTION_ID"), help="Zentao execution ID; when provided and build ID missing, auto-create version under it")
    parser.add_argument("--zentao-build-name", default=os.getenv("ZENTAO_BUILD_NAME"), help="Zentao build/version name; defaults to current ref when creating")
    parser.add_argument("--zentao-product", default=os.getenv("ZENTAO_PRODUCT_ID"), help="Zentao product ID used when creating build/version")
    parser.add_argument("--branch", default=os.getenv("BRANCH"), help="Jenkins parameter BRANCH; skipped if not provided")
    parser.add_argument("--web-branch", default=os.getenv("WEB_BRANCH"), help="Jenkins parameter WEB_BRANCH; skipped if not provided")
    parser.add_argument("--package-type", default=os.getenv("PACKAGE_TYPE"), help="Jenkins parameter PACKAGE_TYPE; skipped if not provided")
    parser.add_argument("--tag-name", default=os.getenv("TAG_NAME"), help="Jenkins parameter TAG_NAME; skipped if not provided")
    parser.add_argument("--rtype", default=os.getenv("RTYPE"), help="Jenkins parameter RTYPE; skipped if not provided")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running tests after build")
    parser.add_argument("--dry-run", action="store_true", help="Trigger nothing, only print intended actions")
    return parser.parse_args()


def load_env_file(repo_root: Path) -> None:
    env_path = repo_root / ".env"
    if not env_path.exists():
        return
    print(f"[info] loading env from {env_path}")
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        # Do not override values already provided by the environment.
        os.environ.setdefault(key, value)


def ensure_changes_repo(default_root: Path, source: Optional[str]) -> Path:
    """Return a local repo path for change scope; clone/update if a remote URL is provided."""
    if not source:
        return default_root
    candidate = Path(source)
    if candidate.exists():
        return candidate
    cache_dir = default_root / ".cache" / "changes_repo"
    cache_dir.parent.mkdir(parents=True, exist_ok=True)
    try:
        if cache_dir.exists():
            repo = Repo(cache_dir)
            if repo.remotes:
                origin = repo.remotes[0]
                existing_urls = list(origin.urls)
                if source not in existing_urls:
                    origin.set_url(source)
        else:
            repo = Repo.clone_from(source, cache_dir)
        return cache_dir
    except Exception as exc:
        print(f"[warn] prepare changes repo failed: {exc}", file=sys.stderr)
        return default_root


def parse_bool_flag(value: Optional[str]) -> Optional[bool]:
    """Parse a string env/CLI flag into boolean; None when unknown."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    val = str(value).strip().lower()
    if val in {"1", "true", "yes", "on"}:
        return True
    if val in {"0", "false", "no", "off"}:
        return False
    return None


def extract_artifact_zip(artifact_path: Path) -> Optional[Path]:
    """Extract a zip artifact, flatten single top-level folder, and return the extraction directory."""
    if artifact_path.suffix.lower() != ".zip":
        return None
    target_dir = artifact_path.with_suffix("")
    if target_dir.exists():
        return target_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(artifact_path, "r") as zf:
        zf.extractall(target_dir)
    # Flatten if the zip contains a single top-level directory
    children = [p for p in target_dir.iterdir()]
    if len(children) == 1 and children[0].is_dir():
        inner = children[0]
        for item in inner.iterdir():
            shutil.move(str(item), target_dir / item.name)
        try:
            inner.rmdir()
        except OSError:
            shutil.rmtree(inner, ignore_errors=True)
    return target_dir


def find_slicer_exe(search_root: Path) -> Optional[Path]:
    """Find CrealityPrint.exe under a directory tree."""
    for candidate in search_root.rglob("CrealityPrint.exe"):
        return candidate
    return None


def load_platform_jobs(platforms: List[str], base_params: Optional[Dict[str, str]] = None) -> List[PlatformJob]:
    base_params = base_params or {}
    jobs: List[PlatformJob] = []
    for platform in platforms:
        job_env = os.getenv(f"JENKINS_JOB_{platform.upper()}")
        artifact_env = os.getenv(f"JENKINS_ARTIFACT_{platform.upper()}")
        params_env = os.getenv(f"JENKINS_PARAMS_{platform.upper()}")
        parameters = json.loads(params_env) if params_env else None
        if parameters:
            merged_params = {**base_params, **parameters}
        elif base_params:
            merged_params = dict(base_params)
        else:
            merged_params = None
        if not job_env:
            raise ValueError(f"Missing env: JENKINS_JOB_{platform.upper()}")
        jobs.append(PlatformJob(platform=platform, job_name=job_env, artifact_path=artifact_env, parameters=merged_params))
    return jobs


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    print(f"[info] repo root: {repo_root}")
    load_env_file(repo_root)
    args = parse_args()
    artifacts_dir = repo_root / args.artifacts_dir
    resolved_current_ref = args.current_ref
    #changes_repo_root = ensure_changes_repo(repo_root, args.changes_repo)

    base_params = {
        key: value
        for key, value in {
            "BRANCH": args.branch,
            "WEB_BRANCH": args.web_branch,
            "PACKAGE_TYPE": args.package_type,
            "TAG_NAME": args.tag_name,
            "RTYPE": args.rtype,
        }.items()
        if value
    }

    jenkins_base = os.getenv("JENKINS_BASE_URL")
    jenkins_user = os.getenv("JENKINS_USER")
    jenkins_token = os.getenv("JENKINS_TOKEN")
    if not all([jenkins_base, jenkins_user, jenkins_token]):
        print("[error] JENKINS_BASE_URL / JENKINS_USER / JENKINS_TOKEN are required", file=sys.stderr)
        return 2

    feishu_webhook = os.getenv("FEISHU_WEBHOOK")
    notifier = FeishuNotifier(feishu_webhook)

    zentao_client = ZentaoClient(
        base_url=os.getenv("ZENTAO_BASE_URL"),
        account=os.getenv("ZENTAO_ACCOUNT"),
        password=os.getenv("ZENTAO_PASSWORD"),
        token=args.zentao_token,
    )
    zentao_build_id = args.zentao_build_id
    zentao_execution_id = args.zentao_execution
    zentao_build_name = args.zentao_build_name
    zentao_product_id = args.zentao_product
    zentao_object_id = os.getenv("ZENTAO_OBJECT_ID")
    zentao_object_type = os.getenv("ZENTAO_OBJECT_TYPE", "build")
    run_tests_flag = parse_bool_flag(args.run_tests)
    should_run_tests = True if run_tests_flag is None else run_tests_flag
    if run_tests_flag is None and args.skip_tests:
        should_run_tests = False

    try:
        platform_jobs = load_platform_jobs(args.platforms, base_params=base_params)
    except ValueError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2
    client = JenkinsClient(jenkins_base, jenkins_user, jenkins_token)
    build_results: List[BuildOutcome] = []

    from concurrent.futures import ThreadPoolExecutor, as_completed

    def run_job(job: PlatformJob) -> BuildOutcome:
        print(f"[info] triggering {job.platform} -> {job.job_name}")
        if args.dry_run:
            return BuildOutcome(platform=job.platform, job_name=job.job_name, status="DRY_RUN")
        try:
            queue_api = client.trigger_job(job.job_name, parameters=job.parameters)
            build_number = client.wait_for_build_number(queue_api)
            build_info = client.wait_for_result(job.job_name, build_number)

            status = build_info.get("result") or "UNKNOWN"
            url = build_info.get("url")
            nonlocal resolved_current_ref
            if resolved_current_ref in (None, "HEAD"):
                detected_ref = extract_revision_from_build(build_info)
                if detected_ref:
                    resolved_current_ref = detected_ref
            console = client.fetch_console(job.job_name, build_number)
            if len(console.encode("utf-8")) > 2 * 1024 * 1024:
                tail_bytes = console.encode("utf-8")[-2 * 1024 * 1024 :]
                console = tail_bytes.decode("utf-8", errors="ignore")
            outcome = BuildOutcome(
                platform=job.platform,
                job_name=job.job_name,
                build_number=build_number,
                status=status,
                url=url,
                artifact_path=job.artifact_path,
                console_excerpt=console[-1200:],
            )
            if status == "SUCCESS":
                downloaded, artifact_url, artifacts_meta = client.download_artifact(job.job_name, build_number, job.artifact_path, artifacts_dir / job.platform)
                outcome.artifact_local_path = downloaded
                outcome.artifact_url = artifact_url
                outcome.artifact_urls = [
                    f"{jenkins_base}/job/{job.job_name}/{build_number}/artifact/{a.get('relativePath')}"
                    for a in artifacts_meta
                    if a.get("relativePath")
                ]
            else:
                error_lines = [line for line in console.splitlines() if "error:" in line.lower()]
                summary_input = "\n".join(error_lines) if error_lines else console
                summary = summary_input[:600]
                notifier.send_text(
                    title=f"{job.platform} 构建失败",
                    lines=[
                        f"Job: {job.job_name}",
                        f"Build: #{build_number}",
                        f"Link: {url}",
                        f"console: {summary_input[:1000]}",
                        f"Summary: {summary}",
                    ],
                )
            return outcome
        except Exception as exc:
            print(f"[error] build for {job.platform} failed: {exc}", file=sys.stderr)
            return BuildOutcome(platform=job.platform, job_name=job.job_name, status="ERROR")

    with ThreadPoolExecutor(max_workers=len(platform_jobs)) as executor:
        future_map = {executor.submit(run_job, job): job.platform for job in platform_jobs}
        for future in as_completed(future_map):
            build_results.append(future.result())

    #changes = collect_change_scope(changes_repo_root, args.previous_ref, resolved_current_ref)
    write_result_json(
        repo_root=repo_root,
        output_path=args.result_json,
        changes=args.current_ref,
        resolved_current_ref=resolved_current_ref,
        previous_ref= args.previous_ref,
        builds=build_results,
    )

    if any(b.status != "SUCCESS" for b in build_results):
        notifier.send_text("跨平台构建未通过", build_feishu_lines(build_results, None))
        return 1

    test_result: Optional[TestOutcome] = None
    if should_run_tests and not args.dry_run:
        test_pipeline = os.getenv("JENKINS_JOB_TEST_PIPELINE") or os.getenv("JENKINS_JOB_TESTER")
        windows_builds = [b for b in build_results if b.platform.lower() == "windows" and b.status == "SUCCESS"]
        if not windows_builds:
            print("[warn] run_tests enabled but no successful windows build found; skipping tests", file=sys.stderr)
        elif not test_pipeline:
            print("[warn] run_tests enabled but JENKINS_JOB_TEST_PIPELINE/JENKINS_JOB_TESTER not set; skipping tests", file=sys.stderr)
        else:
            target = windows_builds[0]
            params = {
                "JOB_NAME": target.job_name,
                "BUILD_ID": str(target.build_number or ""),
                "PLATFORM": target.platform,
            }
            if target.artifact_path:
                params["ARTIFACT_PATH"] = target.artifact_path
            #if args.test_command:
            #    params["TEST_COMMAND"] = args.test_command
            try:
                queue_api = client.trigger_job(test_pipeline, parameters=params)
                print(f"[info] triggered test pipeline {test_pipeline} for {target.job_name}#{target.build_number}: {queue_api}")
            except Exception as exc:
                print(f"[warn] failed to trigger test pipeline {test_pipeline}: {exc}", file=sys.stderr)

    #print(f"[info] change scope from {changes}")
    # send change scope directly to Feishu, no LLM summary
    feishu_lines = build_feishu_lines(build_results, test_result)
    artifact_lines = []
    for build in build_results:
        chosen_url = preferred_artifact_url(build)
        if chosen_url:
            artifact_lines.append(f"{build.platform} artifact: {chosen_url}")
    if artifact_lines:
        feishu_lines.append("")
        feishu_lines.extend(artifact_lines)
    notifier.send_text("跨平台构建+测试通过", feishu_lines)
    # if not args.dry_run and zentao_client.active() and zentao_execution_id and not zentao_build_id:
    #     artifact_tag = None
    #     for build in build_results:
    #         if build.artifact_local_path:
    #             artifact_tag = f"{build.platform}_{Path(build.artifact_local_path).name}"
    #             break
    #     target_name = zentao_build_name or artifact_tag or changes.get("current_ref") or resolved_current_ref or "auto-build"
    #     try:
    #         existing = zentao_client.find_build_by_name(zentao_execution_id, target_name)
    #         print(f"[info] zentao existing build: {existing}")
    #         if existing:
    #             zentao_build_id = str(existing.get("id") or existing.get("build") or existing.get("ID"))
    #         else:
    #             created_id = zentao_client.create_build(
    #                 execution_id=zentao_execution_id,
    #                 name=target_name,
    #                 desc=focus or changes.get("shortlog", ""),
    #                 product_id=zentao_product_id,
    #             )
    #             if created_id:
    #                 zentao_build_id = created_id
    #     except Exception as exc:
    #         print(f"[warn] Zentao ensure build failed: {exc}", file=sys.stderr)

    # notifier.send_text("跨平台构建+测试通过", build_feishu_lines(build_results, test_result))

    # if zentao_build_id and zentao_client.active() and not args.dry_run:
    #     body = render_zentao_body(build_results, test_result, changes, focus)
    #     try:
    #         zentao_client.post_build_summary(zentao_build_id, f"{changes.get('current_ref')} 构建回传", body)
    #         if zentao_object_id:
    #             zentao_client.attach_comment(zentao_object_type, zentao_object_id, body)
    #     except Exception as exc:
    #         print(f"[warn] Zentao update failed: {exc}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
