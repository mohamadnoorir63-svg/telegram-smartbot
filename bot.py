# ========================= بخش ۱: تنظیمات و پایه =========================
# نویسنده: محمد نوری  |  @NOORI_NOOR

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

# --- OpenAI: هم با نسخه‌های جدید کار می‌کنه، هم قدیمی ---
OPENAI_KEY = (
    os.getenv("OPENAI_API_KEY")
    or os.getenv("OPENAI_KEY")
    or os.getenv("OPENAI")
    or os.getenv("OPENAI-API-KEY")
    or os.getenv("OPENAI_APIKEY")
)

_ai_mode = "v1"
client = None
ask_openai = None
try:
    # نسخه‌های جدید (openai>=1.x)
    from openai import OpenAI
    if OPENAI_KEY:
        client = OpenAI(api_key=OPENAI_KEY)
    def ask_openai(prompt: str) -> str:
        if not client:
            return "کلید OpenAI تنظیم نشده است."
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful, friendly assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        return resp.choices[0].message.content.strip()
except Exception:
    # نسخه‌های قدیمی (openai==0.28.x)
    import openai as _openai
    _ai_mode = "v0"
    if OPENAI_KEY:
        _openai.api_key = OPENAI_KEY
    def ask_openai(prompt: str) -> str:
        if not OPENAI_KEY:
            return "کلید OpenAI تنظیم نشده است."
        resp = _openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful, friendly assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        return resp.choices[0].choices[0].message["content"].strip()

# --- متغیرهای محیطی (با نام‌های جایگزین هم کار می‌کند) ---
BOT_TOKEN = (
    os.getenv("BOT_TOKEN")
    or os.getenv("TELEGRAM_BOT_TOKEN")
    or os.getenv("TOKEN")
    or os.getenv("BOT_TOK")   # اگر اشتباهی این‌طور گذاشته‌ای
)

OWNER_ID = int(
    os.getenv("SUDO_ID")
    or os.getenv("OWNER_ID")
    or os.getenv("ADMIN_ID")
    or "0"
)

# راه‌اندازی بات تلگرام
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN در Config Vars تنظیم نشده است.")
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# --- لاگ ---
logging.basicConfig(
    filename="error.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- فایل داده ---
DATA_FILE = "data.json"

def _base_data():
    return {
        "users": {},      # {uid: {free_left, ai_on, chat_on, ban, mute_until, vip_until}}
        "groups": {},     # {gid: {ai_on, vip_until}}
        "bans": [],       # [uid,...]
        "mutes": {},      # {uid: timestamp}
        "support_pipe": {},   # {user_id: {"open": True, "to": OWNER_ID}}
    }

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(_base_data())
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = _base_data()
    # تضمین کلیدها
    for k, v in _base_data().items():
        data.setdefault(k, v if not isinstance(v, dict) else v.copy())
    return data

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

# --- پیش‌فرض سهمیه رایگان ---
FREE_QUOTA = 5

def ensure_user(uid: int):
    d = load_data()
    suid = str(uid)
    if suid not in d["users"]:
        d["users"][suid] = {
            "free_left": FREE_QUOTA,
            "ai_on": False,      # ربات بگو/نگو (پی‌وی)
            "chat_on": True,     # اجازه چت با سازنده
            "ban": False,
            "mute_until": 0,     # سکوت تا زمان خاص
            "vip_until": 0       # شارژ نامحدود تا تاریخ
        }
        save_data(d)
    return d

def ensure_group(gid: int):
    d = load_data()
    sgid = str(gid)
    if sgid not in d["groups"]:
        d["groups"][sgid] = {
            "ai_on": False,      # ربات بگو/نگو (گروه)
            "vip_until": 0
        }
        save_data(d)
    return d

def is_owner(uid: int) -> bool:
    return uid == OWNER_ID

def is_banned(uid: int) -> bool:
    d = load_data()
    return str(uid) in d.get("bans", []) or d["users"].get(str(uid), {}).get("ban", False)

def is_muted(uid: int) -> bool:
    d = load_data()
    mu = d["users"].get(str(uid), {}).get("mute_until", 0)
    return mu and mu > int(time.time())

def has_vip(uid: int) -> bool:
    d = load_data()
    vip = d["users"].get(str(uid), {}).get("vip_until", 0)
    return vip and vip > int(time.time())

def group_has_vip(gid: int) -> bool:
    d = load_data()
    vip = d["groups"].get(str(gid), {}).get("vip_until", 0)
    return vip and vip > int(time.time())

# --- کیبوردهای شیشه‌ای (پی‌وی + سودو + گروه) ---
def user_main_kb():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("راهنما 📘", callback_data="help"),
        types.InlineKeyboardButton("ارتباط با سازنده 📞", callback_data="contact"),
    )
    kb.add(
        types.InlineKeyboardButton("وضعیت ربات 🟢", callback_data="status"),
        types.InlineKeyboardButton("افزایش اعتبار 🧾", callback_data="buy"),
    )
    kb.add(
        types.InlineKeyboardButton("➕ افزودن به گروه", url="https://t.me/{}/?startgroup=true".format(bot.get_me().username))
    )
    return kb

def owner_panel_kb():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("آمار 👥", callback_data="admin_stats"),
        types.InlineKeyboardButton("ارسال همگانی 📢", callback_data="admin_bc"),
    )
    kb.add(
        types.InlineKeyboardButton("لیست بن 🚫", callback_data="admin_bans"),
        types.InlineKeyboardButton("لفت بده 👋", callback_data="admin_leave"),
    )
    return kb

def group_info_kb():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("وضعیت ربات در گروه 🔌", callback_data="g_status"),
        types.InlineKeyboardButton("راهنمای استفاده 🧭", callback_data="g_help"),
    )
    return kb

# --- پیام خوش‌آمد /start (پی‌وی) ---
@bot.message_handler(commands=["start"])
def start(m):
    ensure_user(m.from_user.id)
    hi = (
        f"سلام 👋\n"
        f"من دستیار هوشمند نوری هستم 🤖\n"
        f"می‌تونم با هوش مصنوعی کمکت کنم — "
        f"برای فعال‌سازی بنویس: <b>ربات بگو</b>\n\n"
        f"⏱ {shamsi_now()}"
    )
    bot.send_message(m.chat.id, hi, reply_markup=user_main_kb())

# =======================================================================
# پایان بخش ۱ — حالا بخش ۲ و ۳ و ۴ را پشت این کد قرار بده
# =======================================================================# ================= بخش ۲ =================

@bot.message_handler(commands=["start"])
def start(m):
    ensure_user(m.from_user.id)
    name = m.from_user.first_name
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📘 راهنما", callback_data="help"),
        types.InlineKeyboardButton("📞 ارتباط با سازنده", url="https://t.me/NOORI_NOOR"),
        types.InlineKeyboardButton("➕ افزودن من به گروه", url="https://t.me/" + bot.get_me().username + "?startgroup=true")
    )
    bot.send_message(
        m.chat.id,
        f"👋 سلام {name}!\n\n"
        "من دستیار هوشمند نوری هستم 🤖\n"
        "می‌تونم با هوش مصنوعی بهت کمک کنم —\n"
        "برای فعال شدن فقط بنویس «ربات بگو» تا شروع کنیم!\n\n"
        "💡 برای راهنما روی دکمه زیر بزن 👇",
        reply_markup=markup
    )

# دکمه راهنما
@bot.callback_query_handler(func=lambda c: c.data == "help")
def help_menu(c):
    help_text = (
        "📘 راهنمای استفاده از ربات هوشمند نوری:\n\n"
        "🤖 برای فعال کردن هوش مصنوعی بنویس:\n"
        "» ربات بگو\n\n"
        "😴 برای خاموش کردن بنویس:\n"
        "» ربات نگو\n\n"
        "💬 هر کاربر ۵ پیام رایگان داره.\n"
        "بعد از تموم شدن باید از طریق پشتیبانی شارژ کنه.\n\n"
        "⚙️ اگر مدیر هستی، با دستور /panel وارد بخش مدیریت شو."
    )
    bot.answer_callback_query(c.id)
    bot.send_message(c.message.chat.id, help_text)

# فعال کردن هوش مصنوعی
@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["ربات بگو", "هوش روشن", "فعال شو"])
def activate_ai(m):
    data = load_data()
    ensure_user(m.from_user.id)
    data["users"][str(m.from_user.id)]["active"] = True
    save_data(data)
    bot.reply_to(m, "✅ هوش مصنوعی فعال شد!\nبگو تا بهت کمک کنم ✨")

# غیرفعال کردن هوش مصنوعی
@bot.message_handler(func=lambda m: m.text and m.text.lower() in ["ربات نگو", "خاموش شو", "هوش خاموش"])
def deactivate_ai(m):
    data = load_data()
    ensure_user(m.from_user.id)
    data["users"][str(m.from_user.id)]["active"] = False
    save_data(data)
    bot.reply_to(m, "😴 هوش مصنوعی خاموش شد.\nهر وقت خواستی بنویس «ربات بگو» تا دوباره فعال شم 💡")# ================= بخش ۳ =================

# دریافت پاسخ از ChatGPT
def ask_chatgpt(prompt):
    try:
        response = ai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ خطا در پاسخ از سرور هوش مصنوعی: {e}"

# پاسخ به کاربران عادی
@bot.message_handler(func=lambda m: True)
def handle_user_message(m):
    if not m.text:
        return
    uid = str(m.from_user.id)
    ensure_user(uid)
    data = load_data()

    u = data["users"].get(uid, {})
    if u.get("banned"):
        return  # بن شده‌ها بی‌جواب
    if u.get("muted_until"):
        mute_time = datetime.fromisoformat(u["muted_until"])
        if datetime.now() < mute_time:
            return  # هنوز در سکوت است
        else:
            u["muted_until"] = None  # رفع سکوت
            save_data(data)

    if not u.get("active"):
        return  # غیرفعال بودن هوش

    credits = u.get("credits", 0)
    if credits <= 0:
        bot.reply_to(m, "🔋 شارژت تموم شده!\nبرای شارژ مجدد به پشتیبانی مراجعه کن 🧠")
        return

    # کسر اعتبار و دریافت پاسخ از ChatGPT
    u["credits"] -= 1
    save_data(data)
    bot.send_chat_action(m.chat.id, "typing")
    reply = ask_chatgpt(m.text)
    bot.reply_to(m, f"💬 {reply}")

# 🔒 سکوت کاربر (۵ ساعت)
@bot.message_handler(func=lambda m: m.reply_to_message and m.text == "سکوت")
def mute_user(m):
    if m.from_user.id != OWNER_ID:
        return
    data = load_data()
    uid = str(m.reply_to_message.from_user.id)
    ensure_user(uid)
    mute_until = datetime.now() + timedelta(hours=5)
    data["users"][uid]["muted_until"] = mute_until.isoformat()
    save_data(data)
    bot.reply_to(m, f"🔇 کاربر برای ۵ ساعت در سکوت است.")

# 🚫 بن کاربر
@bot.message_handler(func=lambda m: m.reply_to_message and m.text == "بن")
def ban_user(m):
    if m.from_user.id != OWNER_ID:
        return
    data = load_data()
    uid = str(m.reply_to_message.from_user.id)
    ensure_user(uid)
    data["users"][uid]["banned"] = True
    save_data(data)
    bot.reply_to(m, f"🚫 کاربر بن شد و دیگر پاسخی دریافت نخواهد کرد.")

# 🔓 حذف بن
@bot.message_handler(func=lambda m: m.reply_to_message and m.text == "حذف بن")
def unban_user(m):
    if m.from_user.id != OWNER_ID:
        return
    data = load_data()
    uid = str(m.reply_to_message.from_user.id)
    ensure_user(uid)
    data["users"][uid]["banned"] = False
    save_data(data)
    bot.reply_to(m, f"✅ کاربر از بن خارج شد.")

# 💎 شارژ عددی برای کاربر (مثلاً: ریپلای روی کاربر بنویس شارژ 10)
@bot.message_handler(func=lambda m: m.reply_to_message and m.text.startswith("شارژ "))
def charge_user(m):
    if m.from_user.id != OWNER_ID:
        return
    try:
        amount = int(m.text.split()[1])
    except:
        return bot.reply_to(m, "⚠️ فرمت نادرست! مثال: شارژ 10")
    data = load_data()
    uid = str(m.reply_to_message.from_user.id)
    ensure_user(uid)
    data["users"][uid]["credits"] += amount
    save_data(data)
    bot.reply_to(m, f"💎 کاربر {amount} پیام شارژ شد ✅")

# 👑 پنل سودو
@bot.message_handler(commands=["panel"])
def sudo_panel(m):
    if m.from_user.id != OWNER_ID:
        return
    data = load_data()
    total_users = len(data["users"])
    active = sum(1 for u in data["users"].values() if u.get("active"))
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📢 ارسال همگانی", callback_data="broadcast"),
        types.InlineKeyboardButton("📊 آمار ربات", callback_data="stats"),
        types.InlineKeyboardButton("🚪 لفت بده", callback_data="leave")
    )
    bot.send_message(
        m.chat.id,
        f"👑 پنل مدیریتی نوری\n\n"
        f"👥 کاربران ثبت‌شده: {total_users}\n"
        f"💬 کاربران فعال: {active}\n"
        f"⚡ سازنده: @NOORI_NOOR",
        reply_markup=markup
    )

# دکمه‌های پنل مدیریتی
@bot.callback_query_handler(func=lambda c: c.data in ["stats", "broadcast", "leave"])
def admin_actions(c):
    data = load_data()
    if c.from_user.id != OWNER_ID:
        return bot.answer_callback_query(c.id, "فقط سازنده می‌تونه از این بخش استفاده کنه ⚠️", show_alert=True)

    if c.data == "stats":
        total_users = len(data["users"])
        total_groups = len(data["groups"])
        bot.answer_callback_query(c.id)
        bot.send_message(c.message.chat.id, f"📊 آمار فعلی:\n👤 کاربران: {total_users}\n👥 گروه‌ها: {total_groups}")

    elif c.data == "broadcast":
        bot.answer_callback_query(c.id, "برای ارسال همگانی، روی پیامی ریپلای کن و بنویس ارسال", show_alert=True)

    elif c.data == "leave":
        bot.answer_callback_query(c.id)
        bot.leave_chat(c.message.chat.id)
        bot.send_message(c.from_user.id, f"🚪 از گروه {c.message.chat.title} خارج شدم.")# ================= بخش ۴ =================

# دستور "ارسال" برای همگانی از طریق سودو
@bot.message_handler(func=lambda m: m.reply_to_message and m.text == "ارسال")
def broadcast_message(m):
    if m.from_user.id != OWNER_ID:
        return
    data = load_data()
    total = 0
    for uid in list(data["users"].keys()):
        try:
            if m.reply_to_message.text:
                bot.send_message(uid, m.reply_to_message.text)
            elif m.reply_to_message.photo:
                bot.send_photo(uid, m.reply_to_message.photo[-1].file_id, caption=m.reply_to_message.caption or "")
            total += 1
        except:
            continue
    bot.reply_to(m, f"📢 پیام برای {total} کاربر ارسال شد ✅")

# پیام خطاهای غیرمنتظره
@bot.message_handler(func=lambda m: True, content_types=["text", "photo", "video", "document", "sticker"])
def fallback_message(m):
    """هر پیام غیرقابل شناسایی به این بخش می‌ره تا ربات هنگ نکنه"""
    pass

# پیام روشن‌شدن ربات
print("🤖 ربات هوشمند نوری با موفقیت راه‌اندازی شد!")
print("✨ طراحی و توسعه توسط محمد نوری | @NOORI_NOOR")
print("🚀 آماده پاسخ‌گویی و مدیریت گروه‌هاست...")

# اجرای مداوم بدون توقف (در صورت قطع ارتباط، دوباره متصل می‌شود)
while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        print(f"⚠️ خطا در polling: {e}")
        import time
        time.sleep(5)
