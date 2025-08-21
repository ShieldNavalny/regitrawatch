# session/keep_alive.py

import time
import threading
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from shared_lock import driver_lock


def start_keep_alive(driver, interval=60):
    def _keep_alive():
        wait = WebDriverWait(driver, 10)

        while True:
            try:
                with driver_lock:
                    driver.switch_to.window(driver.window_handles[-1])
                    driver.get("https://vp.regitra.lt/#/paslaugos")
                    wait.until(EC.url_contains("/paslaugos"))
                    print("[keep_alive] Страница обновлена.")
                time.sleep(interval)
            except Exception as e:
                print(f"[keep_alive] Ошибка: {e}")
                break

    # Открыть вкладку один раз и оставить её
    with driver_lock:
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[-1])
        driver.get("https://vp.regitra.lt/#/paslaugos")

    thread = threading.Thread(target=_keep_alive, daemon=True)
    thread.start()
