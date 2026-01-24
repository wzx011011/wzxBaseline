from pathlib import Path

import winreg
import pytest


UNINSTALL_KEY = r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\CrealityPrint-7"


@pytest.mark.installation_suite
def test_uninstall_then_reinstall(installed_app: Path, install_controller) -> None:
    assert installed_app.exists()
    install_controller.uninstall()
    path = install_controller.install()
    assert path.exists()
    exe = path / "CrealityPrint.exe"
    assert exe.exists()
