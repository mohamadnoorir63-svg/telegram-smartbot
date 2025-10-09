# -*- coding: utf-8 -*-
import os, json, time, datetime
from telebot import TeleBot, types
from openai import OpenAI

# --------- ENV ---------
BOT_TOKEN        = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
ADMIN_ID         = int(os.getenv("ADMIN_ID") or "0")  # عددی
ADMIN_USERNAME   = os.getenv("ADMIN_USERNAME") or "@NOORI_NOOR"
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
    kb.row(types.KeyboardButton("📋 لیست گروه‌ها"), types.KeyboardButton("بازگشت BACK"))
    return kb

def ikb_support(uid):
    ik = types.InlineKeyboardMarkup()
    ik.add(
        types.InlineKeyboardButton("پاسخ به کاربر ✉️", callback_data=f"reply:{uid}"),
        types.InlineKeyboardButton("بستن گفتگو ❌", callback_data=f"close:{uid}")
    )
    return ik

# -------- اطلاع به ادمین وقتی ربات وارد یا خارج گروه می‌شود --------
@bot.message_handler(content_types=["new_chat_members"])
def bot_added_to_group(m):
    me = bot.get_me()
    for u in m.new_chat_members:
        if u.id == me.id:
            gid = str(m.chat.id)
            data["groups"].setdefault(gid, {"expires": 0, "active": False, "title": m.chat.title})
            save_data(data)
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
        gid = str(m.chat.id)
        data["groups"].pop(gid, None)
        save_data(data)
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

# --------- ADMIN PANEL BUTTONS ---------
@bot.message_handler(func=lambda m: m.chat.type == "private" and is_admin(m.from_user.id))
def admin_private(m):
    txt = (m.text or "").strip()

    if txt == "📋 لیست گروه‌ها":
        if not data["groups"]:
            bot.reply_to(m, "📭 هیچ گروه فعالی وجود ندارد.")
        else:
            msg = "📋 گروه‌هایی که ربات در آنهاست:\n\n"
            for gid, ginfo in data["groups"].items():
                title = ginfo.get("title", "—")
                msg += f"• {title} — <code>{gid}</code>\n"
            bot.reply_to(m, msg, parse_mode="HTML")
        return# ارسال همگانی  
    if txt == "ارسال همگانی 📣":
        data["pending_broadcast"] = True
        save_data(data)
        bot.reply_to(m, "✍️ پیام خود را همینجا بفرست؛ همان پیام برای همهٔ کاربران و گروه‌ها کپی می‌شود.\n(برای انصراف: «بازگشت BACK»)")
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

    # آمار
    if txt == "آمار کاربران 📊":
        total = len(data["users"])
        total_ban = len(data["banned"])
        total_mute = len([1 for k,v in data["muted"].items() if v > now_ts()])
        bot.reply_to(m, f"📈 کاربران: {total}\n🚫 بن‌شده: {total_ban}\n🤐 در سکوت: {total_mute}")
        return

    # راهنمای دستورات نوشتاری سودو
    if txt == "بازگشت BACK":
        bot.reply_to(m,
            "دستورات تایپی سودو (فقط خصوصی):\n"
            "• <b>شارژ [uid] [تعداد]</b>\n"
            "• <b>بن [uid]</b> | <b>حذف بن [uid]</b>\n"
            "• <b>سکوت [uid] [ساعت]</b> | <b>حذف سکوت [uid]</b>\n"
            "• در گروه: <b>شارژ گروه [روز]</b> | <b>لفت بده</b>\n"
            "• <b>لیست بن‌ها</b> | <b>لیست سکوت‌ها</b>",
            reply_markup=kb_admin())
        return

    # میانبر دکمه‌ها
    if txt == "لفت بده ↩️":
        bot.reply_to(m, "دستور را داخل گروه بزن: «لفت بده»")
        return

    # بقیه دستورات تایپی مدیر همونطور که بودن، بدون حذف 👇
    parts = txt.replace("‌", " ").split()
    if not parts:
        return
    try:
        if parts[0] == "شارژ" and len(parts) == 3:
            uid = int(parts[1]); count = int(parts[2])
            ensure_user(uid)
            data["users"][str(uid)]["coins"] += count
            save_data(data)
            bot.reply_to(m, f"✅ به کاربر {uid} {count} سکه اضافه شد.")
            try: bot.send_message(uid, f"💰 سکه‌های شما {count} عدد شارژ شد.")
            except: pass
            return

        if parts[0] == "بن" and len(parts) == 2:
            uid = int(parts[1])
            if str(uid) not in data["banned"]:
                data["banned"].append(str(uid))
                save_data(data)
            bot.reply_to(m, f"🚫 کاربر {uid} بن شد.")
            return

        if parts[0] == "حذف" and len(parts) == 3 and parts[1] == "بن":
            uid = int(parts[2])
            if str(uid) in data["banned"]:
                data["banned"].remove(str(uid))
                save_data(data)
            bot.reply_to(m, f"✅ بن کاربر {uid} برداشته شد.")
            return

        if parts[0] == "سکوت" and len(parts) == 3:
            uid = int(parts[1]); hours = float(parts[2])
            expire = now_ts() + int(hours * 3600)
            data["muted"][str(uid)] = expire
            save_data(data)
            bot.reply_to(m, f"🤐 کاربر {uid} تا {hours} ساعت در سکوت است.")
            return

        if parts[0] == "حذف" and len(parts) == 3 and parts[1] == "سکوت":
            uid = int(parts[2])
            data["muted"].pop(str(uid), None)
            save_data(data)
            bot.reply_to(m, f"✅ سکوت کاربر {uid} برداشته شد.")
            return
    except Exception as e:
        bot.reply_to(m, f"❌ خطا: {e}")

# -------- افزودن به گروه با لینک دکمه --------
@bot.message_handler(func=lambda m: m.text == "افزودن به گروه ➕")
def add_group_btn(m):
    link = f"https://t.me/{BOT_USERNAME}?startgroup=true"
    bot.reply_to(m,
        f"برای افزودن من به گروه، روی دکمه زیر بزن 👇\n\n"
        f"<a href='{link}'>➕ افزودن {BOT_NAME_FARSI} به گروه</a>\n\n"
        "بعد از افزودن من به گروه:\n"
        "1️⃣ دسترسی ارسال پیام بده.\n"
        "2️⃣ مدیر گروه بنویسد:\n"
        "<code>شارژ گروه [روز]</code> تا فعال شود ✅",
        parse_mode="HTML")

# --------- گروه AI ---------
@bot.message_handler(func=lambda m: m.chat.type in ["group", "supergroup"])
def group_ai(m):
    uid = m.from_user.id
    if str(uid) in data["banned"]: return
    if str(uid) in data["muted"] and data["muted"][str(uid)] > now_ts(): return
    text = (m.text or "").strip()
    if not text: return

    want = False
    if text.startswith("ربات "): want = True
    if bot.get_me().username and ("@" + bot.get_me().username.lower()) in text.lower(): want = True
    if m.reply_to_message and m.reply_to_message.from_user and m.reply_to_message.from_user.id == bot.get_me().id:
        want = True
    if not want: return

    gid = str(m.chat.id)
    g = data["groups"].get(gid, {"expires":0,"active":False})
    if g.get("expires",0) < now_ts():
        if is_admin(uid):
            bot.reply_to(m, "⛔️ شارژ گروه تمام شده. «شارژ گروه [روز]» را بزن.")
        return
    if g.get("active") is False: return

    prompt = text.replace("ربات ","").strip()
    if not prompt: prompt = "به این پیام پاسخ بده: " + text

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role":"system","content":"You are a helpful AI that answers in Persian."},
                {"role":"user","content": prompt}
            ]
        )
        answer = resp.choices[0].message.content
        bot.reply_to(m, f"🤖 {answer}")
    except Exception as e:
        if is_admin(uid):
            bot.reply_to(m, f"❌ خطا: {e}")

# --------- POLLING ---------
if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling(skip_pending=True, timeout=20)
