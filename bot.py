import telebot
import os
from openai import OpenAI
from datetime import datetime
import json

# 📦 متغیرهای اصلی (از Heroku Config Vars)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))

bot = telebot.TeleBot(BOT_TOKEN)
client = OpenAI(api_key=OPENAI_KEY)

# 📁 فایل دیتابیس کاربران
DB_FILE = "users.json"
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump({"users": {}, "banned": [], "muted": []}, f)

def read_db():
    with open(DB_FILE, "r") as f:
        return json.load(f)

def write_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

# 🏁 شروع
@bot.message_handler(commands=["start"])
def start_message(message):
    bot.reply_to(message, f"""
👋 سلام {message.from_user.first_name}  
من **ربات هوشمند نوری 🤖** هستم!

با هوش مصنوعی ChatGPT بهت کمک می‌کنم 🌟  
برای فعال‌سازی بنویس: **ربات بگو**  
برای خاموش کردن: **ربات نگو**

📘 از دکمه‌های زیر استفاده کن 👇
""", reply_markup=main_menu())

# 🧭 منوی اصلی
def main_menu():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("📘 راهنما", callback_data="help"),
        telebot.types.InlineKeyboardButton("💬 ارتباط با سازنده", url="https://t.me/NoorirSmartBot")
    )
    markup.add(telebot.types.InlineKeyboardButton("➕ افزودن من به گروه", url="https://t.me/NoorirSmartBot?startgroup=true"))
    return markup

@bot.callback_query_handler(func=lambda call: True)
def callback_buttons(c):
    if c.data == "help":
        text = """📚 راهنمای ربات هوشمند نوری:

🔹 بنویس "ربات بگو" تا فعال شم  
🔹 بنویس "ربات نگو" تا خاموش شم  
🔹 هر پیام ۱ سکه مصرف می‌کند  
🔹 مدیر می‌تواند سکه شارژ کند 💰  
"""
        try:
            bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=main_menu())
        except:
            bot.send_message(c.message.chat.id, text, reply_markup=main_menu())

# 💬 پاسخ به پیام‌ها
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    uid = str(message.from_user.id)
    data = read_db()

    # 🔒 بن یا سکوت
    if uid in data.get("banned", []):
        return
    if uid in data.get("muted", []):
        bot.reply_to(message, "🔇 شما در حالت سکوت هستید و نمی‌توانید پیام دهید.")
        return

    # 🧩 ثبت کاربر جدید
    if uid not in data["users"]:
        data["users"][uid] = {"coins": 5, "active": True}
        write_db(data)

    user = data["users"][uid]

    # خاموش؟
    if not user["active"]:
        if "ربات بگو" in message.text:
            user["active"] = True
            write_db(data)
            bot.reply_to(message, "✅ هوش مصنوعی فعال شد.")
        return

    # خاموش کردن
    if "ربات نگو" in message.text:
        user["active"] = False
        write_db(data)
        bot.reply_to(message, "❌ هوش مصنوعی خاموش شد.")
        return

    # پنل مدیر
    if message.text.startswith("/admin") and message.from_user.id == SUDO_ID:
        return admin_panel(message)

    # ⚡ سکه چک
    if user["coins"] <= 0:
        bot.reply_to(message, "💸 اعتبارت تموم شده! از مدیر بخواه شارژت کنه.")
        return

    # 🧠 پاسخ ChatGPT جدید
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a smart Persian AI assistant."},
                {"role": "user", "content": message.text}
            ]
        )
        answer = response.choices[0].message.content
        bot.reply_to(message, f"🤖 پاسخ:\n{answer}")

        # کم کردن ۱ سکه
        user["coins"] -= 1
        write_db(data)
    except Exception as e:
        bot.reply_to(message, f"⚠️ خطا در پاسخ هوش مصنوعی:\n{e}")

# 🎛 پنل مدیر
def admin_panel(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("💰 شارژ سکه", callback_data="add_coins"),
        telebot.types.InlineKeyboardButton("🚫 بن کاربر", callback_data="ban_user")
    )
    markup.row(
        telebot.types.InlineKeyboardButton("🔇 سکوت", callback_data="mute_user"),
        telebot.types.InlineKeyboardButton("👋 لفت بده", callback_data="leave_group")
    )
    markup.row(
        telebot.types.InlineKeyboardButton("📤 ارسال همگانی", callback_data="broadcast")
    )
    bot.reply_to(message, "📍 پنل مدیریتی فعال شد:", reply_markup=markup)

# 🧠 دستورات مدیر
@bot.callback_query_handler(func=lambda c: c.data in ["add_coins", "ban_user", "mute_user", "broadcast", "leave_group"])
def admin_actions(c):
    data = read_db()

    if c.from_user.id != SUDO_ID:
        bot.answer_callback_query(c.id, "فقط مدیر مجاز است!", show_alert=True)
        return

    if c.data == "add_coins":
        bot.send_message(c.message.chat.id, "💰 آیدی عددی کاربر و مقدار سکه را وارد کن:\nمثال:\n7089376754 10")
        bot.register_next_step_handler(c.message, add_coins)
    elif c.data == "ban_user":
        bot.send_message(c.message.chat.id, "🚫 آیدی عددی کاربری که می‌خواهی بن شود را بفرست:")
        bot.register_next_step_handler(c.message, ban_user)
    elif c.data == "mute_user":
        bot.send_message(c.message.chat.id, "🔇 آیدی عددی کاربر برای سکوت را بفرست:")
        bot.register_next_step_handler(c.message, mute_user)
    elif c.data == "broadcast":
        bot.send_message(c.message.chat.id, "📢 پیامی که می‌خواهی همگانی ارسال شود را بنویس:")
        bot.register_next_step_handler(c.message, broadcast)
    elif c.data == "leave_group":
        bot.send_message(c.message.chat.id, "👋 در حال ترک گروه...")
        bot.leave_chat(c.message.chat.id)

# 💰 شارژ سکه
def add_coins(message):
    try:
        uid, coins = message.text.split()
        data = read_db()
        uid = str(uid)
        coins = int(coins)
        if uid not in data["users"]:
            data["users"][uid] = {"coins": 0, "active": True}
        data["users"][uid]["coins"] += coins
        write_db(data)
        bot.reply_to(message, f"✅ {coins} سکه به کاربر {uid} اضافه شد.")
    except:
        bot.reply_to(message, "❌ فرمت اشتباه است. مثال درست:\n7089376754 10")

# 🚫 بن
def ban_user(message):
    uid = message.text.strip()
    data = read_db()
    if uid not in data["banned"]:
        data["banned"].append(uid)
        write_db(data)
        bot.reply_to(message, f"🚫 کاربر {uid} بن شد.")
    else:
        bot.reply_to(message, "⚠️ قبلاً بن شده.")

# 🔇 سکوت
def mute_user(message):
    uid = message.text.strip()
    data = read_db()
    if uid not in data["muted"]:
        data["muted"].append(uid)
        write_db(data)
        bot.reply_to(message, f"🔇 کاربر {uid} در حالت سکوت قرار گرفت.")
    else:
        bot.reply_to(message, "⚠️ این کاربر قبلاً سایلنت بوده.")

# 📢 ارسال همگانی
def broadcast(message):
    text = message.text
    data = read_db()
    for uid in data["users"].keys():
        try:
            bot.send_message(uid, f"📢 پیام مدیر:\n{text}")
        except:
            pass
    bot.reply_to(message, "✅ پیام همگانی ارسال شد.")

print("🤖 SmartBot-Noori آماده به کار است...")
bot.infinity_polling()
