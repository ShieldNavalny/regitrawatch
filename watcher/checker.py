# watcher/checker.py

import json
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.select import Select
from selenium.webdriver.support import expected_conditions as EC
from watcher.captcha_solver import recaptcha_2captcha
from shared_lock import driver_lock 

def load_config(path="config.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def go_to_exam_schedule(driver):
    with driver_lock:  # KeepAlive sort
        config = load_config()
        prasymo_nr = config["request"]["prasymo_nr"]
        deadline_str = config["request"]["deadline"]
        vehicle_type = config["request"]["vehicle_type"]
        notify_only = config["request"]["notify_only"]

        deadline = datetime.strptime(deadline_str, "%Y-%m-%d")
        wait = WebDriverWait(driver, 10)

        exam_url = f"https://vp.regitra.lt/#/egzaminas/{prasymo_nr}"
        print(f"[checker] Переход на {exam_url}")
        driver.get(exam_url)

        try:
            edit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Keisti datą ir laiką')]")))
            print("[checker] Кнопка найдена, кликаем...")
            edit_button.click()
        except Exception as e:
            print(f"[checker] Не удалось найти кнопку: {e}")
            return False

        try:
            wait.until(EC.url_contains("/registracija/tvarkarastis"))
            print("[checker] Успешный переход на страницу расписания.")
        except Exception as e:
            print(f"[checker] Не удалось перейти на страницу расписания: {e}")
            return False

        # Решение капчи
        try:
            print("[checker] Ожидание появления iframe с капчей...")
            iframe = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='recaptcha']"))
            )
            src = iframe.get_attribute("src")
            sitekey = src.split("k=")[1].split("&")[0]
            page_url = driver.current_url

            print(f"[checker] Найден sitekey: {sitekey}")
            print("[checker] Решаем капчу через 2Captcha...")
            token = recaptcha_2captcha.solve_recaptcha(sitekey, page_url)
            if token:
                print("[checker] Вставляем токен...")
                recaptcha_2captcha.inject_token(driver, token)
                time.sleep(2)
                driver.find_element(By.TAG_NAME, "body").click()  # триггерим событие
                time.sleep(2)
            else:
                print("[checker] Не удалось получить токен")
                return False
        except Exception as e:
            print(f"[checker] Ошибка при обработке капчи: {e}")
            with open("debug.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            return False

        # Проверка типа транспорта
        try:
            select_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "select")))
            select = Select(select_elem)
            if vehicle_type == "regitra":
                select.select_by_visible_text('pateiks AB "Regitra"')
            else:
                select.select_by_visible_text("pateiksiu pats")
            print(f"[checker] Установлен тип транспорта: {vehicle_type}")
            time.sleep(1)
        except Exception as e:
            print(f"[checker] Не удалось установить тип транспорта: {e}")
            return False

        # Поиск доступных слотов
        try:
            slots = []
            date_blocks = driver.find_elements(By.CSS_SELECTOR, ".col-md-12 > div > div")
            for block in date_blocks:
                try:
                    date_text = block.find_element(By.TAG_NAME, "strong").text.strip()
                    date_obj = datetime.strptime(date_text.split(" ")[0] + ".2025", "%d.%m.%Y")
                    if date_obj > deadline:
                        continue
                    time_buttons = block.find_elements(By.TAG_NAME, "button")
                    for btn in time_buttons:
                        if btn.is_enabled():
                            slots.append((date_obj, btn))
                except Exception:
                    continue

            if not slots:
                print("[checker] Нет доступных слотов до дедлайна.")
                return False

            slots.sort(key=lambda x: x[0])
            earliest_slot = slots[0]

            if notify_only:
                print(f"[checker] Найден слот: {earliest_slot[0].date()} (уведомление TODO)")
                return True

            print(f"[checker] Бронируем слот: {earliest_slot[0].date()}")
            earliest_slot[1].click()
            time.sleep(1)

            continue_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Tęsti')]")))
            continue_btn.click()

            register_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Registruotis')]")))
            register_btn.click()

            print("[checker] Регистрация завершена.")
            return True

        except Exception as e:
            print(f"[checker] Ошибка при поиске или бронировании слота: {e}")
            return False
