from pathlib import Path

import winreg
import pytest


UNINSTALL_KEY = r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\CrealityPrint-7"


@pytest.mark.installation_suite
def test_fresh_install_files(installed_app: Path) -> None:
    assert installed_app.exists()
    exe = installed_app / "CrealityPrint.exe"
    assert exe.exists()


@pytest.mark.installation_suite
def test_fresh_install_registry(installed_app: Path) -> None:
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, UNINSTALL_KEY) as key:
        display_name, _ = winreg.QueryValueEx(key, "DisplayName")
    assert "Creality Print" in display_name
