# -*- coding: utf-8 -*-
# Persian Lux Smart Panel – ChatGPT Integrated Edition
# Designed and Developed by Mohammad Noori 👑

import os, json, random, time, logging
import jdatetime, telebot
from telebot import types
from openai import OpenAI

# ================= ⚙️ تنظیمات پایه =================
TOKEN = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
client = OpenAI(api_key=OPENAI_KEY)

DATA_FILE = "data.json"
LOG_FILE  = "error.log"

logging.basicConfig(filename=LOG_FILE, level=logging.ERROR,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# ================= 💾 فایل داده =================
def base_data():
    return {"users": [], "jokes": [], "falls": []}

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(base_data())
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        data = base_data()
    for k in base_data():
        if k not in data:
            data[k] = base_data()[k]
    save_data(data)
    return data

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def shamsi_date(): return jdatetime.datetime.now().strftime("%A %d %B %Y")
def shamsi_time(): return jdatetime.datetime.now().strftime("%H:%M:%S")
def cmd_text(m): return (getattr(m, "text", None) or "").strip()
def is_sudo(uid): return str(uid) == str(SUDO_ID)

# ================= 🧠 اتصال به ChatGPT =================
def ask_chatgpt(question):
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "تو یک ربات فارسی‌زبان مودب و باهوش هستی."},
                {"role": "user", "content": question}
            ],
            max_tokens=200
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"ChatGPT error: {e}")
        return "❗ خطایی در ارتباط با ChatGPT رخ داد."

# ================= 🧾 دستور /start با دکمه شیشه‌ای =================
@bot.message_handler(commands=["start"])
def start_cmd(m):
    data = load_data()
    uid = str(m.from_user.id)
    if uid not in data["users"]:
        data["users"].append(uid)
        save_data(data)

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("➕ افزودن ربات به گروه", url=f"https://t.me/{bot.get_me().username}?startgroup=true"),
        types.InlineKeyboardButton("🧑‍💻 پشتیبانی", url="https://t.me/NOORI_NOOR")
    )

    msg = (
        "👋 سلام به ربات هوشمند و مدیریتی <b>Persian Lux</b> خوش اومدی!\n\n"
        "🤖 من ساخته شده‌ام توسط <b>محمد نوری</b> ❤️\n"
        "من می‌تونم گروهت رو مدیریت کنم، فال و جوک بگم، و حتی با هوش مصنوعی ChatGPT باهات حرف بزنم 😎\n\n"
        "برای شروع می‌تونی منو به گروهت اضافه کنی یا همین‌جا باهام گپ بزنی 💬\n\n"
        f"📅 تاریخ امروز: {shamsi_date()}\n"
        f"⏰ ساعت: {shamsi_time()}"
    )
    bot.reply_to(m, msg, reply_markup=markup)

# ================= 🧩 دستورات ویژه =================
@bot.message_handler(func=lambda m: True)
def handle_all(m):
    text = cmd_text(m)
    uid = str(m.from_user.id)
    data = load_data()

    # ثبت کاربر جدید
    if uid not in data["users"]:
        data["users"].append(uid)
        save_data(data)

    # پاسخ‌های پیش‌فرض ساده
    if text in ["سلام", "سلام ربات", "هی"]:
        return bot.reply_to(m, f"✨ سلام {m.from_user.first_name}! من ربات محمد نوری هستم 🤖 چطور می‌تونم کمکت کنم؟")

    # جوک
    if text == "جوک":
        jokes = data.get("jokes", [])
        if jokes:
            return bot.reply_to(m, f"😂 {random.choice(jokes)}")
        return bot.reply_to(m, "😅 هنوز جوکی ثبت نشده!")

    # فال
    if text == "فال":
        falls = data.get("falls", [])
        if falls:
            return bot.reply_to(m, f"🔮 فال امروز:\n{random.choice(falls)}")
        return bot.reply_to(m, "😅 هنوز فالی ثبت نشده!")

    # ثبت جوک
    if m.reply_to_message and text == "ثبت جوک" and is_sudo(m.from_user.id):
        txt = (m.reply_to_message.text or "").strip()
        if not txt:
            return bot.reply_to(m, "⚠️ لطفاً روی پیام متنی ریپلای کن تا ذخیره کنم.")
        data["jokes"].append(txt)
        save_data(data)
        return bot.reply_to(m, "✅ جوک جدید ثبت شد!")

    # ثبت فال
    if m.reply_to_message and text == "ثبت فال" and is_sudo(m.from_user.id):
        txt = (m.reply_to_message.text or "").strip()
        if not txt:
            return bot.reply_to(m, "⚠️ لطفاً روی پیام متنی ریپلای کن تا ذخیره کنم.")
        data["falls"].append(txt)
        save_data(data)
        return bot.reply_to(m, "✅ فال جدید ثبت شد!")

    # لیست جوک‌ها
    if text == "لیست جوک":
        jokes = data.get("jokes", [])
        if not jokes:
            return bot.reply_to(m, "❗ هنوز جوکی ثبت نشده.")
        msg = "\n".join([f"{i+1}. {j}" for i, j in enumerate(jokes)])
        return bot.reply_to(m, f"📜 <b>لیست جوک‌ها:</b>\n{msg}")

    # لیست فال‌ها
    if text == "لیست فال":
        falls = data.get("falls", [])
        if not falls:
            return bot.reply_to(m, "❗ هنوز فالی ثبت نشده.")
        msg = "\n".join([f"{i+1}. {f}" for i, f in enumerate(falls)])
        return bot.reply_to(m, f"🔮 <b>لیست فال‌ها:</b>\n{msg}")

    # خروج از گروه
    if text == "لفت بده":
        if m.chat.type in ["group", "supergroup"]:
            bot.reply_to(m, "👋 خداحافظ دوستان 🌹")
            time.sleep(1)
            bot.leave_chat(m.chat.id)
        else:
            bot.reply_to(m, "❗ این دستور فقط در گروه کار می‌کند.")
        return

    # پاسخ از ChatGPT اگر هیچ دستور خاصی نبود
    reply = ask_chatgpt(text)
    bot.reply_to(m, reply)

# ================= 🚀 اجرای نهایی =================
print("🤖 Persian Lux Smart Panel (ChatGPT Edition - Mohammad Noori) در حال اجراست...")
while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        logging.error(f"polling crash: {e}")
        time.sleep(5)
