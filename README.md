# Regitra Exam Slot Watcher

Автоматический бот для поиска и бронирования слотов экзамена на сайте [vp.regitra.lt](https://vp.regitra.lt) с использованием Selenium и 2Captcha.

## 📦 Установка

```bash
git clone https://github.com/yourname/regitra-watcher.git
cd regitra-watcher
pip install -r requirements.txt


## 🛠 Пример `config.json`

> ⚠️ Это пример с комментариями. Удалите `//` перед использованием, так как JSON не поддерживает комментарии.

```jsonc
{
  // === CONFIGURATION FILE FOR regitra watcher v2===
  // This file contains credentials, request parameters, and runtime settings.
  // DO NOT commit real credentials to version control!
  // Replace placeholder values before running.
  // For interval I recommend to use something like 3900 cause Regitra throw out slots every hour -/+

  "credentials": {
    // Swedbank BankID login credentials
    "login": "YOUR_SWEDBANK_LOGIN",         // e.g. usernameID
    "asmens_kodas": "YOUR_PERSONAL_CODE"    // Lithuanian personal ID code
  },

  "request": {
    // Request-specific parameters
    "prasymo_nr": "12345678",               // Application number (Prašymo Nr.)
    "deadline": "2025-09-01",               // Latest acceptable date (YYYY-MM-DD)
    "vehicle_type": "regitra",              // "regitra" or "nuosava" (Regitra or personal vehicle)
    "notify_only": false                    // true = only notify, false = auto-book
  },

  "settings": {
    // Runtime behavior
    "headless": true,                       // Run browser in headless mode
    "debug": false,                         // Enable debug logging and visual browser
    "check_interval_sec": 60,               // Interval between checks (in seconds)
    "timeout_sec": 30,                      // Timeout for page loads and waits
    "captchaapikey": "PASTEYOURKEYHERE"     // API key from https://2captcha.com/enterpage
  }
}
