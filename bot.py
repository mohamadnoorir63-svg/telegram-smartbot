# main.py
# -*- coding: utf-8 -*-
import os, json, time, logging
from datetime import datetime, timedelta
import telebot
from telebot import types
import openai

# =============== تنظیمات اصلی ===============
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not BOT_TOKEN or not OPENAI_API_KEY:
    raise ValueError("❌ لطفاً BOT_TOKEN و OPENAI_API_KEY را در Heroku تنظیم کنید.")

openai.api_key = OPENAI_API_KEY
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

DATA_FILE = "data.json"
logging.basicConfig(filename="bot.log", level=logging.ERROR)

# =============== ذخیره داده ===============
def load_data():
    if not os.path.exists(DATA_FILE):
        save_data({
            "ai_on": False,
            "users": {},
            "meta": {"free_msgs": 5},
            "awaiting_contact": {},
            "awaiting_broadcast": False,
            "awaiting_reset": False
        })
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

DATA = load_data()

def ensure_user(uid):
    uid = str(uid)
    if uid not in DATA["users"]:
        DATA["users"][uid] = {
            "credits": DATA["meta"]["free_msgs"],
            "banned": False,
            "muted_until": None
        }
        save_data(DATA)

# =============== توابع کمکی ===============
def is_banned(uid):
    return DATA["users"].get(str(uid), {}).get("banned", False)

def is_muted(uid):
    u = DATA["users"].get(str(uid), {})
    if not u.get("muted_until"):
        return False
    until = datetime.fromisoformat(u["muted_until"])
    if datetime.utcnow() > until:
        u["muted_until"] = None
        save_data(DATA)
        return False
    return True

def ask_openai(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "شما یک دستیار فارسی مودب و باهوش هستید."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=600
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.error(str(e))
        return None# =============== ساخت پنل‌ها ===============
def user_panel():
    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("📞 ارتباط با سازنده", callback_data="contact_admin"),
        types.InlineKeyboardButton("📗 راهنما", callback_data="help_user")
    )
    kb.row(
        types.InlineKeyboardButton("💳 افزایش اعتبار", callback_data="recharge"),
        types.InlineKeyboardButton("🟢 وضعیت ربات", callback_data="status")
    )
    kb.row(
        types.InlineKeyboardButton("➕ افزودن به گروه", url=f"https://t.me/{bot.get_me().username}?startgroup=true")
    )
    return kb

def admin_panel():
    kb = types.InlineKeyboardMarkup()
    kb.row(types.InlineKeyboardButton("📊 آمار", callback_data="admin_stats"))
    kb.row(
        types.InlineKeyboardButton("📢 ارسال همگانی", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("💰 افزودن اعتبار", callback_data="admin_add_credit")
    )
    kb.row(types.InlineKeyboardButton("♻️ ریست داده‌ها", callback_data="admin_reset"))
    return kb

# =============== دستورات شروع / راهنما ===============
@bot.message_handler(commands=["start"])
def start(m):
    ensure_user(m.from_user.id)
    credits = DATA["users"][str(m.from_user.id)]["credits"]
    msg = (
        f"👋 سلام {m.from_user.first_name}!\n"
        f"من ربات هوش مصنوعی <b>نوری</b> هستم 🤖\n\n"
        f"✨ شما {credits} پیام رایگان دارید.\n"
        "برای شروع از منوهای زیر استفاده کنید 👇"
    )
    bot.send_message(m.chat.id, msg, reply_markup=user_panel())

@bot.callback_query_handler(func=lambda c: c.data == "help_user")
def help_user(c):
    bot.answer_callback_query(c.id)
    txt = (
        "📘 <b>راهنمای استفاده:</b>\n"
        "• بنویس هر سوالی داری، من با هوش مصنوعی جواب می‌دم.\n"
        "• با دستور <b>ربات روشن</b> یا <b>خاموش</b>، مدیر می‌تونه هوش مصنوعی رو فعال یا غیرفعال کنه.\n"
        "• برای افزایش اعتبار، روی «💳 افزایش اعتبار» بزن.\n"
        "• برای ارتباط با سازنده، دکمه 📞 رو بزن.\n"
        "\n🔹 سازنده: <b>محمد نوری</b> (@NOORI_NOOR)"
    )
    bot.send_message(c.message.chat.id, txt)

# =============== وضعیت کاربر ===============
@bot.callback_query_handler(func=lambda c: c.data == "status")
def status(c):
    bot.answer_callback_query(c.id)
    ensure_user(c.from_user.id)
    state = "✅ روشن" if DATA["ai_on"] else "❌ خاموش"
    credits = DATA["users"][str(c.from_user.id)]["credits"]
    bot.send_message(c.message.chat.id, f"🧠 وضعیت هوش مصنوعی: {state}\n💎 اعتبار شما: {credits} پیام")

# =============== ارتباط با سازنده ===============
@bot.callback_query_handler(func=lambda c: c.data == "contact_admin")
def contact_admin(c):
    bot.answer_callback_query(c.id)
    ensure_user(c.from_user.id)
    DATA["awaiting_contact"][str(c.from_user.id)] = True
    save_data(DATA)
    bot.send_message(c.message.chat.id, "✉️ پیام خود را بنویسید تا برای سازنده ارسال شود.")

@bot.message_handler(func=lambda m: DATA["awaiting_contact"].get(str(m.from_user.id)))
def handle_contact(m):
    DATA["awaiting_contact"].pop(str(m.from_user.id), None)
    save_data(DATA)
    text = (
        f"📩 پیام از @{m.from_user.username or m.from_user.first_name}\n"
        f"ID: {m.from_user.id}\n\n"
        f"{m.text}"
    )
    bot.send_message(SUDO_ID, text)
    bot.reply_to(m, "✅ پیام شما ارسال شد و بزودی پاسخ داده می‌شود.")

# =============== افزایش اعتبار ===============
@bot.callback_query_handler(func=lambda c: c.data == "recharge")
def recharge(c):
    bot.answer_callback_query(c.id)
    text = (
        "💳 برای افزایش اعتبار، درخواست شما برای سازنده ارسال می‌شود.\n"
        "سازنده پس از بررسی اعتبار شما را شارژ می‌کند."
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("ارسال درخواست شارژ", callback_data="send_recharge"))
    bot.send_message(c.message.chat.id, text, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == "send_recharge")
def send_recharge(c):
    bot.answer_callback_query(c.id)
    msg = f"📤 درخواست شارژ از @{c.from_user.username or c.from_user.first_name} (ID: {c.from_user.id})"
    bot.send_message(SUDO_ID, msg)
    bot.send_message(c.message.chat.id, "✅ درخواست شما ارسال شد.")

# =============== منطق پاسخ خودکار ===============
@bot.message_handler(func=lambda m: m.text and not m.text.startswith("/"))
def ai_answer(m):
    uid = str(m.from_user.id)
    ensure_user(uid)
    user = DATA["users"][uid]

    # بن / سکوت
    if user["banned"]:
        return
    if user["muted_until"]:
        mute_time = datetime.fromisoformat(user["muted_until"])
        if datetime.utcnow() < mute_time:
            return

    # بررسی وضعیت هوش
    if not DATA["ai_on"]:
        return

    # بررسی اعتبار
    if user["credits"] <= 0 and m.from_user.id != SUDO_ID:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("💳 افزایش اعتبار", callback_data="recharge"))
        bot.reply_to(m, "⚠️ اعتبار شما تمام شده است. برای شارژ مجدد از گزینه زیر استفاده کنید.", reply_markup=kb)
        return

    # کسر اعتبار
    if m.from_user.id != SUDO_ID:
        user["credits"] -= 1
        save_data(DATA)

    bot.send_chat_action(m.chat.id, "typing")
    prompt = f"کاربر {m.from_user.first_name} گفت: {m.text}\nپاسخ را به زبان فارسی مودبانه و کوتاه بنویس."
    answer = ask_openai(prompt)

    if not answer:
        bot.reply_to(m, "❌ خطایی در ارتباط با سرور هوش مصنوعی رخ داد.")
        if m.from_user.id != SUDO_ID:
            user["credits"] += 1
            save_data(DATA)
        return

    bot.reply_to(m, answer)# =============== کنترل هوش و مدیریت ===============

@bot.message_handler(func=lambda m: m.text in ["ربات روشن", "هوش مصنوعی روشن"] and m.from_user.id == SUDO_ID)
def ai_on(m):
    DATA["ai_on"] = True
    save_data(DATA)
    bot.reply_to(m, "🟢 هوش مصنوعی فعال شد — چه کمکی می‌تونم بکنم؟")

@bot.message_handler(func=lambda m: m.text in ["ربات خاموش", "هوش مصنوعی خاموش"] and m.from_user.id == SUDO_ID)
def ai_off(m):
    DATA["ai_on"] = False
    save_data(DATA)
    bot.reply_to(m, "🔴 هوش مصنوعی غیرفعال شد.")

# دستور آمار ربات
@bot.callback_query_handler(func=lambda c: c.data == "admin_stats")
def admin_stats(c):
    if c.from_user.id != SUDO_ID:
        return bot.answer_callback_query(c.id, "فقط سازنده مجاز است.")
    users_count = len(DATA["users"])
    active = "✅ روشن" if DATA["ai_on"] else "❌ خاموش"
    msg = f"📊 آمار ربات:\n👥 کاربران: {users_count}\n🧠 وضعیت هوش: {active}"
    bot.send_message(c.message.chat.id, msg)

# ارسال همگانی
@bot.callback_query_handler(func=lambda c: c.data == "admin_broadcast")
def admin_broadcast(c):
    if c.from_user.id != SUDO_ID:
        return
    bot.send_message(c.message.chat.id, "📢 لطفاً پیامی که می‌خواهی به همه کاربران ارسال شود را بفرست.")
    DATA["awaiting_broadcast"] = True
    save_data(DATA)

@bot.message_handler(func=lambda m: DATA.get("awaiting_broadcast") and m.from_user.id == SUDO_ID)
def handle_broadcast(m):
    DATA["awaiting_broadcast"] = False
    save_data(DATA)
    sent = 0
    for uid in DATA["users"].keys():
        try:
            bot.send_message(int(uid), f"📢 پیام از سازنده:\n\n{m.text}")
            sent += 1
        except:
            pass
    bot.reply_to(m, f"✅ پیام برای {sent} کاربر ارسال شد.")

# افزودن اعتبار دستی
@bot.callback_query_handler(func=lambda c: c.data == "admin_add_credit")
def admin_add_credit(c):
    if c.from_user.id != SUDO_ID:
        return
    bot.send_message(c.message.chat.id, "📥 بنویس: اضافه کن <user_id> <تعداد>")
    DATA["awaiting_credit"] = True
    save_data(DATA)

@bot.message_handler(func=lambda m: DATA.get("awaiting_credit") and m.from_user.id == SUDO_ID)
def handle_add_credit(m):
    DATA["awaiting_credit"] = False
    save_data(DATA)
    try:
        parts = m.text.split()
        uid, count = parts[1], int(parts[2])
        ensure_user(uid)
        DATA["users"][str(uid)]["credits"] += count
        save_data(DATA)
        bot.reply_to(m, f"✅ {count} پیام به کاربر {uid} افزوده شد.")
        try:
            bot.send_message(int(uid), f"💳 {count} پیام جدید به اعتبار شما اضافه شد.")
        except:
            pass
    except:
        bot.reply_to(m, "⚠️ فرمت نادرست است. مثال: اضافه کن 123456 5")

# ریست داده‌ها
@bot.callback_query_handler(func=lambda c: c.data == "admin_reset")
def admin_reset(c):
    if c.from_user.id != SUDO_ID:
        return
    DATA.clear()
    save_data({
        "ai_on": False,
        "users": {},
        "meta": {"free_msgs": 5},
        "awaiting_contact": {},
        "awaiting_broadcast": False,
        "awaiting_reset": False
    })
    bot.send_message(c.message.chat.id, "♻️ تمام داده‌ها ریست شد.")

# =============== مدیریت گروه (بن، سکوت، حذف سکوت) ===============
@bot.message_handler(func=lambda m: m.reply_to_message and m.from_user.id == SUDO_ID)
def admin_group(m):
    target = m.reply_to_message.from_user.id
    ensure_user(target)
    cmd = m.text.strip()

    if cmd == "بن":
        DATA["users"][str(target)]["banned"] = True
        bot.reply_to(m, f"🚫 کاربر {target} بن شد.")
    elif cmd == "حذف بن":
        DATA["users"][str(target)]["banned"] = False
        bot.reply_to(m, f"✅ بن کاربر {target} برداشته شد.")
    elif cmd == "سکوت":
        mute_until = datetime.utcnow() + timedelta(hours=5)
        DATA["users"][str(target)]["muted_until"] = mute_until.isoformat()
        bot.reply_to(m, f"🔇 کاربر {target} برای ۵ ساعت ساکت شد.")
    elif cmd == "حذف سکوت":
        DATA["users"][str(target)]["muted_until"] = None
        bot.reply_to(m, f"🔊 سکوت کاربر {target} برداشته شد.")
    elif cmd == "لفت بده":
        try:
            bot.kick_chat_member(m.chat.id, target)
            bot.unban_chat_member(m.chat.id, target)
            bot.reply_to(m, "👋 کاربر از گروه حذف شد.")
        except:
            bot.reply_to(m, "⚠️ نتوانستم کاربر را حذف کنم.")
    save_data(DATA)

# =============== اجرای ربات ===============
def run():
    print("🤖 ربات هوش مصنوعی نوری اجرا شد...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except Exception as e:
            logging.error(str(e))
            time.sleep(5)

if __name__ == "__main__":
    run()
