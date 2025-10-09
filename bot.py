# -*- coding: utf-8 -*-
# SmartBot-Noori V5 (AI + Credit System)
# Created by Mohammad Noori 👑

import os, json, time, random, logging
from datetime import datetime, timedelta
import telebot
from telebot import types
from openai import OpenAI

# ================= ⚙️ تنظیمات پایه =================
TOKEN = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
ai = OpenAI(api_key=OPENAI_KEY)

DATA_FILE = "data.json"
logging.basicConfig(filename="error.log", level=logging.ERROR)

# ================= 💾 داده‌ها =================
def base_data():
    return {"users": {}, "muted": {}, "banned": {}, "ai_status": True}

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(base_data())
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return base_data()

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ================= 🧩 ابزارها =================
def is_sudo(uid):
    return str(uid) == str(SUDO_ID)

def add_user(uid):
    data = load_data()
    if str(uid) not in data["users"]:
        data["users"][str(uid)] = {"coins": 5, "ai_active": False, "mute_until": 0}
        save_data(data)

# ================= 🎛 پنل اصلی =================
def main_menu():
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("🤖 روشن کردن ربات", callback_data="ai_on"),
        types.InlineKeyboardButton("💤 خاموش کردن ربات", callback_data="ai_off")
    )
    markup.row(
        types.InlineKeyboardButton("💰 موجودی سکه", callback_data="balance"),
        types.InlineKeyboardButton("⚙️ راهنما", callback_data="help")
    )
    markup.row(
        types.InlineKeyboardButton("📞 ارتباط با سازنده", url="https://t.me/NOORI_NOOR"),
        types.InlineKeyboardButton("➕ افزودن به گروه", url="https://t.me/{0}?startgroup=true".format(bot.get_me().username))
    )
    return markup

# ================= 🚀 شروع ربات =================
@bot.message_handler(commands=["start"])
def start_cmd(m):
    add_user(m.from_user.id)
    bot.send_message(
        m.chat.id,
        f"✨ سلام {m.from_user.first_name}!\n"
        "من یه ربات هوش مصنوعی هستم 🤖\n"
        "می‌تونی با دستور <b>ربات روشن</b> فعال‌م کنی.\n"
        "هر کاربر ۵ پیام رایگان داره 💎",
        reply_markup=main_menu()
    )

# ================= 💡 دکمه‌های منو =================
@bot.callback_query_handler(func=lambda c: True)
def callback_menu(c):
    data = load_data()
    uid = str(c.from_user.id)
    add_user(uid)

    if c.data == "ai_on":
        data["users"][uid]["ai_active"] = True
        save_data(data)
        text = "🤖 هوش مصنوعی فعال شد!\nچه کمکی می‌تونم بکنم؟ 💬"

    elif c.data == "ai_off":
        data["users"][uid]["ai_active"] = False
        save_data(data)
        text = "💤 هوش مصنوعی غیرفعال شد.\nبرای فعال‌سازی دوباره روی «روشن کردن ربات» بزن."

    elif c.data == "balance":
        coins = data["users"][uid]["coins"]
        text = f"💰 موجودی شما: <b>{coins}</b> سکه ✨\n"
        text += "هر پیام = ۱ سکه 💬"

    elif c.data == "help":
        text = (
            "📘 <b>راهنمای استفاده:</b>\n"
            "➤ بنویس <b>ربات روشن</b> تا فعال شم.\n"
            "➤ هر پیام هوش مصنوعی ۱ سکه مصرف می‌کنه.\n"
            "➤ با دستور «شارژ X» مدیر می‌تونه برات سکه اضافه کنه.\n"
            "➤ با «ربات خاموش» منو غیرفعال می‌کنه.\n\n"
            "👑 سازنده: @NOORI_NOOR"
        )

    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=main_menu())
    except:
        bot.send_message(c.message.chat.id, text, reply_markup=main_menu())

# ================= 💬 پیام‌های هوش مصنوعی =================
@bot.message_handler(func=lambda m: True)
def ai_reply(m):
    data = load_data()
    uid = str(m.from_user.id)
    add_user(uid)

    # سکوت و بن بررسی
    if uid in data["banned"]:
        return
    if time.time() < data["users"][uid].get("mute_until", 0):
        return

    text = m.text.strip().lower()

    # روشن / خاموش
    if text in ["ربات روشن"]:
        data["users"][uid]["ai_active"] = True
        save_data(data)
        return bot.reply_to(m, "✨ هوش مصنوعی روشن شد، در خدمتتم!")
    if text in ["ربات خاموش", "ربات نگو"]:
        data["users"][uid]["ai_active"] = False
        save_data(data)
        return bot.reply_to(m, "💤 ربات خاموش شد. برای فعال‌سازی بنویس «ربات روشن».")

    # اگر غیرفعال بود
    if not data["users"][uid]["ai_active"]:
        return

    # بررسی سکه
    coins = data["users"][uid]["coins"]
    if coins <= 0:
        return bot.reply_to(m, "💎 سکه‌هات تموم شده!\nبرای شارژ به مدیر پیام بده 💬")

    # مصرف سکه
    data["users"][uid]["coins"] -= 1
    save_data(data)

    try:
        prompt = m.text
        response = ai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )
        answer = response.choices[0].message.content
        bot.reply_to(m, f"🤖 {answer}")
    except Exception as e:
        logging.error(f"AI Error: {e}")
        bot.reply_to(m, "❌ خطا در پاسخ هوش مصنوعی.")# ================= ⚡️ دستورات مدیریتی =================

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and m.text.startswith("شارژ"))
def charge_user(m):
    data = load_data()
    if not m.reply_to_message:
        return bot.reply_to(m, "⚠️ لطفاً روی پیام کاربر ریپلای کن و بنویس:\nشارژ 10")
    try:
        count = int(m.text.split()[1])
    except:
        return bot.reply_to(m, "❗ فرمت درست: شارژ 5")
    uid = str(m.reply_to_message.from_user.id)
    add_user(uid)
    data["users"][uid]["coins"] += count
    save_data(data)
    bot.reply_to(m, f"💰 {count} سکه به کاربر اضافه شد ✅")

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and m.text == "آمار")
def show_stats(m):
    data = load_data()
    total_users = len(data["users"])
    banned = len(data["banned"])
    bot.reply_to(m,
        f"📊 <b>آمار کلی ربات:</b>\n"
        f"👤 کاربران: {total_users}\n"
        f"🚫 بن‌شده‌ها: {banned}\n"
        f"💎 فعال‌ها: {total_users - banned}"
    )

# ================= 🚫 بن / سکوت / لفت =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and m.reply_to_message and m.text == "بن")
def ban_user(m):
    uid = str(m.reply_to_message.from_user.id)
    data = load_data()
    data["banned"][uid] = True
    save_data(data)
    bot.reply_to(m, f"🚫 کاربر بن شد و دیگر پاسخی دریافت نخواهد کرد.")

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and m.reply_to_message and m.text == "حذف بن")
def unban_user(m):
    uid = str(m.reply_to_message.from_user.id)
    data = load_data()
    if uid in data["banned"]:
        del data["banned"][uid]
        save_data(data)
    bot.reply_to(m, "✅ کاربر از بن خارج شد.")

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and m.reply_to_message and m.text.startswith("سکوت"))
def mute_user(m):
    try:
        hours = int(m.text.split()[1])
    except:
        hours = 5
    uid = str(m.reply_to_message.from_user.id)
    data = load_data()
    data["users"][uid]["mute_until"] = time.time() + hours * 3600
    save_data(data)
    bot.reply_to(m, f"🔇 کاربر برای {hours} ساعت ساکت شد.")

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and m.text == "لفت بده")
def leave_group(m):
    try:
        bot.send_message(m.chat.id, "👋 بدرود! با آرزوی موفقیت 🌸")
        bot.leave_chat(m.chat.id)
    except:
        bot.reply_to(m, "⚠️ نتونستم از گروه خارج بشم.")

# ================= 👑 پنل مدیریت =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and m.text == "پنل")
def admin_panel(m):
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("📊 آمار ربات", callback_data="admin_stats"),
        types.InlineKeyboardButton("💌 ارسال همگانی", callback_data="broadcast")
    )
    markup.row(
        types.InlineKeyboardButton("💎 کاربران", callback_data="admin_users"),
        types.InlineKeyboardButton("🚪 خروج از گروه", callback_data="leave_chat")
    )
    bot.send_message(m.chat.id, "👑 <b>پنل مدیریت هوش مصنوعی</b>", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_") or c.data == "broadcast" or c.data == "leave_chat")
def admin_actions(c):
    data = load_data()
    if not is_sudo(c.from_user.id): return

    if c.data == "admin_stats":
        total = len(data["users"])
        bans = len(data["banned"])
        text = f"📊 آمار فعلی:\n👤 کاربران: {total}\n🚫 بن‌شده‌ها: {bans}"
        bot.answer_callback_query(c.id, text, show_alert=True)

    elif c.data == "admin_users":
        users = "\n".join([f"• {u}" for u in list(data['users'].keys())[:30]])
        text = f"👥 کاربران فعال:\n{users if users else 'هیچ کاربری نیست.'}"
        bot.send_message(c.message.chat.id, text)

    elif c.data == "broadcast":
        bot.send_message(c.message.chat.id, "📢 روی پیام مورد نظر ریپلای کن و بنویس «ارسال».")

    elif c.data == "leave_chat":
        try:
            bot.send_message(c.message.chat.id, "👋 خداحافظ! ربات در حال خروج است.")
            bot.leave_chat(c.message.chat.id)
        except:
            bot.send_message(c.message.chat.id, "❗ خطا در خروج از گروه.")

# ================= 📢 ارسال همگانی =================
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and m.reply_to_message and m.text == "ارسال")
def broadcast_msg(m):
    data = load_data()
    msg = m.reply_to_message
    sent = 0
    for uid in data["users"]:
        try:
            if msg.text:
                bot.send_message(uid, msg.text)
            elif msg.photo:
                bot.send_photo(uid, msg.photo[-1].file_id, caption=msg.caption or "")
            sent += 1
        except:
            continue
    bot.reply_to(m, f"📬 پیام برای {sent} کاربر ارسال شد ✅")

# ================= 🔄 اجرای نهایی =================
print("🤖 SmartBot-Noori V5 فعال شد و آماده پاسخگویی است...")
while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        logging.error(f"Polling crash: {e}")
        time.sleep(5)
