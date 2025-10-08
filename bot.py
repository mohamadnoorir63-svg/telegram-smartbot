# ========== 💎 Lux AI Panel Final V2.0 ==========
# سازنده: محمد نوری 👑
# ویژگی‌ها: هوش مصنوعی + پنل سودو + بن + سکوت + شارژ + ارسال همگانی

import os, json, time, logging, telebot, openai
from telebot import types

# ------------------ تنظیمات ------------------
BOT_TOKEN   = os.environ.get("BOT_TOKEN")
OPENAI_KEY  = os.environ.get("OPENAI_API_KEY")
SUDO_ID     = int(os.environ.get("SUDO_ID", "0"))

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
openai.api_key = OPENAI_KEY

DATA_FILE = "data.json"
LOG_FILE  = "error.log"

logging.basicConfig(filename=LOG_FILE, level=logging.ERROR)

# ------------------ داده ------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        data = {"ai_on": True, "users": {}, "banned": {}, "muted": {}, "groups": []}
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ------------------ شروع ------------------
@bot.message_handler(commands=["start"])
def start_cmd(m):
    data = load_data()
    uid = str(m.from_user.id)
    if uid not in data["users"]:
        data["users"][uid] = {"credits": 5}
        save_data(data)

    if m.chat.type in ["group", "supergroup"]:
        if m.chat.id not in data["groups"]:
            data["groups"].append(m.chat.id)
            save_data(data)
        return

    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("⚙️ افزودن به گروه", url=f"https://t.me/{bot.get_me().username}?startgroup=true"),
        types.InlineKeyboardButton("📞 ارتباط با سازنده", callback_data="contact_creator")
    )
    markup.row(
        types.InlineKeyboardButton("💰 افزایش اعتبار", callback_data="buy_credit"),
        types.InlineKeyboardButton("🔋 وضعیت ربات", callback_data="bot_status")
    )
    if m.from_user.id == SUDO_ID:
        markup.row(
            types.InlineKeyboardButton("📊 آمار", callback_data="show_stats"),
            types.InlineKeyboardButton("📢 ارسال همگانی", callback_data="broadcast")
        )
        markup.row(
            types.InlineKeyboardButton("🤖 کنترل هوش مصنوعی", callback_data="toggle_ai"),
            types.InlineKeyboardButton("🚪 خروج از گروه", callback_data="leave_group")
        )

    bot.reply_to(
        m,
        f"👋 سلام {m.from_user.first_name}!\n"
        f"من <b>ربات هوش مصنوعی محمد نوری</b> هستم 🤖\n\n"
        f"💡 بنویس <code>ربات روشن</code> تا فعال شم.\n"
        f"✨ شما ۵ پیام رایگان دارید.",
        reply_markup=markup
    )

# ------------------ کنترل دکمه‌ها ------------------
@bot.callback_query_handler(func=lambda c: True)
def callbacks(c):
    data = load_data()
    uid = str(c.from_user.id)

    if c.data == "contact_creator":
        bot.answer_callback_query(c.id)
        bot.send_message(c.message.chat.id, "📨 پیام خود را بنویس تا برای سازنده ارسال شود.")
        data["users"][uid]["contact_mode"] = True
        save_data(data)

    elif c.data == "buy_credit":
        bot.answer_callback_query(c.id)
        bot.send_message(c.message.chat.id, "💳 برای شارژ مجدد به پشتیبانی پیام دهید:\n@NOORI_NOOR")

    elif c.data == "bot_status":
        status = "🟢 فعال" if data.get("ai_on", True) else "🔴 غیرفعال"
        bot.answer_callback_query(c.id, f"وضعیت فعلی: {status}")

    elif c.data == "toggle_ai" and c.from_user.id == SUDO_ID:
        data["ai_on"] = not data["ai_on"]
        save_data(data)
        bot.answer_callback_query(c.id, "✅ تغییر وضعیت ذخیره شد.")
        bot.send_message(c.message.chat.id, f"🤖 هوش مصنوعی اکنون {'فعال' if data['ai_on'] else 'غیرفعال'} است.")

    elif c.data == "show_stats" and c.from_user.id == SUDO_ID:
        users = len(data["users"])
        groups = len(data["groups"])
        bot.answer_callback_query(c.id)
        bot.send_message(c.message.chat.id, f"📊 آمار:\n👤 کاربران: {users}\n👥 گروه‌ها: {groups}")

    elif c.data == "broadcast" and c.from_user.id == SUDO_ID:
        bot.answer_callback_query(c.id)
        bot.send_message(c.message.chat.id, "📢 پیامت را بفرست تا برای همه ارسال شود.")
        data["broadcast_mode"] = True
        save_data(data)

    elif c.data == "leave_group" and c.from_user.id == SUDO_ID:
        if c.message.chat.type in ["group", "supergroup"]:
            bot.send_message(c.message.chat.id, "👋 ربات از گروه خارج می‌شود.")
            try:
                bot.leave_chat(c.message.chat.id)
            except:
                bot.send_message(c.message.chat.id, "⚠️ خطا در خروج از گروه.")
        else:
            bot.answer_callback_query(c.id, "فقط در گروه‌ها کار می‌کند.")

# ------------------ ادامه در بخش دوم ------------------# ------------------ بخش دوم Lux AI Panel Final ------------------

# پیام‌های ورودی
@bot.message_handler(func=lambda m: True)
def handle_messages(m):
    data = load_data()
    uid = str(m.from_user.id)

    # حالت ارسال همگانی
    if data.get("broadcast_mode") and m.from_user.id == SUDO_ID:
        total = 0
        for u in data["users"]:
            try:
                bot.send_message(u, m.text)
                total += 1
            except:
                continue
        bot.reply_to(m, f"📤 پیام به {total} کاربر ارسال شد.")
        data["broadcast_mode"] = False
        save_data(data)
        return

    # ارتباط با سازنده
    if uid in data["users"] and data["users"][uid].get("contact_mode"):
        bot.send_message(SUDO_ID, f"📩 پیام از {m.from_user.first_name} ({uid}):\n\n{m.text}")
        bot.reply_to(m, "✅ پیام شما برای سازنده ارسال شد.")
        data["users"][uid]["contact_mode"] = False
        save_data(data)
        return

    # پاسخ سازنده
    if m.reply_to_message and m.from_user.id == SUDO_ID and "📩 پیام از" in m.reply_to_message.text:
        target_id = m.reply_to_message.text.split("(")[1].split(")")[0]
        bot.send_message(target_id, f"💬 پاسخ از سازنده:\n{m.text}")
        bot.reply_to(m, "✅ پاسخ ارسال شد.")
        return

    # روشن و خاموش دستی
    if m.text == "ربات روشن" and m.from_user.id == SUDO_ID:
        data["ai_on"] = True
        save_data(data)
        bot.reply_to(m, "🤖 هوش مصنوعی فعال شد.\nچه کمکی می‌تونم بکنم؟")
        return

    if m.text == "ربات خاموش" and m.from_user.id == SUDO_ID:
        data["ai_on"] = False
        save_data(data)
        bot.reply_to(m, "⛔ هوش مصنوعی غیرفعال شد.")
        return

    # اگر ربات خاموش است
    if not data.get("ai_on", True):
        return

    # بررسی بن و سکوت
    if uid in data["banned"]:
        return
    if uid in data["muted"] and data["muted"][uid] > time.time():
        return

    # اضافه کردن کاربر جدید
    if uid not in data["users"]:
        data["users"][uid] = {"credits": 5}
        save_data(data)

    # بررسی اعتبار
    credits = data["users"][uid].get("credits", 0)
    if credits <= 0:
        bot.reply_to(m, "⚠️ اعتبار شما تمام شده!\nبرای شارژ مجدد به پشتیبانی پیام دهید: @NOORI_NOOR")
        return

    # پاسخ هوش مصنوعی
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": m.text}]
        )
        answer = response["choices"][0]["message"]["content"]
        bot.reply_to(m, answer)
        data["users"][uid]["credits"] -= 1
        save_data(data)
    except Exception as e:
        bot.reply_to(m, "❌ خطا در اتصال به هوش مصنوعی.")
        logging.error(f"AI Error: {e}")

# ------------------ دستورات مدیریتی ------------------
@bot.message_handler(func=lambda m: m.reply_to_message and m.text == "بن")
def ban_user(m):
    if m.from_user.id != SUDO_ID: return
    uid = str(m.reply_to_message.from_user.id)
    data = load_data()
    data["banned"][uid] = True
    save_data(data)
    bot.reply_to(m, f"🚫 کاربر <a href='tg://user?id={uid}'>بن شد</a> و دیگر پاسخی دریافت نمی‌کند.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text == "سکوت")
def mute_user(m):
    if m.from_user.id != SUDO_ID: return
    uid = str(m.reply_to_message.from_user.id)
    data = load_data()
    data["muted"][uid] = time.time() + 5 * 3600  # ۵ ساعت سکوت
    save_data(data)
    bot.reply_to(m, f"🔇 کاربر <a href='tg://user?id={uid}'>برای ۵ ساعت ساکت شد</a>.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text == "حذف سکوت")
def unmute_user(m):
    if m.from_user.id != SUDO_ID: return
    uid = str(m.reply_to_message.from_user.id)
    data = load_data()
    data["muted"].pop(uid, None)
    save_data(data)
    bot.reply_to(m, f"🔊 سکوت <a href='tg://user?id={uid}'>برداشته شد</a>.")

@bot.message_handler(func=lambda m: m.text.startswith("شارژ ") and m.from_user.id == SUDO_ID)
def charge_user(m):
    try:
        _, amount, username = m.text.split()
        amount = int(amount)
        data = load_data()
        target = None
        for uid, info in data["users"].items():
            if info.get("username") == username.replace("@", ""):
                target = uid
                break
        if not target:
            bot.reply_to(m, "❗ کاربر یافت نشد.")
            return
        data["users"][target]["credits"] += amount
        save_data(data)
        bot.reply_to(m, f"✅ {amount} پیام به کاربر @{username} اضافه شد.")
    except:
        bot.reply_to(m, "⚠️ فرمت صحیح: شارژ 10 @username")

# ------------------ اجرای ربات ------------------
print("🚀 Lux AI Panel Final V2.0 آماده است...")
while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        logging.error(f"Crash: {e}")
        time.sleep(5)
