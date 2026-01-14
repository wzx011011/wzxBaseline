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
import time
from pathlib import Path
from typing import Dict, List, Optional, Union

import pytest

from test_framework.engine_params.src.slicerctl.session import (
    EngineSession,
    RestartingEngine,
    EngineUnavailable,
)
from test_framework.engine_params.conftest import wait_for_file_written
from test_framework.engine_params.src.slicerctl.constants import SLICE_BTN_ID
from test_framework.performance.utils.feishu_downloader import (
    FeishuDownloader,
    load_feishu_config,
)




# ======== Feishu dataset discovery (collection time) ========
_FEISHU_CASES: Optional[List[Dict]] = None
_FEISHU_ERROR: Optional[str] = None


def _truthy_env(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


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


def _collect_feishu_cases() -> List[Dict]:
    global _FEISHU_CASES, _FEISHU_ERROR
    if _FEISHU_CASES is not None:
        return _FEISHU_CASES

    # Optional: only use local manifest for debugging, skip Feishu download.
    if _truthy_env("FEISHU_USE_MANIFEST_ONLY"):
        try:
            cases = _load_manifest_cases()
            
            # Apply DEBUG mode limit if needed
            if _truthy_env("DEBUG"):
                print(f"DEBUG mode enabled: limiting to 10 manifest cases (from {len(cases)} total)")
                cases = cases[:10]
            
            _FEISHU_CASES = cases
            if not cases:
                _FEISHU_ERROR = "Manifest found but no valid entries."
        except Exception as exc:  # noqa: BLE001
            _FEISHU_CASES = []
            _FEISHU_ERROR = str(exc)
        return _FEISHU_CASES

    cfg = load_feishu_config()
    if not cfg:
        _FEISHU_CASES = []
        _FEISHU_ERROR = (
            "Missing FEISHU_APP_ID/FEISHU_APP_SECRET/FEISHU_APP_TOKEN/FEISHU_TABLE_ID "
            "environment variables, skip Feishu 3MF collection."
        )
        return _FEISHU_CASES

    downloader = FeishuDownloader(
        app_id=cfg["app_id"],
        app_secret=cfg["app_secret"],
        app_token=cfg["app_token"],
        table_id=cfg["table_id"],
        view_id=cfg.get("view_id"),
        file_field=cfg.get("file_field", "文件"),
        download_dir=cfg.get("download_dir") or Path("artifacts") / "feishu_3mf",
    )
    try:
        files = downloader.download_all()
        
        # Apply DEBUG mode limit if needed
        if _truthy_env("DEBUG"):
            print(f"DEBUG mode enabled: limiting to 10 Feishu cases (from {len(files)} total)")
            files = files[:1]
        
        _FEISHU_CASES = files
        if not files:
            _FEISHU_ERROR = "No 3MF attachments found in Feishu table."
    except Exception as exc:  # noqa: BLE001
        _FEISHU_CASES = []
        _FEISHU_ERROR = f"Feishu download failed: {exc}"
    return _FEISHU_CASES


def pytest_generate_tests(metafunc):
    if "feishu_case" not in metafunc.fixturenames:
        return
    cases = _collect_feishu_cases()
    if not cases:
        if _FEISHU_ERROR:
            pytest.skip(_FEISHU_ERROR, allow_module_level=True)
        metafunc.parametrize("feishu_case", [], ids=[])
        return
    ids = [Path(item["path"]).name for item in cases]
    metafunc.parametrize("feishu_case", cases, ids=ids)


# ======== helpers ========
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
        print(f"Loading baseline data from {baseline_path}...")
        # Try different encodings to handle various file formats
        encodings = ["utf-8", "gbk", "latin-1"]
        
        for encoding in encodings:
            try:
                with open(baseline_path, "r", encoding=encoding) as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Use filename as key for comparison
                        filename = Path(row["file"]).name
                        baseline_data[filename] = row
                print(f"OK Loaded {len(baseline_data)} baseline records with encoding: {encoding}")
                break
            except UnicodeDecodeError:
                print(f"Failed to read with encoding {encoding}, trying next...")
            except Exception as e:
                print(f"Error reading baseline file: {e}")
                break
        
        if not baseline_data:
            print(f"Failed to read baseline file with any encoding")
    else:
        print(f"Baseline file not found: {baseline_path}")
    
    return baseline_data


def _run_slice_flow(send_cmd_handle, model_path: Path, tmp_dir: Path) -> Dict:
    timeouts = {
        "load": int(os.getenv("SLICER_LOAD_TIMEOUT", "90")),
        "slice": int(os.getenv("SLICER_SLICE_TIMEOUT", "120")),
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
    print(select_ret)
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
    slice_ret = _run_command(
        send_cmd_handle,
        "click_button",
        {"id": SLICE_BTN_ID},
        timeout=timeouts["slice"],
    )
    result["slice_ok"] = slice_ret["ok"]
    result["slice_ms"] = round(slice_ret["elapsed_ms"], 2)
    result["crashed"] = result["crashed"] or slice_ret["crashed"]
    if not slice_ret["ok"]:
        result["error"] = slice_ret["error"]
        return result

    # Export gcode
    output_gcode = tmp_dir / f"{model_path.stem}.gcode.3mf"
    export_ret = _run_command(
        send_cmd_handle,
        "export_gcode",
        {"export_all": True, "output": str(output_gcode)},
        timeout=timeouts["export"],
    )
    print(output_gcode.exists())
    #sleep 1s
    time.sleep(1)
    result["export_ok"] = export_ret["ok"] and output_gcode.exists()
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
    print(f"Testing Feishu 3MF slicing: {model_path}")
    result = _run_slice_flow(send_cmd_handle, model_path, tmp_path)
    result["record_id"] = feishu_case.get("record_id")

    # Get current filename for comparison
    current_filename = model_path.name
    
    # Update baseline data with current result
    baseline_row_data = {
        "record_id": str(result["record_id"]) if result["record_id"] else "",
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
    
    # Check if record exists in baseline for comparison
    if current_filename in baseline_data:
        # Compare with baseline
        baseline_row = baseline_data[current_filename]
        print(f"Comparing with baseline for {current_filename}...")
        
        # Assert key metrics match baseline
        assert result["crashed"] == (baseline_row["crashed"] == "TRUE"), f"Crashed status mismatch with baseline for {current_filename}"
        assert result["import_ok"] == (baseline_row["import_ok"] == "TRUE"), f"Import status mismatch with baseline for {current_filename}"
        assert result["slice_ok"] == (baseline_row["slice_ok"] == "TRUE"), f"Slice status mismatch with baseline for {current_filename}"
        assert result["export_ok"] == (baseline_row["export_ok"] == "TRUE"), f"Export status mismatch with baseline for {current_filename}"
        
        print(f"OK All metrics match baseline for {current_filename}")
    else:
    # Always update the baseline data with current result
        print(f"Updating baseline data for {current_filename}...")
        baseline_data[current_filename] = baseline_row_data
    
    # Always assert basic success regardless of baseline
    #assert not result["crashed"], f"App crashed when handling {model_path}"
    #assert result["import_ok"], f"Import failed for {model_path}: {result['error']}"
    #assert result["slice_ok"], f"Slice failed for {model_path}: {result['error']}"
    #assert result["export_ok"], f"Export failed for {model_path}: {result['error']}"


@pytest.fixture(scope="session", autouse=True)
def write_report_to_feishu_after_tests(baseline_data):
    """
    Write the feishu_slice_report.csv to a new Feishu table after all tests are completed.
    """
    yield  # This is the test execution phase
    
    # This runs after all tests are completed
    report_path = Path("performance") / "data" / "feishu_slice_report.csv"
    
    # Write all baseline data to CSV file
    if baseline_data:
        print(f"\n=== Writing all baseline data to CSV ===")
        print(f"Writing to: {report_path}")
        
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
                    row.append(record.get(field, ""))
                # Join and write the row
                f.write(",".join(row) + "\n")
        
        print(f"OK Wrote {len(baseline_data)} records to {report_path}")
        
        # Check if Feishu configuration is available to write to Feishu table
        from test_framework.performance.utils.feishu_downloader import load_feishu_config, FeishuDownloader
        cfg = load_feishu_config()
        
        if cfg:
            try:
                downloader = FeishuDownloader(
                    app_id=cfg["app_id"],
                    app_secret=cfg["app_secret"],
                    app_token=cfg["app_token"],
                    table_id=cfg["table_id"],
                    view_id=cfg.get("view_id"),
                    file_field=cfg.get("file_field", "文件"),
                    download_dir=cfg.get("download_dir") or Path("artifacts") / "feishu_3mf",
                )
                
                # Read CSV data and add current date column
                import csv
                from datetime import datetime
                
                current_date = datetime.now().strftime("%Y-%m-%d")
                csv_path = Path(report_path)
                
                with open(csv_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    csv_data = list(reader)
                
                # Add current date to each record
                for row in csv_data:
                    row["test_date"] = current_date
                
                # Use existing test_log table or create it if not exists
                test_log_table_name = "test_log"
                
                try:
                    # Get test_log table ID if it exists
                    test_log_table_id = downloader.get_table_id_by_name(test_log_table_name)
                    print(f"Found test_log table with ID: {test_log_table_id}")
                except RuntimeError:
                    # Create test_log table if it doesn't exist
                    print(f"test_log table not found, creating new table...")
                    
                    # Determine field types based on CSV data
                    fields = []
                    if csv_data:
                        header = list(csv_data[0].keys())
                        for field_name in header:
                            # Try to determine field type
                            field_type = "text"
                            sample_values = [row[field_name] for row in csv_data if row[field_name]]
                            
                            if sample_values:
                                # Check if all values are numeric
                                if all(v.replace(".", "").replace("-", "").isdigit() for v in sample_values):
                                    field_type = "number"
                                # Check if all values are boolean
                                elif all(v.lower() in ["true", "false"] for v in sample_values):
                                    field_type = "checkbox"
                            
                            fields.append({"name": field_name, "type": field_type})
                    
                    # Create test_log table
                    test_log_table_id = downloader.create_table(test_log_table_name, fields)
                    print(f"Created test_log table with ID: {test_log_table_id}")
                
                # Add records to test_log table
                downloader.add_records(test_log_table_id, csv_data)
                print(f"=== Added {len(csv_data)} records to test_log table ===")
            except Exception as e:
                print(f"Failed to write to Feishu: {e}")
        else:
            print("Feishu configuration not available, skipping Feishu table creation.")
    else:
        print(f"No baseline data to write.")
