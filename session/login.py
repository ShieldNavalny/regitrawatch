# session/login.py

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from notifier.telegram_bot import notify


def login(driver, config):
    wait = WebDriverWait(driver, 30)

    # 1. Открыть начальную страницу
    driver.get("https://vp.regitra.lt/#/")

    # 2. Клик по иконке входа
    wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "icon-cntr"))).click()

    # 3. Ждать редиректа на epaslaugos.lt
    wait.until(EC.url_contains("epaslaugos.lt/portal/login"))

    # 4. Клик по иконке Swedbank
    banks = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "login-bank")))
    swedbank = next((b for b in banks if "Swedbank" in b.get_attribute("innerHTML")), banks[0])
    swedbank.click()

    # 5. Ждать редиректа на swedbank.lt
    wait.until(EC.url_contains("swedbank.lt"))

    # 6. Ввести Naudotojo ID и Asmens kodas
    user_id_input = wait.until(EC.element_to_be_clickable((By.NAME, "userId")))
    user_id_input.clear()
    user_id_input.send_keys(config["swedbank_id"])

    asmens_input = wait.until(EC.element_to_be_clickable((By.NAME, "identityNumber")))
    asmens_input.clear()
    asmens_input.send_keys(config["asmens_kodas"])

    # 7. Нажать Prisijungti
    driver.find_element(By.XPATH, "//button[contains(text(), 'Prisijungti')]").click()

    # 8. Ждать появления контрольного кода
    code_container = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'kontrolinis kodas')]/..")))
    # Ждём, пока в элементе появится непустой текст
    code_elem = wait.until(EC.presence_of_element_located((By.ID, "ui-signing-code-sid")))
    wait.until(lambda d: code_elem.text.strip() != "")
    code_text = code_elem.text.strip()
    print(f"[login] Ждём подтверждение входа в приложении банка. Код: {code_text}")
    notify("🔐 Вход в банк", f"Подтвердите вход в Swedbank.\nКод: <b>{code_text}</b>")


    # 9. Ждать редиректа на banklink/auth (увеличено до 5 минут)
    WebDriverWait(driver, 300).until(EC.url_contains("banklink/auth"))

    # 10. Найти и нажать кнопку отправки данных
    wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='button' and contains(@onclick, 'linkAction')]"))).click()

    # 11. Ждать попадания на страницу услуг
    wait.until(EC.url_contains("/#/paslaugos"))

    print("[login] Успешный вход")
    notify("✅ Вход выполнен", "Успешно вошли в систему Regitra.")



# Пример использования:
# from selenium import webdriver
# from session.login import login
# config = {"swedbank_id": "27673141", "asmens_kodas": "12345678901"}
# driver = webdriver.Chrome()
# login(driver, config)
