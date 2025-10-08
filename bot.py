# -*- coding: utf-8 -*-
# 🤖 Smart AI Bot – Mohammad Noori (@NOORI_NOOR)
# نسخه نهایی با پنل شیشه‌ای، هوش مصنوعی، پشتیبانی و شارژ

import os, json, random, time, logging, datetime
import telebot
from telebot import types
from openai import OpenAI

# ========== ⚙️ تنظیمات اولیه ==========
TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
ai = OpenAI(api_key=OPENAI_KEY)

DATA_FILE = "data.json"
LOG_FILE = "error.log"

logging.basicConfig(filename=LOG_FILE, level=logging.ERROR)

# ========== 📁 داده ==========
def load_data():
    if not os.path.exists(DATA_FILE):
        save_data({"users": {}, "banned": [], "muted": {}, "ai_on": True})
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ========== 💬 پیام خوش‌آمد ==========
@bot.message_handler(commands=["start"])
def start(m):
    data = load_data()
    uid = str(m.from_user.id)
    if uid not in data["users"]:
        data["users"][uid] = {"credits": 5}
        save_data(data)
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("➕ افزودن به گروه", url=f"https://t.me/{bot.get_me().username}?startgroup=true"),
        types.InlineKeyboardButton("💬 پشتیبانی", callback_data="support"),
    )
    markup.add(
        types.InlineKeyboardButton("⚡ افزایش اعتبار", callback_data="buy_credit"),
        types.InlineKeyboardButton("👑 ارتباط با سازنده", callback_data="contact_dev"),
    )
    bot.reply_to(m,
        "🤖 <b>سلام!</b>\nمن ربات هوشمند نوری هستم.\n"
        "🧠 از هوش مصنوعی ChatGPT برای پاسخ دقیق استفاده می‌کنم.\n"
        "✨ برای استفاده ۵ پیام رایگان داری.\n"
        "برای شروع گفت‌وگو فقط بنویس <b>ربات روشن</b> 🌙",
        reply_markup=markup
    )

# ========== 👑 پنل سودو ==========
@bot.message_handler(commands=["panel"])
def panel(m):
    if m.from_user.id != SUDO_ID: return
    data = load_data()
    users = len(data["users"])
    banned = len(data["banned"])
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 آمار کاربران", callback_data="stats"),
        types.InlineKeyboardButton("📢 ارسال همگانی", callback_data="broadcast"),
        types.InlineKeyboardButton("💰 شارژ کاربر", callback_data="charge_user"),
        types.InlineKeyboardButton("🚫 لیست بن", callback_data="list_ban"),
    )
    bot.send_message(m.chat.id,
        f"👑 <b>پنل مدیریتی سودو</b>\n"
        f"👥 کاربران: {users}\n🚫 بن شده‌ها: {banned}",
        reply_markup=markup
    )

# ========== ⚡ کنترل روشن و خاموش ==========
@bot.message_handler(func=lambda m: m.text and m.text.lower() == "ربات روشن")
def ai_on(m):
    data = load_data()
    data["ai_on"] = True
    save_data(data)
    bot.reply_to(m, "🧠 هوش مصنوعی فعال شد!\nچه کمکی می‌تونم بکنم؟ 🌟")

@bot.message_handler(func=lambda m: m.text and m.text.lower() == "ربات خاموش")
def ai_off(m):
    data = load_data()
    data["ai_on"] = False
    save_data(data)
    bot.reply_to(m, "💤 هوش مصنوعی غیرفعال شد.\nبرای فعال‌سازی دوباره بنویس «ربات روشن»")

# ========== 🚫 بن / سکوت ==========
@bot.message_handler(func=lambda m: m.reply_to_message and m.text == "بن")
def ban_user(m):
    if m.from_user.id != SUDO_ID: return
    uid = m.reply_to_message.from_user.id
    data = load_data()
    if uid not in data["banned"]:
        data["banned"].append(uid)
        save_data(data)
        bot.reply_to(m, "🚫 کاربر بن شد.")
    else:
        bot.reply_to(m, "⚠️ این کاربر قبلاً بن شده.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text == "حذف بن")
def unban_user(m):
    if m.from_user.id != SUDO_ID: return
    uid = m.reply_to_message.from_user.id
    data = load_data()
    if uid in data["banned"]:
        data["banned"].remove(uid)
        save_data(data)
        bot.reply_to(m, "✅ کاربر از بن خارج شد.")
    else:
        bot.reply_to(m, "❗ کاربر بن نشده بود.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text == "سکوت")
def mute_user(m):
    if m.from_user.id != SUDO_ID: return
    uid = str(m.reply_to_message.from_user.id)
    data = load_data()
    data["muted"][uid] = time.time() + 5*3600  # ۵ ساعت
    save_data(data)
    bot.reply_to(m, "🔇 کاربر تا ۵ ساعت آینده ساکت شد.")

# ========== 💬 ارتباط با سازنده ==========
@bot.callback_query_handler(func=lambda call: call.data == "contact_dev")
def contact_dev(call):
    bot.send_message(call.message.chat.id,
        "📩 پیام خود را بفرستید.\n👑 محمد نوری به‌زودی پاسخ خواهد داد.")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, forward_to_dev)

def forward_to_dev(m):
    text = m.text
    bot.send_message(SUDO_ID,
        f"📬 پیام جدید از کاربر:\n"
        f"👤 <a href='tg://user?id={m.from_user.id}'>{m.from_user.first_name}</a>\n"
        f"🆔 {m.from_user.id}\n💬 {text}")
    bot.reply_to(m, "✅ پیام شما ارسال شد، لطفاً منتظر پاسخ باشید.")

# وقتی محمد (سودو) ریپلای بزند:
@bot.message_handler(func=lambda m: m.reply_to_message and m.from_user.id == SUDO_ID)
def reply_from_sudo(m):
    lines = m.reply_to_message.text.split("\n")
    if "🆔" in lines[-2]:
        uid = int(lines[-2].split()[-1])
        bot.send_message(uid, f"👑 پاسخ از محمد نوری:\n{m.text}")

# ========== 🧠 ChatGPT پاسخ هوشمند ==========
@bot.message_handler(func=lambda m: True, content_types=["text"])
def chat_ai(m):
    data = load_data()
    uid = str(m.from_user.id)
    if m.from_user.id in data["banned"]: return
    if uid in data["muted"] and time.time() < data["muted"][uid]: return
    if not data["ai_on"]: return
    if uid not in data["users"]:
        data["users"][uid] = {"credits": 5}
        save_data(data)

    credits = data["users"][uid]["credits"]
    if credits <= 0:
        bot.reply_to(m, "⚠️ اعتبار شما تمام شده است.\nبرای شارژ مجدد روی «⚡ افزایش اعتبار» کلیک کنید.")
        return

    try:
        reply = ai.responses.create(model="gpt-4.1-mini", input=m.text)
        ans = reply.output[0].content[0].text
        bot.reply_to(m, ans)
        data["users"][uid]["credits"] -= 1
        save_data(data)
    except Exception as e:
        bot.reply_to(m, "❗ خطا در دریافت پاسخ از ChatGPT.")

# ========== 🚀 اجرا ==========
print("🤖 Smart AI Bot Mohammad Noori is running...")
while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        logging.error(str(e))
        time.sleep(5)
