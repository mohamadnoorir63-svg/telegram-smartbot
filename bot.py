# -*- coding: utf-8 -*-
# Persian Lux AI Manager V25 – Mohammad Edition 👑

import os, json, random, time, logging
from datetime import datetime, timedelta
import jdatetime
import telebot
from telebot import types
import openai

# ⚙️ تنظیمات پایه
TOKEN   = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
openai.api_key = OPENAI_KEY

DATA_FILE = "data.json"
LOG_FILE  = "error.log"
logging.basicConfig(filename=LOG_FILE, level=logging.ERROR, format="%(asctime)s - %(message)s")

# 💾 فایل داده
def base_data():
    return {
        "users": {}, "groups": {}, "muted": {}, "banned": [],
        "ai_status": {}, "welcome": {}, "admins": {},
        "sudo_list": [], "locks": {}, "credits": {}
    }

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(base_data())
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        data = base_data()
    for k in base_data():
        if k not in data: data[k] = base_data()[k]
    save_data(data)
    return data

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

# 🧩 ابزارها
def shamsi_date(): return jdatetime.datetime.now().strftime("%A %d %B %Y")
def shamsi_time(): return jdatetime.datetime.now().strftime("%H:%M:%S")
def cmd_text(m): return (getattr(m, "text", None) or "").strip()
def is_sudo(uid): 
    d = load_data()
    return str(uid) in [str(SUDO_ID)] + d.get("sudo_list", [])

def is_admin(chat_id, uid):
    d = load_data(); gid = str(chat_id)
    if is_sudo(uid): return True
    if str(uid) in d["admins"].get(gid, []): return True
    try:
        status = bot.get_chat_member(chat_id, uid).status
        return status in ("administrator", "creator")
    except: return False

# 🧾 ثبت کاربران
@bot.message_handler(commands=["start"])
def start_user(m):
    d = load_data()
    uid = str(m.from_user.id)
    if uid not in d["users"]:
        d["users"][uid] = {"messages": 0, "active": True}
        d["credits"][uid] = {"free": 5, "paid_until": None}
        save_data(d)

    text = (
        f"👋 سلام {m.from_user.first_name}!\n"
        f"من <b>دستیار هوشمند نوری</b> هستم 🤖\n"
        f"می‌تونم با هوش مصنوعی بهت کمک کنم — بنویس «ربات بگو» تا فعال شم!\n\n"
        f"💡 برای راهنما دکمه پایین رو بزن 👇"
    )

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("📘 راهنما", callback_data="help"),
        types.InlineKeyboardButton("💬 ارتباط با سازنده", url="https://t.me/NOORI_NOOR"),
        types.InlineKeyboardButton("➕ افزودن من به گروه", url=f"https://t.me/{bot.get_me().username}?startgroup=true")
    )

    bot.send_message(m.chat.id, text, reply_markup=kb)# ===================== 🚫 بن / 🔇 سکوت / 💳 شارژ / 🧠 هوش مصنوعی =====================

# 🛑 بن کاربر
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "بن")
def ban_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = str(m.reply_to_message.from_user.id)
    d = load_data()
    if uid in d["banned"]:
        return bot.reply_to(m, "⚠️ این کاربر از قبل بن است.")
    d["banned"].append(uid)
    save_data(d)
    bot.reply_to(m, f"🚫 کاربر <a href='tg://user?id={uid}'>بن شد</a> و دیگر پاسخ نمی‌گیرد.")

# 🔓 حذف بن
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف بن")
def unban_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = str(m.reply_to_message.from_user.id)
    d = load_data()
    if uid in d["banned"]:
        d["banned"].remove(uid)
        save_data(d)
        bot.reply_to(m, "✅ کاربر از لیست بن خارج شد.")
    else:
        bot.reply_to(m, "❗ این کاربر بن نیست.")

# 🔇 سکوت ۵ ساعته
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "سکوت")
def mute_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = str(m.reply_to_message.from_user.id)
    d = load_data()
    d["muted"][uid] = time.time() + 18000  # ۵ ساعت
    save_data(d)
    bot.reply_to(m, f"🔇 کاربر <a href='tg://user?id={uid}'>برای ۵ ساعت ساکت شد</a>.")

# 🔊 حذف سکوت
@bot.message_handler(func=lambda m: m.reply_to_message and cmd_text(m) == "حذف سکوت")
def unmute_user(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    uid = str(m.reply_to_message.from_user.id)
    d = load_data()
    if uid in d["muted"]:
        d["muted"].pop(uid)
        save_data(d)
        bot.reply_to(m, "🔊 سکوت کاربر برداشته شد.")
    else:
        bot.reply_to(m, "⚠️ این کاربر ساکت نیست.")

# 👑 لفت بده (فقط سودو)
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "لفت بده")
def leave_group(m):
    try:
        bot.send_message(m.chat.id, "👋 با اجازه، من از گروه خارج می‌شم 💫")
        bot.leave_chat(m.chat.id)
    except:
        bot.reply_to(m, "⚠️ خطایی در خروج پیش آمد.")

# 💳 شارژ عددی – فقط سودو
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and m.reply_to_message and cmd_text(m).startswith("شارژ "))
def charge_user(m):
    try:
        days = int(cmd_text(m).split()[1])
    except:
        return bot.reply_to(m, "⚠️ فرمت درست: شارژ 3")

    uid = str(m.reply_to_message.from_user.id)
    d = load_data()
    now = datetime.now()
    paid_until = now + timedelta(days=days)
    d["credits"][uid] = {"free": 0, "paid_until": paid_until.timestamp()}
    save_data(d)

    bot.reply_to(m, f"💎 کاربر برای {days} روز شارژ شد.\n⏰ تا {paid_until.strftime('%Y-%m-%d %H:%M')}")
    bot.send_message(uid, f"✨ حساب شما برای {days} روز شارژ شد!\nمی‌تونید بدون محدودیت از هوش مصنوعی استفاده کنید 💬")

# 💰 نمایش شارژ
@bot.message_handler(func=lambda m: cmd_text(m) == "شارژ من")
def show_credit(m):
    d = load_data()
    uid = str(m.from_user.id)
    info = d["credits"].get(uid, {"free": 5, "paid_until": None})
    if info["paid_until"]:
        remaining = int(info["paid_until"] - time.time())
        if remaining > 0:
            h = remaining // 3600
            bot.reply_to(m, f"💎 شارژ فعال شما هنوز {h} ساعت اعتبار دارد.")
            return
    bot.reply_to(m, f"💬 پیام‌های رایگان باقی‌مانده: {info.get('free',5)}")

# 🧠 روشن و خاموش هوش مصنوعی
@bot.message_handler(func=lambda m: cmd_text(m) in ["ربات بگو", "ربات نگو"])
def toggle_ai(m):
    uid = str(m.from_user.id)
    d = load_data()
    d["ai_status"][uid] = (cmd_text(m) == "ربات بگو")
    save_data(d)
    if d["ai_status"][uid]:
        bot.reply_to(m, "🤖 هوش مصنوعی فعال شد!\nچی می‌خوای بدونی؟ 🧩")
    else:
        bot.reply_to(m, "🛑 هوش مصنوعی غیرفعال شد. برای فعال‌سازی بگو: «ربات بگو»")# ===================== 🧠 پاسخ هوش مصنوعی ChatGPT =====================

@bot.message_handler(func=lambda m: True, content_types=["text"])
def ai_chat(m):
    d = load_data()
    uid = str(m.from_user.id)
    text = cmd_text(m)

    # بررسی بن
    if uid in d["banned"]:
        return

    # بررسی سکوت
    if uid in d["muted"] and time.time() < d["muted"][uid]:
        return

    # بررسی وضعیت هوش مصنوعی
    if not d["ai_status"].get(uid, False):
        return

    # بررسی اعتبار و محدودیت
    credits = d["credits"].get(uid, {"free": 5, "paid_until": None})
    now = time.time()

    if credits["paid_until"]:
        if credits["paid_until"] < now:
            # شارژ تموم شده
            credits["paid_until"] = None
            credits["free"] = 0

    if not credits["paid_until"]:
        if credits["free"] <= 0:
            bot.reply_to(m, "⚠️ اعتبار شما به پایان رسیده است.\nبرای تمدید، روی گزینه «💳 شارژ مجدد» در پنل کلیک کنید.")
            return
        else:
            credits["free"] -= 1

    d["credits"][uid] = credits
    save_data(d)

    try:
        # پاسخ ChatGPT
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "تو یک ربات هوشمند و دوست‌داشتنی فارسی هستی به نام 'دستیار نوری'. لحن دوستانه، فانتزی و طبیعی داشته باش."},
                {"role": "user", "content": text}
            ]
        )
        answer = response["choices"][0]["message"]["content"]

        bot.reply_to(m, f"💬 {answer}")

    except Exception as e:
        logging.error(f"AI error: {e}")
        bot.reply_to(m, "⚠️ متاسفم، مشکلی در ارتباط با هوش مصنوعی پیش اومده 😔")# ===================== ⚙️ پنل مدیریتی و راهنما =====================

# 🎛 منوی راهنما برای کاربران
@bot.callback_query_handler(func=lambda call: call.data == "help")
def show_help_menu(call):
    text = (
        "📘 <b>راهنمای دستیار نوری 🤖</b>\n\n"
        "🌟 با نوشتن <b>ربات بگو</b> هوش مصنوعی فعال میشه.\n"
        "🚫 با نوشتن <b>ربات نگو</b> غیرفعال میشه.\n\n"
        "💬 هر کاربر ۵ پیام رایگان داره، بعدش باید شارژ کنه.\n"
        "👑 مدیر (سودو) می‌تونه با دستور <b>شارژ عددی</b> برای کسی شارژ بده.\n\n"
        "📢 در گروه‌ها بگو: «لفت بده» تا ربات خارج شه.\n"
        "🔇 سکوت = ۵ ساعت بدون پاسخ\n🚫 بن = بدون پاسخ دائمی\n\n"
        "برای پشتیبانی، روی دکمه زیر بزن 👇"
    )

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("💬 ارتباط با سازنده", url="https://t.me/NOORI_NOOR"),
        types.InlineKeyboardButton("🔙 برگشت", callback_data="main")
    )

    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=kb)


# 🧠 پنل اصلی کاربر
@bot.callback_query_handler(func=lambda call: call.data == "main")
def main_panel(call):
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("🤖 راهنما", callback_data="help"),
        types.InlineKeyboardButton("💳 شارژ من", callback_data="credit"),
        types.InlineKeyboardButton("💬 ارتباط با سازنده", url="https://t.me/NOORI_NOOR")
    )
    text = (
        "🌈 <b>به دستیار نوری خوش اومدی!</b>\n"
        "🤖 من هوش مصنوعی فارسی هستم، با من راحت حرف بزن 😍\n\n"
        "برای شروع فقط بنویس <b>ربات بگو</b> 🌟"
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=kb)


# 💳 نمایش شارژ از پنل
@bot.callback_query_handler(func=lambda call: call.data == "credit")
def credit_panel(call):
    d = load_data()
    uid = str(call.from_user.id)
    info = d["credits"].get(uid, {"free": 5, "paid_until": None})

    if info["paid_until"]:
        remaining = int(info["paid_until"] - time.time())
        if remaining > 0:
            h = remaining // 3600
            text = f"💎 شارژ فعال شما هنوز {h} ساعت اعتبار دارد."
        else:
            text = "⚠️ شارژ شما منقضی شده است."
    else:
        text = f"💬 پیام‌های رایگان باقی‌مانده: {info.get('free',5)}"

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("💬 ارتباط با پشتیبانی", url="https://t.me/NOORI_NOOR"),
        types.InlineKeyboardButton("🔙 برگشت", callback_data="main")
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=kb)


# 📊 آمار و ارسال همگانی (فقط سودو)
@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and cmd_text(m) == "پنل")
def admin_panel(m):
    d = load_data()
    total_users = len(d["users"])
    banned = len(d["banned"])
    muted = len(d["muted"])
    groups = len(d["groups"])

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("📢 ارسال همگانی", callback_data="broadcast"),
        types.InlineKeyboardButton("📊 آمار کاربران", callback_data="stats")
    )
    bot.reply_to(m, (
        f"👑 <b>پنل مدیریتی سودو</b>\n"
        f"👥 کاربران: {total_users}\n"
        f"🚫 بن‌شده‌ها: {banned}\n"
        f"🔇 در سکوت: {muted}\n"
        f"💬 گروه‌ها: {groups}"
    ), parse_mode="HTML", reply_markup=kb)


# 📢 ارسال همگانی
@bot.callback_query_handler(func=lambda call: call.data == "broadcast")
def ask_broadcast(call):
    bot.send_message(call.message.chat.id, "📨 لطفاً پیامی که می‌خواهی برای همه ارسال شود را ریپلای کن و بنویس «ارسال».")

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and m.reply_to_message and cmd_text(m) == "ارسال")
def do_broadcast(m):
    d = load_data()
    users = list(d["users"].keys())
    success = 0
    for uid in users:
        try:
            bot.copy_message(uid, m.chat.id, m.reply_to_message.message_id)
            success += 1
        except:
            continue
    bot.reply_to(m, f"📢 پیام برای {success} کاربر ارسال شد.")


# 📈 آمار کاربران
@bot.callback_query_handler(func=lambda call: call.data == "stats")
def show_stats(call):
    d = load_data()
    users = len(d["users"])
    banned = len(d["banned"])
    muted = len(d["muted"])
    groups = len(d["groups"])
    bot.edit_message_text(
        f"📊 <b>آمار کلی ربات</b>\n"
        f"👥 کاربران: {users}\n🚫 بن‌شده‌ها: {banned}\n🔇 ساکت‌ها: {muted}\n💬 گروه‌ها: {groups}",
        call.message.chat.id, call.message.message_id, parse_mode="HTML"
    )


# ===================== 🚀 اجرای نهایی =====================
print("🤖 Persian Lux AI Manager V25 در حال اجراست...")

while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        logging.error(f"Polling error: {e}")
        time.sleep(5)
