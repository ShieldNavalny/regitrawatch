# captcha_solver/recaptcha_2captcha.py

import requests
import time
import json
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


def load_config(path="config.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def inject_token(driver, token):
    driver.switch_to.default_content()

    # Найти iframe с капчей
    iframe = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='recaptcha']"))
    )
    driver.switch_to.frame(iframe)

    # Вставить токен в textarea
    driver.execute_script("""
        const textarea = document.querySelector('textarea[name="g-recaptcha-response"]');
        textarea.value = arguments[0];
        textarea.dispatchEvent(new Event('input', { bubbles: true }));
        textarea.dispatchEvent(new Event('change', { bubbles: true }));
    """, token)

    driver.switch_to.default_content()

    # Вызвать AngularJS $apply, чтобы он увидел изменения
    driver.execute_script("""
        const el = document.querySelector('form[name="examForm"]');
        if (window.angular && angular.element(el).scope()) {
            angular.element(el).scope().$apply();
        }
    """)

    time.sleep(1)


def solve_recaptcha(site_key, page_url, max_wait=120):
    config = load_config()
    API_KEY = config["settings"]["captchaapikey"]
    print("[2captcha] Отправка задачи...")

    resp = requests.post("http://2captcha.com/in.php", data={
        'key': API_KEY,
        'method': 'userrecaptcha',
        'googlekey': site_key,
        'pageurl': page_url,
        'json': 1
    })

    try:
        result = resp.json()
    except Exception as e:
        print(f"[2captcha] Ошибка JSON (in.php): {e}")
        return None

    if result['status'] != 1:
        print(f"[2captcha] Ошибка: {result}")
        return None

    request_id = result['request']
    print(f"[2captcha] Ожидание решения (ID: {request_id})...")

    for _ in range(max_wait // 5):
        time.sleep(5)
        res = requests.get("http://2captcha.com/res.php", params={
            'key': API_KEY,
            'action': 'get',
            'id': request_id,
            'json': 1
        })

        try:
            result = res.json()
        except Exception as e:
            print(f"[2captcha] Ошибка JSON (res.php): {e}")
            return None

        if result['status'] == 1:
            print("[2captcha] Решение получено")
            return result['request']
        elif result['request'] != 'CAPCHA_NOT_READY':
            print(f"[2captcha] Ошибка: {result}")
            return None

    print("[2captcha] Время ожидания истекло")
    return None
