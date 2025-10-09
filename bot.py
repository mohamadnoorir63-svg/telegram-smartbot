# ========================= بخش ۱: تنظیمات و پایه =========================
# نسخه نهایی ربات هوش مصنوعی نوری 🤖
# نویسنده: محمد نوری | @NOORI_NOOR

import os, json, time, logging
from datetime import datetime, timedelta

# --- تاریخ شمسی (اختیاری) ---
try:
    import jdatetime
    def shamsi_now():
        return jdatetime.datetime.now().strftime("%Y/%m/%d - %H:%M:%S")
except Exception:
    jdatetime = None
    def shamsi_now():
        return datetime.now().strftime("%Y/%m/%d - %H:%M:%S")

# --- تلگرام ---
import telebot
from telebot import types

# --- OpenAI ---
OPENAI_KEY = (
    os.getenv("OPENAI_API_KEY")
    or os.getenv("OPENAI_KEY")
    or os.getenv("OPENAI")
    or os.getenv("OPENAI-API-KEY")
    or os.getenv("OPENAI_APIKEY")
)

client = None
ask_openai = None

try:
    from openai import OpenAI
    if OPENAI_KEY:
        client = OpenAI(api_key=OPENAI_KEY)
    def ask_openai(prompt: str) -> str:
        if not client:
            return "❌ کلید OpenAI تنظیم نشده است."
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a friendly AI assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        return resp.choices[0].message.content.strip()
except Exception:
    import openai
    if OPENAI_KEY:
        openai.api_key = OPENAI_KEY
    def ask_openai(prompt: str) -> str:
        try:
            resp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a friendly AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
            )
            return resp["choices"][0]["message"]["content"]
        except Exception as e:
            return f"❌ خطا در ارتباط با هوش مصنوعی:\n{e}"

# --- متغیرهای محیطی ---
BOT_TOKEN = (
    os.getenv("BOT_TOKEN")
    or os.getenv("BOT_TOK")
    or os.getenv("TELEGRAM_BOT_TOKEN")
    or os.getenv("TOKEN")
)
OWNER_ID = int(os.getenv("SUDO_ID") or os.getenv("OWNER_ID") or "0")

if not BOT_TOKEN:
    raise RuntimeError("⚠️ توکن ربات (BOT_TOKEN) در Config Vars تنظیم نشده است!")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# --- لاگ ---
logging.basicConfig(
    filename="error.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- فایل داده ---
DATA_FILE = "data.json"

def base_data():
    return {
        "users": {},
        "groups": {},
        "bans": [],
        "mutes": {},
    }

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(base_data())
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return base_data()

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

FREE_LIMIT = 5  # تعداد پیام رایگان برای کاربران

def ensure_user(uid):
    d = load_data()
    u = str(uid)
    if u not in d["users"]:
        d["users"][u] = {
            "free_msgs": FREE_LIMIT,
            "ai_on": False,
            "ban": False,
            "mute": 0,
            "vip": 0
        }
        save_data(d)
    return d

def ensure_group(gid):
    d = load_data()
    g = str(gid)
    if g not in d["groups"]:
        d["groups"][g] = {"ai_on": False, "vip": 0}
        save_data(d)
    return d

def is_owner(uid):
    return uid == OWNER_ID

def is_banned(uid):
    d = load_data()
    return str(uid) in d["bans"] or d["users"].get(str(uid), {}).get("ban", False)

def is_muted(uid):
    d = load_data()
    mu = d["users"].get(str(uid), {}).get("mute", 0)
    return mu and mu > time.time()

def has_vip(uid):
    d = load_data()
    vip = d["users"].get(str(uid), {}).get("vip", 0)
    return vip and vip > time.time()

def group_has_vip(gid):
    d = load_data()
    vip = d["groups"].get(str(gid), {}).get("vip", 0)
    return vip and vip > time.time()# ========================= بخش ۲: منوی استارت و راهنما =========================

# ساخت منوی شیشه‌ای اصلی
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📘 راهنما", callback_data="help"),
        types.InlineKeyboardButton("📞 ارتباط با سازنده", url="https://t.me/NOORI_NOOR"),
    )
    markup.add(
        types.InlineKeyboardButton("➕ افزودن به گروه", url="https://t.me/" + bot.get_me().username + "?startgroup=true"),
    )
    return markup

# پیام خوش‌آمد و راه‌اندازی
@bot.message_handler(commands=["start"])
def start(m):
    d = ensure_user(m.from_user.id)
    user = str(m.from_user.id)
    name = m.from_user.first_name
    if not name:
        name = "کاربر عزیز"

    text = (
        f"سلام 👋 {name}!\n"
        f"من دستیار هوشمند نوری هستم 🤖\n"
        f"می‌تونم با هوش مصنوعی بهت کمک کنم ✨\n\n"
        f"برای شروع بنویس <b>ربات بگو</b> تا فعال شم!\n"
        f"🧠 هر کاربر {FREE_LIMIT} پیام رایگان داره 💬\n\n"
        f"برای راهنما دکمه پایین رو بزن 👇"
    )
    bot.send_message(m.chat.id, text, reply_markup=main_menu())

# راهنما
@bot.callback_query_handler(func=lambda c: c.data == "help")
def show_help(c):
    text = (
        "📘 <b>راهنمای استفاده از ربات هوشمند نوری</b>\n\n"
        "🤖 برای فعال کردن هوش مصنوعی بنویس:\n"
        "➡️ <code>ربات بگو</code>\n\n"
        "❌ برای قطع ارتباط بنویس:\n"
        "➡️ <code>ربات نگو</code>\n\n"
        "💬 بعد از فعال شدن، هر چی بگی جواب می‌دم!\n"
        f"🪙 کاربران معمولی {FREE_LIMIT} پیام رایگان دارن.\n"
        "💎 اگه خواستی بیشتر استفاده کنی، از پشتیبانی درخواست شارژ کن.\n\n"
        "🧑‍💻 سازنده: @NOORI_NOOR"
    )
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=main_menu())

# افزودن به گروه
@bot.callback_query_handler(func=lambda c: c.data == "add_group")
def add_group(c):
    bot.answer_callback_query(c.id, "برای افزودن ربات به گروه روی لینک بالا کلیک کن ✅")

# وقتی یکی ربات رو توی گروه اضافه کنه
@bot.message_handler(content_types=["new_chat_members"])
def joined_group(m):
    bot.reply_to(m, "سلام به همگی 👋\nمن دستیار هوشمند نوری هستم 🤖\nبرای فعال کردنم بنویسید <b>ربات بگو</b>")

# وقتی یکی از گروه بره
@bot.message_handler(content_types=["left_chat_member"])
def left_group(m):
    bot.reply_to(m, "یکی از اعضا گروه رو ترک کرد 😢")

# ذخیره پیام کاربران برای هوش مصنوعی
def decrease_free_msgs(uid):
    d = load_data()
    user = str(uid)
    if user in d["users"]:
        if d["users"][user]["free_msgs"] > 0:
            d["users"][user]["free_msgs"] -= 1
            save_data(d)

# نمایش وضعیت کاربر
@bot.message_handler(commands=["status"])
def show_status(m):
    d = load_data()
    user = str(m.from_user.id)
    if user not in d["users"]:
        ensure_user(m.from_user.id)
    u = d["users"][user]
    msgs = u.get("free_msgs", FREE_LIMIT)
    vip_time = u.get("vip", 0)
    status = "✅ فعال" if u.get("ai_on") else "❌ غیرفعال"
    if vip_time and vip_time > time.time():
        status += f"\n💎 حساب ویژه تا {time.ctime(vip_time)}"
    bot.reply_to(m, f"📊 وضعیت شما:\n🔹 وضعیت: {status}\n💬 پیام‌های رایگان باقیمانده: {msgs}")

# ارتباط با سازنده (ارسال پیام به مدیر)
@bot.message_handler(commands=["support"])
def support_start(m):
    bot.reply_to(m, "✉️ پیام خود را بنویسید تا برای سازنده ارسال شود.")

@bot.message_handler(func=lambda msg: msg.reply_to_message and "پیام خود را بنویسید" in msg.reply_to_message.text)
def support_send(m):
    text = f"📩 پیام از طرف @{m.from_user.username or m.from_user.id}:\n\n{m.text}"
    if OWNER_ID:
        bot.send_message(OWNER_ID, text)
    bot.reply_to(m, "✅ پیام شما برای سازنده ارسال شد. منتظر پاسخ بمانید 💬")# ========================= بخش ۳: هوش مصنوعی و مدیریت =========================

# ✨ روشن و خاموش کردن هوش مصنوعی توسط کاربران
@bot.message_handler(func=lambda m: m.text and m.text.strip() == "ربات بگو")
def enable_ai(m):
    d = load_data()
    user = str(m.from_user.id)
    ensure_user(user)
    d["users"][user]["ai_on"] = True
    save_data(d)
    bot.reply_to(m, "🤖 هوش مصنوعی فعال شد!\nچه کمکی می‌تونم بکنم؟ 💡")

@bot.message_handler(func=lambda m: m.text and m.text.strip() == "ربات نگو")
def disable_ai(m):
    d = load_data()
    user = str(m.from_user.id)
    ensure_user(user)
    d["users"][user]["ai_on"] = False
    save_data(d)
    bot.reply_to(m, "🧠 هوش مصنوعی غیرفعال شد.\nهر وقت خواستی دوباره بنویس «ربات بگو» 💬")

# 🔇 سکوت موقت (فقط سودو)
@bot.message_handler(func=lambda m: is_owner(m.from_user.id) and m.reply_to_message and m.text.startswith("سکوت "))
def mute_user(m):
    try:
        parts = m.text.split()
        hours = int(parts[1])
        uid = str(m.reply_to_message.from_user.id)
        d = load_data()
        d["users"][uid]["mute"] = time.time() + hours * 3600
        save_data(d)
        bot.reply_to(m, f"🔇 کاربر برای {hours} ساعت ساکت شد.")
    except:
        bot.reply_to(m, "⚠️ فرمت درست: <code>سکوت 5</code> (۵ ساعت سکوت)")

# 🚫 بن کاربر (فقط سودو)
@bot.message_handler(func=lambda m: is_owner(m.from_user.id) and m.reply_to_message and m.text == "بن")
def ban_user(m):
    uid = str(m.reply_to_message.from_user.id)
    d = load_data()
    if uid not in d["bans"]:
        d["bans"].append(uid)
        save_data(d)
        bot.reply_to(m, f"🚫 کاربر بن شد و دیگر پاسخی دریافت نخواهد کرد.")
    else:
        bot.reply_to(m, "⚠️ این کاربر قبلاً بن شده است.")

# 🔓 حذف بن
@bot.message_handler(func=lambda m: is_owner(m.from_user.id) and m.reply_to_message and m.text == "حذف بن")
def unban_user(m):
    uid = str(m.reply_to_message.from_user.id)
    d = load_data()
    if uid in d["bans"]:
        d["bans"].remove(uid)
        save_data(d)
        bot.reply_to(m, f"✅ بن کاربر برداشته شد.")
    else:
        bot.reply_to(m, "❗ این کاربر بن نبود.")

# 💎 شارژ کاربر (مثلاً «شارژ 3» یعنی ۳ روز نامحدود)
@bot.message_handler(func=lambda m: is_owner(m.from_user.id) and m.reply_to_message and m.text.startswith("شارژ "))
def charge_user(m):
    try:
        days = int(m.text.split()[1])
        uid = str(m.reply_to_message.from_user.id)
        d = load_data()
        d["users"][uid]["vip"] = time.time() + days * 86400
        save_data(d)
        bot.reply_to(m, f"💎 کاربر برای {days} روز شارژ شد (دسترسی نامحدود).")
        bot.send_message(int(uid), f"💡 حساب شما برای {days} روز فعال شد! حالا می‌تونی بدون محدودیت از من استفاده کنی 🤖")
    except:
        bot.reply_to(m, "⚠️ فرمت درست: <code>شارژ 3</code> (۳ روز شارژ)")

# 🚪 لفت دادن از گروه (فقط سودو)
@bot.message_handler(func=lambda m: is_owner(m.from_user.id) and m.text == "لفت بده")
def leave_group(m):
    try:
        bot.send_message(m.chat.id, "👋 بدرود دوستان! من طبق دستور سودو از گروه خارج می‌شم 💫")
        bot.leave_chat(m.chat.id)
    except:
        bot.reply_to(m, "❌ خطا در خروج از گروه.")

# 💬 پاسخ هوش مصنوعی برای کاربران
@bot.message_handler(func=lambda m: m.text and not m.text.startswith("/"))
def handle_ai(m):
    uid = str(m.from_user.id)
    if is_owner(m.from_user.id):  # سودو همیشه نامحدود است
        return bot.reply_to(m, ask_openai(m.text))

    d = load_data()
    ensure_user(uid)
    u = d["users"][uid]

    # چک بن
    if is_banned(m.from_user.id):
        return

    # چک سکوت
    if is_muted(m.from_user.id):
        return

    # چک فعال بودن
    if not u["ai_on"]:
        return

    # بررسی شارژ یا تعداد پیام رایگان
    if has_vip(m.from_user.id):
        reply = ask_openai(m.text)
        bot.reply_to(m, reply)
    elif u["free_msgs"] > 0:
        reply = ask_openai(m.text)
        decrease_free_msgs(m.from_user.id)
        bot.reply_to(m, reply + f"\n\n💬 پیام‌های رایگان باقیمانده: {u['free_msgs'] - 1}")
    else:
        bot.reply_to(m, "⚠️ شارژ شما تمام شده!\nبرای تمدید بنویسید /support و درخواست شارژ دهید 💎")# ========================= بخش ۴: پنل مدیریتی سودو و اجرای نهایی =========================

# پنل سودو برای کنترل ربات
@bot.message_handler(func=lambda m: is_owner(m.from_user.id) and m.text == "پنل")
def sudo_panel(m):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 آمار", callback_data="stats"),
        types.InlineKeyboardButton("📢 ارسال همگانی", callback_data="broadcast"),
    )
    markup.add(
        types.InlineKeyboardButton("🚪 خروج از گروه", callback_data="leave_all"),
        types.InlineKeyboardButton("💾 ذخیره فوری", callback_data="save_data")
    )
    bot.send_message(m.chat.id, "👑 <b>پنل مدیریتی سودو</b>\nیکی از گزینه‌ها رو انتخاب کن 👇", reply_markup=markup)

# آمار ربات
@bot.callback_query_handler(func=lambda c: c.data == "stats")
def show_stats(c):
    d = load_data()
    users = len(d["users"])
    groups = len(d["groups"])
    bans = len(d["bans"])
    actives = sum(1 for u in d["users"].values() if u.get("ai_on"))
    msg = (
        f"📊 <b>آمار کلی ربات</b>\n\n"
        f"👤 کاربران ثبت‌شده: {users}\n"
        f"👥 گروه‌های ثبت‌شده: {groups}\n"
        f"🚫 کاربران بن‌شده: {bans}\n"
        f"💬 کاربران فعال: {actives}\n"
        f"🕓 زمان: {shamsi_now()}"
    )
    bot.edit_message_text(msg, c.message.chat.id, c.message.message_id)

# ارسال همگانی (پیام متنی)
@bot.callback_query_handler(func=lambda c: c.data == "broadcast")
def ask_broadcast(c):
    bot.send_message(c.message.chat.id, "📢 لطفاً متنی که می‌خوای ارسال بشه رو بنویس (ریپلای لازم نیست):")
    bot.register_next_step_handler(c.message, do_broadcast)

def do_broadcast(m):
    d = load_data()
    targets = list(d["users"].keys())
    sent = 0
    for uid in targets:
        try:
            bot.send_message(uid, m.text)
            sent += 1
        except:
            continue
    bot.send_message(m.chat.id, f"✅ پیام همگانی برای {sent} نفر ارسال شد.")

# خروج از همه گروه‌ها
@bot.callback_query_handler(func=lambda c: c.data == "leave_all")
def leave_all_groups(c):
    d = load_data()
    left = 0
    for gid in list(d["groups"].keys()):
        try:
            bot.leave_chat(int(gid))
            left += 1
        except:
            continue
    bot.send_message(c.message.chat.id, f"🚪 از {left} گروه خارج شدم.")
    bot.answer_callback_query(c.id, "انجام شد ✅")

# ذخیره دستی اطلاعات
@bot.callback_query_handler(func=lambda c: c.data == "save_data")
def save_now(c):
    save_data(load_data())
    bot.answer_callback_query(c.id, "✅ داده‌ها ذخیره شدند.")
    bot.send_message(c.message.chat.id, "💾 اطلاعات ربات ذخیره شد.")

# ========== اجرای نهایی ==========
if __name__ == "__main__":
    print("🤖 ربات هوش مصنوعی نوری در حال اجراست...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except Exception as e:
            logging.error(f"polling crash: {e}")
            time.sleep(5)
