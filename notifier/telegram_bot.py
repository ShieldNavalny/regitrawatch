# notifier/telegram_bot.py

import json
import traceback
from datetime import datetime
from telegram import Bot, Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes
import threading
import asyncio

_config = None
_bot = None
_user_map_file = "telegram_users.json"
_user_map = {}
_app_started = False

def load_config():
    global _config
    if _config is None:
        with open("config.json", "r", encoding="utf-8") as f:
            _config = json.load(f)
    return _config

def get_bot():
    global _bot
    if _bot is None:
        cfg = load_config()
        _bot = Bot(token=cfg["telegram"]["token"])
    return _bot

def load_user_map():
    global _user_map
    try:
        with open(_user_map_file, "r", encoding="utf-8") as f:
            _user_map = json.load(f)
    except FileNotFoundError:
        _user_map = {}

def save_user_map():
    with open(_user_map_file, "w", encoding="utf-8") as f:
        json.dump(_user_map, f, indent=2)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username
    user_id = update.effective_user.id
    if not username:
        await update.message.reply_text("У вас не установлен username в Telegram.")
        return

    load_user_map()
    _user_map[f"@{username}"] = user_id
    save_user_map()
    await update.message.reply_text("✅ Вы зарегистрированы для получения уведомлений.")

def start_bot_polling():
    global _app_started
    if _app_started:
        return
    _app_started = True

    cfg = load_config()
    if not cfg.get("telegram", {}).get("enabled", False):
        return

    load_user_map()

    async def run():
        app = Application.builder().token(cfg["telegram"]["token"]).build()
        app.add_handler(CommandHandler("start", start_handler))
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        # Бот будет работать в фоне, пока жив event loop
        while True:
            await asyncio.sleep(3600)

    def runner():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run())

    threading.Thread(target=runner, daemon=True).start()

def notify(title: str, message: str, is_error=False):
    cfg = load_config()
    if not cfg.get("telegram", {}).get("enabled", False):
        return
    if is_error and not cfg["settings"].get("debug", False):
        return

    load_user_map()
    allowed_usernames = cfg["telegram"].get("usernames", [])
    recipients = [uid for uname, uid in _user_map.items() if uname in allowed_usernames]

    if not recipients:
        return

    bot = get_bot()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = f"📢 <b>{title}</b>\n🕒 <i>{now}</i>\n\n{message}"

    async def send_all():
        for user_id in recipients:
            try:
                await bot.send_message(chat_id=user_id, text=text, parse_mode=ParseMode.HTML)
            except Exception as e:
                print(f"[telegram] Ошибка отправки {user_id}: {e}")

    # Запускаем асинхронную отправку в фоне
    try:
        loop = asyncio.get_running_loop()
        asyncio.run_coroutine_threadsafe(send_all(), loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(send_all())

        
def notify_exception(title: str, exc: Exception):
    tb = traceback.format_exc()
    message = f"<code>{str(exc)}</code>\n\n<pre>{tb}</pre>"
    notify(title, message, is_error=True)

