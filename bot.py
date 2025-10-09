# -*- coding: utf-8 -*-
# Persian AI & Management Bot – Official Final Version
# Designed for Mohammad Noori 👑

import os, json, random, time, logging
from datetime import datetime, timedelta
import telebot
from telebot import types
import openai

# ================= ⚙️ تنظیمات پایه =================
TOKEN = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
openai.api_key = OPENAI_KEY

DATA_FILE = "data.json"
LOG_FILE = "error.log"

logging.basicConfig(filename=LOG_FILE, level=logging.ERROR, format="%(asctime)s - %(message)s")

# ================= 💾 فایل داده =================
def base_data():
    return {
        "users": {},
        "banned": [],
        "muted": {},
        "support": {},
        "coins": {},
        "groups": {},
        "ai_active": True
    }

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(base_data())
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return base_data()

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

# ================= 🧩 ابزارها =================
def cmd(m): return (getattr(m, "text", "") or "").strip()
def is_sudo(uid): return uid == SUDO_ID
def now(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ================= 🪙 سیستم سکه و شارژ =================
def get_user(uid):
    d = load_data()
    u = str(uid)
    if u not in d["users"]:
        d["users"][u] = {"messages": 0}
        d["coins"][u] = 5  # پیش‌فرض ۵ پیام رایگان
        save_data(d)
    return d

def add_coins(uid, amount):
    d = load_data()
    u = str(uid)
    d["coins"][u] = d["coins"].get(u, 0) + amount
    save_data(d)

def use_coin(uid):
    d = load_data()
    u = str(uid)
    if d["coins"].get(u, 0) > 0:
        d["coins"][u] -= 1
        save_data(d)
        return True
    return False

# ================= 👋 استارت و پنل کاربر =================
@bot.message_handler(commands=["start"])
def start_cmd(m):
    d = get_user(m.from_user.id)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🤖 ربات بگو", "🔕 ربات نگو")
    kb.row("💬 پشتیبانی", "ℹ️ راهنما", "💰 موجودی سکه")
    kb.row("➕ افزودن به گروه")
    bot.send_message(m.chat.id,
        "سلام 👋\nبه ربات رسمی نوری خوش آمدید.\n"
        "با استفاده از این ربات می‌توانید از هوش مصنوعی و پشتیبانی مستقیم استفاده کنید.",
        reply_markup=kb)

# ================= 💬 پشتیبانی زنده =================
@bot.message_handler(func=lambda m: cmd(m) == "💬 پشتیبانی")
def support_start(m):
    d = load_data()
    d["support"][str(m.from_user.id)] = True
    save_data(d)
    bot.send_message(m.chat.id, "لطفاً پیام خود را بنویسید تا به پشتیبانی ارسال شود.")

@bot.message_handler(func=lambda m: str(m.from_user.id) in load_data().get("support", {}) and not is_sudo(m.from_user.id))
def user_to_support(m):
    d = load_data()
    if str(m.from_user.id) in d["banned"]:
        return bot.reply_to(m, "شما از پشتیبانی مسدود شده‌اید.")
    text = f"📩 پیام جدید از کاربر @{m.from_user.username or m.from_user.first_name} ({m.from_user.id}):\n\n{m.text}"
    kb = types.InlineKeyboardMarkup()
    kb.row(types.InlineKeyboardButton("✏️ پاسخ دادن", callback_data=f"reply_{m.from_user.id}"),
           types.InlineKeyboardButton("❌ بستن گفتگو", callback_data=f"close_{m.from_user.id}"))
    bot.send_message(SUDO_ID, text, reply_markup=kb)
    bot.reply_to(m, "پیام شما به پشتیبانی ارسال شد ✅")

@bot.callback_query_handler(func=lambda c: c.data.startswith("reply_") or c.data.startswith("close_"))
def handle_support_callback(c):
    uid = c.data.split("_")[1]
    if c.data.startswith("reply_"):
        bot.send_message(SUDO_ID, f"✉️ لطفاً پیام خود را برای ارسال به کاربر {uid} بنویسید.")
        load_data()["support"][uid] = "waiting_reply"
    elif c.data.startswith("close_"):
        d = load_data()
        if uid in d["support"]:
            d["support"].pop(uid)
            save_data(d)
        bot.send_message(int(uid), "🔒 گفت‌وگو با پشتیبانی بسته شد.")
        bot.send_message(SUDO_ID, "✅ گفتگو بسته شد.")
    try:
        bot.edit_message_text("در حال پردازش...", c.message.chat.id, c.message.message_id)
    except:
        pass# ================= ⚙️ پنل مدیریت و دستورات سودو =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd(m) == "پنل مدیریت")
def admin_panel(m):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📢 ارسال همگانی", "💸 شارژ کاربر", "💬 شارژ گروه")
    kb.row("🚫 بن", "🔇 سکوت", "🔊 حذف سکوت", "🚪 لفت بده")
    kb.row("📊 آمار", "🔙 بازگشت")
    bot.send_message(m.chat.id, "🔹 پنل مدیریت فعال شد.", reply_markup=kb)

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd(m) == "بازگشت")
def back_admin(m):
    start_cmd(m)

# ================= 🔕 سکوت و 🚫 بن =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and m.reply_to_message and cmd(m) == "🚫 بن")
def ban_user(m):
    uid = m.reply_to_message.from_user.id
    d = load_data()
    if str(uid) not in d["banned"]:
        d["banned"].append(str(uid))
        save_data(d)
        bot.reply_to(m, "کاربر بن شد و دیگر پاسخی دریافت نخواهد کرد.")
    else:
        bot.reply_to(m, "کاربر از قبل بن شده است.")

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and m.reply_to_message and cmd(m) == "🔇 سکوت")
def mute_user(m):
    uid = str(m.reply_to_message.from_user.id)
    until = (datetime.now() + timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S")
    d = load_data()
    d["muted"][uid] = until
    save_data(d)
    bot.reply_to(m, f"کاربر تا ۵ ساعت آینده در سکوت قرار گرفت.")

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and m.reply_to_message and cmd(m) == "🔊 حذف سکوت")
def unmute_user(m):
    uid = str(m.reply_to_message.from_user.id)
    d = load_data()
    if uid in d["muted"]:
        d["muted"].pop(uid)
        save_data(d)
        bot.reply_to(m, "سکوت کاربر برداشته شد.")
    else:
        bot.reply_to(m, "کاربر در سکوت نبود.")

# ================= 💸 شارژ و آمار =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd(m).startswith("💸 شارژ "))
def charge_user(m):
    try:
        amount = int(cmd(m).split(" ")[2])
        uid = str(m.reply_to_message.from_user.id)
        add_coins(uid, amount)
        bot.reply_to(m, f"کاربر با {amount} سکه شارژ شد.")
    except:
        bot.reply_to(m, "فرمت درست: با ریپلای بزن «💸 شارژ 5»")

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd(m) == "📊 آمار")
def show_stats(m):
    d = load_data()
    users = len(d["users"])
    banned = len(d["banned"])
    bot.reply_to(m, f"📈 آمار فعلی:\n👤 کاربران: {users}\n🚫 بن‌شده‌ها: {banned}")

# ================= 🚪 لفت دادن ربات =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd(m) == "🚪 لفت بده")
def leave_group(m):
    try:
        bot.leave_chat(m.chat.id)
    except:
        bot.reply_to(m, "خطا در خروج از گروه.")

# ================= 🧠 سیستم هوش مصنوعی =================
@bot.message_handler(func=lambda m: cmd(m) in ["🤖 ربات بگو", "🔕 ربات نگو"])
def toggle_ai(m):
    d = load_data()
    d["ai_active"] = (cmd(m) == "🤖 ربات بگو")
    save_data(d)
    if d["ai_active"]:
        bot.send_message(m.chat.id, "✅ هوش مصنوعی فعال شد. چه کمکی می‌توانم انجام دهم؟")
    else:
        bot.send_message(m.chat.id, "❎ هوش مصنوعی غیرفعال شد.")

def ai_response(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": text}]
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.error(f"OpenAI Error: {e}")
        return "⚠️ خطا در دریافت پاسخ از هوش مصنوعی."

@bot.message_handler(func=lambda m: True)
def handle_ai(m):
    d = load_data()
    uid = str(m.from_user.id)

    if uid in d["banned"]:
        return
    if uid in d["muted"]:
        mute_until = datetime.strptime(d["muted"][uid], "%Y-%m-%d %H:%M:%S")
        if datetime.now() < mute_until:
            return

    if not d.get("ai_active", True):
        return

    if is_sudo(uid):
        pass
    else:
        if not use_coin(uid):
            return bot.reply_to(m, "🔒 شارژ شما تمام شده است. برای شارژ مجدد با پشتیبانی تماس بگیرید.")

    reply = ai_response(m.text)
    bot.send_message(m.chat.id, reply)

# ================= 🧱 اجرای نهایی =================
print("🤖 Persian AI Management Bot Running…")
while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        logging.error(f"polling crash: {e}")
        time.sleep(5)
