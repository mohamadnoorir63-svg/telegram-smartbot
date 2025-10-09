import telebot, json, time, logging, os
from datetime import datetime, timedelta
import openai

# 🌟 تنظیمات اصلی
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
SUDO_ID = 612345678  # آیدی عددی تو (تغییر بده)

openai.api_key = OPENAI_KEY
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# 📁 فایل داده
DATA_FILE = "data.json"
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"users": {}, "groups": {}, "active_ai": True}, f)

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def user_register(uid):
    data = load_data()
    if str(uid) not in data["users"]:
        data["users"][str(uid)] = {"messages": 0, "charged_until": None}
        save_data(data)

# 💬 درخواست به ChatGPT
def ask_ai(prompt):
    try:
        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return res.choices[0].message["content"]
    except Exception as e:
        return f"⚠️ خطا در اتصال به سرور: {e}"

# 🎛 کیبورد اصلی
def main_keyboard():
    kb = telebot.types.InlineKeyboardMarkup()
    kb.add(
        telebot.types.InlineKeyboardButton("📚 راهنما", callback_data="help"),
        telebot.types.InlineKeyboardButton("📞 ارتباط با سازنده", callback_data="contact")
    )
    kb.add(
        telebot.types.InlineKeyboardButton("💎 افزایش اعتبار", url="https://t.me/NOORI_NOOR"),
        telebot.types.InlineKeyboardButton("➕ افزودن به گروه", url=f"https://t.me/{bot.get_me().username}?startgroup=true")
    )
    return kb# ===================== ⚙️ مدیریت و کنترل =====================

@bot.message_handler(commands=['start'])
def start_message(m):
    user_register(m.from_user.id)
    name = m.from_user.first_name
    bot.send_message(
        m.chat.id,
        f"👋 سلام <b>{name}</b>!\n"
        "من 🤖 <b>ربات هوش مصنوعی نوری</b> هستم.\n\n"
        "✨ شما ۵ پیام رایگان دارید.\n"
        "برای شروع بنویس <b>ربات بگو</b> تا فعال شم 💬\n\n"
        "از منوهای زیر استفاده کن 👇",
        reply_markup=main_keyboard()
    )

@bot.message_handler(func=lambda m: m.text and m.text.lower() == "ربات بگو")
def turn_on_ai(m):
    data = load_data()
    data["active_ai"] = True
    save_data(data)
    bot.reply_to(m, "✅ هوش مصنوعی فعال شد.\nچه کمکی می‌تونم بکنم؟ 💡")

@bot.message_handler(func=lambda m: m.text and m.text.lower() == "ربات نگو")
def turn_off_ai(m):
    data = load_data()
    data["active_ai"] = False
    save_data(data)
    bot.reply_to(m, "🤖 هوش مصنوعی غیرفعال شد.\nبرای فعال‌سازی دوباره بنویس <b>ربات بگو</b>")

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("شارژ "))
def charge_user(m):
    if m.from_user.id != SUDO_ID:
        return
    try:
        days = int(m.text.split(" ")[1])
        if m.reply_to_message:
            uid = m.reply_to_message.from_user.id
            data = load_data()
            exp = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M")
            data["users"][str(uid)]["charged_until"] = exp
            save_data(data)
            bot.reply_to(m, f"✅ کاربر {uid} برای {days} روز شارژ شد 🌟")
            bot.send_message(uid, f"💎 حساب شما تا {exp} فعال شد!\nاز ربات بدون محدودیت استفاده کن 😍")
    except:
        bot.reply_to(m, "❌ فرمت نادرست است. روی پیام کاربر ریپلای بزن و بنویس:\n<code>شارژ 3</code>")

@bot.message_handler(func=lambda m: m.text and m.text.lower() == "لفت بده")
def leave_group(m):
    if m.from_user.id == SUDO_ID and m.chat.type in ["group", "supergroup"]:
        bot.send_message(m.chat.id, "👋 خداحافظ! به امید دیدار 💫")
        bot.leave_chat(m.chat.id)

# 🎯 پاسخ به پیام‌ها
@bot.message_handler(func=lambda m: True)
def chat_ai(m):
    if m.chat.type not in ["private", "group", "supergroup"]:
        return

    data = load_data()
    user_register(m.from_user.id)
    user = data["users"][str(m.from_user.id)]
    ai_on = data["active_ai"]

    # بررسی فعال بودن هوش مصنوعی
    if not ai_on:
        return

    # بررسی شارژ
    charged = user["charged_until"]
    now = datetime.now()
    if charged:
        if now < datetime.strptime(charged, "%Y-%m-%d %H:%M"):
            reply = ask_ai(m.text)
            bot.reply_to(m, reply)
            return

    # بررسی تعداد پیام رایگان
    if user["messages"] < 5:
        reply = ask_ai(m.text)
        bot.reply_to(m, reply)
        user["messages"] += 1
        save_data(data)
    else:
        bot.reply_to(m, "⚠️ اعتبار رایگان شما تمام شد.\nبرای شارژ مجدد به پشتیبانی پیام دهید 💌 @NOORI_NOOR")# ===================== 🌐 پنل و راهنما =====================

# ✳️ راهنما
@bot.callback_query_handler(func=lambda c: c.data == "help")
def help_callback(c):
    bot.answer_callback_query(c.id)
    msg = (
        "📘 <b>راهنمای استفاده از ربات نوری</b>\n\n"
        "✨ برای شروع بنویس: <b>ربات بگو</b>\n"
        "🤫 برای خاموش کردن بنویس: <b>ربات نگو</b>\n"
        "🧠 ازم بپرس هر چی خواستی — برنامه‌نویسی، ترجمه، مشاوره و حتی شعر! 😄\n\n"
        "💎 هر کاربر ۵ پیام رایگان دارد، برای استفاده نامحدود باید شارژ شود.\n"
        "📨 جهت شارژ به پشتیبانی پیام بده 👉 @NOORI_NOOR"
    )
    bot.edit_message_text(msg, c.message.chat.id, c.message.message_id, reply_markup=main_keyboard())

# ✉️ ارتباط با سازنده
waiting_contact = {}

@bot.callback_query_handler(func=lambda c: c.data == "contact")
def contact_callback(c):
    bot.answer_callback_query(c.id)
    uid = c.from_user.id
    waiting_contact[uid] = True
    bot.send_message(uid, "📩 پیام خود را بنویسید تا برای سازنده ارسال شود:")

@bot.message_handler(func=lambda m: m.from_user.id in waiting_contact)
def forward_to_owner(m):
    del waiting_contact[m.from_user.id]
    bot.send_message(SUDO_ID, f"📬 پیام از {m.from_user.first_name} ({m.from_user.id}):\n\n{m.text}")
    bot.reply_to(m, "✅ پیام شما برای سازنده ارسال شد.\nمنتظر پاسخ باشید 💬")

# 💚 وضعیت ربات و شارژ
@bot.callback_query_handler(func=lambda c: c.data == "status")
def status_callback(c):
    bot.answer_callback_query(c.id)
    data = load_data()
    user = data["users"].get(str(c.from_user.id))
    if not user:
        bot.send_message(c.from_user.id, "❌ شما هنوز ثبت‌نام نکردید. بنویس /start")
        return

    charged_until = user.get("charged_until")
    if charged_until:
        status = f"💎 تا تاریخ {charged_until} فعال هستی."
    else:
        status = f"⚠️ هنوز شارژ نداری. پیام‌های رایگان: {max(0, 5 - user['messages'])}"

    bot.send_message(c.from_user.id, f"📊 وضعیت شما:\n{status}", reply_markup=main_keyboard())

# ===================== 🚀 اجرای نهایی =====================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("🤖 Bot is running...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
