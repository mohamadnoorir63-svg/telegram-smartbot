# -*- coding: utf-8 -*-
# Persian Smart Panel – Final Build (AI + Admin + Coins + Support)
# Designed for Mohammad 👑

import os, json, time, logging, datetime, random
import telebot
from telebot import types
import openai

# ================= ⚙️ تنظیمات اصلی =================
TOKEN   = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
openai.api_key = OPENAI_KEY

DATA_FILE = "data.json"
LOG_FILE  = "error.log"

logging.basicConfig(filename=LOG_FILE, level=logging.ERROR,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# ================= 💾 فایل داده خودترمیمی =================
def base_data():
    return {
        "users": {},
        "coins": {},
        "banned": [],
        "muted": {},
        "ai_active": True,
        "groups": {},
        "support": {}
    }

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(base_data())
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        data = base_data()
        save_data(data)
    base = base_data()
    fixed = False
    for k in base:
        if k not in data:
            data[k] = base[k]
            fixed = True
    if fixed:
        save_data(data)
    return data

# ================= 🧩 ابزارها =================
def is_sudo(uid): return str(uid) == str(SUDO_ID)
def now(): return datetime.datetime.now().strftime("%H:%M:%S")
def today(): return datetime.datetime.now().strftime("%Y-%m-%d")

# ================= ⚙️ پنل سودو =================
def admin_panel():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📊 آمار", "📢 ارسال همگانی",
               "💰 شارژ کاربر", "🔋 شارژ گروه",
               "🔇 سکوت", "🚫 بن",
               "⬅️ لفت بده", "📨 پیام‌ها")
    return markup

# ================= ⚙️ پنل کاربر =================
def user_panel():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("💡 راهنما", "🔋 شارژ مجدد",
               "📞 پشتیبانی", "👤 سازنده",
               "➕ افزودن به گروه")
    return markup

# ================= 💬 استارت =================
@bot.message_handler(commands=["start"])
def start_cmd(m):
    d = load_data()
    uid = str(m.from_user.id)
    if uid not in d["users"]:
        d["users"][uid] = {"messages": 0, "charged": False, "mute_until": None}
    save_data(d)
    text = (
        "👋 سلام! به ربات هوشمند <b>Persian Smart Panel</b> خوش اومدی!\n\n"
        "🤖 اینجا می‌تونی با هوش مصنوعی حرف بزنی، سوال بپرسی، یا حتی کمک بگیری.\n"
        "💬 هر کاربر ۵ پیام رایگان داره، بعدش می‌تونه با دکمه «🔋 شارژ مجدد» ادامه بده.\n\n"
        "⚙️ سازنده: <a href='tg://user?id={0}'>محمد نوری</a>".format(SUDO_ID)
    )
    if is_sudo(m.from_user.id):
        bot.send_message(m.chat.id, "👑 سلام رئیس! وارد پنل مدیریتی شدی.", reply_markup=admin_panel())
    else:
        bot.send_message(m.chat.id, text, reply_markup=user_panel())

# ================= 🚫 بن و 🔇 سکوت =================
@bot.message_handler(func=lambda m: m.reply_to_message and m.text == "🚫 بن")
def ban_user(m):
    if not is_sudo(m.from_user.id): return
    d = load_data()
    uid = str(m.reply_to_message.from_user.id)
    if uid not in d["banned"]:
        d["banned"].append(uid)
    save_data(d)
    bot.reply_to(m, "🚫 کاربر بن شد و دیگر پاسخ نمی‌گیرد.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text == "🔇 سکوت")
def mute_user(m):
    if not is_sudo(m.from_user.id): return
    d = load_data()
    uid = str(m.reply_to_message.from_user.id)
    until = time.time() + 5*3600
    d["muted"][uid] = until
    save_data(d)
    bot.reply_to(m, "🔕 کاربر برای ۵ ساعت ساکت شد.")

# ================= ↩️ لفت بده =================
@bot.message_handler(func=lambda m: m.text == "⬅️ لفت بده")
def leave_chat(m):
    if not is_sudo(m.from_user.id): return
    try:
        bot.send_message(m.chat.id, "👋 ربات در حال خروج از گروه است...")
        bot.leave_chat(m.chat.id)
    except:
        bot.reply_to(m, "❗ خطا در خروج از گروه.")# ================= 💬 پاسخ هوش مصنوعی =================
def ai_answer(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.error(f"OpenAI error: {e}")
        return "❗ خطایی در پاسخ هوش مصنوعی رخ داد."

@bot.message_handler(func=lambda m: True, content_types=["text"])
def handle_ai(m):
    d = load_data()
    uid = str(m.from_user.id)
    txt = m.text.strip()

    # 🧱 جلوگیری از خطاهای کلید
    if uid not in d["users"]:
        d["users"][uid] = {"messages": 0, "charged": False, "mute_until": None}
    if uid not in d["coins"]:
        d["coins"][uid] = 0
    save_data(d)

    # 🚫 بن / سکوت
    if uid in d["banned"]:
        return
    if uid in d["muted"] and d["muted"][uid] and time.time() < d["muted"][uid]:
        return

    # 🧠 فرمان‌های سودو
    if is_sudo(uid):
        if txt == "📢 ارسال همگانی":
            d["support"]["mode"] = "broadcast"
            save_data(d)
            return bot.reply_to(m, "📨 پیام خود را ریپلای کن تا همگانی شود.")
        if txt.startswith("💰 شارژ کاربر"):
            return bot.reply_to(m, "روی پیام کاربر ریپلای کن و بنویس: شارژ 3")
        if txt.startswith("🔋 شارژ گروه"):
            return bot.reply_to(m, "در گروه بنویس: شارژ گروه 2 (برای دو روز)")

    # 💌 سیستم پشتیبانی پیام‌رسان
    if txt == "📞 پشتیبانی":
        d["support"][uid] = {"waiting": True}
        save_data(d)
        return bot.reply_to(m, "📨 پیام خود را ارسال کنید تا پشتیبانی پاسخ دهد.")
    if uid in d["support"] and d["support"][uid].get("waiting"):
        bot.send_message(SUDO_ID, f"📩 پیام جدید از {m.from_user.first_name} ({uid}):\n\n{txt}")
        bot.reply_to(m, "✅ پیام شما برای پشتیبانی ارسال شد. لطفاً منتظر پاسخ باشید.")
        d["support"][uid]["waiting"] = False
        save_data(d)
        return

    # 💬 پاسخ سودو به کاربران از طریق ریپلای
    if is_sudo(m.from_user.id) and m.reply_to_message and "از" in m.reply_to_message.text:
        try:
            target_id = m.reply_to_message.text.split("(")[1].split(")")[0]
            bot.send_message(target_id, f"💬 پاسخ پشتیبانی:\n{txt}")
            bot.reply_to(m, "✅ پیام ارسال شد.")
        except Exception as e:
            bot.reply_to(m, f"⚠️ خطا در ارسال پیام: {e}")
        return

    # 🔋 شارژ کاربر یا گروه
    if is_sudo(m.from_user.id) and m.reply_to_message and txt.startswith("شارژ "):
        try:
            days = int(txt.split()[1])
            target = str(m.reply_to_message.from_user.id)
            until = time.time() + days * 86400
            d["users"][target]["charged"] = until
            save_data(d)
            return bot.reply_to(m, f"✅ کاربر برای {days} روز شارژ شد.")
        except:
            return bot.reply_to(m, "⚠️ فرمت درست: شارژ 2")

    if is_sudo(m.from_user.id) and txt.startswith("شارژ گروه "):
        try:
            days = int(txt.split()[2])
            gid = str(m.chat.id)
            until = time.time() + days * 86400
            d["groups"][gid] = until
            save_data(d)
            return bot.reply_to(m, f"✅ گروه برای {days} روز شارژ شد.")
        except:
            return bot.reply_to(m, "⚠️ فرمت درست: شارژ گروه 2")

    # 💰 سیستم سکه برای کاربران
    if txt == "🔋 شارژ مجدد":
        return bot.reply_to(m, "💎 برای دریافت سکه، به پشتیبانی پیام بده تا شارژت کنم.")

    # 👤 اطلاعات سازنده و افزودن
    if txt == "👤 سازنده":
        return bot.reply_to(m, "👑 سازنده: محمد نوری\n🆔 @NOORI_NOOR")

    if txt == "➕ افزودن به گروه":
        return bot.reply_to(m, "📎 لینک افزودن ربات به گروه:\nhttps://t.me/{0}?startgroup=true".format(bot.get_me().username))

    if txt == "💡 راهنما":
        return bot.reply_to(m, "📘 برای گفت‌وگو با هوش مصنوعی فقط پیام خود را بنویسید!\nهر کاربر ۵ پیام رایگان دارد.\n\n🔋 برای شارژ بیشتر از دکمه شارژ مجدد استفاده کنید.")

    # 💬 پاسخ هوش مصنوعی
    d = load_data()
    user = d["users"][uid]
    coins = d["coins"].get(uid, 0)
    now_time = time.time()

    # بررسی شارژ یا پیام رایگان
    charged = user.get("charged", False)
    if charged and now_time > charged:
        user["charged"] = False
        save_data(d)
        charged = False

    if not charged and user["messages"] >= 5 and coins <= 0:
        return bot.reply_to(m, "⚠️ شارژ شما تمام شده است!\nبرای ادامه دکمه «🔋 شارژ مجدد» را بزنید.")

    reply = ai_answer(txt)
    bot.send_chat_action(m.chat.id, "typing")
    bot.reply_to(m, reply)

    # ثبت استفاده از پیام یا مصرف سکه
    user["messages"] += 1
    if not charged:
        d["coins"][uid] = max(0, coins - 1)
    save_data(d)

# ================= 🚀 اجرای نهایی =================
print("🤖 Persian Smart Panel Final (AI + Admin + Coins) Running...")
while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        logging.error(f"polling crash: {e}")
        time.sleep(5)
