import telebot
from telebot import types
import openai
import os
import json

# ---- تنظیمات اصلی ----
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUDO_ID = int(os.getenv("SUDO_ID"))

bot = telebot.TeleBot(BOT_TOKEN)
openai.api_key = OPENAI_API_KEY

# ---- ذخیره‌سازی داده‌ها ----
DATA_FILE = "data.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

users = load_data()

# ---- تولید پاسخ با ChatGPT جدید ----
def chatgpt_answer(prompt):
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ خطا در پاسخ هوش مصنوعی:\n{e}"

# ---- ساخت منو ----
def main_menu(is_admin=False):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("🤖 روشن کردن ربات")
    btn2 = types.KeyboardButton("😴 خاموش کردن ربات")
    btn3 = types.KeyboardButton("💰 موجودی سکه")
    btn4 = types.KeyboardButton("⚙️ راهنما")
    btn5 = types.KeyboardButton("➕ افزودن من به گروه")
    btn6 = types.KeyboardButton("📞 ارتباط با سازنده")

    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    markup.add(btn5, btn6)

    # اگر مدیر بود، گزینه‌های ویژه اضافه کن
    if is_admin:
        markup.add("💵 شارژ سکه برای کاربر", "📊 آمار کاربران", "📢 ارسال پیام همگانی")

    return markup

# ---- شروع ربات ----
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    if user_id not in users:
        users[user_id] = {"active": False, "coins": 5}
        save_data(users)

    is_admin = message.from_user.id == SUDO_ID
    text = (
        "✨سلام {}\n"
        "من یه ربات هوش مصنوعی هستم 🤖\n"
        "می‌تونی با دستور «ربات بگو» منو روشن کنی و ازم سوال بپرسی 💬\n"
        "هر کاربر ۵ پیام رایگان داره 💎"
    ).format(message.from_user.first_name)
    bot.send_message(message.chat.id, text, reply_markup=main_menu(is_admin))

# ---- راهنما ----
@bot.message_handler(func=lambda m: m.text == "⚙️ راهنما")
def help_menu(message):
    text = (
        "📖 راهنمای استفاده از ربات:\n\n"
        "🔹 بنویس «ربات بگو» تا فعال شم\n"
        "🔹 بنویس «ربات نگو» تا خاموش شم\n"
        "🔹 هر پیام ۱ سکه مصرف می‌کنه 💰\n"
        "🔹 مدیر می‌تونه سکه شارژ کنه 💵"
    )
    bot.send_message(message.chat.id, text)

# ---- روشن کردن ربات ----
@bot.message_handler(func=lambda m: m.text == "🤖 روشن کردن ربات")
def turn_on(message):
    user_id = str(message.from_user.id)
    users[user_id]["active"] = True
    save_data(users)
    bot.send_message(message.chat.id, "✅ هوش مصنوعی فعال شد! حالا هر چی بگی جواب می‌دم 🤖")

# ---- خاموش کردن ربات ----
@bot.message_handler(func=lambda m: m.text == "😴 خاموش کردن ربات")
def turn_off(message):
    user_id = str(message.from_user.id)
    users[user_id]["active"] = False
    save_data(users)
    bot.send_message(message.chat.id, "😴 هوش مصنوعی خاموش شد.")

# ---- مشاهده سکه ----
@bot.message_handler(func=lambda m: m.text == "💰 موجودی سکه")
def check_coins(message):
    user_id = str(message.from_user.id)
    coins = users.get(user_id, {}).get("coins", 0)
    bot.send_message(message.chat.id, f"💰 موجودی سکه شما: {coins}")

# ---- پیام کاربران به هوش مصنوعی ----
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    user_id = str(message.from_user.id)

    # فقط اگه فعال بود پاسخ بده
    if user_id in users and users[user_id].get("active", False):
        if users[user_id]["coins"] <= 0 and message.from_user.id != SUDO_ID:
            bot.send_message(message.chat.id, "❌ سکه‌هات تموم شده! از مدیر بخواه شارژت کنه 💵")
            return

        users[user_id]["coins"] -= 1
        save_data(users)

        reply = chatgpt_answer(message.text)
        bot.send_message(message.chat.id, reply)

bot.infinity_polling()# ---- بخش ویژه مدیریت ----

@bot.message_handler(func=lambda m: m.text == "💵 شارژ سکه برای کاربر")
def admin_add_coins(message):
    if message.from_user.id != SUDO_ID:
        bot.send_message(message.chat.id, "🚫 فقط مدیر می‌تونه از این گزینه استفاده کنه.")
        return
    bot.send_message(message.chat.id, "👤 ریپلای کن روی پیام کاربر و بنویس مقدار سکه‌ای که می‌خوای اضافه شه (مثلاً 10).")

@bot.message_handler(func=lambda m: m.reply_to_message and m.from_user.id == SUDO_ID)
def reply_add_coins(message):
    target_id = str(message.reply_to_message.from_user.id)
    try:
        amount = int(message.text)
        if target_id not in users:
            users[target_id] = {"active": False, "coins": 0}
        users[target_id]["coins"] += amount
        save_data(users)
        bot.send_message(message.chat.id, f"✅ {amount} سکه برای کاربر {users[target_id]} اضافه شد.")
        bot.send_message(target_id, f"💰 حساب شما توسط مدیر با {amount} سکه شارژ شد! 🎉")
    except ValueError:
        bot.send_message(message.chat.id, "⚠️ لطفاً فقط عدد بفرست (مثلاً 5 یا 10).")

# ---- آمار کاربران ----
@bot.message_handler(func=lambda m: m.text == "📊 آمار کاربران")
def stats(message):
    if message.from_user.id != SUDO_ID:
        bot.send_message(message.chat.id, "🚫 فقط مدیر می‌تونه آمار ببینه.")
        return
    total = len(users)
    active = sum(1 for u in users.values() if u.get("active"))
    bot.send_message(message.chat.id, f"📊 آمار ربات:\n👥 کل کاربران: {total}\n🤖 فعال: {active}")

# ---- ارسال پیام همگانی ----
@bot.message_handler(func=lambda m: m.text == "📢 ارسال پیام همگانی")
def broadcast_start(message):
    if message.from_user.id != SUDO_ID:
        bot.send_message(message.chat.id, "🚫 فقط مدیر می‌تونه پیام همگانی بفرسته.")
        return
    bot.send_message(message.chat.id, "📝 پیامی که می‌خوای برای همه ارسال بشه رو بفرست:")

    bot.register_next_step_handler(message, broadcast_send)

def broadcast_send(message):
    if message.from_user.id != SUDO_ID:
        return
    sent, failed = 0, 0
    for uid in list(users.keys()):
        try:
            bot.send_message(uid, f"📢 پیام از طرف مدیر:\n\n{message.text}")
            sent += 1
        except:
            failed += 1
    bot.send_message(message.chat.id, f"✅ ارسال شد به {sent} نفر. ❌ ناموفق: {failed}")# ---- 🧠 بخش مخصوص مدیر (Admin Panel) ----

@bot.message_handler(func=lambda m: m.text == "💵 شارژ سکه برای کاربر")
def admin_add_coins(message):
    if message.from_user.id != SUDO_ID:
        bot.send_message(message.chat.id, "🚫 فقط مدیر می‌تونه از این گزینه استفاده کنه.")
        return
    bot.send_message(message.chat.id, "👤 ریپلای کن روی پیام کاربر و مقدار سکه‌ای که می‌خوای اضافه بشه رو بنویس (مثلاً 10).")

@bot.message_handler(func=lambda m: m.reply_to_message and m.from_user.id == SUDO_ID)
def reply_add_coins(message):
    target_id = str(message.reply_to_message.from_user.id)
    try:
        amount = int(message.text)
        if target_id not in users:
            users[target_id] = {"active": False, "coins": 0}
        users[target_id]["coins"] += amount
        save_data(users)
        bot.send_message(message.chat.id, f"✅ {amount} سکه برای کاربر {target_id} اضافه شد.")
        try:
            bot.send_message(target_id, f"💰 حسابت توسط مدیر با {amount} سکه شارژ شد! 🎉")
        except:
            pass
    except ValueError:
        bot.send_message(message.chat.id, "⚠️ لطفاً فقط عدد بفرست (مثل 5 یا 10).")

# ---- 📊 آمار کاربران ----
@bot.message_handler(func=lambda m: m.text == "📊 آمار کاربران")
def stats(message):
    if message.from_user.id != SUDO_ID:
        bot.send_message(message.chat.id, "🚫 فقط مدیر می‌تونه آمار ببینه.")
        return
    total = len(users)
    active = sum(1 for u in users.values() if u.get("active"))
    bot.send_message(message.chat.id, f"📊 آمار ربات:\n👥 کل کاربران: {total}\n🤖 فعال: {active}")

# ---- 📢 ارسال پیام همگانی ----
@bot.message_handler(func=lambda m: m.text == "📢 ارسال پیام همگانی")
def broadcast_start(message):
    if message.from_user.id != SUDO_ID:
        bot.send_message(message.chat.id, "🚫 فقط مدیر می‌تونه پیام همگانی بفرسته.")
        return
    bot.send_message(message.chat.id, "📝 پیامی که می‌خوای برای همه ارسال بشه رو بفرست:")

    bot.register_next_step_handler(message, broadcast_send)

def broadcast_send(message):
    if message.from_user.id != SUDO_ID:
        return
    sent, failed = 0, 0
    for uid in list(users.keys()):
        try:
            bot.send_message(uid, f"📢 پیام از طرف مدیر:\n\n{message.text}")
            sent += 1
        except:
            failed += 1
    bot.send_message(message.chat.id, f"✅ ارسال شد به {sent} نفر. ❌ ناموفق: {failed}")

# ---- پایان ----
print("✅ ربات با موفقیت اجرا شد و آماده پاسخ‌گویی است.")
