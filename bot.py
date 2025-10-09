# -*- coding: utf-8 -*-
import os, json, time, pytz, datetime
import telebot
from telebot import types
from openai import OpenAI

# ===== تنظیمات اصلی =====
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = telebot.TeleBot(TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)

# ===== توابع داده =====
def load_data():
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"users": {}, "banned": {}, "muted": {}}

def save_data(data):
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

# ===== منوی کاربر =====
def user_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🧠 روشن / خاموش", "💎 سکه من")
    markup.add("💡 راهنما", "☎️ پشتیبانی")
    markup.add("👤 سازنده", "➕ افزودن به گروه")
    return markup

# ===== منوی مدیر =====
def admin_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 آمار کاربران", "💰 شارژ کاربر")
    markup.add("🔇 سکوت کاربر", "🚫 بن کاربر")
    markup.add("📢 ارسال همگانی", "↩️ لفت بده")
    markup.add("بازگشت 🔙")
    return markup

# ===== شروع =====
@bot.message_handler(commands=['start'])
def start(m):
    uid = str(m.chat.id)
    if uid not in data["users"]:
        data["users"][uid] = {"coins": 5, "active": True}
        save_data(data)

    if str(m.chat.id) == str(ADMIN_ID):
        bot.send_message(m.chat.id, "👑 سلام رئیس! وارد پنل مدیریتی شدی.", reply_markup=admin_menu())
    else:
        bot.send_message(
            m.chat.id,
            "🤖 سلام!\nبه ربات هوش مصنوعی نوری خوش اومدی 🌙\n\n"
            "💬 با من حرف بزن، سوال بپرس یا کمک بخواه.\n"
            "هر کاربر ۵ پیام رایگان داره، بعدش باید شارژ مجدد انجام بدی 💎",
            reply_markup=user_menu()
        )

# ===== راهنما =====
@bot.message_handler(func=lambda m: m.text == "💡 راهنما")
def help_msg(m):
    bot.send_message(
        m.chat.id,
        "📘 راهنمای استفاده از ربات:\n"
        "🔹 بنویس «روشن / خاموش» برای فعال یا غیرفعال کردن.\n"
        "🔹 هر پیام یک سکه مصرف می‌کند.\n"
        "🔹 با دکمه پشتیبانی مستقیماً با سازنده در تماس باش.\n"
        "🔹 مدیر می‌تواند کاربران را شارژ یا بن کند."
    )

# ===== روشن / خاموش =====
@bot.message_handler(func=lambda m: m.text == "🧠 روشن / خاموش")
def toggle_ai(m):
    uid = str(m.chat.id)
    user = data["users"].get(uid, {"coins": 5, "active": True})
    user["active"] = not user["active"]
    data["users"][uid] = user
    save_data(data)
    msg = "✅ هوش مصنوعی فعال شد!" if user["active"] else "😴 هوش مصنوعی غیرفعال شد."
    bot.send_message(m.chat.id, msg)

# ===== سکه من =====
@bot.message_handler(func=lambda m: m.text == "💎 سکه من")
def my_coins(m):
    uid = str(m.chat.id)
    coins = data["users"].get(uid, {}).get("coins", 0)
    bot.send_message(m.chat.id, f"💰 موجودی سکه شما: {coins}")

# ===== سازنده =====
@bot.message_handler(func=lambda m: m.text == "👤 سازنده")
def creator(m):
    bot.send_message(
        m.chat.id,
        "👨‍💻 سازنده: محمد نوری\n"
        "📱 ارتباط مستقیم: @NOORI_NOOR\n"
        "✨ قدرت‌گرفته از ChatGPT 5"
    )

# ===== افزودن به گروه =====
@bot.message_handler(func=lambda m: m.text == "➕ افزودن به گروه")
def add_to_group(m):
    bot.send_message(
        m.chat.id,
        f"📎 برای افزودن من به گروه، روی لینک زیر بزن:\n"
        f"https://t.me/{bot.get_me().username}?startgroup=true"
    )

# ===== درخواست پشتیبانی =====
@bot.message_handler(func=lambda m: m.text == "☎️ پشتیبانی")
def support_start(m):
    uid = str(m.chat.id)
    bot.send_message(m.chat.id, "📩 لطفاً پیام خود را بنویسید تا به مدیر ارسال شود.")
    data["users"][uid]["await_support"] = True
    save_data(data)# ===== پاسخ پشتیبانی =====
@bot.message_handler(func=lambda m: str(m.chat.id) != str(ADMIN_ID))
def handle_user_support(m):
    uid = str(m.chat.id)
    user = data["users"].get(uid, {})
    if user.get("await_support"):
        msg = f"📨 پیام جدید از کاربر:\n\n👤 {m.from_user.first_name}\n🆔 {uid}\n\n💬 {m.text}"
        bot.send_message(ADMIN_ID, msg)
        user["await_support"] = False
        save_data(data)
        bot.send_message(m.chat.id, "✅ پیام شما ارسال شد. منتظر پاسخ باشید.")
    else:
        handle_ai(m)

# ===== پاسخ مدیر به کاربر =====
@bot.message_handler(func=lambda m: str(m.chat.id) == str(ADMIN_ID) and m.reply_to_message)
def reply_user(m):
    try:
        lines = m.reply_to_message.text.split("🆔 ")
        uid = lines[1].split("\n")[0].strip()
        bot.send_message(int(uid), f"💬 پاسخ پشتیبانی:\n{m.text}")
        bot.send_message(ADMIN_ID, "✅ پاسخ ارسال شد.")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ خطا در ارسال پاسخ: {e}")

# ===== هوش مصنوعی ChatGPT =====
def handle_ai(m):
    uid = str(m.chat.id)
    user = data["users"].get(uid)
    if not user or not user.get("active", True):
        return
    if uid in data.get("banned", {}):
        return bot.send_message(m.chat.id, "🚫 شما از استفاده از ربات مسدود شدید.")
    if uid in data.get("muted", {}) and time.time() < data["muted"][uid]:
        return bot.send_message(m.chat.id, "🔇 شما موقتاً در حالت سکوت هستید.")

    coins = user.get("coins", 0)
    if coins <= 0:
        return bot.send_message(m.chat.id, "⚠️ موجودی شما تمام شده است.\nبرای شارژ مجدد با پشتیبانی تماس بگیرید.")

    try:
        reply = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": m.text}]
        )
        answer = reply.choices[0].message.content
        bot.send_message(m.chat.id, f"🤖 {answer}")
        user["coins"] -= 1
        save_data(data)
    except Exception as e:
        bot.send_message(m.chat.id, "❌ خطا در ارتباط با هوش مصنوعی.")

# ===== آمار =====
@bot.message_handler(func=lambda m: str(m.chat.id) == str(ADMIN_ID) and m.text == "📊 آمار کاربران")
def stats(m):
    users = len(data["users"])
    banned = len(data["banned"])
    muted = len(data["muted"])
    bot.send_message(m.chat.id, f"📈 کاربران: {users}\n🚫 بن‌شده: {banned}\n🔇 در سکوت: {muted}")

# ===== شارژ کاربر =====
@bot.message_handler(func=lambda m: str(m.chat.id) == str(ADMIN_ID) and m.text.startswith("💰 شارژ "))
def charge_user(m):
    try:
        parts = m.text.split()
        uid = parts[2]
        coins = int(parts[3])
        if uid not in data["users"]:
            return bot.send_message(m.chat.id, "❗ کاربر یافت نشد.")
        data["users"][uid]["coins"] += coins
        save_data(data)
        bot.send_message(int(uid), f"🎁 شما {coins} سکه جدید دریافت کردید!")
        bot.send_message(m.chat.id, "✅ شارژ انجام شد.")
    except:
        bot.send_message(m.chat.id, "⚠️ فرمت درست: 💰 شارژ [uid] [تعداد]")

# ===== سکوت =====
@bot.message_handler(func=lambda m: str(m.chat.id) == str(ADMIN_ID) and m.text.startswith("🔇 سکوت "))
def mute_user(m):
    try:
        parts = m.text.split()
        uid = parts[2]
        hours = int(parts[3]) if len(parts) > 3 else 5
        data["muted"][uid] = time.time() + (hours * 3600)
        save_data(data)
        bot.send_message(int(uid), f"🔇 شما برای {hours} ساعت در حالت سکوت قرار گرفتید.")
        bot.send_message(m.chat.id, "✅ سکوت اعمال شد.")
    except:
        bot.send_message(m.chat.id, "⚠️ فرمت درست: 🔇 سکوت [uid] [ساعت]")

# ===== بن =====
@bot.message_handler(func=lambda m: str(m.chat.id) == str(ADMIN_ID) and m.text.startswith("🚫 بن "))
def ban_user(m):
    try:
        uid = m.text.split()[2]
        data["banned"][uid] = True
        save_data(data)
        bot.send_message(int(uid), "🚫 شما از ربات بن شدید.")
        bot.send_message(m.chat.id, f"✅ کاربر {uid} بن شد.")
    except:
        bot.send_message(m.chat.id, "⚠️ فرمت درست: 🚫 بن [uid]")

# ===== ارسال همگانی =====
@bot.message_handler(func=lambda m: str(m.chat.id) == str(ADMIN_ID) and m.text == "📢 ارسال همگانی")
def start_broadcast(m):
    bot.send_message(m.chat.id, "✍️ پیام خود را ریپلای کنید تا به همه ارسال شود.")

@bot.message_handler(func=lambda m: str(m.chat.id) == str(ADMIN_ID) and m.reply_to_message)
def broadcast(m):
    msg = m.reply_to_message
    count = 0
    for uid in data["users"]:
        try:
            if msg.text:
                bot.send_message(int(uid), msg.text)
            count += 1
        except:
            pass
    bot.send_message(m.chat.id, f"📢 پیام برای {count} کاربر ارسال شد.")

# ===== لفت بده =====
@bot.message_handler(func=lambda m: str(m.chat.id) == str(ADMIN_ID) and m.text == "↩️ لفت بده")
def leave_group(m):
    try:
        bot.leave_chat(m.chat.id)
    except:
        bot.send_message(m.chat.id, "❌ خطا در خروج از گروه.")

# ===== اجرای ربات =====
print("🤖 Bot is running...")
while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        print("⛔ خطا:", e)
        time.sleep(5)
