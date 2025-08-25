# watcher/checker.py

import json
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from watcher.captcha_solver import recaptcha_2captcha
from shared_lock import driver_lock 
from notifier.telegram_bot import notify, notify_exception

def load_config(path="config.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def go_to_exam_schedule(driver):
    with driver_lock:
        config = load_config()
        prasymo_nr = config["request"]["prasymo_nr"]
        deadline_str = config["request"]["deadline"]
        notify_only = config["request"]["notify_only"]
        debug = config["settings"].get("debug", False)

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
            token = recaptcha_2captcha.solve_recaptcha(sitekey, page_url, config)
            if token:
                print("[checker] Вставляем токен...")
                recaptcha_2captcha.inject_token(driver, token)
                time.sleep(2)
                driver.find_element(By.TAG_NAME, "body").click()
                time.sleep(2)
            else:
                print("[checker] Не удалось получить токен")
                return False
        except Exception as e:
            print(f"[checker] Ошибка при обработке капчи: {e}")
            with open("debug.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            return False

        
        # Получение текущей даты экзамена из текста "Keičiamas egzaminas"
        try:
            exam_info_p = driver.find_element(By.XPATH, "//p[span[contains(text(), 'Keičiamas egzaminas')]]")
            full_text = exam_info_p.text  # "Keičiamas egzaminas 2025-09-25 12:45, Lentvario g. 7, Vilnius"
            date_part = full_text.split("Keičiamas egzaminas")[-1].strip().split(",")[0]  # "2025-09-25 12:45"
            current_exam_dt = datetime.strptime(date_part, "%Y-%m-%d %H:%M")
            print(f"[checker] Текущий экзамен: {current_exam_dt}")
        except Exception as e:
            print(f"[checker] Не удалось получить текущую дату экзамена: {e}")
            current_exam_dt = None



        # Поиск доступных слотов
        try:
            date_blocks = driver.find_elements(By.CSS_SELECTOR, ".row-top")
            month_map = {
                "Sausio": "01", "Vasario": "02", "Kovo": "03", "Balandžio": "04",
                "Gegužės": "05", "Birželio": "06", "Liepos": "07", "Rugpjūčio": "08",
                "Rugsėjo": "09", "Spalio": "10", "Lapkričio": "11", "Gruodžio": "12"
            }

            current_slot_dt = None
            debug_slots = []

            if current_exam_dt:
                current_slot_dt = current_exam_dt
                print(f"[checker] Используем текущую дату экзамена как ограничение: {current_slot_dt}")
            else:
                # Определяем текущий слот (btn-success)
                for block in date_blocks:
                    try:
                        btn = block.find_element(By.CSS_SELECTOR, "button.btn-success")
                        day_text = block.find_element(By.CSS_SELECTOR, "p.col-sm-2 b").text.strip()
                        day = day_text.replace("d.", "").strip().zfill(2)
                        month_header = block.find_element(By.XPATH, "./preceding-sibling::h4[1]").text.strip()

                        current_month = next((num for name, num in month_map.items() if name in month_header), None)
                        if not current_month:
                            continue

                        date_str = f"2025-{current_month}-{day}"
                        time_str = btn.text.strip()
                        current_slot_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                        print(f"[checker] Текущий слот (btn-success): {current_slot_dt}")
                        break
                    except:
                        continue

            if not current_slot_dt:
                current_slot_dt = deadline.replace(hour=23, minute=59)
                print(f"[checker] btn-success и текущий экзамен не найдены, используем дедлайн: {current_slot_dt}")

            # Сбор всех доступных слотов
            slots = []
            for block in date_blocks:
                try:
                    day_text = block.find_element(By.CSS_SELECTOR, "p.col-sm-2 b").text.strip()
                    day = day_text.replace("d.", "").strip().zfill(2)
                    month_header = block.find_element(By.XPATH, "./preceding-sibling::h4[1]").text.strip()
                    current_month = next((num for name, num in month_map.items() if name in month_header), None)
                    if not current_month:
                        continue

                    date_str = f"2025-{current_month}-{day}"
                    buttons = block.find_elements(By.CSS_SELECTOR, "button")

                    for btn in buttons:
                        btn_class = btn.get_attribute("class")
                        time_str = btn.text.strip()
                        if not time_str:
                            continue
                        try:
                            slot_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                            if debug:
                                debug_slots.append((slot_dt, btn_class))
                            if slot_dt < current_slot_dt:
                                slots.append((slot_dt, btn))
                        except:
                            continue
                except:
                    continue

            if debug and debug_slots:
                debug_text = "\n".join([f"{dt} — {cls}" for dt, cls in debug_slots])
                print("[debug] Найденные слоты:\n" + debug_text)
                print("[debug] Текущая дата экзамена", f"{current_slot_dt}")
                print("[debug] Дедлайн", f"{deadline}")

                notify("🛠 Debug: Найденные слоты", f"<pre>{debug_text}</pre>")
                notify("🛠 Debug: Текущая дата экзамена", f"<pre>{current_slot_dt}</pre>")
                notify("🛠 Debug: Дедлайн", f"<pre>{deadline}</pre>")


            if not slots:
                print("[checker] Нет доступных слотов раньше текущего.")
                return False

            slots.sort(key=lambda x: x[0])
            earliest_slot = slots[0]

            if notify_only:
                print(f"[checker] Найден слот: {earliest_slot[0]} (Уведомлен в TG)")
                notify("📅 Найден слот", f"Доступен слот: <b>{earliest_slot[0]}</b>")
                return True

            print(f"[checker] Бронируем слот: {earliest_slot[0]}")
            try:
                earliest_slot[1].click()
                time.sleep(1)
                continue_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Tęsti')]")))
                continue_btn.click()
                register_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Registruotis')]")))
                register_btn.click()
                print("[checker] Регистрация завершена.")
                notify("✅ Забронировано", f"Слот успешно забронирован: <b>{earliest_slot[0]}</b>")
                return True
            except Exception as e:
                print(f"[checker] Ошибка при бронировании: {e}")
                notify_exception("❌ Ошибка при бронировании CHECKER", e)
                return False

        except Exception as e:
            print(f"[checker] Ошибка при поиске или бронировании слота: {e}")
            notify_exception("❌ Ошибка при поиске или бронировании слота CHECKER", e)
            return False
