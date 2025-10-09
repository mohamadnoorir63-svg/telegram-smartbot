# -- coding: utf-8 --

import os, json, time, datetime
from telebot import TeleBot, types
from openai import OpenAI

# --------- ENV ---------

BOT_TOKEN        = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
ADMIN_ID         = int(os.getenv("ADMIN_ID") or "0")  # عددی
ADMIN_USERNAME   = os.getenv("ADMIN_USERNAME") or "@NOORI_NOOR"  # اختیاری برای دکمه «سازنده»
BOT_NAME_FARSI   = "ربات هوشمند نوری 🤖"
BOT_USERNAME     = "NoorirSmartBot"

if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN تعریف نشده است.")
if not ADMIN_ID:
    raise SystemExit("ADMIN_ID (عددی) تعریف نشده است.")
if not OPENAI_API_KEY:
    raise SystemExit("OPENAI_API_KEY تعریف نشده است.")

# --------- INIT ---------

bot    = TeleBot(BOT_TOKEN, parse_mode="HTML")
client = OpenAI(api_key=OPENAI_API_KEY)

DATA_FILE = "data.json"
DEFAULT_FREE_COINS = 5

def now_ts():
    return int(time.time())

def load_data():
    if not os.path.exists(DATA_FILE):
        data = {
            "users": {},
            "banned": [],
            "muted": {},
            "groups": {},
            "support_open": {},
            "admin_reply_to": None,
            "pending_broadcast": False
        }
        save_data(data)
        return data
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        d = json.load(f)

    d.setdefault("users", {})
    d.setdefault("banned", [])
    d.setdefault("muted", {})
    d.setdefault("groups", {})
    d.setdefault("support_open", {})
    d.setdefault("admin_reply_to", None)
    d.setdefault("pending_broadcast", False)
    return d

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

data = load_data()

def is_admin(uid): 
    return int(uid) == int(ADMIN_ID)

def ensure_user(uid, name=""):
    suid = str(uid)
    if suid not in data["users"]:
        data["users"][suid] = {"coins": DEFAULT_FREE_COINS, "active": True, "name": name or ""}
        save_data(data)

# --------- KEYBOARDS ---------

def kb_user(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(types.KeyboardButton("راهنما 💡"), types.KeyboardButton("شارژ مجدد 🟩"))
    kb.row(types.KeyboardButton("پشتیبانی ☎️"), types.KeyboardButton("سازنده 👤"))
    kb.row(types.KeyboardButton("افزودن به گروه ➕"))
    kb.row(types.KeyboardButton("روشن / خاموش 🧠"))
    return kb

def kb_admin():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(types.KeyboardButton("آمار کاربران 📊"), types.KeyboardButton("شارژ کاربر 💰"))
    kb.row(types.KeyboardButton("سکوت کاربر 🤐"), types.KeyboardButton("بن کاربر 🚫"))
    kb.row(types.KeyboardButton("لیست بن‌ها 🚫"), types.KeyboardButton("لیست سکوت‌ها 🤫"))
    kb.row(types.KeyboardButton("ارسال همگانی 📣"), types.KeyboardButton("لفت بده ↩️"))
    kb.row(types.KeyboardButton("بازگشت BACK"))
    return kb

def ikb_support(uid):
    ik = types.InlineKeyboardMarkup()
    ik.add(
        types.InlineKeyboardButton("پاسخ به کاربر ✉️", callback_data=f"reply:{uid}"),
        types.InlineKeyboardButton("بستن گفتگو ❌", callback_data=f"close:{uid}")
    )
    return ik

# --------- START ---------

@bot.message_handler(commands=["start"])
def start_cmd(m):
    uid = m.from_user.id
    ensure_user(uid, f"{m.from_user.first_name or ''} {m.from_user.last_name or ''}".strip())
    if is_admin(uid):
        bot.reply_to(m, "👑 سلام رئیس! وارد پنل مدیریتی شدی.", reply_markup=kb_admin())
    else:
        bot.reply_to(
            m,
            f"سلام! 👋 به <b>{BOT_NAME_FARSI}</b> خوش اومدی.\n"
            "اینجا می‌تونی با هوش مصنوعی حرف بزنی یا عکس بفرستی تا تحلیل کنه.\n"
            f"هر کاربر {DEFAULT_FREE_COINS} پیام رایگان داره؛ بعدش با «شارژ مجدد 🟩» ادامه بده.",
            reply_markup=kb_user(uid)
        )

# --------- ADMIN PANEL ---------

@bot.message_handler(func=lambda m: m.chat.type == "private" and is_admin(m.from_user.id))
def admin_private(m):
    txt = (m.text or "").strip()

    if txt == "ارسال همگانی 📣":
        data["pending_broadcast"] = True
        save_data(data)
        bot.reply_to(m, "✍️ پیام خود را بنویس؛ همان پیام برای همه کاربران و گروه‌ها ارسال می‌شود.")
        return

    if data.get("pending_broadcast"):
        if txt == "بازگشت BACK":
            data["pending_broadcast"] = False
            save_data(data)
            bot.reply_to(m, "ارسال همگانی لغو شد.")
            return
        ok, fail = 0, 0
        for suid in list(data["users"].keys()):
            try:
                bot.copy_message(int(suid), m.chat.id, m.message_id)
                ok += 1
            except:
                fail += 1
        for sgid in list(data["groups"].keys()):
            try:
                bot.copy_message(int(sgid), m.chat.id, m.message_id)
                ok += 1
            except:
                fail += 1
        data["pending_broadcast"] = False
        save_data(data)
        bot.reply_to(m, f"📣 ارسال شد. موفق: {ok} | ناموفق: {fail}")
        return

    if txt == "آمار کاربران 📊":
        total = len(data["users"])
        total_ban = len(data["banned"])
        total_mute = len([1 for k,v in data["muted"].items() if v > now_ts()])
        bot.reply_to(m, f"📈 کاربران: {total}\n🚫 بن‌شده: {total_ban}\n🤐 در سکوت: {total_mute}")
        return

# --------- USER PANEL ---------

@bot.message_handler(func=lambda m: m.chat.type=="private" and not is_admin(m.from_user.id))
def user_private(m):
    uid = m.from_user.id
    ensure_user(uid, f"{m.from_user.first_name or ''} {m.from_user.last_name or ''}".strip())
    txt = (m.text or "").strip()

    if str(uid) in data["banned"]: return
    if str(uid) in data["muted"] and data["muted"][str(uid)] > now_ts(): return

    if txt == "راهنما 💡":
        bot.reply_to(m, "راهنما:\n• ارسال متن = پاسخ هوش مصنوعی\n• ارسال عکس = تحلیل تصویری\n• هر پیام 1 سکه مصرف می‌کند.")
        return

    if txt == "سازنده 👤":
        bot.reply_to(m, f"سازنده: {ADMIN_USERNAME}")
        return

    # ✅ بخش جدید با لینک واقعی برای افزودن ربات به گروه
    if txt == "افزودن به گروه ➕":
        link = f"https://t.me/{BOT_USERNAME}?startgroup=true"
        bot.reply_to(
            m,
            "برای افزودن من به گروه، فقط کافیست روی لینک زیر بزنید 👇\n\n"
            f"<a href='{link}'>➕ افزودن {BOT_NAME_FARSI} به گروه</a>\n\n"
            "بعد از افزودن، به من دسترسی ارسال پیام بدهید.\n"
            "سپس مدیر گروه می‌تواند دستور «شارژ گروه [روز]» را بزند تا هوش فعال شود.",
            parse_mode="HTML"
        )
        return

    if txt == "شارژ مجدد 🟩":
        bot.reply_to(m, "برای شارژ سکه با پشتیبانی تماس بگیر: «پشتیبانی ☎️»")
        return

    if txt == "پشتیبانی ☎️":
        data["support_open"][str(uid)] = True
        save_data(data)
        bot.reply_to(m, "✉️ گفتگوی پشتیبانی باز شد. پیام بده؛ به سازنده وصل می‌شود.")
        try:
            bot.send_message(ADMIN_ID, f"📥 پیام جدید از کاربر {uid}")
        except: pass
        return

    if txt == "پایان پشتیبانی":
        data["support_open"][str(uid)] = False
        save_data(data)
        bot.reply_to(m, "✅ گفتگوی پشتیبانی بسته شد.")
        return

    cu = data["users"][str(uid)]
    if not cu.get("active", True):
        return bot.reply_to(m, "⏸ حالت گفتگو غیرفعال است.")
    if cu.get("coins", 0) <= 0:
        return bot.reply_to(m, "💸 سکه شما تمام شده است.")

    if m.content_type == "text":
        ask_text = (m.text or "").strip()
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful AI that answers in Persian."},
                    {"role": "user", "content": ask_text}
                ]
            )
            answer = resp.choices[0].message.content
            bot.reply_to(m, f"🤖 {answer}")
            cu["coins"] -= 1
            save_data(data)
        except Exception as e:
            bot.reply_to(m, f"❌ خطایی رخ داد:\n{e}")

# --------- PHOTO ---------

@bot.message_handler(content_types=["photo"])
def handle_photo(m):
    uid = m.from_user.id
    ensure_user(uid)
    if str(uid) in data["banned"]: return
    if str(uid) in data["muted"] and data["muted"][str(uid)] > now_ts(): return

    cu = data["users"][str(uid)]
    if not cu.get("active", True):
        return bot.reply_to(m, "⏸ حالت گفتگو غیرفعال است.")
    if cu.get("coins", 0) <= 0:
        return bot.reply_to(m, "💸 سکه شما تمام شده است.")

    try:
        file_info = bot.get_file(m.photo[-1].file_id)
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "این تصویر را توصیف و تحلیل کن."},
                    {"type": "image_url", "image_url": {"url": file_url}}
                ]
            }]
        )
        answer = resp.choices[0].message.content
        bot.reply_to(m, f"🖼️ تحلیل تصویر:\n{answer}")
        cu["coins"] -= 1
        save_data(data)
    except Exception as e:
        bot.reply_to(m, f"❌ خطا در تحلیل تصویر:\n{e}")

# --------- POLLING ---------
if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling(skip_pending=True, timeout=20)
