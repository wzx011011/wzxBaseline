"""
Download 3MF files from a Feishu (Lark) Bitable and measure
import/slice/export performance with CrealityPrint.
Config via env:
    FEISHU_APP_ID / FEISHU_APP_SECRET / FEISHU_APP_TOKEN / FEISHU_TABLE_ID
    [FEISHU_VIEW_ID] [FEISHU_FILE_FIELD] [FEISHU_DOWNLOAD_DIR]
Results are appended to performance/data/feishu_slice_report.csv.
"""

import csv
import json
import os
import re
import sys
import time
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Union
from urllib.parse import urljoin, unquote

import pytest
import requests

from test_framework.engine_params.src.slicerctl.session import (
    EngineSession,
    RestartingEngine,
    EngineUnavailable,
)
from test_framework.engine_params.conftest import wait_for_file_written
from test_framework.engine_params.src.slicerctl.constants import SLICE_BTN_ID


def _safe_print(*args, **kwargs) -> None:
    try:
        print(*args, **kwargs)
        return
    except UnicodeEncodeError:
        pass
    stream = kwargs.get("file") or getattr(sys, "stdout", None)
    if stream is None:
        return
    encoding = getattr(stream, "encoding", None) or "utf-8"
    sep = kwargs.get("sep", " ")
    end = kwargs.get("end", "\n")
    text = sep.join(str(a) for a in args)
    safe_text = text.encode(encoding, errors="backslashreplace").decode(encoding, errors="replace")
    try:
        stream.write(safe_text + end)
    except UnicodeEncodeError:
        buffer = getattr(stream, "buffer", None)
        if buffer:
            buffer.write((text + end).encode(encoding, errors="backslashreplace"))
        else:
            stream.write((text + end).encode("ascii", errors="backslashreplace").decode("ascii"))


def _safe_pytest_id(text: str) -> str:
    # Force a terminal-safe ASCII id on Windows cp936/gbk consoles.
    return text.encode("ascii", errors="backslashreplace").decode("ascii")


# ======== Feishu dataset discovery (collection time) ========
_FEISHU_CASES: Optional[List[Dict]] = None
_FEISHU_ERROR: Optional[str] = None


def _truthy_env(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _truthy_text(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _resolve_cli_or_env(pytestconfig, cli_name: str, env_name: str, default: str = "") -> str:
    if pytestconfig is not None:
        cli_val = pytestconfig.getoption(cli_name, default=None)
        if cli_val not in (None, ""):
            return str(cli_val).strip()
    return os.getenv(env_name, default).strip()


def _resolve_notify_enabled(pytestconfig) -> bool:
    value = _resolve_cli_or_env(pytestconfig, "feishu_notify", "FEISHU_NOTIFY", default="")
    if not value:
        return True
    if value in {"on", "off"}:
        return value == "on"
    return _truthy_text(value)


def _manifest_path() -> Path:
    download_dir = os.getenv("FEISHU_DOWNLOAD_DIR")
    base = Path(download_dir) if download_dir else Path("artifacts") / "feishu_3mf"
    return base / "downloads.json"


def _load_manifest_cases() -> List[Dict]:
    manifest = _manifest_path()
    if not manifest.exists():
        raise FileNotFoundError(f"manifest not found: {manifest}")
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"manifest parse failed: {exc}") from exc
    if not isinstance(data, list):
        raise ValueError("manifest content is not a list")

    cases: List[Dict] = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        path = entry.get("path")
        if not path or not Path(path).exists():
            continue
        cases.append(
            {
                "record_id": entry.get("record_id") or "",
                "name": entry.get("name") or Path(path).name,
                "path": path,
                "title": entry.get("title") or "",
            }
        )
    return cases


HTTP_3MF_ROOT_DEFAULT = "http://172.20.180.14/shared/test_3mf/"


def _http_3mf_root() -> str:
    base = os.getenv("HTTP_3MF_ROOT", HTTP_3MF_ROOT_DEFAULT).strip()
    if not base:
        base = HTTP_3MF_ROOT_DEFAULT
    if not base.endswith("/"):
        base += "/"
    return base


def _http_3mf_download_dir() -> Path:
    custom = os.getenv("HTTP_3MF_DOWNLOAD_DIR")
    if custom:
        return Path(custom)
    return Path("artifacts") / "http_3mf"


def _safe_local_name(href: str) -> str:
    name = href.split("/")[-1]
    name = unquote(name)
    for ch in '<>:"/\\|?*':
        name = name.replace(ch, "_")
    if len(name) > 120:
        base, dot, ext = name.rpartition(".")
        if not dot:
            return name[:120]
        base = base[:100]
        name = base + dot + ext
    return name


def _http_list_links(html: str) -> List[str]:
    links: List[str] = []
    pos = 0
    while True:
        idx = html.find("href=", pos)
        if idx == -1:
            break
        quote = html[idx + 5]
        if quote not in ("'", '"'):
            pos = idx + 5
            continue
        end = html.find(quote, idx + 6)
        if end == -1:
            break
        href = html[idx + 6:end]
        links.append(href)
        pos = end + 1
    return links


def _download_http_3mf_files() -> List[Dict]:
    base_url = _http_3mf_root()
    download_dir = _http_3mf_download_dir()
    download_dir.mkdir(parents=True, exist_ok=True)
    _safe_print(f"[http_3mf] base_url={base_url}")
    _safe_print(f"[http_3mf] download_dir={download_dir}")

    session = requests.Session()
    files: List[Dict] = []

    def walk(url: str, rel: str = "") -> None:
        if _truthy_env("DEBUG") and len(files) >= 10:
            return
        try:
            resp = session.get(url, timeout=30)
            resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            _safe_print(f"[http_3mf] failed to list {url}: {exc}")
            return
        links = [
            href
            for href in _http_list_links(resp.text)
            if href not in ("../", "/")
            and not href.startswith("../")
            and not href.lstrip("/").startswith("shared")
            and not href.lstrip("/").startswith("erro")
        ]
        for href in links:
            full = urljoin(url, href)
            if href.endswith("/"):
                dir_name = _safe_local_name(href.rstrip("/"))
                walk(full, rel + dir_name + "/")
            elif href.lower().endswith(".3mf"):
                local_name = _safe_local_name(href)
                local_path = download_dir / rel / local_name
                local_path.parent.mkdir(parents=True, exist_ok=True)
                if not local_path.exists():
                    _safe_print(f"[http_3mf] downloading {full} -> {local_path}")
                    try:
                        with session.get(full, stream=True, timeout=60) as r:
                            r.raise_for_status()
                            with local_path.open("wb") as f:
                                for chunk in r.iter_content(chunk_size=8192):
                                    if not chunk:
                                        continue
                                    f.write(chunk)
                    except Exception as exc:  # noqa: BLE001
                        _safe_print(f"[http_3mf] download failed for {full}: {exc}")
                        if local_path.exists():
                            local_path.unlink()
                        continue
                files.append(
                    {
                        "record_id": "",
                        "name": local_name,
                        "path": str(local_path),
                        "title": rel + local_name,
                    }
                )

    walk(base_url, "")

    if _truthy_env("DEBUG"):
        if files:
            _safe_print(f"DEBUG mode enabled: limiting to 10 HTTP cases (from {len(files)} total)")
            files = files[:10]

    return files


def _collect_feishu_cases() -> List[Dict]:
    global _FEISHU_CASES, _FEISHU_ERROR
    if _FEISHU_CASES is not None:
        return _FEISHU_CASES

    # Optional: only use local manifest for debugging, skip HTTP download.
    if _truthy_env("FEISHU_USE_MANIFEST_ONLY"):
        try:
            cases = _load_manifest_cases()
            
            # Apply DEBUG mode limit if needed
            if _truthy_env("DEBUG"):
                _safe_print(f"DEBUG mode enabled: limiting to 10 manifest cases (from {len(cases)} total)")
                cases = cases[:10]
            
            _FEISHU_CASES = cases
            if not cases:
                _FEISHU_ERROR = "Manifest found but no valid entries."
        except Exception as exc:  # noqa: BLE001
            _FEISHU_CASES = []
            _FEISHU_ERROR = str(exc)
        return _FEISHU_CASES

    try:
        files = _download_http_3mf_files()
        _FEISHU_CASES = files
        if not files:
            _FEISHU_ERROR = "No 3MF files found from HTTP source."
    except Exception as exc:  # noqa: BLE001
        _FEISHU_CASES = []
        _FEISHU_ERROR = f"HTTP 3MF collection failed: {exc}"
    return _FEISHU_CASES


def pytest_generate_tests(metafunc):
    if "feishu_case" not in metafunc.fixturenames:
        return
    cases = _collect_feishu_cases()
    regex_filter = _resolve_cli_or_env(
        metafunc.config,
        "feishu_case_regex",
        "FEISHU_CASE_REGEX",
        default="",
    )
    if regex_filter:
        try:
            pattern = re.compile(regex_filter)
        except re.error as exc:
            pytest.skip(f"Invalid FEISHU_CASE_REGEX={regex_filter}: {exc}", allow_module_level=True)
        filtered = []
        for c in cases:
            path = str(c.get("path") or "")
            suffix = _extract_http_3mf_suffix(path)
            name = str(c.get("name") or "")
            title = str(c.get("title") or "")
            if (
                pattern.search(suffix)
                or pattern.search(name)
                or pattern.search(path)
                or pattern.search(title)
            ):
                filtered.append(c)
        _safe_print(f"[filter-regex] pattern={regex_filter}, filtered count: {len(filtered)}")
        if not filtered:
            pytest.skip(
                f"No HTTP 3MF cases matching FEISHU_CASE_REGEX={regex_filter}",
                allow_module_level=True,
            )
        cases = filtered
    if not cases:
        if _FEISHU_ERROR:
            pytest.skip(_FEISHU_ERROR, allow_module_level=True)
        metafunc.parametrize("feishu_case", [], ids=[])
        return
    ids = [_safe_pytest_id(Path(item["path"]).name) for item in cases]
    metafunc.parametrize("feishu_case", cases, ids=ids)


# ======== helpers ========
def _extract_http_3mf_suffix(path: str) -> str:
    if not path:
        return ""
    path_str = str(path)
    # 查找 http_3mf 在路径中的位置
    http_3mf_index = path_str.find("http_3mf")
    if http_3mf_index != -1:
        # 提取 http_3mf 后面的部分（跳过 http_3mf 和路径分隔符）
        suffix_start = http_3mf_index + len("http_3mf")
        # 跳过路径分隔符
        while suffix_start < len(path_str) and path_str[suffix_start] in {"/", "\\"}:
            suffix_start += 1
        return path_str[suffix_start:]
    return path_str


def _decode_response(raw: Union[bytes, str, None]) -> Dict:
    if raw is None:
        return {}
    if isinstance(raw, bytes):
        text = raw.decode("utf-8", errors="ignore")
    else:
        text = raw
    try:
        _, payload = text.split(";", 1)
    except ValueError:
        payload = text
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return {"raw": text}


def _run_command(send_cmd_handle, command: str, params: Dict, timeout: int) -> Dict:
    start = time.perf_counter()
    ret, status, resp = send_cmd_handle(command, json.dumps(params), timeout, True)
    elapsed_ms = (time.perf_counter() - start) * 1000
    payload = _decode_response(resp)
    code = payload.get("code")

    ok = ret and status == "ok" and (code is None or code == 0)
    crashed = status in {"lostconnect"} or (not ret and status not in {"timeout", "ok"})
    error_msg = None
    if not ok:
        error_msg = payload.get("error") or payload.get("msg")
        if not error_msg:
            error_msg = status if status != "ok" else str(payload)

    return {
        "ok": ok,
        "code": code,
        "status": status,
        "crashed": crashed,
        "elapsed_ms": elapsed_ms,
        "error": error_msg,
        "raw": payload,
    }


def _progress_percentage_0_100(value) -> Optional[float]:
    if value is None:
        return None
    try:
        pct = float(value)
    except (TypeError, ValueError):
        return None
    # Some engines report [0..1] while others report [0..100].
    if 0.0 <= pct <= 1.0:
        return pct * 100.0
    return pct


def _extract_slicing_progress(ret: Dict) -> Optional[Dict]:
    raw = ret.get("raw")
    if not isinstance(raw, dict):
        return None
    payload = raw.get("payload")
    if not isinstance(payload, dict):
        return None
    progress = payload.get("progress")
    if not isinstance(progress, dict):
        return None
    return progress


def _is_slicing_done(progress: Dict) -> bool:
    raw_pct = progress.get("percentage")
    try:
        raw_pct_f = float(raw_pct)
    except (TypeError, ValueError):
        raw_pct_f = None
    # For this engine: percentage > 1 or < 0 indicates slicing is finished.
    if raw_pct_f is not None and (raw_pct_f > 1.0 or raw_pct_f < 0.0):
        return True

    pct = _progress_percentage_0_100(progress.get("percentage"))
    if pct is not None and pct >= 100.0 - 1e-6:
        return True
    if progress.get("export") is True:
        return True
    state = str(progress.get("state") or "").strip().lower()
    if state in {"done", "finish", "finished", "complete", "completed", "success"}:
        return True
    return False


def _wait_for_slicing_done(
    send_cmd_handle,
    timeout_s: float,
    poll_interval_s: float = 0.5,
) -> Dict:
    start = time.perf_counter()
    deadline = time.monotonic() + max(0.0, float(timeout_s))
    last_progress: Optional[Dict] = None
    last_error: Optional[str] = None
    last_pct = None
    last_change_ts = time.monotonic()
    stall_seconds = 120.0

    while time.monotonic() < deadline:
        progress_ret = _run_command(
            send_cmd_handle,
            "get_slicing_progress",
            {},
            timeout=60,
        )
        if progress_ret["ok"]:
            progress = _extract_slicing_progress(progress_ret)
            if progress is not None:
                last_progress = progress
                pct = _progress_percentage_0_100(progress.get("percentage"))
                now = time.monotonic()
                if pct is not None:
                    if last_pct is None or pct != last_pct:
                        last_pct = pct
                        last_change_ts = now
                    elif now - last_change_ts >= stall_seconds:
                        pct_str = f"{pct:.3f}"
                        state_str = str(progress.get("state") or "unknown")
                        return {
                            "ok": False,
                            "crashed": False,
                            "elapsed_ms": (time.perf_counter() - start) * 1000,
                            "progress": last_progress,
                            "error": f"slicing progress stalled for {stall_seconds}s (percentage={pct_str}, state={state_str})",
                        }
                if _is_slicing_done(progress):
                    return {
                        "ok": True,
                        "crashed": False,
                        "elapsed_ms": (time.perf_counter() - start) * 1000,
                        "progress": last_progress,
                        "error": None,
                    }
        else:
            if progress_ret["crashed"]:
                return {
                    "ok": False,
                    "crashed": True,
                    "elapsed_ms": (time.perf_counter() - start) * 1000,
                    "progress": last_progress,
                    "error": progress_ret["error"] or "engine crashed while waiting slicing progress",
                }
            last_error = progress_ret["error"] or progress_ret["status"]

        time.sleep(poll_interval_s)

    pct = _progress_percentage_0_100((last_progress or {}).get("percentage"))
    pct_str = f"{pct:.3f}" if pct is not None else "unknown"
    state_str = str((last_progress or {}).get("state") or "unknown")
    return {
        "ok": False,
        "crashed": False,
        "elapsed_ms": (time.perf_counter() - start) * 1000,
        "progress": last_progress,
        "error": last_error or f"slicing not finished in {timeout_s}s (percentage={pct_str}, state={state_str})",
    }


def _write_report_line(report_path: Path, row: Dict) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    header = [
        "record_id",
        "file",
        "import_ms",
        "slice_ms",
        "export_ms",
        "import_ok",
        "slice_ok",
        "export_ok",
        "crashed",
        "error",
        "gcode_path",
    ]
    if not report_path.exists():
        report_path.write_text(",".join(header) + "\n", encoding="utf-8")

    ordered = [
        row.get("record_id", ""),
        row.get("file", ""),
        f"{row.get('import_ms', '')}",
        f"{row.get('slice_ms', '')}",
        f"{row.get('export_ms', '')}",
        str(row.get("import_ok", "")),
        str(row.get("slice_ok", "")),
        str(row.get("export_ok", "")),
        str(row.get("crashed", "")),
        row.get("error", "") or "",
        row.get("gcode_path", "") or "",
    ]
    ordered = ["" if v is None else str(v) for v in ordered]
    with report_path.open("a", encoding="utf-8") as f:
        f.write(",".join(ordered) + "\n")

# ======== engine session fixture ========
def _require_path(key: str) -> str:
    path = os.getenv(key)
    if not path:
        pytest.skip(f"{key} not set, skip engine session usage.")
    if not Path(path).exists():
        pytest.skip(f"{key} points to non-existing path: {path}")
    return path


@pytest.fixture(scope="session")
def engine_manager_perf(pytestconfig):
    # Check if --slicer-exe is provided via command line
    slicer_exe = pytestconfig.getoption("--slicer-exe")
    
    if slicer_exe:
        # Use the provided path from command line
        exe_path = slicer_exe
        # Validate the path exists
        if not Path(exe_path).exists():
            pytest.skip(f"--slicer-exe points to non-existing path: {exe_path}")
    else:
        # Fall back to environment variable via _require_path
        exe_path = _require_path("CREALITY_PRINTER_PATH")
    
    # Resolve to absolute path
    exe_path = str(Path(exe_path).resolve())
    host = os.getenv("SLICER_TEST_HOST", "127.0.0.1")
    port = int(os.getenv("SLICER_TEST_PORT", "12345"))
    stdout_log = Path(os.getenv("SLICER_STDOUT_LOG", "artifacts/slicer_stdout.log")).resolve()
    stdout_log.parent.mkdir(parents=True, exist_ok=True)

    inter_delay = float(os.getenv("SLICER_INTER_DELAY", "0.2"))
    retries = int(os.getenv("SLICER_RETRIES", "1"))
    backoff = float(os.getenv("SLICER_BACKOFF", "0.5"))
    ping_timeout = float(os.getenv("SLICER_PING_TIMEOUT", "3.0"))
    cool_down = float(os.getenv("SLICER_COOLDOWN", "5.0"))
    session_timeout = float(os.getenv("SLICER_SESSION_TIMEOUT", "30.0"))

    def _mk_session():
        return EngineSession(
            exe_path=exe_path,
            log_path=str(stdout_log),
            cli_args=[exe_path, "test#157369"],
            host=host,
            port=port,
            timeout=session_timeout,
            inter_command_delay=inter_delay,
            retries=retries,
            backoff=backoff,
        )

    mgr = RestartingEngine(mk_session=_mk_session, ping_timeout=ping_timeout, cool_down=cool_down)
    try:
        yield mgr
    finally:
        mgr.close()


@pytest.fixture(scope="session")
def engine_injector_perf(engine_manager_perf):
    policy = os.getenv("SLICER_ENGINE_UNAVAIL", "error").lower()

    class InjectorAdapter:
        __slots__ = ("_mgr",)

        def __init__(self, mgr):
            self._mgr = mgr

        def submit(self, *args, **kwargs):
            try:
                return self._mgr.submit(*args, **kwargs)
            except EngineUnavailable as e:
                if policy == "skip":
                    pytest.skip(str(e))
                if policy == "xfail":
                    pytest.xfail(str(e))
                raise

    return InjectorAdapter(engine_manager_perf)


@pytest.fixture(scope="session")
def engine_session_send_cmd(engine_injector_perf):
    def send_cmd_handle(command, params_json, recvcmd_timeout=None, band_output=False):
        try:
            payload = json.loads(params_json) if params_json else {}
        except Exception:
            payload = {}
        try:
            fut = engine_injector_perf.submit(command, payload, timeout=recvcmd_timeout)
            resp = fut.result(timeout=recvcmd_timeout)
            resp_bytes = f"{command}_respone;{json.dumps(resp)}".encode("utf-8")
            return True, "ok", resp_bytes
        except TimeoutError:
            return False, "timeout", b""
        except EngineUnavailable as exc:
            return False, "lostconnect", str(exc).encode("utf-8")
        except Exception as exc:  # noqa: BLE001
            return False, "error", str(exc).encode("utf-8")

    return send_cmd_handle


@pytest.fixture(scope="session")
def baseline_data():
    """
    Load baseline data from feishu_slice_report.csv at test startup.
    """
    baseline_path = Path("performance") / "data" / "feishu_slice_report.csv"
    baseline_data = {}
    
    if baseline_path.exists():
        _safe_print(f"Loading baseline data from {baseline_path}...")
        encodings = ["utf-8", "gbk", "latin-1"]
        
        for encoding in encodings:
            try:
                with open(baseline_path, "r", encoding=encoding) as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        record_id = (row.get("record_id") or "").strip()
                        file_value = row.get("file") or ""
                        filename = Path(file_value).name if file_value else ""
                        key = record_id or filename
                        if not key:
                            continue
                        baseline_data[key] = row
                _safe_print(f"OK Loaded {len(baseline_data)} baseline records with encoding: {encoding}")
                break
            except UnicodeDecodeError:
                _safe_print(f"Failed to read with encoding {encoding}, trying next...")
            except Exception as e:
                _safe_print(f"Error reading baseline file: {e}")
                break
        
        if not baseline_data:
            _safe_print(f"Failed to read baseline file with any encoding")
    else:
        _safe_print(f"Baseline file not found: {baseline_path}")
    
    return baseline_data


def _run_slice_flow(send_cmd_handle, model_path: Path, tmp_dir: Path) -> Dict:
    timeouts = {
        "load": int(os.getenv("SLICER_LOAD_TIMEOUT", "90")),
        "slice": int(os.getenv("SLICER_SLICE_TIMEOUT", "600")),
        "export": int(os.getenv("SLICER_EXPORT_TIMEOUT", "360")),
        "wait": float(os.getenv("SLICER_WAIT_WRITTEN", "60")),
        "settle": float(os.getenv("SLICER_SETTLE_SECONDS", "1.0")),
    }
    project_name = os.getenv("SLICER_PROJECT_NAME", "pytest_case_project")
    result = {
        "record_id": "",
        "file": str(model_path),
        "import_ms": None,
        "slice_ms": None,
        "export_ms": None,
        "import_ok": False,
        "slice_ok": False,
        "export_ok": False,
        "crashed": False,
        "error": None,
        "gcode_path": None,
    }

    # Reset project to avoid residue between runs.
    reset_ret = _run_command(
        send_cmd_handle,
        "reset_project",
        {"skip_confirm": True, "silent": True, "project_name": project_name},
        timeout=30,
    )
    if not reset_ret["ok"]:
        result["error"] = reset_ret["error"] or "reset_project failed"
        result["crashed"] = reset_ret["crashed"]
        return result
    # select_printer
    select_ret = _run_command(
        send_cmd_handle,
        "select_printer",
        {"printer_name": "Creality K2 Plus 0.4 nozzle"},
        timeout=5,
    )
    _safe_print(select_ret)
    # Import model
    import_ret = _run_command(
        send_cmd_handle,
        "trigger_load_project2",
        {"file": str(model_path), "discard_preset_changes": True},
        timeout=timeouts["load"],
    )
    result["import_ok"] = import_ret["ok"]
    result["import_ms"] = round(import_ret["elapsed_ms"], 2)
    result["crashed"] = import_ret["crashed"]
    if not import_ret["ok"]:
        result["error"] = import_ret["error"]
        return result
    #get error
    import_error = _run_command(
        send_cmd_handle,
        "get_error",
        {"type":"all"},
        timeout=5,
    )
    
    if(import_error["ok"]):
        payload = import_error["raw"]
        errors = payload["payload"]["data"]
        for error in errors:
            if error["level"] >=9:
                result["error"] = error["type"]
                return result
    # Slice
    slice_start = time.perf_counter()
    slice_ret = _run_command(
        send_cmd_handle,
        "trigger_slice",
        {"id": SLICE_BTN_ID},
        timeout=timeouts["slice"],
    )
    result["crashed"] = result["crashed"] or slice_ret["crashed"]
    if not slice_ret["ok"]:
        result["slice_ok"] = False
        result["slice_ms"] = round((time.perf_counter() - slice_start) * 1000, 2)
        result["error"] = slice_ret["error"]
        return result

    # Wait until slicing progress reaches 100% (or engine reports export-ready),
    # then continue with export_gcode.
    wait_ret = _wait_for_slicing_done(
        send_cmd_handle,
        timeout_s=float(timeouts["slice"]),
        poll_interval_s=float(os.getenv("SLICER_PROGRESS_POLL", "0.5")),
    )
    result["crashed"] = result["crashed"] or wait_ret["crashed"]
    result["slice_ok"] = wait_ret["ok"]
    result["slice_ms"] = round((time.perf_counter() - slice_start) * 1000, 2)
    if not wait_ret["ok"]:
        result["error"] = wait_ret["error"]
        return result

    # Export gcode
    output_gcode = tmp_dir / f"{model_path.stem}.gcode.3mf"
    export_ret = _run_command(
        send_cmd_handle,
        "export_gcode",
        {"export_all": True, "output": str(output_gcode)},
        timeout=timeouts["export"],
    )
    _safe_print(output_gcode.exists())
    zip_ok = False
    if output_gcode.exists():
        try:
            with zipfile.ZipFile(output_gcode, "r") as zf:
                for name in zf.namelist():
                    if name.lower().endswith(".gcode"):
                        zip_ok = True
                        break
        except zipfile.BadZipFile:
            zip_ok = False
    result["export_ok"] = export_ret["ok"] and zip_ok
    result["export_ms"] = round(export_ret["elapsed_ms"], 2)
    result["crashed"] = result["crashed"] or export_ret["crashed"]
    result["gcode_path"] = str(output_gcode)
    if not result["export_ok"]:
        result["error"] = export_ret["error"] or "gcode not generated"
        return result

    # Wait file written (watchdog style)
    try:
        wait_for_file_written(output_gcode, timeout=timeouts["wait"], settle_time=timeouts["settle"])
    except Exception as exc:  # noqa: BLE001
        result["error"] = f"wait_for_file_written failed: {exc}"
        result["export_ok"] = False
        return result

    return result


# ======== tests ========
@pytest.mark.performance
def test_feishu_slice(
    feishu_case,
    engine_session_send_cmd,
    tmp_path,
    baseline_data,  # Use the fixture for baseline data
):
    if not _FEISHU_CASES:
        pytest.skip(_FEISHU_ERROR or "Feishu dataset not configured.")

    send_cmd_handle = engine_session_send_cmd
    model_path = Path(feishu_case["path"]).resolve()  # Ensure absolute path
    #model_path = Path("C:\work\C3DBaseline\test_framework\artifacts\feishu_3mf\baby-groot.3mf")
    _safe_print(f"Testing Feishu 3MF slicing: {model_path}")
    result = _run_slice_flow(send_cmd_handle, model_path, tmp_path)

    current_filename = _extract_http_3mf_suffix(model_path)
    result["record_id"] = current_filename
    key = current_filename
    
    baseline_row_data = {
        "record_id": current_filename,
        "file": str(model_path),
        "import_ms": str(result["import_ms"]),
        "slice_ms": str(result["slice_ms"]),
        "export_ms": str(result["export_ms"]),
        "import_ok": str(result["import_ok"]),
        "slice_ok": str(result["slice_ok"]),
        "export_ok": str(result["export_ok"]),
        "crashed": str(result["crashed"]),
        "error": result["error"] or "",
        "gcode_path": str(result["gcode_path"]) if result["gcode_path"] else ""
    }
    
    if key in baseline_data:
        # Compare with baseline
        baseline_row = baseline_data[key]
        _safe_print(f"Comparing with baseline for {key}...")
        
        # Assert key metrics match baseline
        assert result["crashed"] == (baseline_row["crashed"] == "True"), f"Crashed status mismatch with baseline for {key}"
        assert result["import_ok"] == (baseline_row["import_ok"] == "True"), f"Import status mismatch with baseline for {key}"
        assert result["slice_ok"] == (baseline_row["slice_ok"] == "True"), f"Slice status mismatch with baseline for {key}"
        assert result["export_ok"] == (baseline_row["export_ok"] == "True"), f"Export status mismatch with baseline for {key}"
        
        _safe_print(f"OK All metrics match baseline for {key}")
    else:
        _safe_print(f"Updating baseline data for {key}...")
        baseline_data[key] = baseline_row_data
    
    # Always assert basic success regardless of baseline
    #assert not result["crashed"], f"App crashed when handling {model_path}"
    #assert result["import_ok"], f"Import failed for {model_path}: {result['error']}"
    #assert result["slice_ok"], f"Slice failed for {model_path}: {result['error']}"
    #assert result["export_ok"], f"Export failed for {model_path}: {result['error']}"


@pytest.fixture(scope="session", autouse=True)
def write_report_to_feishu_after_tests(baseline_data, pytestconfig):
    """
    Write the feishu_slice_report.csv to a new Feishu table after all tests are completed.
    """
    yield  # This is the test execution phase

    if not _resolve_notify_enabled(pytestconfig):
        _safe_print("FEISHU notify disabled by --feishu-notify/FEISHU_NOTIFY, skip post-test report step.")
        return
    
    # This runs after all tests are completed
    report_path = Path("performance") / "data" / "feishu_slice_report.csv"
    
    # Write all baseline data to CSV file
    if baseline_data:
        _safe_print(f"\n=== Writing all baseline data to CSV ===")
        _safe_print(f"Writing to: {report_path}")
        
        # Create directory if it doesn't exist
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write CSV header
        header = [
            "record_id",
            "file",
            "import_ms",
            "slice_ms",
            "export_ms",
            "import_ok",
            "slice_ok",
            "export_ok",
            "crashed",
            "error",
            "gcode_path",
        ]
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(",".join(header) + "\n")
            
            # Write all baseline records
            for filename, record in baseline_data.items():
                # Ensure all fields are present and in order
                row = []
                for field in header:
                    # Convert all values to string to avoid TypeError during join
                    row.append(str(record.get(field, "")))
                # Join and write the row
                f.write(",".join(row) + "\n")
        
        _safe_print(f"OK Wrote {len(baseline_data)} records to {report_path}")
    
    # Check if report file exists
    if not report_path.exists():
        _safe_print(f"Report file not found: {report_path}")
        return
