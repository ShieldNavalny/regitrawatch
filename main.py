# main.py

import json
import time
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from session.cookies import cookies_exist, load_cookies, save_cookies
from session.login import login
from session.keepalive import start_keep_alive
from watcher.checker import go_to_exam_schedule
from session.keepalive import start_keep_alive, session_expired
from notifier.telegram_bot import notify, notify_exception, start_bot_polling



def load_config(path="config.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def create_driver(config):
    options = uc.ChromeOptions()
    if config["settings"]["headless"]:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

    driver = uc.Chrome(options=options, headless=config["settings"]["headless"])
    driver.set_page_load_timeout(config["settings"]["timeout_sec"])
    return driver



def accept_cookies(driver, timeout=10):
    try:
        print("[cookies] Ждём появления кнопки 'Принять все'...")
        btn = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.cmpboxbtnyes"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
        driver.execute_script("arguments[0].click();", btn)
        print("[cookies] Клик по кнопке 'Принять все' выполнен.")

        WebDriverWait(driver, timeout).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.cmpboxinner"))
        )
        print("[cookies] Баннер исчез.")
    except Exception as e:
        print(f"[cookies] Не удалось принять куки: {e}")


def main():
    config = load_config()
    start_bot_polling()
    notify("🟢 Бот запущен", "Начинаем мониторинг Regitra.")

    while True:
        driver = create_driver(config)
        session_expired.clear()
        prasymo_nr = config["request"]["prasymo_nr"]

        try:
            if cookies_exist():
                print("[main] Загружаем cookies...")
                driver.get("https://vp.regitra.lt/")
                accept_cookies(driver)
                load_cookies(driver)
                driver.get(f"https://vp.regitra.lt/#/egzaminas/{prasymo_nr}")
                time.sleep(2)

                try:
                    WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Keisti datą ir laiką')]"))
                    )
                    print("[main] Cookies валидны.")
                except Exception:
                    print("[main] Cookies устарели, очищаем сессию...")
                    driver.delete_all_cookies()
                    driver.execute_script("window.localStorage.clear(); window.sessionStorage.clear();")
                    driver.get("https://vp.regitra.lt/")
                    time.sleep(2)

                    print("[main] Повторный вход через Swedbank...")
                    login(driver, {
                        "swedbank_id": config["credentials"]["login"],
                        "asmens_kodas": config["credentials"]["asmens_kodas"]
                    })
                    save_cookies(driver)
            else:
                print("[main] Вход через Swedbank...")
                login(driver, {
                    "swedbank_id": config["credentials"]["login"],
                    "asmens_kodas": config["credentials"]["asmens_kodas"]
                })
                save_cookies(driver)

            start_keep_alive(driver, config)

            while True:
                if session_expired.is_set():
                    notify("⚠️ Сессия истекла", "Regitra выкинула нас — перезапускаем.")
                    raise Exception("Сессия Regitra истекла")

                print("[main] Проверка расписания...")
                success = go_to_exam_schedule(driver)
                if success:
                    print("[main] Слот найден или регистрация выполнена.")
                    if not config["settings"].get("retry_on_success", False):
                        return
                    print("[main] Повторный поиск включён — продолжаем мониторинг...")

                if session_expired.is_set():
                    notify("⚠️ Сессия истекла", "Regitra выкинула нас — перезапускаем.")
                    raise Exception("Сессия Regitra истекла")

                print("[main] Повтор через", config["settings"]["check_interval_sec"], "секунд...")
                time.sleep(config["settings"]["check_interval_sec"])

        except Exception as e:
            print(f"[main] Ошибка: {e}")
            notify_exception("❌ Ошибка в main", e)
            if not config["settings"].get("retry_on_fail", False):
                break
            print("[main] Перезапуск из-за ошибки...")
            time.sleep(5)

        finally:
            driver.quit()



if __name__ == "__main__":
    main()
