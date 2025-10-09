import telebot
from telebot import types
import openai
import os, json
from datetime import datetime, timedelta

# ⚙️ تنظیمات متغیرهای محیطی
BOT_TOKEN = os.getenv("BOT_TOK")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
SUDO_ID = int(os.getenv("SUDO_ID") or 0)

openai.api_key = OPENAI_KEY
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# 📁 مدیریت داده‌ها
DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        d = {"users": {}, "groups": {}, "bans": {}, "mutes": {}, "charges": {}}
        save_data(d)
        return d
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
    except:
        d = {"users": {}, "groups": {}, "bans": {}, "mutes": {}, "charges": {}}
    for key in ["users", "groups", "bans", "mutes", "charges"]:
        if key not in d:
            d[key] = {}
    return d

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

d = load_data()

# 🧠 منوی شروع
def main_menu():
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.add("📘 راهنما", "👨‍💻 ارتباط با سازنده", "➕ افزودن من به گروه")
    return menu

# 📜 راهنما
HELP_TEXT = """
🤖 <b>دستیار هوشمند نوری</b>

سلام! من با هوش مصنوعی کار می‌کنم و می‌تونم بهت کمک کنم —  
برای فعال شدن در گفتگو فقط بنویس:
🔹 <b>ربات بگو</b> برای فعال‌سازی
🔹 <b>ربات نگو</b> برای توقف پاسخ‌دهی

اگر مدیر گروه هستی:
• دستور <code>شارژ X</code> با ریپلای روی گروه: فعال برای X روز
• دستور <code>بن</code> یا <code>سکوت</code> برای کنترل اعضا
• دستور <code>لفت بده</code> برای خروج ربات از گروه
"""

# 🚀 استارت ربات
@bot.message_handler(commands=['start'])
def start(msg):
    user = str(msg.from_user.id)
    if user not in d["users"]:
        d["users"][user] = {"limit": 5, "active": False}
        save_data(d)
    name = msg.from_user.first_name
    text = f"سلام 👋\nمن دستیار هوشمند نوری هستم 🤖!\nمی‌تونم با هوش مصنوعی کمکت کنم، {name} عزیز 💫\n\nبرای شروع بنویس <b>ربات بگو</b> تا فعال شم!\n👇 برای راهنما دکمه پایین رو بزن"
    bot.send_message(msg.chat.id, text, reply_markup=main_menu())# 🎛 پنل مدیریت (فقط برای SUDO_ID)
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
        types.InlineKeyboardButton("🔄 راه‌اندازی مجدد", callback_data="restart")
    )
    bot.send_message(msg.chat.id, "🔰 پنل مدیریتی فعال است:", reply_markup=markup)

# 🪄 پاسخ به دکمه‌های پنل
@bot.callback_query_handler(func=lambda c: True)
def callback(c):
    if c.from_user.id != SUDO_ID:
        bot.answer_callback_query(c.id, "فقط سازنده می‌تواند از این بخش استفاده کند ❌", show_alert=True)
        return

    if c.data == "groups":
        text = "📋 گروه‌های فعال:\n"
        if not d["groups"]:
            text += "هیچ گروه فعالی ثبت نشده."
        else:
            for g in d["groups"]:
                text += f"• {g} — {d['groups'][g].get('expire', 'بدون زمان')}\n"
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
        bot.send_message(c.message.chat.id, "برای شارژ گروه در خود گروه دستور زیر را بزن:\n\n<code>شارژ X</code> (X = تعداد روزها)")

    elif c.data == "restart":
        bot.send_message(c.message.chat.id, "♻️ ربات با موفقیت ریستارت شد.")
        os._exit(0)


# 🧠 فعال / غیرفعال کردن هوش مصنوعی
@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["ربات بگو", "ربات بگو🤖"])
def activate_ai(msg):
    uid = str(msg.from_user.id)
    d["users"][uid]["active"] = True
    save_data(d)
    bot.send_message(msg.chat.id, "🤖 حالت هوش مصنوعی فعال شد! حالا می‌تونم باهات صحبت کنم 🌟")

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
    bot.reply_to(msg.reply_to_message, "🚫 کاربر بن شد، دیگر پاسخی دریافت نمی‌کند.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text.startswith("سکوت") and m.from_user.id == SUDO_ID)
def mute_user(msg):
    uid = str(msg.reply_to_message.from_user.id)
    d["mutes"][uid] = (datetime.now() + timedelta(hours=5)).isoformat()
    save_data(d)
    bot.reply_to(msg.reply_to_message, "🔇 کاربر به مدت ۵ ساعت در سکوت است.")

@bot.message_handler(func=lambda m: m.text.lower().startswith("لفت بده") and m.from_user.id == SUDO_ID)
def leave_group(msg):
    bot.send_message(msg.chat.id, "👋 با اجازه، از گروه خارج می‌شوم.")
    bot.leave_chat(msg.chat.id)


# ⚡ شارژ گروه
@bot.message_handler(func=lambda m: m.reply_to_message and m.text.startswith("شارژ") and m.from_user.id == SUDO_ID)
def charge_group(msg):
    try:
        days = int(msg.text.split()[1])
        gid = str(msg.reply_to_message.chat.id)
        expire_date = (datetime.now() + timedelta(days=days)).isoformat()
        d["groups"][gid] = {"expire": expire_date}
        save_data(d)
        bot.reply_to(msg.reply_to_message, f"✅ گروه برای {days} روز شارژ شد.")
    except:
        bot.reply_to(msg, "⚠️ دستور اشتباه است. مثال:\n<code>شارژ 3</code>")


# 💬 پاسخ به پیام‌های کاربران
@bot.message_handler(func=lambda m: True)
def handle_message(msg):
    uid = str(msg.from_user.id)
    cid = msg.chat.id

    # 🔹 جلوگیری از خطا در صورت حذف دیتا
    if "bans" not in d: d["bans"] = {}
    if "users" not in d: d["users"] = {}

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
        bot.send_message(cid, "⚠️ محدودیت پیام شما تمام شده.\nبرای ادامه، منتظر شارژ شوید یا دوباره فعال کنید.")
        return

    # 🎯 پاسخ هوش مصنوعی
    try:
        r = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": msg.text}]
        )
        answer = r.choices[0].message.content
        bot.reply_to(msg, answer)
        d["users"][uid]["limit"] -= 1
        save_data(d)
    except Exception as e:
        bot.send_message(cid, f"❌ خطا در ارتباط با سرور:\n{e}")

# 🔁 اجرای همیشگی ربات
bot.infinity_polling()
