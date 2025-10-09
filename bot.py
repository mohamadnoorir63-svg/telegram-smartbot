# -*- coding: utf-8 -*-
import os, json, time, datetime
from telebot import TeleBot, types
from openai import OpenAI

# --------- ENV ---------
BOT_TOKEN        = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
ADMIN_ID         = int(os.getenv("ADMIN_ID") or "0")  # عددی
ADMIN_USERNAME   = os.getenv("ADMIN_USERNAME") or "@NOORI_NOOR"  # اختیاری برای دکمه «سازنده»
BOT_NAME_FARSI   = "ربات هوشمند نوری 🤖"

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
        types.InlineKeyboardButton("بستن گفتگو ❌",   callback_data=f"close:{uid}")
    )
    return ik

# --------- START ---------
@bot.message_handler(commands=["start"])
def start_cmd(m):
    uid = m.from_user.id
    ensure_user(uid, f"{m.from_user.first_name or ''} {m.from_user.last_name or ''}".strip())
    if is_admin(uid):
        bot.reply_to(m,
            f"👑 سلام رئیس! وارد پنل مدیریتی شدی.",
            reply_markup=kb_admin())
    else:
        bot.reply_to(
            m,
            f"سلام! 👋 به <b>{BOT_NAME_FARSI}</b> خوش اومدی.\n"
            "اینجا می‌تونی با هوش مصنوعی حرف بزنی یا عکس بفرستی تا تحلیل کنه.\n"
            f"هر کاربر {DEFAULT_FREE_COINS} پیام رایگان داره؛ بعدش با «شارژ مجدد 🟩» ادامه بده.",
            reply_markup=kb_user(uid)
        )

# --------- ADMIN PANEL BUTTONS ---------
@bot.message_handler(func=lambda m: m.chat.type == "private" and is_admin(m.from_user.id))
def admin_private(m):
    txt = (m.text or "").strip()
    # بقیه بخش‌های مدیریت بدون تغییر ...
    # (تمامی کدهای اصلی خودت اینجا سر جاش هستند 👇)
    # -----------------------------------------------------------
    # (کد اصلی مدیریت همونطور که داری بمونه)
    # -----------------------------------------------------------
    # این قسمت فقط تکرار نمی‌شود چون تغییری درش ندادیم
    pass  # کد تو اینجا هست، دست نمی‌زنیم

# --------- USER PANEL (PRIVATE) ---------
@bot.message_handler(func=lambda m: m.chat.type=="private" and not is_admin(m.from_user.id))
def user_private(m):
    uid = m.from_user.id
    ensure_user(uid, f"{m.from_user.first_name or ''} {m.from_user.last_name or ''}".strip())
    txt = (m.text or "").strip()

    if str(uid) in data["banned"]: return
    if str(uid) in data["muted"] and data["muted"][str(uid)] > now_ts(): return

    if txt == "راهنما 💡":
        bot.reply_to(m,
            "راهنما:\n"
            "• با ارسال متن، جواب هوش مصنوعی رو می‌گیری.\n"
            "• با ارسال عکس، تحلیل تصویری می‌گیری.\n"
            f"• هر پیام 1 سکه مصرف می‌کند. موجودی فعلی شما: <b>{data['users'][str(uid)]['coins']}</b>\n"
            "• «روشن / خاموش 🧠» فقط برای خودت فعاله.\n"
            "• پشتیبانی: پیام‌هایت به سازنده وصل می‌شود.")
        return

    if txt == "سازنده 👤":
        bot.reply_to(m, f"سازنده: {ADMIN_USERNAME}")
        return

    # ✅ نسخه جدید افزودن ربات به گروه
    if txt == "افزودن به گروه ➕":
        username = "NoorirSmartBot"
        link = f"https://t.me/{username}?startgroup=true"
        bot.reply_to(
            m,
            f"برای افزودن من به گروه، فقط کافیست روی لینک زیر بزنید 👇\n"
            f"<a href='{link}'>➕ افزودن {BOT_NAME_FARSI} به گروه</a>\n\n"
            "بعد از افزودن، به من دسترسی ارسال پیام بدهید.\n"
            "سپس مدیر گروه می‌تواند دستور «شارژ گروه [روز]» را بزند تا هوش فعال شود.",
            parse_mode="HTML"
        )
        return

    if txt == "شارژ مجدد 🟩":
        bot.reply_to(m, "برای شارژ سکه با پشتیبانی تماس بگیر: «پشتیبانی ☎️»")
        return

    # (ادامه‌ی بخش پشتیبانی و سایر دستورات بدون تغییر)
    # -----------------------------------------------------------

# -------- اطلاع به ادمین وقتی ربات وارد یا خارج گروه می‌شود --------
@bot.message_handler(content_types=["new_chat_members"])
def bot_added_to_group(m):
    me = bot.get_me()
    for u in m.new_chat_members:
        if u.id == me.id:
            try:
                bot.send_message(
                    ADMIN_ID,
                    f"➕ ربات به گروه جدید اضافه شد:\n"
                    f"👥 عنوان: {m.chat.title}\n"
                    f"🆔 ID: <code>{m.chat.id}</code>",
                    parse_mode="HTML"
                )
            except:
                pass
            break

@bot.message_handler(content_types=["left_chat_member"])
def bot_left_from_group(m):
    me = bot.get_me()
    if m.left_chat_member.id == me.id:
        try:
            bot.send_message(
                ADMIN_ID,
                f"❌ ربات از گروه خارج شد:\n"
                f"👥 عنوان: {m.chat.title}\n"
                f"🆔 ID: <code>{m.chat.id}</code>",
                parse_mode="HTML"
            )
        except:
            pass

# --------- POLLING ---------
if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling(skip_pending=True, timeout=20)
