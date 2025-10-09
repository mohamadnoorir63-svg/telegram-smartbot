# ===============================================
# 🤖 ربات هوش مصنوعی نوری (نسخه نهایی)
# مدیریت + هوش مصنوعی + پنل سودو + شارژ گروه‌ها
# ===============================================

import telebot, json, os, time, logging
from telebot import types
from datetime import datetime, timedelta
from openai import OpenAI

# ---------- پیکربندی ----------
BOT_TOKEN = os.getenv("BOT_TOK")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
SUDO_ID = int(os.getenv("SUDO_ID"))

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
client = OpenAI(api_key=OPENAI_KEY)
logging.basicConfig(level=logging.INFO)

DATA_FILE = "data.json"

# ---------- ذخیره و بارگذاری ----------
def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"users": {}, "groups": {}, "bans": {}}, f)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def is_owner(uid): return uid == SUDO_ID

def shamsi_now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ---------- ساخت منوی شیشه‌ای ----------
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📘 راهنما", callback_data="help"),
        types.InlineKeyboardButton("📞 ارتباط با سازنده", callback_data="contact"),
    )
    markup.add(
        types.InlineKeyboardButton("💳 افزایش اعتبار", callback_data="buy"),
        types.InlineKeyboardButton("⚙️ وضعیت ربات", callback_data="status"),
    )
    markup.add(types.InlineKeyboardButton("➕ افزودن به گروه", url="https://t.me/smartbot_noori_bot?startgroup=true"))
    return markup

# ---------- شروع /start ----------
@bot.message_handler(commands=["start"])
def start(m):
    d = load_data()
    uid = str(m.from_user.id)
    if uid not in d["users"]:
        d["users"][uid] = {"credits": 5, "ai_on": False, "muted_until": None}
        save_data(d)

    name = m.from_user.first_name or "کاربر"
    msg = (
        f"سلام 👋 <b>{name}</b>!\n"
        f"من <b>دستیار هوشمند نوری</b> هستم 🤖\n\n"
        "می‌تونم با هوش مصنوعی بهت کمک کنم 💡\n"
        "برای شروع بنویس: <b>ربات بگو</b> تا فعال شم.\n\n"
        "✨ شما ۵ پیام رایگان دارید.\n\n"
        "برای راهنما روی دکمه زیر بزن 👇"
    )
    bot.send_message(m.chat.id, msg, reply_markup=main_menu())

# ---------- فعال / غیرفعال کردن ربات ----------
@bot.message_handler(func=lambda m: m.text and "ربات بگو" in m.text)
def enable_ai(m):
    d = load_data()
    uid = str(m.from_user.id)
    if uid not in d["users"]: return
    d["users"][uid]["ai_on"] = True
    save_data(d)
    bot.reply_to(m, "✨ هوش مصنوعی فعال شد!\nبپرس تا کمکت کنم 💬")

@bot.message_handler(func=lambda m: m.text and "ربات نگو" in m.text)
def disable_ai(m):
    d = load_data()
    uid = str(m.from_user.id)
    if uid not in d["users"]: return
    d["users"][uid]["ai_on"] = False
    save_data(d)
    bot.reply_to(m, "😴 هوش مصنوعی غیرفعال شد.")

# ---------- پاسخ هوش مصنوعی ----------
def ask_ai(prompt):
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"⚠️ خطا در پاسخ هوش مصنوعی: {e}"

@bot.message_handler(func=lambda m: True)
def handle_message(m):
    d = load_data()
    uid = str(m.from_user.id)

    # بن / سکوت بررسی شود
    if uid in d["bans"]:
        bot.reply_to(m, "🚫 شما از استفاده از ربات بن شدید.")
        return

    user = d["users"].get(uid, {"ai_on": False, "credits": 5})
    muted_until = user.get("muted_until")
    if muted_until and datetime.now() < datetime.fromisoformat(muted_until):
        bot.reply_to(m, "⏳ شما تا پایان محدودیت سکوت نمی‌تونید پیام بدید.")
        return

    if not user["ai_on"]:
        return

    # بررسی اعتبار پیام‌ها
    if user["credits"] <= 0:
        bot.reply_to(m, "⚠️ اعتبار شما تمام شده است. برای شارژ روی افزایش اعتبار بزنید 💳")
        return

    # پاسخ هوش مصنوعی
    answer = ask_ai(m.text)
    bot.reply_to(m, answer)

    user["credits"] -= 1
    d["users"][uid] = user
    save_data(d)# =====================================================
# 🔧 بخش مدیریتی ربات هوشمند نوری
# شامل: بن، سکوت، شارژ، لفت، آمار، و پنل سودو
# =====================================================

# ---------- دکمه‌ها ----------
def sudo_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 آمار ربات", callback_data="stats"),
        types.InlineKeyboardButton("📢 ارسال همگانی", callback_data="broadcast"),
    )
    markup.add(types.InlineKeyboardButton("🚪 لفت بده", callback_data="leave"))
    return markup

# ---------- پنل سودو ----------
@bot.message_handler(commands=["panel"])
def sudo_panel(m):
    if not is_owner(m.from_user.id):
        return bot.reply_to(m, "❌ فقط مدیر اصلی به این بخش دسترسی دارد.")
    text = (
        "⚙️ <b>پنل مدیریت هوش مصنوعی نوری</b>\n\n"
        "از دکمه‌های زیر برای مدیریت ربات استفاده کنید 👇"
    )
    bot.send_message(m.chat.id, text, reply_markup=sudo_menu())

# ---------- آمار ----------
@bot.callback_query_handler(func=lambda c: c.data == "stats")
def show_stats(c):
    d = load_data()
    users = len(d["users"])
    groups = len(d["groups"])
    bans = len(d["bans"])
    actives = sum(1 for u in d["users"].values() if u.get("ai_on"))
    msg = (
        f"📊 <b>آمار کلی ربات</b>\n\n"
        f"👤 کاربران: {users}\n"
        f"👥 گروه‌ها: {groups}\n"
        f"🚫 بن‌شده‌ها: {bans}\n"
        f"⚡ فعال‌ها: {actives}\n"
        f"🕓 زمان: {shamsi_now()}"
    )
    try:
        bot.edit_message_text(msg, c.message.chat.id, c.message.message_id)
    except:
        bot.send_message(c.message.chat.id, msg)

# ---------- ارسال همگانی ----------
@bot.callback_query_handler(func=lambda c: c.data == "broadcast")
def broadcast_start(c):
    if c.from_user.id != SUDO_ID:
        return
    msg = bot.send_message(c.message.chat.id, "📝 لطفاً پیام همگانی خود را ارسال کنید:")
    bot.register_next_step_handler(msg, process_broadcast)

def process_broadcast(m):
    d = load_data()
    text = m.text
    for uid in d["users"]:
        try:
            bot.send_message(uid, f"📢 پیام از مدیر:\n\n{text}")
        except:
            pass
    bot.reply_to(m, "✅ پیام همگانی برای همه ارسال شد.")

# ---------- لفت بده ----------
@bot.callback_query_handler(func=lambda c: c.data == "leave")
def leave_group(c):
    if c.from_user.id != SUDO_ID:
        return
    bot.send_message(c.message.chat.id, "🚪 ربات از گروه خارج شد.")
    bot.leave_chat(c.message.chat.id)

# ---------- شارژ گروه ----------
@bot.message_handler(func=lambda m: m.reply_to_message and m.text.startswith("شارژ"))
def charge_user(m):
    if not is_owner(m.from_user.id):
        return
    try:
        days = int(m.text.split()[1])
        target_id = str(m.reply_to_message.from_user.id)
        d = load_data()
        user = d["users"].get(target_id, {"credits": 0, "ai_on": True})
        user["credits"] = 999999
        user["expire"] = (datetime.now() + timedelta(days=days)).isoformat()
        d["users"][target_id] = user
        save_data(d)
        bot.reply_to(m, f"✅ کاربر برای {days} روز شارژ شد و محدودیت برداشته شد.")
        bot.send_message(target_id, f"💳 حساب شما برای {days} روز فعال شد!")
    except Exception as e:
        bot.reply_to(m, f"⚠️ خطا در شارژ: {e}")

# ---------- بن ----------
@bot.message_handler(func=lambda m: m.reply_to_message and m.text == "بن")
def ban_user(m):
    if not is_owner(m.from_user.id):
        return
    target_id = str(m.reply_to_message.from_user.id)
    d = load_data()
    d["bans"][target_id] = True
    save_data(d)
    bot.reply_to(m, "🚫 کاربر بن شد و دیگر پاسخی دریافت نخواهد کرد.")
    bot.send_message(target_id, "⛔ شما از ربات بن شدید.")

# ---------- سکوت ----------
@bot.message_handler(func=lambda m: m.reply_to_message and m.text == "سکوت")
def mute_user(m):
    if not is_owner(m.from_user.id):
        return
    target_id = str(m.reply_to_message.from_user.id)
    d = load_data()
    user = d["users"].get(target_id, {"ai_on": True})
    user["muted_until"] = (datetime.now() + timedelta(hours=5)).isoformat()
    d["users"][target_id] = user
    save_data(d)
    bot.reply_to(m, "🔇 کاربر برای ۵ ساعت در حالت سکوت قرار گرفت.")
    bot.send_message(target_id, "🤫 شما به مدت ۵ ساعت در سکوت هستید.")

# ---------- راهنما ----------
@bot.callback_query_handler(func=lambda c: c.data == "help")
def show_help(c):
    text = (
        "📘 <b>راهنمای ربات هوشمند نوری</b>\n\n"
        "💡 دستورات اصلی:\n"
        "🔹 بنویس «ربات بگو» تا فعال شم.\n"
        "🔹 بنویس «ربات نگو» تا خاموش شم.\n"
        "🔹 با من صحبت کن، هر سوالی داشتی بپرس!\n\n"
        "📦 اعتبار پیش‌فرض: ۵ پیام رایگان.\n"
        "برای افزایش پیام یا شارژ با مدیر تماس بگیر 💳"
    )
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=main_menu())
    except:
        bot.send_message(c.message.chat.id, text, reply_markup=main_menu())

# ---------- اجرای مداوم ----------
bot.infinity_polling(timeout=30, long_polling_timeout=10)
