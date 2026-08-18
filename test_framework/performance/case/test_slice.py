"""
Download 3MF files from a Feishu (Lark) Bitable and measure
import/slice/export performance with CrealityPrint.
Config via env:
    FEISHU_APP_ID / FEISHU_APP_SECRET / FEISHU_APP_TOKEN / FEISHU_TABLE_ID
    [FEISHU_VIEW_ID] [FEISHU_FILE_FIELD] [FEISHU_DOWNLOAD_DIR]
Results are appended to performance/data/feishu_slice_report.csv.
"""

import csv
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
import xml.etree.ElementTree as ET
from concurrent.futures import TimeoutError as FutureTimeoutError
from html import unescape as html_unescape
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
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
from test_framework.performance.summary import build_efficiency_summary, write_summary_files
from test_framework.performance.trend import write_performance_artifacts


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


_MAX_GCODE_CASE_COMPONENT_LENGTH = 80


def _gcode_only_3mf_skip_reason(model_path: Path) -> Optional[str]:
    """Return a skip reason only for a confidently identified G-code-only 3MF."""
    if model_path.suffix.lower() != ".3mf":
        return None

    try:
        with zipfile.ZipFile(model_path, "r") as zf:
            entries = {name.replace("\\", "/").lower(): name for name in zf.namelist()}
            model_entry = entries.get("3d/3dmodel.model")
            has_embedded_gcode = any(
                name.startswith("metadata/plate_") and name.endswith(".gcode")
                for name in entries
            )
            if model_entry is None or not has_embedded_gcode:
                return None
            root = ET.fromstring(zf.read(model_entry))
    except (OSError, KeyError, ET.ParseError, zipfile.BadZipFile):
        # Let the slicer report malformed or unsupported projects normally.
        return None

    build = next((element for element in root if element.tag.rsplit("}", 1)[-1] == "build"), None)
    has_build_items = build is not None and any(
        child.tag.rsplit("}", 1)[-1] == "item" for child in build
    )
    if has_build_items:
        return None

    return "3MF contains embedded G-code but no printable model objects (G-code-only project)"


def _prepare_3mf_without_empty_plates(model_path: Path, tmp_dir: Path) -> Tuple[Path, int]:
    """Create a temporary 3MF without empty plates, leaving the source untouched."""
    if model_path.suffix.lower() != ".3mf":
        return model_path, 0

    try:
        with zipfile.ZipFile(model_path, "r") as source_zip:
            settings_entry = next(
                (
                    name
                    for name in source_zip.namelist()
                    if name.replace("\\", "/").lower() == "metadata/model_settings.config"
                ),
                None,
            )
            if settings_entry is None:
                return model_path, 0

            root = ET.fromstring(source_zip.read(settings_entry))
            plates = [child for child in list(root) if child.tag.rsplit("}", 1)[-1] == "plate"]
            empty_plates = [
                plate
                for plate in plates
                if not any(node.tag.rsplit("}", 1)[-1] == "model_instance" for node in plate.iter())
            ]
            if not empty_plates or len(empty_plates) == len(plates):
                return model_path, 0

            for plate in empty_plates:
                root.remove(plate)

            remaining_plates = [child for child in list(root) if child.tag.rsplit("}", 1)[-1] == "plate"]
            for plate_number, plate in enumerate(remaining_plates, start=1):
                for metadata in plate:
                    if (
                        metadata.tag.rsplit("}", 1)[-1] == "metadata"
                        and metadata.get("key") == "plater_id"
                    ):
                        metadata.set("value", str(plate_number))
                        break

            # Keep the path short. performance_gcode_dir already contains the
            # full pytest node id and may push Windows paths beyond MAX_PATH.
            prepared_dir = Path(tempfile.gettempdir()) / "c3d3mf"
            prepared_dir.mkdir(parents=True, exist_ok=True)
            digest_input = f"{model_path}|{tmp_dir}".encode("utf-8")
            digest = hashlib.sha256(digest_input).hexdigest()[:16]
            prepared_path = prepared_dir / f"{os.getpid()}_{digest}.3mf"
            settings_xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)

            with zipfile.ZipFile(prepared_path, "w") as target_zip:
                for entry in source_zip.infolist():
                    data = settings_xml if entry.filename == settings_entry else source_zip.read(entry.filename)
                    target_zip.writestr(entry, data)
            return prepared_path, len(empty_plates)
    except (OSError, StopIteration, ET.ParseError, zipfile.BadZipFile):
        return model_path, 0


def _sanitize_path_component(
    text: str,
    max_length: int = _MAX_GCODE_CASE_COMPONENT_LENGTH,
) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9_.-]+", "_", text)
    if len(sanitized) <= max_length:
        return sanitized

    # pytest node ids include the full parameter value and can easily exceed
    # Windows path limits. Keep a readable prefix and a stable hash so that
    # truncated case directories remain deterministic and collision-resistant.
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    prefix_length = max_length - len(digest) - 1
    prefix = sanitized[:prefix_length].rstrip("._-")
    return f"{prefix}_{digest}" if prefix else digest[:max_length]


@pytest.fixture
def performance_gcode_dir(request, pytestconfig, clean_gcode_param) -> Path:
    root = Path(pytestconfig.getoption("--gcode-root")).resolve()
    nodeid = _sanitize_path_component(request.node.nodeid)
    output_dir = root / "performance" / f"case_{nodeid}"
    output_dir.mkdir(parents=True, exist_ok=True)

    if clean_gcode_param:
        request.addfinalizer(lambda: shutil.rmtree(output_dir, ignore_errors=True))

    return output_dir


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


def _result_row_failed(row: Dict) -> bool:
    return (
        str(row.get("crashed", "")).strip().lower() == "true"
        or str(row.get("import_ok", "")).strip().lower() != "true"
        or str(row.get("move_ok", "")).strip().lower() != "true"
        or str(row.get("slice_ok", "")).strip().lower() != "true"
        or str(row.get("export_ok", "")).strip().lower() != "true"
    )


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
# Cached CrealityPrint product version for the exe under test (read once per process).
_EXE_VERSION_CACHE: Dict[str, str] = {}


def _read_exe_version(exe_path: str) -> str:
    """Read the CrealityPrint product version (e.g. 7.1.1.4472) from the exe's
    Windows file version resource. Returns "unknown" when unavailable so the
    test never blocks on a missing version label.
    """
    resolved = str(Path(exe_path).resolve())
    if resolved in _EXE_VERSION_CACHE:
        return _EXE_VERSION_CACHE[resolved]
    version = "unknown"
    if sys.platform.startswith("win") and Path(resolved).exists():
        try:
            ps = (
                "(Get-Item -LiteralPath '%s').VersionInfo.ProductVersion"
                % resolved.replace("'", "''")
            )
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            v = (out.stdout or "").strip()
            if v:
                version = v
        except Exception:  # noqa: BLE001
            version = "unknown"
    _EXE_VERSION_CACHE[resolved] = version
    return version


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


def _http_list_links(page_html: str) -> List[str]:
    links: List[str] = []
    pos = 0
    while True:
        idx = page_html.find("href=", pos)
        if idx == -1:
            break
        quote = page_html[idx + 5]
        if quote not in ("'", '"'):
            pos = idx + 5
            continue
        end = page_html.find(quote, idx + 6)
        if end == -1:
            break
        href = html_unescape(page_html[idx + 6:end])
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

    def remote_file_size(file_url: str) -> Optional[int]:
        try:
            resp = session.head(file_url, allow_redirects=True, timeout=30)
            resp.raise_for_status()
        except Exception:
            return None
        content_length = resp.headers.get("Content-Length", "").strip()
        if not content_length:
            return None
        try:
            return int(content_length)
        except ValueError:
            return None

    def download_file(file_url: str, local_path: Path) -> bool:
        _safe_print(f"[http_3mf] downloading {file_url} -> {local_path}")
        try:
            with session.get(file_url, stream=True, timeout=60) as r:
                r.raise_for_status()
                with local_path.open("wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if not chunk:
                            continue
                        f.write(chunk)
        except Exception as exc:  # noqa: BLE001
            _safe_print(f"[http_3mf] download failed for {file_url}: {exc}")
            if local_path.exists():
                local_path.unlink()
            return False
        return True

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
                should_download = not local_path.exists()
                expected_size = remote_file_size(full)
                if local_path.exists() and expected_size is not None:
                    local_size = local_path.stat().st_size
                    if local_size != expected_size:
                        _safe_print(
                            f"[http_3mf] size mismatch for {local_path}: "
                            f"local={local_size}, remote={expected_size}, redownloading"
                        )
                        local_path.unlink()
                        should_download = True
                if should_download and not download_file(full, local_path):
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


def _collect_feishu_cases(pytestconfig=None) -> List[Dict]:
    global _FEISHU_CASES, _FEISHU_ERROR
    if _FEISHU_CASES is not None:
        return _FEISHU_CASES

    fixed_model_value = pytestconfig.getoption("--second-slice-model") if pytestconfig else ""
    if fixed_model_value:
        fixed_model = Path(fixed_model_value).expanduser().resolve()
        if not fixed_model.exists():
            _FEISHU_CASES = []
            _FEISHU_ERROR = f"--second-slice-model points to non-existing path: {fixed_model}"
            return _FEISHU_CASES
        _FEISHU_CASES = [
            {
                "record_id": fixed_model.name,
                "name": fixed_model.name,
                "path": str(fixed_model),
                "title": "second_slice/" + fixed_model.name,
            }
        ]
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
    cases = _collect_feishu_cases(metafunc.config)
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
    model_path = Path(path).expanduser()
    download_dir = _http_3mf_download_dir().expanduser()
    try:
        return model_path.resolve().relative_to(download_dir.resolve()).as_posix()
    except (OSError, ValueError):
        # Fixed/local models may not come from the configured HTTP cache.
        return model_path.name


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
            raw_error = payload.get("raw")
            if raw_error:
                error_msg = f"{status}: {raw_error}" if status != "ok" else str(raw_error)
            else:
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


def _product_duration_ms(command_result: Dict) -> Optional[float]:
    """Return a valid product-side duration_ms from a command response."""
    raw = command_result.get("raw")
    if not isinstance(raw, dict):
        return None
    payload = raw.get("payload")
    if not isinstance(payload, dict):
        return None
    value = payload.get("duration_ms")
    if isinstance(value, bool):
        return None
    try:
        duration_ms = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(duration_ms) or duration_ms < 0:
        return None
    return duration_ms


def _engine_process_state(engine_injector) -> Optional[Dict]:
    get_state = getattr(engine_injector, "process_state", None)
    if not callable(get_state):
        return None
    try:
        state = get_state()
    except Exception:  # noqa: BLE001
        return None
    return state if isinstance(state, dict) else None


def _send_handle_process_state(send_cmd_handle) -> Optional[Dict]:
    get_state = getattr(send_cmd_handle, "process_state", None)
    if not callable(get_state):
        return None
    try:
        state = get_state()
    except Exception:  # noqa: BLE001
        return None
    return state if isinstance(state, dict) else None


def _cpu_activity_delta(previous: Optional[Dict], current: Optional[Dict]) -> Optional[float]:
    if not isinstance(previous, dict) or not isinstance(current, dict):
        return None
    if not previous.get("running") or not current.get("running"):
        return None
    if previous.get("pid") != current.get("pid"):
        return None
    try:
        delta = float(current.get("cpu_seconds")) - float(previous.get("cpu_seconds"))
    except (TypeError, ValueError):
        return None
    return delta if delta >= 0 else None


def _engine_exception_detail(exc: Exception, process_state: Optional[Dict]) -> str:
    detail = type(exc).__name__
    message = str(exc).strip()
    if message:
        detail += f": {message}"
    if process_state is not None:
        running = process_state.get("running")
        pid = process_state.get("pid")
        returncode = process_state.get("returncode")
        if running:
            detail += f"; process=running; pid={pid}"
        else:
            detail += f"; process=exited; pid={pid}; returncode={returncode}"
    return detail


def _send_engine_command(engine_injector, command, params_json, recvcmd_timeout=None, band_output=False):
    try:
        payload = json.loads(params_json) if params_json else {}
    except Exception:
        payload = {}
    try:
        fut = engine_injector.submit(command, payload, timeout=recvcmd_timeout)
        # Let the injector publish its socket timeout to the Future first. Using
        # the exact same deadline here creates a race where FutureTimeoutError
        # hides the underlying command exception and leaves the worker running.
        future_timeout = None if recvcmd_timeout is None else recvcmd_timeout + 1.0
        resp = fut.result(timeout=future_timeout)
        resp_bytes = f"{command}_respone;{json.dumps(resp)}".encode("utf-8")
        return True, "ok", resp_bytes
    except (FutureTimeoutError, TimeoutError) as exc:
        process_state = _engine_process_state(engine_injector)
        status = "lostconnect" if process_state is not None and not process_state.get("running") else "timeout"
        detail = _engine_exception_detail(exc, process_state)
        return False, status, detail.encode("utf-8")
    except EngineUnavailable as exc:
        process_state = _engine_process_state(engine_injector)
        detail = _engine_exception_detail(exc, process_state)
        return False, "lostconnect", detail.encode("utf-8")
    except Exception as exc:  # noqa: BLE001
        process_state = _engine_process_state(engine_injector)
        status = "lostconnect" if process_state is not None and not process_state.get("running") else "error"
        detail = _engine_exception_detail(exc, process_state)
        return False, status, detail.encode("utf-8")


def _command_brief(ret: Dict) -> Dict:
    raw = ret.get("raw")
    if isinstance(raw, dict):
        raw = raw.copy()
    return {
        "ok": ret.get("ok"),
        "code": ret.get("code"),
        "status": ret.get("status"),
        "crashed": ret.get("crashed"),
        "elapsed_ms": round(float(ret.get("elapsed_ms") or 0), 2),
        "error": ret.get("error"),
        "raw": raw,
    }


def _log_command_result(label: str, ret: Dict) -> None:
    try:
        payload = json.dumps(_command_brief(ret), ensure_ascii=False, sort_keys=True)
    except Exception:  # noqa: BLE001
        payload = str(_command_brief(ret))
    _safe_print(f"[cmd] {label}: {payload}")


def _error_summary(error: Dict) -> str:
    try:
        return json.dumps(error, ensure_ascii=False, sort_keys=True)
    except Exception:  # noqa: BLE001
        return str(error)


def _is_blocking_import_error(error: Dict) -> bool:
    if not isinstance(error, dict):
        return False
    level = error.get("level")
    if level == 9:
        return True
    return str(level or "").strip().lower() in {"error", "fatal"}


def _blocking_validation_errors(ret: Dict) -> List[Dict]:
    """Extract deterministic validation failures from a get_error response."""
    if not ret.get("ok"):
        return []
    raw = ret.get("raw")
    if not isinstance(raw, dict):
        return []
    payload = raw.get("payload")
    if not isinstance(payload, dict):
        return []
    errors = payload.get("data")
    if not isinstance(errors, list):
        return []
    return [error for error in errors if _is_blocking_import_error(error)]


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
    progress["all_plate_finished"] = payload.get("all_plate_finished")
    return progress


def _is_slicing_done(progress: Dict) -> bool:
    # The engine exposes a slicing state machine via get_slicing_progress:
    #   "began" / "progress" / "cancelled" -> slice is in flight, NOT done
    #   "completed"                         -> slice just finished (transient)
    #   "no_slicing"                        -> idle; no slice running right now
    # The "completed" state is transient: the SlicingProgressNotification resets
    # to SP_NO_SLICING shortly after a slice finishes, so polling almost never
    # observes "completed". After a slice completes the engine sits at
    # state="no_slicing" with all_plate_finished=True (the on-disk result is
    # ready), which is the stable post-slice signal we must rely on.
    #
    # "progress"/"began"/"cancelled" always mean still working, even if a stale
    # previous result keeps all_plate_finished True (re-slice case). For any
    # other state (completed / no_slicing / unknown / missing) the on-disk
    # all_plate_finished flag is the completion authority.
    state = str(progress.get("state") or "").lower()
    if state in {"progress", "began", "cancelled"}:
        return False
    if state == "completed":
        return True
    return bool(progress.get("all_plate_finished"))


def _is_idle_no_slicing_progress(progress: Optional[Dict]) -> bool:
    """Return whether slicing never left the engine's idle state."""
    if not isinstance(progress, dict):
        return False
    percentage = _progress_percentage_0_100(progress.get("percentage"))
    state = str(progress.get("state") or "").strip().lower()
    return percentage == -1.0 and state == "no_slicing"


def _wait_for_slicing_done(
    send_cmd_handle,
    timeout_s: float,
    poll_interval_s: float = 0.5,
    wait_for_transition: bool = False,
) -> Dict:
    start = time.perf_counter()
    deadline = time.monotonic() + max(0.0, float(timeout_s))
    last_progress: Optional[Dict] = None
    last_error: Optional[str] = None
    last_progress_marker = None
    last_change_ts = time.monotonic()
    last_visible_change_ts = None
    last_activity_state = _send_handle_process_state(send_cmd_handle)
    stall_seconds = float(os.getenv("SLICER_PROGRESS_STALL_SECONDS", "120"))
    active_cpu_seconds = float(os.getenv("SLICER_ACTIVE_CPU_SECONDS", "1"))
    # When re-slicing, the "all_plate_finished" flag stays True from the previous
    # slice result until the new slice overwrites it. wait_for_transition requires
    # observing at least one False (slice in progress) before accepting True, so a
    # stale True cannot short-circuit the wait of a subsequent slice.
    saw_unfinished = not wait_for_transition

    while True:
        now = time.monotonic()
        visible_progress_is_recent = (
            last_visible_change_ts is not None
            and stall_seconds > 0
            and now - last_visible_change_ts < stall_seconds
        )
        # The configured timeout is a hard limit only when the engine has not
        # reported recent visible progress. Long slices whose percentage or
        # status text (for example, the current layer) keeps changing are
        # governed by the shorter stall detector instead.
        if now >= deadline and not visible_progress_is_recent:
            break

        progress_ret = _run_command(
            send_cmd_handle,
            "get_slicing_progress",
            {},
            timeout=60,
        )
        #all_plate_finished = progress_ret["all_plate_finished"]
        if progress_ret["ok"]:
            progress = _extract_slicing_progress(progress_ret)
            if progress is not None:
                last_progress = progress
                pct = _progress_percentage_0_100(progress.get("percentage"))
                now = time.monotonic()
                if pct is not None:
                    # Long-running stages may keep the same percentage while reporting
                    # completed layer counts in the status text.
                    progress_marker = (pct, str(progress.get("text") or ""))
                    if last_progress_marker is None or progress_marker != last_progress_marker:
                        last_progress_marker = progress_marker
                        last_change_ts = now
                        last_visible_change_ts = now
                        last_activity_state = _send_handle_process_state(send_cmd_handle)
                        _safe_print(
                            f"[slice-progress] percentage={pct:.3f}, "
                            f"state={progress.get('state') or 'unknown'}, "
                            f"text={progress_marker[1] or '<empty>'}"
                        )
                    elif now - last_change_ts >= stall_seconds:
                        current_activity_state = _send_handle_process_state(send_cmd_handle)
                        cpu_delta = _cpu_activity_delta(last_activity_state, current_activity_state)
                        if cpu_delta is not None and cpu_delta >= active_cpu_seconds:
                            _safe_print(
                                f"[slice-progress] API status unchanged for {stall_seconds}s, "
                                f"but engine CPU advanced by {cpu_delta:.1f}s; extending stall window"
                            )
                            last_change_ts = now
                            last_activity_state = current_activity_state
                            continue
                        pct_str = f"{pct:.3f}"
                        state_str = str(progress.get("state") or "unknown")
                        text_str = str(progress.get("text") or "")
                        return {
                            "ok": False,
                            "crashed": False,
                            "elapsed_ms": (time.perf_counter() - start) * 1000,
                            "progress": last_progress,
                            "error": (
                                f"slicing progress stalled for {stall_seconds}s "
                                f"(percentage={pct_str}, state={state_str}, text={text_str!r})"
                            ),
                        }
                if not _is_slicing_done(progress):
                    saw_unfinished = True
                    # Some project validations are only raised after Slice All is
                    # triggered (for example, a later plate using spiral-vase mode
                    # with multiple objects). In that case the engine remains idle
                    # at -1/no_slicing. Surface the deterministic validation error
                    # immediately instead of treating it as an engine stall and
                    # retrying the whole model after 120 seconds.
                    if _is_idle_no_slicing_progress(progress):
                        validation_ret = _run_command(
                            send_cmd_handle,
                            "get_error",
                            {"type": "all"},
                            timeout=5,
                        )
                        blocking_errors = _blocking_validation_errors(validation_ret)
                        if blocking_errors:
                            return {
                                "ok": False,
                                "crashed": False,
                                "elapsed_ms": (time.perf_counter() - start) * 1000,
                                "progress": last_progress,
                                "blocking_validation": blocking_errors[0],
                                "error": f"slicing blocked by validation: {_error_summary(blocking_errors[0])}",
                            }
                elif saw_unfinished:
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


REPORT_FIELDS = (
    "record_id",
    "version",
    "import_ms",
    "first_slice_ms",
    "move_ms",
    "second_slice_trials",
    "second_slice_ms",
    "slice_ms",
    "export_ms",
    "import_ok",
    "move_ok",
    "slice_ok",
    "export_ok",
    "crashed",
    "error",
)


def _write_report_rows(report_path: Path, rows, *, append: bool = False) -> None:
    """Write report rows with CSV quoting for free-text fields such as error."""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not append or not report_path.exists() or report_path.stat().st_size == 0
    mode = "a" if append else "w"
    with report_path.open(mode, encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=REPORT_FIELDS,
            extrasaction="ignore",
            lineterminator="\n",
        )
        if write_header:
            writer.writeheader()
        writer.writerows(rows)


def _write_report_line(report_path: Path, row: Dict) -> None:
    _write_report_rows(report_path, (row,), append=True)

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
    slicer_datadir = pytestconfig.getoption("--slicer-datadir") or os.getenv("SLICER_DATADIR", "")
    cli_args = [exe_path, "test#157369"]
    if slicer_datadir:
        datadir_path = Path(slicer_datadir).resolve()
        datadir_path.mkdir(parents=True, exist_ok=True)
        cli_args.append(f"--datadir={datadir_path}")
        _safe_print(f"[datadir] CrealityPrint isolated data dir: {datadir_path}")

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
            cli_args=cli_args,
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

        def process_state(self):
            return self._mgr.process_state()

    return InjectorAdapter(engine_manager_perf)


@pytest.fixture(scope="session")
def engine_session_send_cmd(engine_injector_perf):
    def send_cmd_handle(command, params_json, recvcmd_timeout=None, band_output=False):
        return _send_engine_command(
            engine_injector_perf,
            command,
            params_json,
            recvcmd_timeout,
            band_output,
        )

    send_cmd_handle.process_state = engine_injector_perf.process_state

    return send_cmd_handle


@pytest.fixture(scope="session")
def exe_version_perf(pytestconfig):
    """CrealityPrint product version label for the exe under test (read once)."""
    slicer_exe = pytestconfig.getoption("--slicer-exe")
    if slicer_exe:
        exe_path = slicer_exe
    else:
        exe_path = os.getenv("CREALITY_PRINTER_PATH", "")
    version = _read_exe_version(exe_path) if exe_path else "unknown"
    _safe_print(f"[version] CrealityPrint under test: {version}")
    return version


@pytest.fixture(scope="session")
def baseline_data():
    """
    Load baseline data from feishu_slice_report.csv at test startup.
    """
    baseline_path = Path(os.getenv("SECOND_SLICE_BASELINE_CSV") or Path("performance") / "data" / "feishu_slice_report.csv")
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
                        key = record_id
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


@pytest.fixture(scope="session")
def baseline_snapshot(baseline_data):
    return {key: dict(value) for key, value in baseline_data.items()}


@pytest.fixture(scope="session")
def current_results():
    """Rows produced by this test session, kept separate from the loaded baseline."""
    return {}


def _run_slice_flow(send_cmd_handle, model_path: Path, tmp_dir: Path) -> Dict:
    second_slice_enabled = _truthy_env("ENABLE_SECOND_SLICE")
    timeouts = {
        "load": int(os.getenv("SLICER_LOAD_TIMEOUT", "300")),
        # Complex tree-support / high-layer-count projects legitimately take
        # around 8 minutes on an otherwise idle workstation. Keep the shorter
        # activity-aware stall detector for hangs, and leave headroom for a
        # loaded Jenkins worker here.
        "slice": int(os.getenv("SLICER_SLICE_TIMEOUT", "900")),
        "export": int(os.getenv("SLICER_EXPORT_TIMEOUT", "360")),
        "wait": float(os.getenv("SLICER_WAIT_WRITTEN", "180")),
        "settle": float(os.getenv("SLICER_SETTLE_SECONDS", "1.0")),
    }
    project_name = os.getenv("SLICER_PROJECT_NAME", "pytest_case_project")
    result = {
        "record_id": "",
        "import_ms": None,
        "first_slice_ms": None,
        "move_ms": None,
        "second_slice_ms": None,
        "second_slice_trials": [],  # raw ms of each second-slice repeat
        "slice_ms": None,
        "export_ms": None,
        "import_ok": False,
        "move_ok": False,
        "slice_ok": False,
        "export_ok": False,
        "crashed": False,
        "retryable_idle_no_slicing": False,
        "idle_no_slicing_retries": 0,
        "skip_reason": None,
        "_prepared_model_path": None,
        "error": None,
    }

    gcode_only_reason = _gcode_only_3mf_skip_reason(model_path)
    if gcode_only_reason:
        result["skip_reason"] = gcode_only_reason
        return result

    prepared_model_path, removed_empty_plates = _prepare_3mf_without_empty_plates(model_path, tmp_dir)
    if removed_empty_plates:
        result["_prepared_model_path"] = str(prepared_model_path)
        _safe_print(
            f"[3mf] removed {removed_empty_plates} empty plate(s); "
            f"slicing temporary copy: {prepared_model_path}"
        )

    def run_slice_once(label: str, wait_for_transition: bool = False) -> Optional[float]:
        slice_client_started = time.perf_counter()
        slice_ret = _run_command(
            send_cmd_handle,
            "trigger_slice",
            {"id": SLICE_BTN_ID},
            timeout=timeouts["slice"],
        )
        _log_command_result(f"{label}.trigger_slice", slice_ret)
        result["crashed"] = result["crashed"] or slice_ret["crashed"]
        if not slice_ret["ok"]:
            result["slice_ok"] = False
            result["error"] = slice_ret["error"] or f"{label} trigger_slice failed: {_command_brief(slice_ret)}"
            return None

        product_slice_ms = _product_duration_ms(slice_ret)
        wait_ret = _wait_for_slicing_done(
            send_cmd_handle,
            timeout_s=float(timeouts["slice"]),
            poll_interval_s=float(os.getenv("SLICER_PROGRESS_POLL", "1")),
            # A product duration means trigger_slice returned after this slice's
            # first Preview frame. Legacy products return at slice start and still
            # need the transition guard for second-slice polling.
            wait_for_transition=wait_for_transition and product_slice_ms is None,
        )
        _log_command_result(f"{label}.wait_slicing_done", wait_ret)
        result["crashed"] = result["crashed"] or wait_ret["crashed"]
        if not wait_ret["ok"]:
            result["slice_ok"] = False
            blocking_validation = wait_ret.get("blocking_validation")
            if blocking_validation:
                result["skip_reason"] = (
                    f"slicing blocked by validation: {_error_summary(blocking_validation)}"
                )
                result["retryable_idle_no_slicing"] = False
            else:
                result["retryable_idle_no_slicing"] = _is_idle_no_slicing_progress(wait_ret.get("progress"))
            result["error"] = wait_ret["error"] or f"{label} slicing did not finish"
            return None
        client_slice_ms = round((time.perf_counter() - slice_client_started) * 1000, 2)
        if product_slice_ms is None:
            _safe_print(
                "[timing] WARNING trigger_slice did not return a valid "
                "payload.duration_ms; using legacy client wall-clock timing"
            )
            return client_slice_ms

        product_slice_ms = round(product_slice_ms, 2)
        _safe_print(
            f"[timing] {label} slice product={product_slice_ms}ms; "
            f"client_wall={client_slice_ms}ms"
        )
        return product_slice_ms

    # Reset project to avoid residue between runs.
    reset_ret = _run_command(
        send_cmd_handle,
        "reset_project",
        {"skip_confirm": True, "silent": True, "project_name": project_name},
        timeout=30,
    )
    _log_command_result("reset_project", reset_ret)
    if not reset_ret["ok"]:
        result["error"] = reset_ret["error"] or "reset_project failed"
        result["crashed"] = reset_ret["crashed"]
        return result
    printer_name = os.getenv("SECOND_SLICE_PRINTER_NAME", "").strip()
    if printer_name:
        select_ret = _run_command(
            send_cmd_handle,
            "select_printer",
            {"printer_name": printer_name},
            timeout=5,
        )
        _safe_print(select_ret)
        if not select_ret["ok"]:
            result["error"] = f"select_printer failed: {select_ret['error'] or select_ret['raw']}"
            result["crashed"] = select_ret["crashed"]
            return result
    else:
        _safe_print("[printer] SECOND_SLICE_PRINTER_NAME is empty; using project/current printer")
    # Import model
    import_ret = _run_command(
        send_cmd_handle,
        "trigger_load_project2",
        {"file": str(prepared_model_path), "discard_preset_changes": True},
        timeout=timeouts["load"],
    )
    _log_command_result("trigger_load_project2", import_ret)
    result["crashed"] = import_ret["crashed"]
    if not import_ret["ok"]:
        result["error"] = import_ret["error"]
        return result
    import_ms = _product_duration_ms(import_ret)
    result["import_ok"] = True
    if import_ms is None:
        result["import_ms"] = round(import_ret["elapsed_ms"], 2)
        _safe_print(
            "[timing] WARNING trigger_load_project2 did not return a valid "
            "payload.duration_ms; using legacy client wall-clock timing"
        )
    else:
        result["import_ms"] = round(import_ms, 2)
        _safe_print(
            f"[timing] open product={result['import_ms']}ms; "
            f"client_wall={round(import_ret['elapsed_ms'], 2)}ms"
        )
    #get error
    import_error = _run_command(
        send_cmd_handle,
        "get_error",
        {"type":"all"},
        timeout=5,
    )
    _log_command_result("get_error.after_import", import_error)
    
    for error in _blocking_validation_errors(import_error):
        result["skip_reason"] = f"slicing blocked by import validation: {_error_summary(error)}"
        return result
    first_slice_ms = run_slice_once("first")
    result["first_slice_ms"] = first_slice_ms
    if first_slice_ms is None:
        return result
    if not second_slice_enabled:
        _safe_print("[second-slice] disabled; exporting the first-slice result")
        result["move_ok"] = True
        result["slice_ok"] = True
        result["slice_ms"] = first_slice_ms
    else:
        move_ret = _run_command(
            send_cmd_handle,
            "move_model_instance",
            {
                "object_index": int(os.getenv("SECOND_SLICE_OBJECT_INDEX", "0")),
                "instance_index": int(os.getenv("SECOND_SLICE_INSTANCE_INDEX", "0")),
                "delta_x": float(os.getenv("SECOND_SLICE_MOVE_X", "10")),
                "delta_y": float(os.getenv("SECOND_SLICE_MOVE_Y", "0")),
                "delta_z": float(os.getenv("SECOND_SLICE_MOVE_Z", "0")),
            },
            timeout=int(os.getenv("SLICER_MOVE_TIMEOUT", "30")),
        )
        _log_command_result("move_model_instance", move_ret)
        result["move_ok"] = move_ret["ok"]
        result["move_ms"] = round(move_ret["elapsed_ms"], 2) if move_ret["ok"] else None
        result["crashed"] = result["crashed"] or move_ret["crashed"]
        if not move_ret["ok"]:
            result["error"] = move_ret["error"] or "move_model_instance failed"
            return result

        # Second slice (slice after moving the model). One first slice + one
        # moved-model slice is one test group. Repeat >1 only when a more stable
        # mean is explicitly requested via SECOND_SLICE_REPEAT.
        repeat = max(1, int(os.getenv("SECOND_SLICE_REPEAT", "1")))
        second_trials = []
        for i in range(repeat):
            # Re-slicing: a previous slice result is already on disk, so use the
            # live state signal (progress->completed) to avoid a stale "finished" flag.
            trial = run_slice_once(f"second-{i + 1}", wait_for_transition=True)
            if trial is None:
                return result
            second_trials.append(trial)
        result["second_slice_trials"] = second_trials
        second_slice_ms = round(sum(second_trials) / len(second_trials), 2)
        result["second_slice_ms"] = second_slice_ms
        result["slice_ms"] = second_slice_ms
        result["slice_ok"] = second_slice_ms is not None
        if second_slice_ms is None:
            return result

    # Export gcode
    output_gcode = tmp_dir / f"{model_path.stem}.gcode.3mf"
    export_ret = _run_command(
        send_cmd_handle,
        "export_gcode",
        {"export_all": True, "output": str(output_gcode)},
        timeout=timeouts["export"],
    )
    _log_command_result("export_gcode", export_ret)
    client_export_ms = round(export_ret["elapsed_ms"], 2)
    product_export_ms = _product_duration_ms(export_ret)
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
    if result["export_ok"]:
        if product_export_ms is None:
            _safe_print(
                "[timing] WARNING export_gcode did not return a valid "
                "payload.duration_ms; using legacy client wall-clock timing"
            )
            result["export_ms"] = client_export_ms
        else:
            result["export_ms"] = round(product_export_ms, 2)
            _safe_print(
                f"[timing] export product={result['export_ms']}ms; "
                f"client_wall={client_export_ms}ms"
            )
    else:
        result["export_ms"] = None
    result["crashed"] = result["crashed"] or export_ret["crashed"]
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


def _run_slice_flow_with_idle_retry(
    send_cmd_handle,
    engine_manager,
    model_path: Path,
    tmp_dir: Path,
) -> Dict:
    """Retry a whole model once when slicing stays at -1/no_slicing."""
    try:
        max_retries = min(1, max(0, int(os.getenv("SLICER_IDLE_NO_SLICING_RETRIES", "1"))))
    except ValueError:
        max_retries = 1

    retries_used = 0
    while True:
        result = _run_slice_flow(send_cmd_handle, model_path, tmp_dir)
        result["idle_no_slicing_retries"] = retries_used
        if not result.get("retryable_idle_no_slicing") or retries_used >= max_retries:
            return result

        retries_used += 1
        _safe_print(
            f"[retry] slicing stayed at percentage=-1/state=no_slicing; "
            f"restarting engine and rerunning current model ({retries_used}/{max_retries}) ..."
        )
        try:
            engine_manager.restart()
        except Exception as exc:  # noqa: BLE001
            _safe_print(f"[retry] engine restart failed: {exc}")
            return result


# ======== tests ========
@pytest.mark.performance
def test_feishu_slice(
    request,
    feishu_case,
    engine_session_send_cmd,
    engine_manager_perf,
    performance_gcode_dir,
    baseline_data,  # Use the fixture for baseline data
    current_results,
    exe_version_perf,
):
    if not _FEISHU_CASES:
        pytest.skip(_FEISHU_ERROR or "Feishu dataset not configured.")

    send_cmd_handle = engine_session_send_cmd
    model_path = Path(feishu_case["path"]).resolve()  # Ensure absolute path
    #model_path = Path("C:\work\C3DBaseline\test_framework\artifacts\feishu_3mf\baby-groot.3mf")
    _safe_print(f"Testing Feishu 3MF slicing: {model_path}")
    result = _run_slice_flow_with_idle_retry(
        send_cmd_handle,
        engine_manager_perf,
        model_path,
        performance_gcode_dir,
    )

    prepared_model_path = result.pop("_prepared_model_path", None)
    if prepared_model_path:
        def cleanup_prepared_model() -> None:
            prepared_path = Path(prepared_model_path)
            prepared_path.unlink(missing_ok=True)
            try:
                prepared_path.parent.rmdir()
            except OSError:
                pass

        request.addfinalizer(cleanup_prepared_model)

    if result.get("skip_reason"):
        pytest.skip(result["skip_reason"])

    # If the case failed (deadlock / timeout / crash), force-restart the engine
    # so the next parametrized case starts with a clean state.
    if not result.get("export_ok"):
        error_msg = result.get("error") or ""
        _safe_print(f"[recovery] case failed ({error_msg}), restarting engine ...")
        try:
            engine_manager_perf.restart()
        except Exception as exc:  # noqa: BLE001
            _safe_print(f"[recovery] engine restart failed: {exc}")

    current_filename = _extract_http_3mf_suffix(model_path)
    result["record_id"] = current_filename
    key = current_filename
    
    baseline_row_data = {
        "record_id": current_filename,
        "version": str(exe_version_perf),
        "import_ms": str(result["import_ms"]),
        "first_slice_ms": str(result["first_slice_ms"]),
        "move_ms": str(result["move_ms"]),
        "second_slice_trials": ";".join(str(t) for t in result["second_slice_trials"]),
        "second_slice_ms": str(result["second_slice_ms"]),
        "slice_ms": str(result["slice_ms"]),
        "export_ms": str(result["export_ms"]),
        "import_ok": str(result["import_ok"]),
        "move_ok": str(result["move_ok"]),
        "slice_ok": str(result["slice_ok"]),
        "export_ok": str(result["export_ok"]),
        "crashed": str(result["crashed"]),
        "error": result["error"] or "",
    }
    
    baseline_row = baseline_data.get(key)

    # Preserve the observed row before any comparison assertion can abort the
    # test. The session teardown then writes an accurate failure report.
    baseline_data[key] = baseline_row_data
    current_results[key] = baseline_row_data

    if baseline_row:
        # Compare with baseline
        _safe_print(f"Comparing with baseline for {key}...")

        # A baseline row that itself failed (crashed/import/move/slice/export not ok)
        # is stale and cannot be a stability reference: the whole point of this job
        # is to detect behavior change across builds, and a freshly fixed build must
        # be allowed to overwrite a previously broken result. summary.py already
        # skips failed baselines when computing the regression verdict, so the
        # consistency checks here are only meaningful against a healthy baseline.
        if _result_row_failed(baseline_row):
            _safe_print(f"Baseline for {key} is a failed/stale run; allowing current run to overwrite it.")
        else:
            # Assert key metrics match baseline (only against a healthy baseline)
            assert result["crashed"] == (baseline_row["crashed"] == "True"), f"Crashed status mismatch with baseline for {key}"
            assert result["import_ok"] == (baseline_row["import_ok"] == "True"), f"Import status mismatch with baseline for {key}"
            if _truthy_env("ENABLE_SECOND_SLICE") and "move_ok" in baseline_row:
                assert result["move_ok"] == (baseline_row.get("move_ok") == "True"), f"Move status mismatch with baseline for {key}"
            assert result["slice_ok"] == (baseline_row["slice_ok"] == "True"), f"Slice status mismatch with baseline for {key}"
            assert result["export_ok"] == (baseline_row["export_ok"] == "True"), f"Export status mismatch with baseline for {key}"

            _safe_print(f"OK All metrics match baseline for {key}")
    else:
        _safe_print(f"New baseline entry for {key}")

    assert not result["crashed"], f"App crashed when handling {model_path}"
    assert result["import_ok"], f"Import failed for {model_path}: {result['error']}"
    assert result["first_slice_ms"] is not None, f"First slice failed for {model_path}: {result['error']}"
    if _truthy_env("ENABLE_SECOND_SLICE"):
        assert result["move_ok"], f"Move model failed for {model_path}: {result['error']}"
        assert result["slice_ok"], f"Second slice failed for {model_path}: {result['error']}"
        assert result["second_slice_ms"] is not None, f"Second slice timing missing for {model_path}: {result['error']}"
    assert result["export_ok"], f"Export failed for {model_path}: {result['error']}"


@pytest.fixture(scope="session", autouse=True)
def write_report_to_feishu_after_tests(baseline_data, baseline_snapshot, current_results, pytestconfig):
    """
    Write the feishu_slice_report.csv to a new Feishu table after all tests are completed.
    """
    yield  # This is the test execution phase

    # Always write CSV report regardless of feishu-notify setting
    report_path = Path("performance") / "data" / "feishu_slice_report.csv"
    
    _safe_print(f"\n=== Writing all baseline data to CSV ===")
    _safe_print(f"Writing to: {report_path}")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_written_this_run = False
    last_exc = None
    for _attempt in range(5):
        try:
            _write_report_rows(report_path, baseline_data.values())
            _safe_print(f"OK Wrote {len(baseline_data)} records to {report_path}")
            report_written_this_run = True
            break
        except PermissionError as exc:
            last_exc = exc
            _safe_print(f"[csv-write] file locked, retrying ({_attempt + 1}/5)...")
            time.sleep(2)
    if last_exc is not None and not report_written_this_run:
        _safe_print(f"[csv-write] failed after retries: {last_exc}")

    try:
        outputs = write_performance_artifacts(current_results, report_path.parent)
        if outputs:
            _safe_print(f"OK Wrote performance trend report: {outputs['trend_html']}")
    except Exception as exc:  # noqa: BLE001
        _safe_print(f"[performance-trend] failed to write report: {exc}")

    if not _truthy_env("ENABLE_SECOND_SLICE"):
        _safe_print("Skip second-slice efficiency summary and baseline update: second slice is disabled.")
        return

    summary = build_efficiency_summary(
        baseline_snapshot,
        baseline_data,
        regression_percent=float(os.getenv("SECOND_SLICE_REGRESSION_PERCENT", "5")),
        min_delta_ms=float(os.getenv("SECOND_SLICE_MIN_DELTA_MS", "1000")),
    )
    markdown_path, json_path = write_summary_files(summary, report_path.parent)
    _safe_print(f"OK Wrote second-slice efficiency summary: {markdown_path}")
    _safe_print(f"OK Wrote second-slice efficiency summary json: {json_path}")
    
    if not report_written_this_run:
        _safe_print(f"Skip updating persistent second-slice baseline: report was not written in this run.")
        return

    baseline_csv = os.getenv("SECOND_SLICE_BASELINE_CSV")
    if baseline_csv:
        update_baseline = _truthy_text(os.getenv("SECOND_SLICE_UPDATE_BASELINE", ""))
        if not current_results:
            _safe_print("Skip updating persistent second-slice baseline: no current result rows were produced.")
            return
        failed_rows = [record for record in current_results.values() if _result_row_failed(record)]
        if not update_baseline:
            _safe_print(f"Persistent second-slice baseline is read-only for this run: {baseline_csv}")
            return
        if failed_rows:
            _safe_print(f"Skip updating persistent second-slice baseline because {len(failed_rows)} current row(s) failed.")
            return
        try:
            baseline_csv_path = Path(baseline_csv)
            baseline_csv_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(report_path, baseline_csv_path)
            _safe_print(f"OK Updated persistent second-slice baseline: {baseline_csv_path}")
        except Exception as exc:  # noqa: BLE001
            _safe_print(f"[baseline-copy] failed to update persistent baseline: {exc}")
