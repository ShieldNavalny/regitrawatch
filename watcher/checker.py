# watcher/checker.py

import json
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from watcher.captcha_solver import recaptcha_2captcha
from shared_lock import driver_lock 
from notifier.telegram_bot import notify, notify_exception

def load_config(path="config.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def select_vehicle_type(driver, vehicle_type):
    try:
        wait = WebDriverWait(driver, 10)
        config = load_config()
        debug = config["settings"].get("debug", False)

        if vehicle_type not in ("regitra", "own", "both"):
            print(f"[checker] Неизвестный тип транспорта '{vehicle_type}', выбор пропущен.")
            return True  # Пропускаем выбор, продолжаем скрипт
        
        # Кликаем по дропдауну
        dropdown_btn = wait.until(EC.element_to_be_clickable((By.ID, "tp_owner")))
        driver.execute_script("arguments[0].click();", dropdown_btn)
        time.sleep(1)

        # Читаем опции
        options = driver.find_elements(By.CSS_SELECTOR, "ul.dropdown-menu li a")
        available = {}
        for opt in options:
            text = opt.text.strip()
            if "Regitra" in text:
                available["regitra"] = opt
            elif "pateiksiu" in text:
                available["own"] = opt

        if debug:
            print(f"[debug] Найдено опций: {len(available)}")

        # Если одна опция — не выбираем
        if len(available) == 1:
            print("[checker] Только один вариант транспорта, выбор не требуется.")
            return True

        # Если две и более — закрываем капчу
        try:
            close_btn = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Uždaryti')]"))
            )
            close_btn.click()
            print("[checker] Закрыта капча.")
            WebDriverWait(driver, 5).until_not(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[uib-modal-window]"))
            )
        except:
            print("[checker] Капча не найдена или уже закрыта.")

        # Определяем текущий выбор
        current = driver.find_element(By.ID, "tp_owner").text.strip().lower()

        def click_update_button():
            try:
                update_btn = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//button[@ng-click='openModal()']"))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", update_btn)
                time.sleep(0.3)
                driver.execute_script("arguments[0].click();", update_btn)
                print("[checker] Клик по кнопке 'Atnaujinti tvarkaraštį' через JS.")
            except Exception as e:
                print(f"[checker] Кнопка обновления не найдена или недоступна: {e}")


        if vehicle_type == "regitra" and "regitra" not in current:
            driver.execute_script("""
                var scope = angular.element(document.querySelector('[ng-click="setOwner(\\'regitros_tp\\')"]')).scope();
                scope.$apply(function() {
                    scope.setOwner('regitros_tp');
                });
            """)
            print("[checker] Выбран транспорт: Regitra")
            return True

        elif vehicle_type == "own" and "pateiksiu" not in current:
            driver.execute_script("""
                var scope = angular.element(document.querySelector('[ng-click="setOwner(\\'asmenine_tp\\')"]')).scope();
                scope.$apply(function() {
                    scope.setOwner('asmenine_tp');
                });
            """)
            print("[checker] Выбран транспорт: Own")
            return True

        elif vehicle_type == "both":
            if "regitra" in available and "regitra" not in current:
                driver.execute_script("""
                    var scope = angular.element(document.querySelector('[ng-click="setOwner(\\'regitros_tp\\')"]')).scope();
                    scope.$apply(function() {
                        scope.setOwner('regitros_tp');
                    });
                """)
                print("[checker] Выбран транспорт: Regitra (both)")
                return "regitra"
            elif "own" in available and "pateiksiu" not in current:
                driver.execute_script("""
                    var scope = angular.element(document.querySelector('[ng-click="setOwner(\\'asmenine_tp\\')"]')).scope();
                    scope.$apply(function() {
                        scope.setOwner('asmenine_tp');
                    });
                """)
                print("[checker] Выбран транспорт: Own (both)")
                return "own"

        print("[checker] Транспорт уже выбран, ничего не меняем.")
        click_update_button()
        return True

    except Exception as e:
        print(f"[checker] Ошибка при выборе транспорта: {e}")
        return False


def go_to_exam_schedule(driver, vehicle_override=None):
    with driver_lock:
        config = load_config()
        prasymo_nr = config["request"]["prasymo_nr"]
        deadline_str = config["request"]["deadline"]
        notify_only = config["request"]["notify_only"]
        debug = config["settings"].get("debug", False)
        vehicle_type = vehicle_override or config["request"].get("vehicle_type", "regitra")

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

        # Выбор транспорта
        selected_type = select_vehicle_type(driver, vehicle_type)
        if not selected_type:
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
            return False

        # Получение текущей даты экзамена
        try:
            exam_info_p = driver.find_element(By.XPATH, "//p[span[contains(text(), 'Keičiamas egzaminas')]]")
            full_text = exam_info_p.text
            date_part = full_text.split("Keičiamas egzaminas")[-1].strip().split(",")[0]
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

            current_slot_dt = current_exam_dt or deadline.replace(hour=23, minute=59)
            print(f"[checker] Ограничение по дате: {current_slot_dt}")

            slots = []
            debug_slots = []

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
                        time_str = btn.text.strip()
                        if not time_str:
                            continue
                        try:
                            slot_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                            if debug:
                                debug_slots.append((slot_dt, btn.get_attribute("class")))
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
                notify("📅 Найден слот", f"Доступен слот: <b>{earliest_slot[0]}</b>")
                return True

            print(f"[checker] Бронируем слот: {earliest_slot[0]}")
            try:
                earliest_slot[1].click()
                time.sleep(1)
                wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Tęsti')]"))).click()
                wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Registruotis')]"))).click()
                notify("✅ Забронировано", f"Слот успешно забронирован: <b>{earliest_slot[0]}</b>")
                return True
            except Exception as e:
                notify_exception("❌ Ошибка при бронировании", e)
                return False

        except Exception as e:
            notify_exception("❌ Ошибка при поиске слота", e)
            return False

# Для режима "both"
def run_checker_with_both(driver):
    for option in ["regitra", "own"]:
        print(f"[checker] Попытка с вариантом: {option}")
        success = go_to_exam_schedule(driver, vehicle_override=option)
        if success:
            return True
    return False
