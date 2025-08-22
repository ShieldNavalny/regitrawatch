# session/keep_alive.py

import time
import threading
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from shared_lock import driver_lock

session_expired = threading.Event()

def start_keep_alive(driver, interval=60):
    def _keep_alive():
        while not session_expired.is_set():
            acquired = driver_lock.acquire(timeout=1)
            if acquired:
                try:
                    driver.switch_to.window(driver.window_handles[-1])
                    driver.get("https://vp.regitra.lt/#/paslaugos")
                    print("[keep_alive] Страница обновлена.")

                    current_url = driver.current_url
                    if current_url.rstrip('/') == "https://vp.regitra.lt/#":
                        time.sleep(3)
                        if driver.current_url.rstrip('/') == "https://vp.regitra.lt/#":
                            print("[keep_alive] Сессия истекла.")
                            session_expired.set()

                except Exception as e:
                    print(f"[keep_alive] Ошибка при обновлении: {e}")
                finally:
                    driver_lock.release()
            time.sleep(interval)
            
    #Вкладка paslaugos
    with driver_lock:
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[-1])
        driver.get("https://vp.regitra.lt/#/paslaugos")
        WebDriverWait(driver, 10).until(EC.url_contains("/paslaugos"))

    thread = threading.Thread(target=_keep_alive, daemon=True)
    thread.start()
