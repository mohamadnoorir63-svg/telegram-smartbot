# -*- coding: utf-8 -*-
import os, json, time, datetime
from telebot import TeleBot, types
from openai import OpenAI

# --------- ENV ---------
BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID") or "0")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME") or "@NOORI_NOOR"
BOT_NAME_FARSI = "ربات هوشمند نوری 🤖"

if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN تعریف نشده است.")
if not ADMIN_ID:
    raise SystemExit("ADMIN_ID (عددی) تعریف نشده است.")
if not OPENAI_API_KEY:
    raise SystemExit("OPENAI_API_KEY تعریف نشده است.")

# --------- INIT ---------
bot = TeleBot(BOT_TOKEN, parse_mode="HTML")
client = OpenAI(api_key=OPENAI_API_KEY)
DATA_FILE = "data.json"
DEFAULT_FREE_COINS = 5


# --------- UTIL ---------
def now_ts(): return int(time.time())

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

def is_admin(uid): return int(uid) == int(ADMIN_ID)

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
        bot.reply_to(m, f"👑 سلام رئیس! وارد پنل مدیریتی شدی.", reply_markup=kb_admin())
    else:
        bot.reply_to(m,
            f"سلام! 👋 به <b>{BOT_NAME_FARSI}</b> خوش اومدی.\n"
            "اینجا می‌تونی با هوش مصنوعی حرف بزنی یا عکس بفرستی تا تحلیل کنه.\n"
            f"هر کاربر {DEFAULT_FREE_COINS} پیام رایگان داره؛ بعدش با «شارژ مجدد 🟩» ادامه بده.",
            reply_markup=kb_user(uid)
        )


# --------- USER PANEL ---------
@bot.message_handler(func=lambda m: m.chat.type=="private" and not is_admin(m.from_user.id))
def user_private(m):
    uid = m.from_user.id
    ensure_user(uid)
    cu = data["users"][str(uid)]
    txt = (m.text or "").strip()

    if str(uid) in data["banned"]:
        return
    if str(uid) in data["muted"] and data["muted"][str(uid)] > now_ts():
        return

    # دکمه‌ها
    if txt == "راهنما 💡":
        bot.reply_to(m,
            f"راهنما:\n"
            "• با ارسال متن، جواب هوش مصنوعی رو می‌گیری.\n"
            "• با ارسال عکس، تحلیل تصویری می‌گیری.\n"
            f"• هر پیام ۱ سکه مصرف می‌کند. موجودی فعلی: <b>{cu['coins']}</b>")
        return

    if txt == "سازنده 👤":
        bot.reply_to(m, f"سازنده: {ADMIN_USERNAME}")
        return

    if txt == "روشن / خاموش 🧠":
        cu["active"] = not cu["active"]
        save_data(data)
        bot.reply_to(m, f"{'✅ فعال شد' if cu['active'] else '⛔️ غیرفعال شد'}", reply_markup=kb_user(uid))
        return

    if txt == "شارژ مجدد 🟩":
        bot.reply_to(m, "برای شارژ با پشتیبانی تماس بگیر.")
        return

    if txt == "پشتیبانی ☎️":
        data["support_open"][str(uid)] = True
        save_data(data)
        bot.reply_to(m, "✉️ گفتگوی پشتیبانی باز شد.")
        try: bot.send_message(ADMIN_ID, f"📥 پیام جدید از کاربر {uid}")
        except: pass
        return

    if txt == "پایان پشتیبانی":
        data["support_open"][str(uid)] = False
        save_data(data)
        bot.reply_to(m, "✅ گفتگوی پشتیبانی بسته شد.")
        return

    # اگر پشتیبانی باز است
    if data["support_open"].get(str(uid)):
        bot.copy_message(ADMIN_ID, m.chat.id, m.message_id, reply_markup=ikb_support(uid))
        bot.reply_to(m, "📨 پیام به پشتیبانی ارسال شد.")
        return

    # حالت غیرفعال یا بدون سکه
    if not cu.get("active", True):
        bot.reply_to(m, "⏸ حالت گفتگو غیرفعال است.")
        return
    if cu.get("coins", 0) <= 0:
        bot.reply_to(m, "💸 سکه شما تمام شده است.")
        return

    # پیام متنی → GPT-4o
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful AI that answers in Persian."},
                {"role": "user", "content": txt}
            ]
        )
        answer = resp.choices[0].message.content
        bot.reply_to(m, f"🤖 {answer}")
        cu["coins"] -= 1
        save_data(data)
    except Exception as e:
        bot.reply_to(m, f"❌ خطا در پاسخ:\n{e}")


# --------- PHOTO → GPT-4o Vision ---------
@bot.message_handler(content_types=["photo"])
def handle_photo(m):
    uid = m.from_user.id
    ensure_user(uid)
    cu = data["users"][str(uid)]

    if str(uid) in data["banned"]: return
    if str(uid) in data["muted"] and data["muted"][str(uid)] > now_ts(): return
    if not cu.get("active", True):
        bot.reply_to(m, "⏸ حالت گفتگو غیرفعال است.")
        return
    if cu.get("coins", 0) <= 0:
        bot.reply_to(m, "💸 سکه شما تمام شده است.")
        return

    try:
        file_info = bot.get_file(m.photo[-1].file_id)
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
        print(f"📸 دریافت عکس از {uid}: {file_url}")

        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "این تصویر را توصیف و تحلیل کن (به فارسی)."},
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


# --------- MAIN ---------
if __name__ == "__main__":
    print("🤖 Bot is running with GPT-4o...")
    bot.infinity_polling(skip_pending=True, timeout=20)
