# -*- coding: utf-8 -*-
# Persian Lux AI Panel v27 – Final Clean Version
# Coder: Mohammad Noor 👑 (@NOORI_NOOR)

import os, json, random, time, datetime, logging
import telebot
from telebot import types
import openai

# ========== ⚙️ تنظیمات اولیه ==========
TOKEN = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
openai.api_key = OPENAI_KEY

DATA_FILE = "data.json"
LOG_FILE = "error.log"
logging.basicConfig(filename=LOG_FILE, level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

# ========== 💾 داده‌ها ==========
def base_data():
    return {
        "users": {},
        "groups": {},
        "banned": [],
        "muted": {},
        "support": {},
        "ai_global": True
    }

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(base_data())
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ========== ابزار ==========
def is_sudo(uid):
    return str(uid) == str(SUDO_ID)

def ai_reply(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        return f"❌ خطا در پاسخ از هوش: {e}"

# ========== 📱 پنل‌ها ==========
def user_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🧠 روشن / خاموش", "💎 سکه من")
    kb.row("💬 راهنما", "🛠 پشتیبانی")
    kb.row("➕ افزودن به گروه", "👑 سازنده")
    return kb

def admin_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📊 آمار", "💎 شارژ")
    kb.row("💌 ارسال همگانی", "🤖 کنترل هوش")
    kb.row("🚫 بن‌ها", "🔕 سکوت‌ها")
    kb.row("🔚 لفت بده", "🔙 بازگشت")
    return kb

# ========== 🚀 شروع ==========
@bot.message_handler(commands=["start"])
def start_cmd(m):
    d = load_data()
    uid = str(m.from_user.id)
    if uid not in d["users"]:
        d["users"][uid] = {"coins": 5, "ai_on": True, "charged_until": None}
        save_data(d)
    bot.send_message(
        m.chat.id,
        "🤖 سلام! من <b>ربات هوش مصنوعی نوری</b> هستم 💎\n"
        "با من می‌تونی گفتگو کنی یا گروه‌هاتو مدیریت کنی ✨\n\n"
        "از دکمه‌های پایین استفاده کن 👇",
        reply_markup=user_keyboard()
    )

# ========== 👑 پنل مدیریت ==========
@bot.message_handler(commands=["admin"])
def admin_panel(m):
    if is_sudo(m.from_user.id):
        bot.send_message(m.chat.id, "👑 پنل مدیریت فعال شد:", reply_markup=admin_keyboard())

# ========== 💬 پیام‌ها و عملکرد ==========
@bot.message_handler(func=lambda m: True)
def all_msgs(m):
    d = load_data()
    uid = str(m.from_user.id)
    txt = (m.text or "").strip()
    d["users"].setdefault(uid, {"coins": 5, "ai_on": True})
    user = d["users"][uid]

    # -------------------- کاربر عادی --------------------
    if txt == "🧠 روشن / خاموش":
        user["ai_on"] = not user["ai_on"]
        save_data(d)
        bot.reply_to(m, f"🧩 هوش شخصی شما {'روشن ✅' if user['ai_on'] else 'خاموش ❌'} شد.")
        return

    if txt == "💎 سکه من":
        bot.reply_to(m, f"💰 سکه‌های شما: {user['coins']}")
        return

    if txt == "💬 راهنما":
        bot.reply_to(m, "📘 برای استفاده بنویس:\n«ربات بگو + سوالت»\nهر پیام ۱ سکه مصرف می‌کند 💎")
        return

    if txt == "🛠 پشتیبانی":
        d["support"][uid] = True
        save_data(d)
        bot.reply_to(m, "📨 پیام خود را ارسال کنید تا به پشتیبانی برسد 💬")
        return

    if txt == "➕ افزودن به گروه":
        bot.reply_to(m, f"📎 برای افزودن من به گروه: https://t.me/{bot.get_me().username}?startgroup=true")
        return

    if txt == "👑 سازنده":
        bot.reply_to(m, "👤 سازنده: @NOORI_NOOR 💎")
        return

    # -------------------- پنل مدیر --------------------
    if is_sudo(m.from_user.id):
        if txt == "📊 آمار":
            bot.reply_to(m, f"👥 کاربران: {len(d['users'])}\n💬 گروه‌ها: {len(d['groups'])}")
            return
        if txt == "💎 شارژ":
            bot.reply_to(m, "🔋 برای شارژ گروه بنویس:\n<code>شارژ گروه 2</code>\nیا:\n<code>شارژ کاربر 12345 3</code>")
            return
        if txt == "💌 ارسال همگانی":
            bot.reply_to(m, "📢 پیام خود را ریپلای کن و بنویس «ارسال»")
            return
        if txt == "🤖 کنترل هوش":
            d["ai_global"] = not d["ai_global"]
            save_data(d)
            bot.reply_to(m, f"🤖 هوش کلی {'فعال ✅' if d['ai_global'] else 'غیرفعال ❌'} شد.")
            return
        if txt == "🚫 بن‌ها":
            bot.reply_to(m, "📛 برای بن کاربر، روی پیامش ریپلای کن و بنویس «بن»")
            return
        if txt == "🔕 سکوت‌ها":
            bot.reply_to(m, "🔇 برای سکوت، روی پیام کاربر ریپلای کن و بنویس «سکوت»")
            return
        if txt == "🔚 لفت بده":
            bot.send_message(m.chat.id, "👋 ربات از این گفتگو خارج شد.")
            bot.leave_chat(m.chat.id)
            return
        if txt == "🔙 بازگشت":
            bot.send_message(m.chat.id, "↩ بازگشت به پنل کاربر", reply_markup=user_keyboard())
            return

    # -------------------- هوش مصنوعی و سکه --------------------
    if txt.startswith("ربات بگو"):
        if not user["ai_on"]:
            bot.reply_to(m, "🧠 هوش شخصی شما خاموش است!")
            return
        if user["coins"] <= 0:
            bot.reply_to(m, "⚠️ موجودی سکه شما تمام شده است!")
            return
        question = txt.replace("ربات بگو", "").strip()
        bot.send_chat_action(m.chat.id, "typing")
        answer = ai_reply(question)
        user["coins"] -= 1
        save_data(d)
        bot.reply_to(m, answer)
        return

    # -------------------- پشتیبانی --------------------
    if uid in d["support"]:
        bot.forward_message(SUDO_ID, m.chat.id, m.message_id)
        bot.send_message(m.chat.id, "✅ پیام شما به پشتیبانی ارسال شد.")
        d["support"].pop(uid, None)
        save_data(d)
        return

    # -------------------- پاسخ مدیر به کاربر --------------------
    if is_sudo(m.from_user.id) and m.reply_to_message and m.reply_to_message.forward_from:
        try:
            user_id = m.reply_to_message.forward_from.id
            bot.send_message(user_id, f"📬 پاسخ پشتیبانی:\n{m.text}")
            bot.send_message(m.chat.id, "✅ پاسخ ارسال شد.")
        except Exception as e:
            bot.reply_to(m, f"❌ خطا در ارسال: {e}")
        return

print("🤖 Persian Lux AI Panel v27 – بدون خطا اجرا شد 💎")
while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        logging.error(f"Crash: {e}")
        time.sleep(5)
