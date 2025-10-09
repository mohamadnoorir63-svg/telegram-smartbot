import telebot, json, datetime, os, openai
from telebot import types

# =============== تنظیمات پایه ===============
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_KEY")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))  # آیدی عددی مدیر اصلی

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
openai.api_key = OPENAI_KEY

DATA_FILE = "data.json"

# =============== داده‌های ذخیره‌شده ===============
def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({"users": {}, "bans": []}, f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

d = load_data()

# =============== منوی اصلی ===============
def main_menu():
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.row("📘 راهنما", "ارتباط با سازنده 💬")
    menu.row("➕ افزودن من به گروه")
    return menu

# =============== استارت کاربر ===============
@bot.message_handler(commands=["start"])
def start(msg):
    uid = str(msg.from_user.id)
    if uid not in d["users"]:
        d["users"][uid] = {"coins": 5, "active": True, "joined": str(datetime.date.today())}
        save_data(d)
    bot.send_message(
        msg.chat.id,
        f"""
سلام 👋
من <b>دستیار هوشمند نوری</b> هستم 🤖  
با بهره‌گیری از <b>هوش مصنوعی ChatGPT</b> آماده‌ام به پرسش‌هایت پاسخ دهم.

برای فعال‌سازی گفت‌وگوی هوش مصنوعی، عبارت <b>ربات بگو</b> را بنویس.

از دکمه‌های زیر نیز می‌توانی استفاده کنی 👇
        """,
        reply_markup=main_menu(),
    )

# =============== راهنما ===============
@bot.message_handler(func=lambda m: m.text == "📘 راهنما")
def help_menu(msg):
    bot.send_message(
        msg.chat.id,
        """
📘 <b>راهنمای استفاده از ربات هوشمند نوری</b>

🔹 برای فعال‌سازی هوش مصنوعی بنویس: <b>ربات بگو</b>  
🔹 برای غیرفعال کردن بنویس: <b>ربات نگو</b>  
🔹 هر پاسخ، ۱ سکه مصرف می‌کند.  
🔹 برای مشاهده موجودی سکه‌هایت بنویس: <b>/coin</b>  

👑 مدیریت: آقای <b>محمد نوری</b>  
@NoorirSmartBot
        """,
    )

# =============== ارتباط با سازنده ===============
@bot.message_handler(func=lambda m: m.text == "ارتباط با سازنده 💬")
def contact(msg):
    bot.send_message(
        msg.chat.id,
        "📩 لطفاً پیام خود را ارسال کنید تا برای مدیریت فرستاده شود.",
    )
    bot.register_next_step_handler(msg, forward_to_admin)

def forward_to_admin(msg):
    bot.forward_message(SUDO_ID, msg.chat.id, msg.message_id)
    bot.send_message(msg.chat.id, "✅ پیام شما برای مدیریت ارسال شد.")

# =============== نمایش سکه‌ها ===============
@bot.message_handler(commands=["coin"])
def my_coin(msg):
    uid = str(msg.from_user.id)
    coins = d["users"].get(uid, {}).get("coins", 0)
    bot.send_message(msg.chat.id, f"💰 موجودی فعلی شما: <b>{coins}</b> سکه")

# ادامه در بخش ۲ 👇
# شامل: ChatGPT پاسخ‌گویی، شارژ سکه، پنل مدیریت، لفت، بن و سکوت# =============== پاسخ ChatGPT با محدودیت سکه ===============
@bot.message_handler(func=lambda m: True)
def handle_message(msg):
    uid = str(msg.from_user.id)
    text = msg.text.strip()

    # جلوگیری از خطا در صورت نبود داده‌ها
    if "bans" not in d:
        d["bans"] = []
        save_data(d)

    if uid in d["bans"]:
        bot.reply_to(msg, "⛔ شما از استفاده از ربات محروم شده‌اید.")
        return

    if uid not in d["users"]:
        d["users"][uid] = {"coins": 5, "active": True, "joined": str(datetime.date.today())}
        save_data(d)

    user = d["users"][uid]

    # کنترل فعال/غیرفعال
    if text.lower() in ["ربات بگو", "فعال"]:
        user["active"] = True
        save_data(d)
        bot.reply_to(msg, "✅ هوش مصنوعی فعال شد! حالا می‌تونی سؤال بپرسی.")
        return
    elif text.lower() in ["ربات نگو", "غیرفعال"]:
        user["active"] = False
        save_data(d)
        bot.reply_to(msg, "🤖 هوش مصنوعی غیرفعال شد.")
        return

    # پاسخ ChatGPT فقط وقتی فعال است
    if user.get("active"):
        coins = user.get("coins", 0)
        if coins <= 0:
            bot.reply_to(msg, "❌ موجودی سکه شما تمام شده است. برای شارژ از مدیر درخواست کنید.")
            return

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful Persian assistant."},
                    {"role": "user", "content": text},
                ],
            )
            answer = response.choices[0].message["content"]
            bot.reply_to(msg, answer)
            user["coins"] -= 1
            save_data(d)
        except Exception as e:
            bot.reply_to(msg, f"⚠️ خطا در پاسخ هوش مصنوعی:\n<code>{e}</code>")
    else:
        pass


# =============== پنل مدیر ===============
@bot.message_handler(commands=["admin"])
def admin_panel(msg):
    if msg.from_user.id != SUDO_ID:
        return
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("👥 کاربران", callback_data="users"))
    keyboard.add(types.InlineKeyboardButton("💰 شارژ سکه", callback_data="charge"))
    keyboard.add(types.InlineKeyboardButton("🚫 بن کاربر", callback_data="ban"))
    keyboard.add(types.InlineKeyboardButton("🔇 سکوت کاربر", callback_data="mute"))
    keyboard.add(types.InlineKeyboardButton("👋 لفت بده", callback_data="leave"))
    keyboard.add(types.InlineKeyboardButton("📤 ارسال همگانی", callback_data="broadcast"))
    bot.send_message(msg.chat.id, "📍 پنل مدیریتی فعال شد:", reply_markup=keyboard)


# =============== دکمه‌های پنل مدیر ===============
@bot.callback_query_handler(func=lambda c: True)
def callback(c):
    if c.message.chat.id != SUDO_ID:
        return

    if c.data == "users":
        bot.send_message(c.message.chat.id, f"👥 تعداد کاربران فعلی: {len(d['users'])}")

    elif c.data == "charge":
        bot.send_message(c.message.chat.id, "💰 فرمت شارژ: \n<code>شارژ 123456 20</code>")
    elif c.data == "ban":
        bot.send_message(c.message.chat.id, "🚫 فرمت بن: \n<code>بن 123456</code>")
    elif c.data == "mute":
        bot.send_message(c.message.chat.id, "🔇 فرمت سکوت: \n<code>سکوت 123456</code>")
    elif c.data == "leave":
        bot.send_message(c.message.chat.id, "👋 فرمت لفت: \n<code>لفت</code>")
    elif c.data == "broadcast":
        bot.send_message(c.message.chat.id, "📤 پیام خود را برای ارسال همگانی بنویس:")
        bot.register_next_step_handler(c.message, broadcast)


# =============== شارژ، بن، سکوت، لفت ===============
@bot.message_handler(func=lambda m: m.text and m.from_user.id == SUDO_ID)
def admin_cmd(msg):
    parts = msg.text.split()
    if msg.text.startswith("شارژ "):
        try:
            uid = parts[1]
            amount = int(parts[2])
            if uid in d["users"]:
                d["users"][uid]["coins"] += amount
                save_data(d)
                bot.reply_to(msg, f"✅ {amount} سکه به کاربر {uid} اضافه شد.")
            else:
                bot.reply_to(msg, "❌ کاربر یافت نشد.")
        except:
            bot.reply_to(msg, "❗ فرمت نادرست است.")
    elif msg.text.startswith("بن "):
        try:
            uid = parts[1]
            d["bans"].append(uid)
            save_data(d)
            bot.reply_to(msg, f"🚫 کاربر {uid} بن شد.")
        except:
            bot.reply_to(msg, "❗ فرمت نادرست.")
    elif msg.text == "لفت":
        bot.leave_chat(msg.chat.id)
    elif msg.text.startswith("سکوت "):
        bot.reply_to(msg, "⏱ سکوت موقت برای ۵ ساعت فعال شد (نمونه ساده).")


# =============== ارسال همگانی ===============
def broadcast(msg):
    count = 0
    for uid in d["users"]:
        try:
            bot.send_message(uid, msg.text)
            count += 1
        except:
            pass
    bot.send_message(msg.chat.id, f"📢 پیام برای {count} کاربر ارسال شد.")


# =============== اجرای ربات ===============
print("🤖 ربات هوشمند نوری با موفقیت فعال شد.")
bot.infinity_polling()
