# session/keep_alive.py

import time
import threading
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from shared_lock import driver_lock

session_expired = threading.Event()

def start_keep_alive(driver, config):
    interval = config["settings"].get("keep_alive_interval_sec", 60)

    def _keep_alive():
        while not session_expired.is_set():
            acquired = driver_lock.acquire(timeout=1)
            if acquired:
                try:
                    driver.switch_to.window(driver.window_handles[-1])
                    driver.get("https://vp.regitra.lt/#/paslaugos")
                    print("[keep_alive] Refreshed /paslaugos")

                    time.sleep(5)  # дать время на возможный редирект

                    current_url = driver.current_url.rstrip("/")
                    if current_url == "https://vp.regitra.lt/#":
                        try:
                            WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located(
                                    (By.XPATH, "//*[contains(text(), 'Prisijunk ir galėsi')]")
                                )
                            )
                            print("[keep_alive] Session expired — detected login prompt.")
                            session_expired.set()
                        except:
                            print("[keep_alive] Session expired — redirected without expected text.")
                            session_expired.set()
                    else:
                        print("[keep_alive] Session is alive.")

                except Exception as e:
                    print(f"[keep_alive] Error during keep-alive: {e}")
                finally:
                    driver_lock.release()

            time.sleep(interval)

    # Open keep-alive tab
    with driver_lock:
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[-1])
        driver.get("https://vp.regitra.lt/#/paslaugos")
        WebDriverWait(driver, 10).until(EC.url_contains("/paslaugos"))

    thread = threading.Thread(target=_keep_alive, daemon=True)
    thread.start()
