from pathlib import Path

import pyautogui
import pytest
import time


LANG_IMAGES = {
    "zh-CN": {
        "settings_title": Path("localization") / "zh-CN" / "settings_title.png",
        "menu_file": Path("localization") / "zh-CN" / "menu_file.png",
        "home_title": Path("localization") / "zh-CN" / "home_title.png",
        "device_title": Path("localization") / "zh-CN" / "device_title.png",
    },
    "en-US": {
        "settings_title": Path("localization") / "en-US" / "settings_title.png",
        "menu_file": Path("localization") / "en-US" / "menu_file.png",
        "home_title": Path("localization") / "en-US" / "home_title.png",
        "device_title": Path("localization") / "en-US" / "device_title.png",
    },
    "ca_ES": {
        "settings_title": Path("localization") / "ca_ES" / "settings_title.png",
        "menu_file": Path("localization") / "ca_ES" / "menu_file.png",
        "home_title": Path("localization") / "ca_ES" / "home_title.png",
        "device_title": Path("localization") / "ca_ES" / "device_title.png",
    },
    "zh_TW": {
        "settings_title": Path("localization") / "zh_TW" / "settings_title.png",
        "menu_file": Path("localization") / "zh_TW" / "menu_file.png",
        "home_title": Path("localization") / "zh_TW" / "home_title.png",
        "device_title": Path("localization") / "zh_TW" / "device_title.png",
    },
    "zh_CN": {
        "settings_title": Path("localization") / "zh_CN" / "settings_title.png",
        "menu_file": Path("localization") / "zh_CN" / "menu_file.png",
        "home_title": Path("localization") / "zh_CN" / "home_title.png",
        "device_title": Path("localization") / "zh_CN" / "device_title.png",
    },
    "cs_CZ": {
        "settings_title": Path("localization") / "cs_CZ" / "settings_title.png",
        "menu_file": Path("localization") / "cs_CZ" / "menu_file.png",
        "home_title": Path("localization") / "cs_CZ" / "home_title.png",
        "device_title": Path("localization") / "cs_CZ" / "device_title.png",
    },
    "nl_NL": {
        "settings_title": Path("localization") / "nl_NL" / "settings_title.png",
        "menu_file": Path("localization") / "nl_NL" / "menu_file.png",
        "home_title": Path("localization") / "nl_NL" / "home_title.png",
        "device_title": Path("localization") / "nl_NL" / "device_title.png",
    },
    "en_GB": {
        "settings_title": Path("localization") / "en_GB" / "settings_title.png",
        "menu_file": Path("localization") / "en_GB" / "menu_file.png",
        "home_title": Path("localization") / "en_GB" / "home_title.png",
        "device_title": Path("localization") / "en_GB" / "device_title.png",
    },
    "fr_FR": {
        "settings_title": Path("localization") / "fr_FR" / "settings_title.png",
        "menu_file": Path("localization") / "fr_FR" / "menu_file.png",
        "home_title": Path("localization") / "fr_FR" / "home_title.png",
        "device_title": Path("localization") / "fr_FR" / "device_title.png",
    },
    "de_DE": {
        "settings_title": Path("localization") / "de_DE" / "settings_title.png",
        "menu_file": Path("localization") / "de_DE" / "menu_file.png",
        "home_title": Path("localization") / "de_DE" / "home_title.png",
        "device_title": Path("localization") / "de_DE" / "device_title.png",
    },
    "hu_HU": {
        "settings_title": Path("localization") / "hu_HU" / "settings_title.png",
        "menu_file": Path("localization") / "hu_HU" / "menu_file.png",
        "home_title": Path("localization") / "hu_HU" / "home_title.png",
        "device_title": Path("localization") / "hu_HU" / "device_title.png",
    },
    "it_IT": {
        "settings_title": Path("localization") / "it_IT" / "settings_title.png",
        "menu_file": Path("localization") / "it_IT" / "menu_file.png",
        "home_title": Path("localization") / "it_IT" / "home_title.png",
        "device_title": Path("localization") / "it_IT" / "device_title.png",
    },
    "ja_JP": {
        "settings_title": Path("localization") / "ja_JP" / "settings_title.png",
        "menu_file": Path("localization") / "ja_JP" / "menu_file.png",
        "home_title": Path("localization") / "ja_JP" / "home_title.png",
        "device_title": Path("localization") / "ja_JP" / "device_title.png",
    },
    "ko_KR": {
        "settings_title": Path("localization") / "ko_KR" / "settings_title.png",
        "menu_file": Path("localization") / "ko_KR" / "menu_file.png",
        "home_title": Path("localization") / "ko_KR" / "home_title.png",
        "device_title": Path("localization") / "ko_KR" / "device_title.png",
    },
    "pl_PL": {
        "settings_title": Path("localization") / "pl_PL" / "settings_title.png",
        "menu_file": Path("localization") / "pl_PL" / "menu_file.png",
        "home_title": Path("localization") / "pl_PL" / "home_title.png",
        "device_title": Path("localization") / "pl_PL" / "device_title.png",
    },
    "pt_BR": {
        "settings_title": Path("localization") / "pt_BR" / "settings_title.png",
        "menu_file": Path("localization") / "pt_BR" / "menu_file.png",
        "home_title": Path("localization") / "pt_BR" / "home_title.png",
        "device_title": Path("localization") / "pt_BR" / "device_title.png",
    },
    "ru_RU": {
        "settings_title": Path("localization") / "ru_RU" / "settings_title.png",
        "menu_file": Path("localization") / "ru_RU" / "menu_file.png",
        "home_title": Path("localization") / "ru_RU" / "home_title.png",
        "device_title": Path("localization") / "ru_RU" / "device_title.png",
    },
    "es_ES": {
        "settings_title": Path("localization") / "es_ES" / "settings_title.png",
        "menu_file": Path("localization") / "es_ES" / "menu_file.png",
        "home_title": Path("localization") / "es_ES" / "home_title.png",
        "device_title": Path("localization") / "es_ES" / "device_title.png",
    },
    "sv_SE": {
        "settings_title": Path("localization") / "sv_SE" / "settings_title.png",
        "menu_file": Path("localization") / "sv_SE" / "menu_file.png",
        "home_title": Path("localization") / "sv_SE" / "home_title.png",
        "device_title": Path("localization") / "sv_SE" / "device_title.png",
    },
    "tr_TR": {
        "settings_title": Path("localization") / "tr_TR" / "settings_title.png",
        "menu_file": Path("localization") / "tr_TR" / "menu_file.png",
        "home_title": Path("localization") / "tr_TR" / "home_title.png",
        "device_title": Path("localization") / "tr_TR" / "device_title.png",
    },
    "uk_UA": {
        "settings_title": Path("localization") / "uk_UA" / "settings_title.png",
        "menu_file": Path("localization") / "uk_UA" / "menu_file.png",
        "home_title": Path("localization") / "uk_UA" / "home_title.png",
        "device_title": Path("localization") / "uk_UA" / "device_title.png",
    },
}


def _get_relative_coords(abs_x: int, abs_y: int, win_width: int = 1600, win_height: int = 900):
    rel_x = int(win_width * (abs_x / 1600))
    rel_y = int(win_height * (abs_y / 900))
    return rel_x, rel_y


def _locate_image(path: Path, region=None):
    try:
        return pyautogui.locateOnScreen(str(path), confidence=0.9, region=region)
    except NotImplementedError:
        try:
            return pyautogui.locateOnScreen(str(path), region=region)
        except pyautogui.ImageNotFoundException:
            return None
    except pyautogui.ImageNotFoundException:
        return None


@pytest.mark.localization_suite
@pytest.mark.parametrize("language_env", list(LANG_IMAGES.keys()), indirect=True)
def test_settings_title_translated(language_env: str, test_resources_path: str) -> None:
    lang = language_env
    base = Path(test_resources_path)
    img_path = base / LANG_IMAGES[lang]["settings_title"]
    if not img_path.exists():
        pytest.skip(f"baseline image not found: {img_path}")
    region = None
    location = _locate_image(img_path, region=region)
    assert location is not None


@pytest.mark.localization_suite
@pytest.mark.parametrize("language_env", list(LANG_IMAGES.keys()), indirect=True)
def test_menu_language_switched(language_env: str, test_resources_path: str) -> None:
    x, y = _get_relative_coords(91, 23)
    pyautogui.click(x, y)
    time.sleep(0.5)
    lang = language_env
    base = Path(test_resources_path)
    target_img = base / LANG_IMAGES[lang]["menu_file"]
    if not target_img.exists():
        pytest.skip(f"baseline image not found: {target_img}")
    region = None
    target_location = _locate_image(target_img, region=region)
    assert target_location is not None
    other_lang = "en-US" if lang == "zh-CN" else "zh-CN"
    other_img = base / LANG_IMAGES[other_lang]["menu_file"]
    if other_img.exists():
        other_location = _locate_image(other_img, region=region)
        assert other_location is None


@pytest.mark.localization_suite
@pytest.mark.parametrize("language_env", list(LANG_IMAGES.keys()), indirect=True)
def test_home_title_translated(language_env: str, test_resources_path: str) -> None:
    x, y = _get_relative_coords(26, 22)
    pyautogui.click(x, y)
    time.sleep(0.5)
    lang = language_env
    base = Path(test_resources_path)
    img_path = base / LANG_IMAGES[lang]["home_title"]
    if not img_path.exists():
        pytest.skip(f"baseline image not found: {img_path}")
    region = None
    location = _locate_image(img_path, region=region)
    assert location is not None


@pytest.mark.localization_suite
@pytest.mark.parametrize("language_env", list(LANG_IMAGES.keys()), indirect=True)
def test_device_title_translated(language_env: str, test_resources_path: str) -> None:
    x, y = _get_relative_coords(980, 20)
    pyautogui.click(x, y)
    time.sleep(0.5)
    lang = language_env
    base = Path(test_resources_path)
    img_path = base / LANG_IMAGES[lang]["device_title"]
    if not img_path.exists():
        pytest.skip(f"baseline image not found: {img_path}")
    region = None
    location = _locate_image(img_path, region=region)
    assert location is not None
