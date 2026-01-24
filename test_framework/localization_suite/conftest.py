from pathlib import Path
from typing import Iterator

import json
import os
import subprocess
import time
import sys

import pytest
import pyautogui

# 确保作为独立脚本运行时也能导入到项目根目录下的模块
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from test_framework.conftest import creality_printer_path


SUPPORTED_LANGUAGES = ("zh-CN", "en-US")

BASELINE_LANGUAGES = (
    "zh-CN",
    "en-US",
    "ca_ES",
    "zh_TW",
    "cs_CZ",
    "nl_NL",
    "en_GB",
    "fr_FR",
    "de_DE",
    "hu_HU",
    "it_IT",
    "ja_JP",
    "ko_KR",
    "pl_PL",
    "pt_BR",
    "ru_RU",
    "es_ES",
    "sv_SE",
    "tr_TR",
    "uk_UA",
)

LANG_MAP = {
    "zh-CN": "zh_CN",
    "en-US": "en_GB",
    "ca_ES": "ca_ES",
    "zh_TW": "zh_TW",
    "zh_CN": "zh_CN",
    "cs_CZ": "cs_CZ",
    "nl_NL": "nl_NL",
    "en_GB": "en_GB",
    "fr_FR": "fr_FR",
    "de_DE": "de_DE",
    "hu_HU": "hu_HU",
    "it_IT": "it_IT",
    "ja_JP": "ja_JP",
    "ko_KR": "ko_KR",
    "pl_PL": "pl_PL",
    "pt_BR": "pt_BR",
    "ru_RU": "ru_RU",
    "es_ES": "es_ES",
    "sv_SE": "sv_SE",
    "tr_TR": "tr_TR",
    "uk_UA": "uk_UA",
}


WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 900

CAPTURE_REGIONS = {
    "settings_title": (939, 805, 195, 78),
    "menu_file": (9, 36, 270, 222),
    "home_title": (242, 53, 559, 95),
    "device_title": (10, 85, 188, 37),
}


def _get_relative_coords(abs_x: int, abs_y: int, win_width: int = 1600, win_height: int = 900):
    rel_x = int(win_width * (abs_x / 1600))
    rel_y = int(win_height * (abs_y / 900))
    return rel_x, rel_y


def _normalize_window_size(width: int = 1600, height: int = 900) -> None:
    try:
        windows = pyautogui.getWindowsWithTitle("Creality Print")
        if not windows:
            windows = pyautogui.getWindowsWithTitle("CrealityPrint")
    except Exception:
        return
    if not windows:
        return
    win = windows[0]
    try:
        if getattr(win, "isMinimized", False):
            win.restore()
        if getattr(win, "isMaximized", False):
            win.restore()
        win.resizeTo(width, height)
        win.moveTo(0, 0)
    except Exception:
        return


class AppClient:
    def __init__(self, rootdir: Path) -> None:
        self.rootdir = rootdir
        self._proc = None

    @property
    def config_path(self) -> Path:
        home = Path.home()
        return home / "AppData" / "Roaming" / "Creality" / "Creality Print" / "7.0" / "Creality.conf"

    def _ensure_stopped(self) -> None:
        subprocess.run(
            ["taskkill", "/F", "/IM", "CrealityPrint.exe"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=True,
            check=False,
        )
        if self._proc is not None:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=5)
            except Exception:
                pass
            finally:
                self._proc = None

    def set_language(self, language: str) -> None:
        code = LANG_MAP.get(language)
        if not code:
            pytest.skip(f"language mapping not defined for {language}")
        cfg = self.config_path
        if not cfg.exists():
            pytest.skip(f"config file not found: {cfg}")
        text = cfg.read_text(encoding="utf-8")
        stripped = text.lstrip()
        offset = len(text) - len(stripped)
        decoder = json.JSONDecoder()
        data, end = decoder.raw_decode(stripped)
        prefix = text[:offset]
        suffix = stripped[end:]
        app_cfg = data.get("app") or {}
        app_cfg["language"] = code
        app_cfg["window_mainframe"] = "0; 0; 1600; 900; 0"
        data["app"] = app_cfg
        main_json = json.dumps(data, ensure_ascii=False, indent=4)
        cfg.write_text(prefix + main_json + suffix, encoding="utf-8")

    def restart(self) -> None:
        self._ensure_stopped()
        exe = creality_printer_path()
        self._proc = subprocess.Popen(
            [exe],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(15)
        _normalize_window_size()


def generate_ui_strings_baseline(languages=BASELINE_LANGUAGES) -> None:
    rootdir = Path(__file__).resolve().parents[2]
    resources_root = rootdir / "test_framework" / "_resources_" / "localization"
    client = AppClient(rootdir)
    win_width = WINDOW_WIDTH
    win_height = WINDOW_HEIGHT
    print(f"[baseline] rootdir={rootdir}")
    print(f"[baseline] resources_root={resources_root}")
    try:
        for language in languages:
            if language not in LANG_MAP:
                print(f"[baseline] skip language without mapping: {language}")
                continue
            print(f"[baseline] start language: {language}")
            client.set_language(language)
            client.restart()
            time.sleep(2)
            lang_dir = resources_root / language
            lang_dir.mkdir(parents=True, exist_ok=True)
            print(f"[baseline] language={language} lang_dir={lang_dir}")
            sx, sy, sw, sh = CAPTURE_REGIONS.get("settings_title", (0, 0, win_width, win_height))
            screenshot = pyautogui.screenshot(region=(sx, sy, sw, sh))
            settings_path = lang_dir / "settings_title.png"
            if not settings_path.exists():
                settings_path.parent.mkdir(parents=True, exist_ok=True)
                screenshot.save(str(settings_path))
                print(f"[baseline] language={language} saved {settings_path}")
            else:
                print(f"[baseline] language={language} exists {settings_path}, skip")
            x, y = _get_relative_coords(120, 21, win_width, win_height)
            pyautogui.click(x, y)
            time.sleep(0.5)
            mx, my, mw, mh = CAPTURE_REGIONS.get("menu_file", (0, 0, win_width, win_height))
            screenshot = pyautogui.screenshot(region=(mx, my, mw, mh))
            menu_path = lang_dir / "menu_file.png"
            if not menu_path.exists():
                menu_path.parent.mkdir(parents=True, exist_ok=True)
                screenshot.save(str(menu_path))
                print(f"[baseline] language={language} saved {menu_path}")
            else:
                print(f"[baseline] language={language} exists {menu_path}, skip")
            x, y = _get_relative_coords(27, 27, win_width, win_height)
            pyautogui.click(x, y)
            time.sleep(0.5)
            hx, hy, hw, hh = CAPTURE_REGIONS.get("home_title", (0, 0, win_width, win_height))
            screenshot = pyautogui.screenshot(region=(hx, hy, hw, hh))
            home_path = lang_dir / "home_title.png"
            if not home_path.exists():
                home_path.parent.mkdir(parents=True, exist_ok=True)
                screenshot.save(str(home_path))
                print(f"[baseline] language={language} saved {home_path}")
            else:
                print(f"[baseline] language={language} exists {home_path}, skip")
            x, y = _get_relative_coords(1035, 30, win_width, win_height)
            pyautogui.click(x, y)
            time.sleep(0.5)
            dx, dy, dw, dh = CAPTURE_REGIONS.get("device_title", (0, 0, win_width, win_height))
            screenshot = pyautogui.screenshot(region=(dx, dy, dw, dh))
            device_path = lang_dir / "device_title.png"
            if not device_path.exists():
                device_path.parent.mkdir(parents=True, exist_ok=True)
                screenshot.save(str(device_path))
                print(f"[baseline] language={language} saved {device_path}")
            else:
                print(f"[baseline] language={language} exists {device_path}, skip")
            print(f"[baseline] done language: {language}")
    finally:
        client._ensure_stopped()


if __name__ == "__main__":
    generate_ui_strings_baseline()


@pytest.fixture(scope="session")
def app_client(pytestconfig) -> AppClient:
    rootdir = Path(pytestconfig.rootdir)
    client = AppClient(rootdir)
    yield client
    client._ensure_stopped()


@pytest.fixture(params=SUPPORTED_LANGUAGES)
def language_env(request, app_client: AppClient) -> Iterator[str]:
    language = request.param
    app_client.set_language(language)
    app_client.restart()
    yield language
