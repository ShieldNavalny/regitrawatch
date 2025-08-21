# captcha_solver/simple_click.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def try_click_recaptcha(driver, timeout=10):
    try:
        WebDriverWait(driver, timeout).until(
            EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[contains(@src, 'recaptcha')]"))
        )
        checkbox = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.ID, "recaptcha-anchor"))
        )
        checkbox.click()
        print("[captcha] Чекбокс reCAPTCHA кликнут")
        driver.switch_to.default_content()
        return True
    except Exception as e:
        print(f"[captcha] Ошибка при клике по капче: {e}")
        driver.switch_to.default_content()
        return False
