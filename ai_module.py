# -*- coding: utf-8 -*-
# Persian Lux Smart AI v2 – For Mohammad 👑
# ماژول هوش مصنوعی با کنترل روشن/خاموش، محدودیت پیام و شارژ سودو

import os, json, time, logging
import openai
from telebot import TeleBot

# ================= ⚙️ تنظیمات پایه =================
BOT_TOKEN   = os.environ.get("BOT_TOKEN")
OPENAI_KEY  = os.environ.get("OPENAI_API_KEY")
SUDO_ID     = int(os.environ.get("SUDO_ID", "0"))

bot = TeleBot(BOT_TOKEN, parse_mode="HTML")
openai.api_key = OPENAI_KEY

DATA_FILE = "ai_data.json"
LOG_FILE  = "ai_error.log"

logging.basicConfig(filename=LOG_FILE, level=logging.ERROR,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# ================= 💾 داده‌ها =================
def load_data():
    if not os.path.exists(DATA_FILE):
        save_data({"active": False, "users": {}})
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ================= 🔘 روشن / خاموش =================
@bot.message_handler(func=lambda m: m.text and m.text.strip() in ["ربات روشن", "ربات خاموش"])
def toggle_ai(m):
    data = load_data()
    uid = m.from_user.id

    if uid != SUDO_ID:
        return bot.reply_to(m, "⚙️ فقط سازنده می‌تواند ربات را روشن یا خاموش کند.")

    if m.text.strip() == "ربات روشن":
        data["active"] = True
        bot.send_message(m.chat.id, "🤖 ربات هوش مصنوعی فعال شد!\nچه کمکی می‌تونم بکنم؟ 🌸")
    else:
        data["active"] = False
        bot.send_message(m.chat.id, "🛑 ربات خاموش شد و دیگر پاسخی نخواهد داد.")
    save_data(data)

# ================= 💰 شارژ کاربران =================
@bot.message_handler(func=lambda m: m.text and m.text.startswith("شارژ "))
def charge_user(m):
    if m.from_user.id != SUDO_ID:
        return
    try:
        parts = m.text.split()
        uid, amount = parts[1], int(parts[2])
        data = load_data()
        data["users"].setdefault(uid, {"credits": 0})
        data["users"][uid]["credits"] += amount
        save_data(data)
        bot.reply_to(m, f"✅ به کاربر <code>{uid}</code> مقدار {amount} پیام شارژ اضافه شد.")
    except Exception as e:
        logging.error(f"charge error: {e}")
        bot.reply_to(m, "⚠️ فرمت درست دستور:\n<code>شارژ [آیدی] [تعداد پیام]</code>")

# ================= 🧠 گفت‌وگو با ChatGPT =================
@bot.message_handler(func=lambda m: True)
def ai_chat(m):
    data = load_data()
    uid = str(m.from_user.id)

    # بررسی فعال بودن
    if not data.get("active", False):
        return

    # بررسی مجوز سودو
    if m.from_user.id != SUDO_ID:
        user_data = data["users"].get(uid, {"credits": 5})
        credits = user_data["credits"]

        if credits <= 0:
            return bot.reply_to(m, "⚠️ شارژ شما تمام شده است.\nبرای شارژ مجدد به پشتیبانی مراجعه کنید.")

        # کم کردن ۱ پیام از اعتبار
        user_data["credits"] = credits - 1
        data["users"][uid] = user_data
        save_data(data)

    # ارسال به ChatGPT
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "شما یک دستیار فارسی مودب و حرفه‌ای هستید."},
                {"role": "user", "content": m.text}
            ],
            max_tokens=300
        )
        answer = response["choices"][0]["message"]["content"].strip()
        bot.reply_to(m, f"🤖 {answer}")
    except Exception as e:
        bot.reply_to(m, "❗ خطا در ارتباط با هوش مصنوعی، لطفاً بعداً تلاش کنید.")
        logging.error(f"AI error: {e}")

# ================= 🚀 اجرای ماژول =================
if __name__ == "__main__":
    print("🤖 Persian Lux Smart AI Module فعال شد...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except Exception as e:
            logging.error(f"polling crash: {e}")
            time.sleep(5)
