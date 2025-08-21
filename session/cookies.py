# session/cookies.py

import json
from pathlib import Path
from selenium.webdriver.chrome.webdriver import WebDriver


def save_cookies(driver: WebDriver, path: str = "sessions/cookies.json") -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(driver.get_cookies(), f, indent=2)


def load_cookies(driver: WebDriver, path: str = "sessions/cookies.json") -> None:
    if not Path(path).exists():
        raise FileNotFoundError(f"Cookie file not found: {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        cookies = json.load(f)

    for cookie in cookies:
        # Удалим поля, которые могут вызвать траблы
        cookie.pop("sameSite", None)
        cookie.pop("expiry", None)
        try:
            driver.add_cookie(cookie)
        except Exception:
            pass  # Иногда куки не применяются до загрузки сайта


def cookies_exist(path: str = "sessions/cookies.json") -> bool:
    return Path(path).exists()
