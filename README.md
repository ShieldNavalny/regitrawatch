# 🇱🇹 Regitra Exam Slot Watcher

A Python bot that automatically searches for and optionally books available exam slots on [vp.regitra.lt](https://vp.regitra.lt), using **Selenium**, **2Captcha**, and **Telegram notifications**.

---

## 🚀 Features

- 🔐 Automated login via Swedbank App
- 🤖 CAPTCHA solving with [2Captcha](https://2captcha.com/)
- 📅 Slot search and optional auto-booking
- 📲 Telegram notifications (start, login, slot found, errors, etc.)
- ♻️ Keep-alive and retry logic for long-running sessions
- 🧪 Headless mode support for background operation

---

## 📦 Installation

```bash
git clone https://github.com/yourname/regitra-watcher.git
cd regitra-watcher
pip install -r requirements.txt
python ./main.py
```


---

## 📲 Telegram Notifications

If enabled, the bot will send messages to allowed users:

- Start of the script
- Login prompts (with confirmation code)
- Errors and exceptions
- Slot found (with details)

To receive notifications:

1. Set `"enabled": true` in the `telegram` config section.
2. Add your `@username` to the `usernames` list.
3. Add a Telegram Bot API key from @BotFather
4. Start a chat with your bot and send `/start`.

> No restart is needed after `/start`, unless you change the config file.

---


## ⚙️ Configuration Reference (`config.json`)

### 🔐 `credentials`

```json
"credentials": {
  "login": "YOUR_SWEDBANK_LOGIN",
  "asmens_kodas": "YOUR_PERSONAL_CODE"
}
```

| Key             | Type   | Description                                      |
|------------------|--------|--------------------------------------------------|
| `login`          | string | Swedbank username                                |
| `asmens_kodas`   | string | Lithuanian personal ID code (Asmens kodas)       |

---

### 📄 `request`

```json
"request": {
  "prasymo_nr": "12345678",
  "deadline": "2025-09-01",
  "vehicle_type": "regitra",
  "notify_only": false
}
```

| Key             | Type    | Description                                                                 |
|------------------|---------|-----------------------------------------------------------------------------|
| `prasymo_nr`     | string  | Application number (Prašymo Nr.) from Regitra                              |
| `deadline`       | string  | Latest acceptable exam date (format: `YYYY-MM-DD`)                         |
| `vehicle_type`   | string  | `"regitra"` (Regitra vehicle) or `"own"` (personal vehicle) or `"both"` for both. If you want to disable this input anything else            |
| `notify_only`    | boolean | If `true`, only notifies; if `false`, attempts to auto-book                |

---

### ⚙️ `settings`

```json
"settings": {
  "headless": true,
  "debug": false,
  "check_interval_sec": 60,
  "timeout_sec": 30,
  "keep_alive_interval_sec": 30,
  "captcha_max_wait_sec": 240,
  "captchaapikey": "PASTEYOURKEYHERE",
  "retry_on_fail": true,
  "retry_on_success": true
}
```

| Key                     | Type    | Description                                                                 |
|--------------------------|---------|-----------------------------------------------------------------------------|
| `headless`               | boolean | Run browser in headless mode (no GUI)                                      |
| `debug`                  | boolean | Show browser and verbose logs even if headless                             |
| `check_interval_sec`     | integer | Interval between slot checks (in seconds)                                  |
| `timeout_sec`            | integer | Timeout for page loading and waits                                         |
| `keep_alive_interval_sec`| integer | Interval to refresh session and keep it alive                              |
| `captcha_max_wait_sec`   | integer | Max time to wait for CAPTCHA solving                                       |
| `captchaapikey`          | string  | API key from [2Captcha](https://2captcha.com/)                             |
| `retry_on_fail`          | boolean | Retry on errors (e.g. login failure, timeout)                              |
| `retry_on_success`       | boolean | Continue checking after successful booking or notification                 |

---

### 📲 `telegram`

```json
"telegram": {
  "enabled": false,
  "token": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
  "usernames": ["@your_username", "@friend_username"]
}
```

| Key         | Type     | Description                                                             |
|--------------|----------|-------------------------------------------------------------------------|
| `enabled`    | boolean  | Enable or disable Telegram notifications                               |
| `token`      | string   | Bot token from [@BotFather](https://t.me/BotFather)                    |
| `usernames`  | string[] | List of allowed Telegram usernames (must start with `@`)               |

> Users must send `/start` to the bot to begin receiving messages.

---

## 🧩 Dependencies

```
selenium>=4.20.0  
requests>=2.31.0  
undetected-chromedriver>=3.5.5  
python-telegram-bot>=20.7  
```

---

## 🧠 Notes
- Regitra will kick you out of session after some time no matter what you do. So you should keep your phone under your hand 
- CAPTCHA solving is done via 2Captcha — make sure your balance is sufficient.
- The script is designed to run continuously and re-authenticate if needed.

---

## 🛡 Disclaimer

This project is for educational purposes only. Use at your own risk.  
You are responsible for complying with Regitra's terms of service.

---

## 📄 License
GPL 3.0
