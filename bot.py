import telebot
from telebot import types
import openai
import os
import json
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUDO_ID = int(os.getenv("SUDO_ID"))  # آیدی عددی مدیر

bot = telebot.TeleBot(BOT_TOKEN)
openai.api_key = OPENAI_API_KEY

DATA_FILE = "users.json"

# -------------------- مدیریت داده‌ها --------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

users = load_data()

# -------------------- دکمه‌های عمومی --------------------
def user_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🧠 روشن کردن ربات", "😴 خاموش کردن ربات")
    markup.add("💰 موجودی سکه", "⚙️ راهنما")
    markup.add("➕ افزودن من به گروه", "📞 ارتباط با سازنده")
    return markup

def admin_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🧠 روشن کردن ربات", "😴 خاموش کردن ربات")
    markup.add("💰 موجودی سکه", "⚙️ راهنما")
    markup.add("➕ افزودن من به گروه", "📞 ارتباط با سازنده")
    markup.add("📊 آمار کاربران", "💵 شارژ سکه برای کاربر")
    markup.add("📣 ارسال پیام همگانی")
    return markup

# -------------------- شروع ربات --------------------
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    if user_id not in users:
        users[user_id] = {"active": False, "coins": 5}
        save_data(users)

    if message.from_user.id == SUDO_ID:
        bot.send_message(message.chat.id, f"👑 سلام {message.from_user.first_name}!\nبه پنل مدیریتی خوش اومدی.", reply_markup=admin_menu())
    else:
        bot.send_message(message.chat.id, f"✨سلام {message.from_user.first_name}\nمن یه ربات هوش مصنوعی هستم 🤖\nمی‌تونی با دستور «ربات بگو» منو فعال کنی.\nهر کاربر ۵ پیام رایگان داره 💎", reply_markup=user_menu())

# -------------------- راهنما --------------------
@bot.message_handler(func=lambda m: m.text == "⚙️ راهنما")
def help_msg(message):
    bot.reply_to(message, "📖 راهنمای استفاده از ربات:\n\n🔹 بنویس «ربات بگو» تا فعال شم\n🔹 بنویس «ربات نگو» تا خاموش شم\n🔹 هر پیام ۱ سکه مصرف می‌کنه 💰\n🔹 مدیر می‌تونه سکه شارژ کنه 💵")

# -------------------- موجودی --------------------
@bot.message_handler(func=lambda m: m.text == "💰 موجودی سکه")
def coins(message):
    user_id = str(message.from_user.id)
    coins = users.get(user_id, {}).get("coins", 0)
    bot.reply_to(message, f"💰 موجودی سکه شما: {coins}")

# -------------------- فعال و غیرفعال --------------------
@bot.message_handler(func=lambda m: m.text == "🧠 روشن کردن ربات")
def activate(message):
    user_id = str(message.from_user.id)
    users[user_id]["active"] = True
    save_data(users)
    bot.reply_to(message, "✅ ربات فعال شد! حالا می‌تونی پیام‌هاتو بفرستی 🌟")

@bot.message_handler(func=lambda m: m.text == "😴 خاموش کردن ربات")
def deactivate(message):
    user_id = str(message.from_user.id)
    users[user_id]["active"] = False
    save_data(users)
    bot.reply_to(message, "❌ ربات غیرفعال شد. برای روشن کردن دوباره، روی دکمه روشن بزن 🤖")

# -------------------- پنل مدیر --------------------
@bot.message_handler(func=lambda m: m.text == "📊 آمار کاربران" and m.from_user.id == SUDO_ID)
def stats(message):
    total_users = len(users)
    bot.reply_to(message, f"📊 تعداد کل کاربران: {total_users}")

@bot.message_handler(func=lambda m: m.text == "💵 شارژ سکه برای کاربر" and m.from_user.id == SUDO_ID)
def ask_id(message):
    msg = bot.reply_to(message, "🆔 آیدی عددی کاربر رو بفرست:")
    bot.register_next_step_handler(msg, process_coin_id)

def process_coin_id(message):
    uid = message.text.strip()
    if uid not in users:
        bot.reply_to(message, "❌ کاربر یافت نشد.")
        return
    msg = bot.reply_to(message, "مقدار شارژ سکه رو بفرست 💰:")
    bot.register_next_step_handler(msg, lambda m: add_coins(uid, m))

def add_coins(uid, message):
    try:
        amount = int(message.text)
        users[uid]["coins"] += amount
        save_data(users)
        bot.reply_to(message, f"✅ {amount} سکه به کاربر {uid} اضافه شد.")
    except:
        bot.reply_to(message, "❌ مقدار اشتباهه.")

@bot.message_handler(func=lambda m: m.text == "📣 ارسال پیام همگانی" and m.from_user.id == SUDO_ID)
def broadcast(message):
    msg = bot.reply_to(message, "📢 پیام همگانی رو بفرست:")
    bot.register_next_step_handler(msg, send_broadcast)

def send_broadcast(message):
    for uid in users.keys():
        try:
            bot.send_message(uid, message.text)
        except:
            pass
    bot.reply_to(message, "📢 پیام برای همه ارسال شد.")

# -------------------- پاسخ هوش مصنوعی --------------------
@bot.message_handler(func=lambda m: True)
def ai_reply(message):
    user_id = str(message.from_user.id)

    if user_id not in users or not users[user_id].get("active"):
        return

    if users[user_id]["coins"] <= 0:
        bot.reply_to(message, "❌ موجودی سکه شما تموم شده! از مدیر بخواه شارژت کنه 💵")
        return

    users[user_id]["coins"] -= 1
    save_data(users)

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": message.text}]
        )
        reply = response.choices[0].message.content
        bot.reply_to(message, reply)
    except Exception as e:
        bot.reply_to(message, f"⚠️ خطا در پاسخ: {e}")

print("🤖 Bot is running...")
bot.infinity_polling()
