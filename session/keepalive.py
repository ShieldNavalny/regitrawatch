# session/keep_alive.py

import time
import threading
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from shared_lock import driver_lock


def start_keep_alive(driver, interval=60):
    def _keep_alive():
        while True:
            acquired = driver_lock.acquire(timeout=1)
            if acquired:
                try:
                    driver.switch_to.window(driver.window_handles[-1])
                    driver.refresh()
                    print("[keep_alive] Страница обновлена.")
                except Exception as e:
                    print(f"[keep_alive] Ошибка при обновлении: {e}")
                finally:
                    driver_lock.release()
            time.sleep(interval)

    # Открыть вкладку один раз и оставить её на /paslaugos
    with driver_lock:
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[-1])
        driver.get("https://vp.regitra.lt/#/paslaugos")
        WebDriverWait(driver, 10).until(EC.url_contains("/paslaugos"))

    thread = threading.Thread(target=_keep_alive, daemon=True)
    thread.start()
