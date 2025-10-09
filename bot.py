# -*- coding: utf-8 -*-
# SmartBot Noori Plus 💎
# Coded by Mohammad Noori
# Version 1.0 (AI + Management)

import os, json, random, time, logging
import telebot
from telebot import types
from datetime import datetime, timedelta
from openai import OpenAI

# تنظیمات
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
client = OpenAI(api_key=OPENAI_KEY)

DATA_FILE = "data.json"
LOG_FILE = "error.log"

logging.basicConfig(filename=LOG_FILE, level=logging.ERROR, format="%(asctime)s - %(message)s")

# 📁 فایل داده
def load_data():
    if not os.path.exists(DATA_FILE):
        data = {"users": {}, "active_ai": True, "groups": []}
        save_data(data)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def user_register(uid):
    data = load_data()
    if str(uid) not in data["users"]:
        data["users"][str(uid)] = {"messages": 0, "charged_until": None}
        save_data(data)

# 🧠 پاسخ هوش مصنوعی
def ask_ai(prompt):
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content
    except Exception as e:
        logging.error(str(e))
        return "⚠️ مشکلی در ارتباط با سرور پیش آمد."

# 💬 دکمه‌های شیشه‌ای
def main_keyboard():
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("➕ افزودن به گروه", url=f"https://t.me/{bot.get_me().username}?startgroup=true"),
        types.InlineKeyboardButton("💬 پشتیبانی", url="https://t.me/NOORI_NOOR")
    )
    kb.add(
        types.InlineKeyboardButton("💎 راهنما", callback_data="help"),
        types.InlineKeyboardButton("📨 ارتباط با سازنده", callback_data="contact")
    )
    return kb# ================= ⚙️ کنترل هوش مصنوعی و شارژ =================

@bot.message_handler(commands=["start"])
def start_cmd(m):
    user_register(m.from_user.id)
    bot.send_message(
        m.chat.id,
        "✨ سلام به ربات هوش مصنوعی <b>SmartBot Noori Plus</b> خوش اومدی!\n"
        "🤖 من یه دستیار هوشمندم که می‌تونم باهات حرف بزنم، برنامه بنویسم، متن تولید کنم و کلی کار دیگه 💡\n\n"
        "برای استفاده بنویس:\n"
        "<b>ربات بگو</b> 👉 تا فعال شم\n"
        "<b>ربات نگو</b> 👉 تا ساکت شم\n"
        "💎 هر کاربر ۵ پیام رایگان دارد!\n\n"
        "👑 سازنده: <a href='https://t.me/NOORI_NOOR'>محمد نوری</a>",
        reply_markup=main_keyboard()
    )

# 🔘 روشن/خاموش هوش مصنوعی
@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["ربات بگو", "ربات روشن"])
def ai_on(m):
    data = load_data()
    data["active_ai"] = True
    save_data(data)
    bot.reply_to(m, "🤖 هوش مصنوعی فعال شد!\n✨ بگو چه کمکی می‌تونم بکنم؟")

@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["ربات نگو", "ربات خاموش"])
def ai_off(m):
    data = load_data()
    data["active_ai"] = False
    save_data(data)
    bot.reply_to(m, "😴 هوش مصنوعی غیرفعال شد.")

# 🚪 لفت بده (فقط سودو)
@bot.message_handler(func=lambda m: m.text == "لفت بده" and m.from_user.id == SUDO_ID)
def leave_group(m):
    bot.reply_to(m, "🚪 با اجازه! در حال ترک گروه هستم...")
    bot.leave_chat(m.chat.id)

# 💎 شارژ کاربر (فقط سودو)
@bot.message_handler(func=lambda m: m.text and m.text.startswith("شارژ ") and m.from_user.id == SUDO_ID)
def charge_user(m):
    try:
        if not m.reply_to_message:
            return bot.reply_to(m, "⚠️ لطفاً روی پیام کاربر ریپلای کن.")
        days = int(m.text.split()[1])
        uid = str(m.reply_to_message.from_user.id)
        data = load_data()
        exp = datetime.now() + timedelta(days=days)
        data["users"][uid]["charged_until"] = exp.strftime("%Y-%m-%d %H:%M:%S")
        save_data(data)
        bot.reply_to(m, f"💎 کاربر برای {days} روز شارژ شد.")
        bot.send_message(int(uid), f"✅ حساب شما برای {days} روز فعال شد.\nاز هوش مصنوعی بدون محدودیت استفاده کنید 💬")
    except Exception as e:
        bot.reply_to(m, f"❗ خطا در شارژ: {e}")

# 📊 آمار و ارسال همگانی
@bot.message_handler(func=lambda m: m.text == "آمار" and m.from_user.id == SUDO_ID)
def show_stats(m):
    data = load_data()
    total = len(data["users"])
    groups = len(data["groups"])
    bot.reply_to(m, f"📈 آمار ربات:\n👤 کاربران: {total}\n👥 گروه‌ها: {groups}")

@bot.message_handler(func=lambda m: m.text == "ارسال همگانی" and m.from_user.id == SUDO_ID and m.reply_to_message)
def broadcast(m):
    data = load_data()
    total = 0
    for uid in data["users"]:
        try:
            bot.copy_message(uid, m.chat.id, m.reply_to_message.message_id)
            total += 1
        except:
            pass
    bot.reply_to(m, f"📢 پیام به {total} نفر ارسال شد.")

# 💬 پاسخ خودکار هوش مصنوعی (۵ پیام رایگان)
@bot.message_handler(func=lambda m: True, content_types=["text"])
def ai_reply(m):
    data = load_data()
    uid = str(m.from_user.id)
    user_register(uid)

    # اگر هوش مصنوعی خاموش باشد
    if not data.get("active_ai", True):
        return

    # بررسی شارژ
    user = data["users"].get(uid, {})
    exp_str = user.get("charged_until")
    now = datetime.now()

    if exp_str and datetime.strptime(exp_str, "%Y-%m-%d %H:%M:%S") > now:
        limit = 99999  # نامحدود در زمان شارژ
    else:
        limit = 5  # فقط ۵ پیام رایگان

    # شمارش پیام‌ها
    count = user.get("messages", 0)
    if count >= limit:
        bot.reply_to(m, "⚠️ شارژ رایگان شما تمام شد.\nبرای فعال‌سازی مجدد با پشتیبانی در تماس باشید 💎")
        return

    # پاسخ از ChatGPT
    reply = ask_ai(m.text)
    bot.reply_to(m, reply)

    # افزایش شمارش
    user["messages"] = count + 1
    data["users"][uid] = user
    save_data(data)# ================= 🎛 پنل شیشه‌ای و پشتیبانی =================

@bot.callback_query_handler(func=lambda c: c.data == "help")
def help_panel(c):
    text = (
        "💎 <b>راهنمای SmartBot Noori Plus</b>\n\n"
        "🤖 من یه ربات هوشمندم که می‌تونم باهات حرف بزنم، برنامه بنویسم، شعر بگم، ترجمه کنم و حتی متن تولید کنم!\n\n"
        "📘 <b>دستورات کاربردی:</b>\n"
        "• <code>ربات بگو</code> → فعال‌سازی هوش مصنوعی\n"
        "• <code>ربات نگو</code> → خاموش‌کردن هوش مصنوعی\n"
        "• <code>لفت بده</code> → خروج ربات از گروه (فقط سودو)\n"
        "• <code>شارژ X</code> → شارژ کاربر برای X روز (فقط سودو)\n\n"
        "⚙️ کاربران معمولی ۵ پیام رایگان دارند.\n"
        "💎 بعد از شارژ، استفاده نامحدود خواهد بود.\n\n"
        "👑 سازنده: <a href='https://t.me/NOORI_NOOR'>محمد نوری</a>"
    )
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, parse_mode="HTML", reply_markup=main_keyboard())

# 📬 ارتباط با سازنده
@bot.callback_query_handler(func=lambda c: c.data == "contact")
def contact_start(c):
    bot.send_message(c.message.chat.id, "📨 پیام خود را برای ارسال به سازنده بنویس:")
    bot.register_next_step_handler_by_chat_id(c.message.chat.id, forward_to_admin)

def forward_to_admin(m):
    try:
        bot.forward_message(SUDO_ID, m.chat.id, m.message_id)
        bot.reply_to(m, "✅ پیام شما برای پشتیبانی ارسال شد.\nمنتظر پاسخ باشید 💬")
        bot.send_message(SUDO_ID, f"📩 پیام جدید از <a href='tg://user?id={m.from_user.id}'>{m.from_user.first_name}</a>:", parse_mode="HTML")
    except Exception as e:
        bot.reply_to(m, f"⚠️ خطا در ارسال پیام: {e}")

# 📥 پاسخ از طرف سودو به کاربر
@bot.message_handler(func=lambda m: m.reply_to_message and m.chat.id == SUDO_ID)
def reply_from_admin(m):
    if m.reply_to_message.forward_from:
        uid = m.reply_to_message.forward_from.id
        bot.send_message(uid, f"📨 پاسخ از پشتیبانی:\n{m.text}")

# ================= 🚀 اجرای نهایی =================

print("🤖 SmartBot Noori Plus is Running...")

while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        logging.error(f"Polling crash: {e}")
        time.sleep(5)
