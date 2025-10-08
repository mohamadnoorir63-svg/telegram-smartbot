# -*- coding: utf-8 -*-
# Persian Lux AI Panel – Smart Edition
# Designed for Mohammad 👑

import os, json, random, time, logging
from datetime import datetime
import jdatetime
import telebot
from telebot import types
import openai

# ================= ⚙️ تنظیمات پایه =================
TOKEN   = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
openai.api_key = OPENAI_API_KEY

DATA_FILE = "data.json"
LOG_FILE  = "error.log"

logging.basicConfig(filename=LOG_FILE, level=logging.ERROR,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# ================= 💾 فایل داده =================
def base_data():
    return {
        "welcome": {}, "locks": {}, "admins": {}, "sudo_list": [],
        "banned": {}, "muted": {}, "warns": {}, "users": [],
        "ai_status": True, "charges": {}
    }

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(base_data())
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = base_data()
    for k in base_data():
        if k not in data:
            data[k] = base_data()[k]
    save_data(data)
    return data

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def register_group(gid):
    data = load_data()
    gid = str(gid)
    data["welcome"].setdefault(gid, {"enabled": True, "type": "text", "content": None, "file_id": None})
    data["locks"].setdefault(gid, {k: False for k in ["link","group","photo","video","sticker","gif","file","music","voice","forward"]})
    save_data(data)

# ================= 🧩 ابزارها =================
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
        st = bot.get_chat_member(chat_id, uid).status
        return st in ("administrator", "creator")
    except: return False# ================= 💬 کنترل هوش مصنوعی و شارژ =================
def get_charge(uid):
    d = load_data()
    return d["charges"].get(str(uid), 5)  # پیش‌فرض ۵ پیام

def reduce_charge(uid):
    d = load_data()
    uid = str(uid)
    if uid not in d["charges"]:
        d["charges"][uid] = 5
    if d["charges"][uid] > 0:
        d["charges"][uid] -= 1
    save_data(d)

def add_charge(uid, amount):
    d = load_data()
    uid = str(uid)
    d["charges"][uid] = d["charges"].get(uid, 0) + amount
    save_data(d)

@bot.message_handler(func=lambda m: is_sudo(m.from_user.id) and m.reply_to_message and cmd_text(m).startswith("شارژ "))
def charge_user(m):
    try:
        amount = int(cmd_text(m).split(" ")[1])
        uid = m.reply_to_message.from_user.id
        add_charge(uid, amount)
        bot.reply_to(m, f"💎 به کاربر <a href='tg://user?id={uid}'>شارژ {amount}</a> اضافه شد.")
    except:
        bot.reply_to(m, "⚠️ فرمت نادرست. مثال: شارژ ۵ (در پاسخ به کاربر)")

@bot.message_handler(func=lambda m: cmd_text(m) in ["ربات جواب بده", "ربات روشن"])
def ai_on(m):
    d = load_data()
    d["ai_status"] = True
    save_data(d)
    bot.reply_to(m, "🤖 ربات هوشمند فعال شد و آماده پاسخ‌گویی است!")

@bot.message_handler(func=lambda m: cmd_text(m) in ["ربات خاموش", "ربات توقف"])
def ai_off(m):
    d = load_data()
    d["ai_status"] = False
    save_data(d)
    bot.reply_to(m, "🔕 ربات خاموش شد و دیگر پاسخ نمی‌دهد.")

# ================= 🧠 پاسخ هوشمند از ChatGPT =================
@bot.message_handler(func=lambda m: not m.text.startswith("/"))
def ai_reply(m):
    d = load_data()
    if not d.get("ai_status", True):
        return  # وقتی ربات خاموش است جواب ندهد
    uid = str(m.from_user.id)
    if is_sudo(uid):  # سودو شارژ ندارد
        pass
    else:
        if get_charge(uid) <= 0:
            return bot.reply_to(m, "⚠️ شارژ شما تمام شده است.\nبرای تمدید با پشتیبانی @NOORI_NOOR تماس بگیرید.")
        reduce_charge(uid)
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant speaking Persian."},
                {"role": "user", "content": m.text}
            ],
        )
        response = completion.choices[0].message["content"].strip()
        bot.reply_to(m, response)
    except Exception as e:
        logging.error(f"AI error: {e}")
        bot.reply_to(m, "❗ خطا در ارتباط با هوش مصنوعی، بعداً تلاش کن.")

# ================= 🎭 فال و جوک =================
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "ثبت جوک")
def add_joke(m):
    d = load_data()
    txt = (m.reply_to_message.text or "").strip()
    if not txt:
        return bot.reply_to(m, "⚠️ لطفاً روی پیام متنی ریپلای کن تا ذخیره کنم.")
    if txt in d["jokes"]:
        return bot.reply_to(m, "⚠️ این جوک قبلاً ثبت شده بود.")
    d["jokes"].append(txt); save_data(d)
    bot.reply_to(m, f"😂 جوک جدید ذخیره شد:\n\n{txt[:60]}")

@bot.message_handler(func=lambda m: cmd_text(m) == "جوک")
def random_joke(m):
    d = load_data(); jokes = d.get("jokes", [])
    if not jokes: return bot.reply_to(m, "😅 هنوز جوکی ثبت نشده!")
    bot.reply_to(m, f"😂 {random.choice(jokes)}")

@bot.message_handler(func=lambda m: cmd_text(m).startswith("حذف جوک "))
def del_joke(m):
    d = load_data(); jokes = d.get("jokes", [])
    try:
        idx = int(cmd_text(m).split(" ")[2]) - 1
        removed = jokes.pop(idx)
        save_data(d)
        bot.reply_to(m, f"🗑 جوک حذف شد:\n«{removed}»")
    except:
        bot.reply_to(m, "❗ شماره جوک نادرست است.")

@bot.message_handler(func=lambda m: cmd_text(m) == "لیست جوک")
def list_jokes(m):
    d = load_data(); jokes = d.get("jokes", [])
    if not jokes: return bot.reply_to(m, "❗ هیچ جوکی ثبت نشده.")
    text = "\n".join([f"{i+1}. {j}" for i, j in enumerate(jokes)])
    bot.reply_to(m, f"📜 <b>لیست جوک‌ها:</b>\n{text}")

# ==== فال ====
@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and m.reply_to_message and cmd_text(m) == "ثبت فال")
def add_fal(m):
    d = load_data()
    txt = (m.reply_to_message.text or "").strip()
    if not txt:
        return bot.reply_to(m, "⚠️ لطفاً روی پیام متنی ریپلای کن.")
    d["falls"].append(txt); save_data(d)
    bot.reply_to(m, "🔮 فال ذخیره شد.")

@bot.message_handler(func=lambda m: cmd_text(m) == "فال")
def random_fal(m):
    d = load_data(); f = d.get("falls", [])
    if not f: return bot.reply_to(m, "😅 هنوز هیچ فالی ثبت نشده!")
    bot.reply_to(m, f"🔮 فال امروز:\n{random.choice(f)}")

@bot.message_handler(func=lambda m: cmd_text(m).startswith("حذف فال "))
def del_fal(m):
    d = load_data(); f = d.get("falls", [])
    try:
        idx = int(cmd_text(m).split(" ")[2]) - 1
        removed = f.pop(idx)
        save_data(d)
        bot.reply_to(m, f"🗑 فال شماره {idx+1} حذف شد:\n«{removed}»")
    except:
        bot.reply_to(m, "❗ شماره فال نامعتبر است یا خطایی رخ داده.")# ================= 🕒 آمار / ساعت =================
@bot.message_handler(func=lambda m: cmd_text(m) == "آمار")
def show_stats(m):
    d = load_data()
    users = len(set(d.get("users", [])))
    groups = len(d.get("welcome", {}))
    bot.reply_to(m,
        f"📊 <b>آمار Persian Lux AI Panel</b>\n"
        f"👤 کاربران: {users}\n👥 گروه‌ها: {groups}\n"
        f"📅 {shamsi_date()} | ⏰ {shamsi_time()}")

@bot.message_handler(func=lambda m: cmd_text(m) == "ساعت")
def show_time(m):
    bot.reply_to(m, f"⏰ {shamsi_time()} | 📅 {shamsi_date()}")

# ================= 👋 خوشامد =================
@bot.message_handler(content_types=["new_chat_members"])
def welcome_new(m):
    register_group(m.chat.id)
    data = load_data(); gid = str(m.chat.id)
    s = data["welcome"].get(gid, {"enabled": True})
    if not s.get("enabled", True): return
    user = m.new_chat_members[0]
    name = user.first_name or "دوست جدید"
    text = s.get("content") or f"✨ سلام {name}!\nبه گروه <b>{m.chat.title}</b> خوش اومدی 🌸\n⏰ {shamsi_time()}"
    text = text.replace("{name}", name).replace("{time}", shamsi_time())
    if s.get("file_id"):
        bot.send_photo(m.chat.id, s["file_id"], caption=text)
    else:
        bot.send_message(m.chat.id, text)

@bot.message_handler(func=lambda m: is_admin(m.chat.id, m.from_user.id) and cmd_text(m) in ["خوشامد روشن","خوشامد خاموش"])
def toggle_welcome(m):
    data = load_data(); gid = str(m.chat.id)
    en = cmd_text(m) == "خوشامد روشن"
    data["welcome"].setdefault(gid, {"enabled": True})
    data["welcome"][gid]["enabled"] = en
    save_data(data)
    bot.reply_to(m, "🟢 خوشامد روشن شد." if en else "🔴 خوشامد خاموش شد.")

# ================= 🔒 قفل‌ها =================
LOCK_MAP = {
    "لینک":"link","گروه":"group","عکس":"photo","ویدیو":"video",
    "استیکر":"sticker","گیف":"gif","فایل":"file","موزیک":"music",
    "ویس":"voice","فوروارد":"forward"
}

@bot.message_handler(func=lambda m: cmd_text(m).startswith("قفل ") or cmd_text(m).startswith("بازکردن "))
def toggle_lock(m):
    if not is_admin(m.chat.id, m.from_user.id): return
    d = load_data(); gid = str(m.chat.id)
    part = cmd_text(m).split(" ")
    if len(part) < 2: return
    key_fa = part[1]; lock_type = LOCK_MAP.get(key_fa)
    if not lock_type: return bot.reply_to(m, "❌ نوع قفل نامعتبر است.")
    en = cmd_text(m).startswith("قفل ")
    d["locks"].setdefault(gid, {k: False for k in LOCK_MAP.values()})
    if d["locks"][gid][lock_type] == en:
        return bot.reply_to(m, "⚠️ این قفل همین حالا هم در همین حالت است.")
    d["locks"][gid][lock_type] = en; save_data(d)
    if lock_type == "group":
        bot.send_message(m.chat.id, f"{'🚫 گروه بسته شد ❌' if en else '✅ گروه باز شد 🌸'}\n⏰ {shamsi_time()}")
    else:
        bot.reply_to(m, f"{'🔒' if en else '🔓'} قفل {key_fa} {'فعال' if en else 'غیرفعال'} شد.")

# ================= 🚪 لفت بده =================
@bot.message_handler(func=lambda m: cmd_text(m) == "لفت بده" and is_admin(m.chat.id, m.from_user.id))
def leave_group(m):
    bot.send_message(m.chat.id, "👋 با آرزوی موفقیت، از گروه خارج می‌شوم.")
    bot.leave_chat(m.chat.id)

# ================= ℹ️ راهنما =================
@bot.message_handler(func=lambda m: cmd_text(m) == "راهنما")
def show_help(m):
    txt = (
        "📘 <b>راهنمای Persian Lux AI Panel</b>\n\n"
        "🧠 هوش مصنوعی: ربات جواب بده | ربات خاموش\n"
        "⚡ شارژ کاربر (فقط سودو): در ریپلای → شارژ ۵\n"
        "😂 جوک‌ها: ثبت جوک | جوک | لیست جوک | حذف جوک N\n"
        "🔮 فال‌ها: ثبت فال | فال | لیست فال | حذف فال N\n"
        "🔒 قفل‌ها | 🚫 بن | 🔇 سکوت | ⚠️ اخطار\n"
        "👋 خوشامد | تنظیم | روشن/خاموش\n"
        "🧹 حذف پیام‌ها | 📢 ارسال همگانی | 🚪 لفت بده\n\n"
        "👑 سازنده: محمد نوری | پشتیبانی: @NOORI_NOOR"
    )
    bot.reply_to(m, txt)

# ================= 🚀 استارت و اجرای نهایی =================
@bot.message_handler(commands=["start"])
def start_cmd(m):
    d = load_data()
    uid = str(m.from_user.id)
    if uid not in d["users"]:
        d["users"].append(uid)
        save_data(d)

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("➕ افزودن به گروه", url="https://t.me/Noorir63_Bot?startgroup=true"),
        types.InlineKeyboardButton("🆘 پشتیبانی", url="https://t.me/NOORI_NOOR")
    )

    bot.send_message(m.chat.id,
        "👋 سلام! من <b>Persian Lux AI Panel</b> هستم.\n"
        "🤖 رباتی هوشمند و چندمنظوره برای مدیریت و گفتگو با هوش مصنوعی.\n"
        "✨ می‌تونی منو به گروهت اضافه کنی یا ازم سوال بپرسی!",
        reply_markup=markup
    )

print("🤖 Persian Lux AI Panel – Smart Edition در حال اجراست...")
while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        logging.error(f"polling crash: {e}")
        time.sleep(5)
