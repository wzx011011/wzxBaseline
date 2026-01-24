from pathlib import Path
from typing import Iterator, Optional

import json
import os
import subprocess
import time
import winreg

import pytest


PRODUCT_UNINSTALL_KEY = r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\CrealityPrint-7"


def _default_install_dir() -> Path:
    base = os.environ.get("ProgramW6432") or os.environ.get("ProgramFiles")
    if not base:
        return Path(r"C:\Program Files") / "Creality" / "Creality Print 7.0 Beta"
    return Path(base) / "Creality" / "Creality Print 7.0 Beta"


def _read_uninstall_string() -> Optional[str]:
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, PRODUCT_UNINSTALL_KEY) as key:
            value, _ = winreg.QueryValueEx(key, "UninstallString")
            return value
    except FileNotFoundError:
        return None
    except OSError:
        return None


def _run_uninstaller() -> None:
    cmd = _read_uninstall_string()
    if not cmd:
        return
    if cmd.strip().startswith('"'):
        full = f"{cmd} /S"
    else:
        full = f'"{cmd}" /S'
    subprocess.run(full, shell=True, check=False)
    time.sleep(5)


def _run_installer(path: Path) -> None:
    result = subprocess.run([str(path), "/S"], check=False)
    if result.returncode != 0:
        pytest.fail(f"Installer exited with code {result.returncode}")
    time.sleep(10)


class InstallController:
    def __init__(self, installer: Path) -> None:
        self.installer = installer

    def install(self) -> Path:
        _run_uninstaller()
        _run_installer(self.installer)
        return _default_install_dir()

    def uninstall(self) -> None:
        _run_uninstaller()


@pytest.fixture(scope="session")
def installer_path(pytestconfig) -> Path:
    value = pytestconfig.getoption("--installer-path")
    if not value:
        pytest.skip("installer_path not provided; use --installer-path")
    path = Path(value).resolve()
    if not path.exists():
        pytest.skip(f"installer not found: {path}")
    return path


@pytest.fixture(scope="session", autouse=True)
def verify_installer_signature(installer_path: Path) -> None:
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            f"Get-AuthenticodeSignature '{str(installer_path)}' | ConvertTo-Json",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(f"Signature check failed: {result.stderr or result.stdout}")
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        pytest.fail("Failed to parse installer signature information")
    if isinstance(data, list) and data:
        info = data[0]
    else:
        info = data
    status = info.get("Status")
    if isinstance(status, int):
        if status != 0:
            pytest.fail(f"Installer signature invalid: {status}")
        return
    if isinstance(status, str):
        if status.lower() not in ("valid", "0"):
            pytest.fail(f"Installer signature invalid: {status}")
        return


@pytest.fixture(scope="session")
def install_controller(installer_path: Path) -> InstallController:
    return InstallController(installer_path)


@pytest.fixture
def installed_app(install_controller: InstallController) -> Iterator[Path]:
    path = install_controller.install()
    yield path
