import telebot, openai, json, os
from telebot import types
from datetime import datetime, timedelta

# 🧠 دریافت متغیرها از Config Vars در Heroku
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")
SUDO_ID = int(os.getenv("SUDO_ID"))

# ✅ تنظیمات اولیه
openai.api_key = OPENAI_KEY
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# 📁 مدیریت فایل داده‌ها
DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "groups": {}, "bans": {}, "mutes": {}, "charges": {}}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"users": {}, "groups": {}, "bans": {}, "mutes": {}, "charges": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

d = load_data()

# 🌟 استارت
@bot.message_handler(commands=['start'])
def start(msg):
    uid = str(msg.from_user.id)
    if uid not in d["users"]:
        d["users"][uid] = {"active": False, "limit": 5}
        save_data(d)

    name = msg.from_user.first_name
    text = f"سلام {name} 👋\nمن دستیار هوشمند نوری هستم 🤖!\nمی‌تونم با هوش مصنوعی بهت کمک کنم.\n\nبرای فعال‌سازی بنویس <b>ربات بگو</b> تا شروع کنیم 🌟\n\nبرای راهنما از دکمه‌های زیر استفاده کن 👇"
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📘 راهنما", callback_data="help"),
        types.InlineKeyboardButton("💬 ارتباط با سازنده", url="https://t.me/NOORI_NOOR")
    )
    markup.add(types.InlineKeyboardButton("➕ افزودن من به گروه", url=f"https://t.me/{bot.get_me().username}?startgroup=true"))
    bot.send_message(msg.chat.id, text, reply_markup=markup)

# 🎓 پنل راهنما
@bot.callback_query_handler(func=lambda c: c.data == "help")
def help_callback(c):
    text = """📘 <b>راهنمای استفاده از ربات هوشمند نوری:</b>

🟢 برای فعال کردن پاسخ هوش مصنوعی:
➖ بنویس «ربات بگو»

🔴 برای غیرفعال کردن:
➖ بنویس «ربات نگو»

🧠 قابلیت‌ها:
• گفتگو و پاسخ هوش مصنوعی ChatGPT
• شارژ گروهی و محدودیت پیام‌ها
• بن، سکوت و خروج ربات از گروه
• پنل مدیریت مخصوص سازنده
"""
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=None)
    except:
        bot.send_message(c.message.chat.id, text)

# 🎛 پنل مدیریت (فقط برای SUDO_ID)
@bot.message_handler(commands=['panel'])
def admin_panel(msg):
    if msg.from_user.id != SUDO_ID:
        return
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("👥 لیست گروه‌ها", callback_data="groups"),
        types.InlineKeyboardButton("🚫 لیست بن‌ها", callback_data="bans")
    )
    markup.add(
        types.InlineKeyboardButton("🔋 شارژ گروه", callback_data="charge"),
        types.InlineKeyboardButton("🔄 ریستارت", callback_data="restart")
    )
    bot.send_message(msg.chat.id, "🛠 <b>پنل مدیریت</b> فعال است:", reply_markup=markup)

# 🔧 پاسخ دکمه‌های پنل
@bot.callback_query_handler(func=lambda c: True)
def callback(c):
    if c.from_user.id != SUDO_ID:
        bot.answer_callback_query(c.id, "فقط سازنده می‌تواند از این بخش استفاده کند ❌", show_alert=True)
        return

    if c.data == "groups":
        text = "📋 گروه‌های فعال:\n"
        if not d["groups"]:
            text += "هیچ گروهی ثبت نشده."
        else:
            for g in d["groups"]:
                exp = d["groups"][g].get("expire", "نامشخص")
                text += f"• {g} — {exp}\n"
        bot.send_message(c.message.chat.id, text)

    elif c.data == "bans":
        text = "🚫 کاربران بن‌شده:\n"
        if not d["bans"]:
            text += "لیست بن خالی است."
        else:
            for u in d["bans"]:
                text += f"• {u}\n"
        bot.send_message(c.message.chat.id, text)

    elif c.data == "charge":
        bot.send_message(c.message.chat.id, "برای شارژ گروه در همان گروه بنویس:\n<code>شارژ X</code> (X=تعداد روزها)")

    elif c.data == "restart":
        bot.send_message(c.message.chat.id, "♻️ ربات ریستارت شد.")
        os._exit(0)

# 🧠 فعال/غیرفعال کردن هوش مصنوعی
@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["ربات بگو", "ربات بگو🤖"])
def activate_ai(msg):
    uid = str(msg.from_user.id)
    d["users"][uid]["active"] = True
    save_data(d)
    bot.send_message(msg.chat.id, "🤖 حالت هوش مصنوعی فعال شد!")

@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["ربات نگو", "ربات نگو🤐"])
def deactivate_ai(msg):
    uid = str(msg.from_user.id)
    d["users"][uid]["active"] = False
    save_data(d)
    bot.send_message(msg.chat.id, "😶 حالت هوش مصنوعی غیرفعال شد!")

# 🚫 بن / سکوت / لفت بده
@bot.message_handler(func=lambda m: m.reply_to_message and m.text.startswith("بن") and m.from_user.id == SUDO_ID)
def ban_user(msg):
    uid = str(msg.reply_to_message.from_user.id)
    d["bans"][uid] = True
    save_data(d)
    bot.reply_to(msg.reply_to_message, "🚫 کاربر بن شد.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text.startswith("سکوت") and m.from_user.id == SUDO_ID)
def mute_user(msg):
    uid = str(msg.reply_to_message.from_user.id)
    d["mutes"][uid] = (datetime.now() + timedelta(hours=5)).isoformat()
    save_data(d)
    bot.reply_to(msg.reply_to_message, "🔇 کاربر برای ۵ ساعت در سکوت است.")

@bot.message_handler(func=lambda m: m.text.lower().startswith("لفت بده") and m.from_user.id == SUDO_ID)
def leave_group(msg):
    bot.send_message(msg.chat.id, "👋 با اجازه، از گروه خارج می‌شوم.")
    bot.leave_chat(msg.chat.id)

# ⚡ شارژ گروه
@bot.message_handler(func=lambda m: m.text.startswith("شارژ") and m.from_user.id == SUDO_ID)
def charge_group(msg):
    try:
        days = int(msg.text.split()[1])
        gid = str(msg.chat.id)
        expire_date = (datetime.now() + timedelta(days=days)).isoformat()
        d["groups"][gid] = {"expire": expire_date}
        save_data(d)
        bot.send_message(msg.chat.id, f"✅ گروه برای {days} روز شارژ شد.")
    except:
        bot.send_message(msg.chat.id, "⚠️ دستور اشتباه است.\nمثال: <code>شارژ 3</code>")

# 💬 پاسخ هوش مصنوعی
@bot.message_handler(func=lambda m: True)
def handle_message(msg):
    uid = str(msg.from_user.id)
    cid = msg.chat.id

    # جلوگیری از KeyError
    for k in ["bans", "users", "mutes", "groups", "charges"]:
        if k not in d:
            d[k] = {}
    save_data(d)

    # 🚫 بن‌شده‌ها
    if uid in d["bans"]:
        return

    # 🔇 سکوت‌شده‌ها
    if uid in d["mutes"]:
        mute_until = datetime.fromisoformat(d["mutes"][uid])
        if datetime.now() < mute_until:
            return
        else:
            del d["mutes"][uid]
            save_data(d)

    # فقط اگر فعال بود پاسخ بده
    if not d["users"].get(uid, {}).get("active", False):
        return

    # بررسی محدودیت ۵ پیام
    if d["users"][uid]["limit"] <= 0:
        bot.send_message(cid, "⚠️ محدودیت پیام شما تمام شده.\nبرای ادامه منتظر شارژ باشید.")
        return

    # 🎯 پاسخ ChatGPT
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": msg.text}]
        )
        answer = response.choices[0].message.content
        bot.reply_to(msg, answer)
        d["users"][uid]["limit"] -= 1
        save_data(d)
    except Exception as e:
        bot.send_message(cid, f"❌ خطا در ارتباط با سرور:\n{e}")

# 🔁 اجرای مداوم
bot.infinity_polling()
