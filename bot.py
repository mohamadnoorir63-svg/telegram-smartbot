# -*- coding: utf-8 -*-
import os, json, time, datetime
from telebot import TeleBot, types
from openai import OpenAI

# --------- تنظیمات اصلی ---------
BOT_TOKEN        = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
ADMIN_ID         = int(os.getenv("ADMIN_ID") or "0")
ADMIN_USERNAME   = os.getenv("ADMIN_USERNAME") or "@NOORI_NOOR"
BOT_NAME_FARSI   = "🤖 ربات هوشمند نوری"

if not BOT_TOKEN or not OPENAI_API_KEY or not ADMIN_ID:
    raise SystemExit("❌ مقادیر BOT_TOKEN / OPENAI_API_KEY / ADMIN_ID تنظیم نشده‌اند.")

bot    = TeleBot(BOT_TOKEN, parse_mode="HTML")
client = OpenAI(api_key=OPENAI_API_KEY)

DATA_FILE = "data.json"
DEFAULT_FREE_COINS = 5

# --------- توابع کمکی ---------
def now_ts():
    return int(time.time())

def load_data():
    if not os.path.exists(DATA_FILE):
        d = {"users": {}, "banned": [], "muted": {}, "groups": {},
             "support_open": {}, "admin_reply_to": None,
             "pending_broadcast": False, "group_status": {}}
        save_data(d)
        return d
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        d = json.load(f)
    d.setdefault("users", {})
    d.setdefault("banned", [])
    d.setdefault("muted", {})
    d.setdefault("groups", {})
    d.setdefault("support_open", {})
    d.setdefault("admin_reply_to", None)
    d.setdefault("pending_broadcast", False)
    d.setdefault("group_status", {})  # گروه‌ها: active / disabled
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

# --------- کیبوردها ---------
def kb_user(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(types.KeyboardButton("راهنما 💡"), types.KeyboardButton("شارژ مجدد 🟩"))
    kb.row(types.KeyboardButton("پشتیبانی ☎️"), types.KeyboardButton("سازنده 👤"))
    kb.row(types.KeyboardButton("افزودن به گروه ➕"))
    kb.row(types.KeyboardButton("روشن / خاموش 🧠"))
    return kb

def kb_admin():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(types.KeyboardButton("آمار کاربران 📊"), types.KeyboardButton("لیست گروه‌ها 📋"))
    kb.row(types.KeyboardButton("شارژ کاربر 💰"), types.KeyboardButton("بن کاربر 🚫"))
    kb.row(types.KeyboardButton("سکوت کاربر 🤐"), types.KeyboardButton("ارسال همگانی 📣"))
    kb.row(types.KeyboardButton("کنترل گروه ⚙️"), types.KeyboardButton("لفت بده ↩️"))
    kb.row(types.KeyboardButton("بازگشت BACK"))
    return kb

def ikb_support(uid):
    ik = types.InlineKeyboardMarkup()
    ik.add(
        types.InlineKeyboardButton("پاسخ ✉️", callback_data=f"reply:{uid}"),
        types.InlineKeyboardButton("بستن ❌", callback_data=f"close:{uid}")
    )
    return ik

# --------- /start ---------
@bot.message_handler(commands=["start"])
def start_cmd(m):
    uid = m.from_user.id
    ensure_user(uid, f"{m.from_user.first_name or ''} {m.from_user.last_name or ''}".strip())
    if is_admin(uid):
        bot.reply_to(m, "👑 سلام رئیس! وارد پنل مدیریتی شدی.", reply_markup=kb_admin())
    else:
        bot.reply_to(
            m,
            f"سلام 👋 به <b>{BOT_NAME_FARSI}</b> خوش اومدی!\n\n"
            "اینجا می‌تونی با هوش مصنوعی متن و عکس بفرستی تا برات تحلیل کنه.\n"
            f"هر کاربر {DEFAULT_FREE_COINS} پیام رایگان داره 🎁\n\n"
            "📸 عکس بفرست تا تحلیل شه.\n"
            "💬 پیام بفرست تا جواب بگیری.\n\n"
            "اینستاگرام ما 👇\n"
            "<a href='https://www.instagram.com/pesar_rostayi'>instagram.com/pesar_rostayi</a>",
            reply_markup=kb_user(uid)
        )

# --------- مدیریت گروه‌ها ---------
@bot.message_handler(func=lambda m: m.chat.type in ["group", "supergroup"], content_types=["new_chat_members"])
def joined_group(m):
    gid = str(m.chat.id)
    gname = m.chat.title or "بدون‌نام"
    data["groups"].setdefault(gid, {"name": gname, "expires": now_ts() + 86400})
    data["group_status"].setdefault(gid, "active")
    save_data(data)
    try:
        bot.send_message(ADMIN_ID, f"📢 ربات به گروه جدید اضافه شد:\n{gname}\nID: {gid}")
    except: pass

# دستور لفت از پنل سودو
@bot.message_handler(func=lambda m: m.chat.type == "private" and is_admin(m.from_user.id))
def admin_panel(m):
    txt = (m.text or "").strip()
    if txt == "لفت بده ↩️":
        bot.reply_to(m, "📝 ID گروه را وارد کن تا ربات از آن خارج شود.")
        data["awaiting_leave"] = True
        save_data(data)
        return

    if data.get("awaiting_leave"):
        gid = txt.strip()
        try:
            bot.leave_chat(int(gid))
            bot.reply_to(m, f"✅ از گروه {gid} خارج شدم.")
        except Exception as e:
            bot.reply_to(m, f"❌ خطا در خروج:\n{e}")
        data["awaiting_leave"] = False
        save_data(data)
        return

    if txt == "لیست گروه‌ها 📋":
        if not data["groups"]:
            bot.reply_to(m, "❌ هنوز در هیچ گروهی نیستم.")
        else:
            msg = "📋 لیست گروه‌ها:\n"
            for gid, info in data["groups"].items():
                name = info.get("name", "بدون‌نام")
                status = data["group_status"].get(gid, "active")
                msg += f"\n• {name} | ID: {gid} | وضعیت: {'✅ فعال' if status == 'active' else '🚫 غیرفعال'}"
            bot.reply_to(m, msg)
        return

    if txt == "کنترل گروه ⚙️":
        bot.reply_to(m, "🔧 ID گروه را وارد کن (برای فعال‌سازی، غیرفعال‌سازی یا لفت دادن).")
        data["awaiting_group_ctrl"] = True
        save_data(data)
        return

    if data.get("awaiting_group_ctrl"):
        gid = txt.strip()
        if gid not in data["groups"]:
            bot.reply_to(m, "❌ گروه پیدا نشد.")
            data["awaiting_group_ctrl"] = False
            save_data(data)
            return
        ik = types.InlineKeyboardMarkup()
        ik.row(
            types.InlineKeyboardButton("✅ فعال کن", callback_data=f"groupon:{gid}"),
            types.InlineKeyboardButton("🚫 غیرفعال کن", callback_data=f"groupoff:{gid}")
        )
        ik.add(types.InlineKeyboardButton("↩️ لفت بده", callback_data=f"groupleave:{gid}"))
        bot.send_message(m.chat.id, f"⚙️ کنترل گروه {gid}", reply_markup=ik)
        data["awaiting_group_ctrl"] = False
        save_data(data)# --------- CALLBACK کنترل گروه از سودو ---------
@bot.callback_query_handler(func=lambda c: c.data and any(c.data.startswith(p) for p in ["groupon:","groupoff:","groupleave:"]))
def cb_group_ctrl(c):
    if not is_admin(c.from_user.id):
        return bot.answer_callback_query(c.id, "فقط سودو می‌تواند.")
    action, gid = c.data.split(":",1)
    if action == "groupon":
        data["group_status"][gid] = "active"
        bot.answer_callback_query(c.id, "✅ گروه فعال شد.")
        bot.send_message(c.message.chat.id, f"گروه {gid} فعال شد ✅")
    elif action == "groupoff":
        data["group_status"][gid] = "disabled"
        bot.answer_callback_query(c.id, "🚫 گروه غیرفعال شد.")
        bot.send_message(c.message.chat.id, f"گروه {gid} غیرفعال شد 🚫")
    elif action == "groupleave":
        try:
            bot.leave_chat(int(gid))
            bot.answer_callback_query(c.id, "↩️ از گروه خارج شدم.")
            bot.send_message(c.message.chat.id, f"✅ از گروه {gid} خارج شدم.")
            data["groups"].pop(gid, None)
            data["group_status"].pop(gid, None)
        except Exception as e:
            bot.send_message(c.message.chat.id, f"❌ خطا در خروج:\n{e}")
    save_data(data)

# --------- پشتیبانی (کال‌بک) ---------
@bot.callback_query_handler(func=lambda c: c.data and (c.data.startswith("reply:") or c.data.startswith("close:")))
def cb_support(c):
    if not is_admin(c.from_user.id): return
    action, raw = c.data.split(":", 1)
    uid = int(raw)
    if action == "reply":
        data["admin_reply_to"] = uid
        save_data(data)
        bot.send_message(c.message.chat.id, f"✍️ حالت پاسخ به کاربر {uid} فعال شد. برای بستن بنویس: پایان {uid}")
    elif action == "close":
        data["support_open"][str(uid)] = False
        save_data(data)
        bot.send_message(c.message.chat.id, f"🔒 گفتگوی پشتیبانی کاربر {uid} بسته شد.")
        try: bot.send_message(uid, "🔒 گفتگوی پشتیبانی بسته شد.")
        except: pass

# --------- پاسخ ادمین در حالت پشتیبانی ---------
@bot.message_handler(func=lambda m: m.chat.type=="private" and is_admin(m.from_user.id) and data.get("admin_reply_to"))
def admin_reply(m):
    target = data.get("admin_reply_to")
    try:
        bot.copy_message(target, m.chat.id, m.message_id)
        bot.reply_to(m, f"✅ پیام برای {target} ارسال شد.")
    except Exception as e:
        bot.reply_to(m, f"❌ خطا در ارسال:\n{e}")

# بستن گفتگوی پشتیبانی از طرف سودو
@bot.message_handler(func=lambda m: m.chat.type=="private" and is_admin(m.from_user.id))
def admin_close(m):
    txt = m.text.strip()
    parts = txt.split()
    if len(parts)==2 and parts[0]=="پایان":
        uid = int(parts[1])
        data["support_open"][str(uid)] = False
        data["admin_reply_to"] = None
        save_data(data)
        bot.reply_to(m, f"🔒 گفتگوی کاربر {uid} بسته شد.")

# --------- پیام کاربران (خصوصی) ---------
@bot.message_handler(func=lambda m: m.chat.type=="private" and not is_admin(m.from_user.id))
def user_private(m):
    uid = m.from_user.id
    ensure_user(uid)
    txt = (m.text or "").strip()
    cu = data["users"][str(uid)]

    # بن یا سکوت
    if str(uid) in data["banned"]: return
    if str(uid) in data["muted"] and data["muted"][str(uid)] > now_ts(): return

    # دکمه‌ها
    if txt == "راهنما 💡":
        bot.reply_to(m, f"""📘 راهنما:
• با ارسال متن، جواب هوش مصنوعی رو می‌گیری.
• با ارسال عکس، تحلیل تصویری می‌گیری.
• هر پیام ۱ سکه مصرف می‌کند.
• موجودی فعلی: {cu['coins']}
• حالت گفتگو با دکمه «روشن / خاموش 🧠» قابل تغییر است.""")
        return

    if txt == "سازنده 👤":
        bot.reply_to(m, f"🧑‍💻 سازنده: {ADMIN_USERNAME}")
        return

    if txt == "افزودن به گروه ➕":
        bot.reply_to(m, "📎 من رو به گروه اضافه کن و دسترسی پیام بده.\nسپس مدیر بنویسه: «شارژ گروه 1»")
        return

    if txt == "شارژ مجدد 🟩":
        bot.reply_to(m, "برای شارژ سکه با پشتیبانی تماس بگیر. «پشتیبانی ☎️»")
        return

    if txt == "پشتیبانی ☎️":
        data["support_open"][str(uid)] = True
        save_data(data)
        bot.reply_to(m, "📩 گفتگو با پشتیبانی باز شد. برای بستن بنویس: «پایان پشتیبانی»")
        try: bot.send_message(ADMIN_ID, f"📨 پیام جدید از کاربر {uid}")
        except: pass
        return

    if txt == "پایان پشتیبانی":
        data["support_open"][str(uid)] = False
        save_data(data)
        bot.reply_to(m, "✅ گفتگوی پشتیبانی بسته شد.")
        return

    if txt == "روشن / خاموش 🧠":
        cu["active"] = not cu["active"]
        save_data(data)
        msg = "✅ حالت گفتگو فعال شد." if cu["active"] else "⛔️ حالت گفتگو غیرفعال شد."
        bot.reply_to(m, msg, reply_markup=kb_user(uid))
        return

    # پشتیبانی باز → پیام مستقیم به ادمین
    if data["support_open"].get(str(uid)):
        bot.copy_message(ADMIN_ID, m.chat.id, m.message_id, reply_markup=ikb_support(uid))
        bot.reply_to(m, "📨 پیام به پشتیبانی ارسال شد.")
        return

    # بررسی سکه
    if cu["coins"] <= 0:
        bot.reply_to(m, "💰 سکه‌های شما تمام شده. برای شارژ از پشتیبانی کمک بگیرید.")
        return

    # بررسی فعال بودن
    if not cu["active"]:
        bot.reply_to(m, "⏸ حالت گفتگو غیرفعال است.")
        return

    # ادامه تحلیل
    if txt.startswith("ادامه تحلیل"):
        user_last = cu.get("last_ai", "")
        if not user_last:
            bot.reply_to(m, "❌ تحلیلی برای ادامه وجود ندارد.")
            return
        ask = txt.replace("ادامه تحلیل", "").strip() or "ادامه توضیح تحلیل قبلی"
        prompt = f"{user_last}\n\nادامه بده و {ask}"
    else:
        prompt = txt

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role":"system","content":"You are a helpful AI that answers in Persian."},
                {"role":"user","content": prompt}
            ]
        )
        ans = resp.choices[0].message.content
        bot.reply_to(m, f"🤖 {ans}")
        cu["coins"] -= 1
        cu["last_ai"] = prompt
        save_data(data)
    except Exception as e:
        bot.reply_to(m, f"❌ خطا در پاسخ هوش:\n{e}")

# --------- عکس‌ها ---------
@bot.message_handler(content_types=["photo"])
def photo_ai(m):
    uid = m.from_user.id
    ensure_user(uid)
    cu = data["users"][str(uid)]
    if cu["coins"] <= 0:
        bot.reply_to(m, "💰 سکه‌های شما تمام شده.")
        return
    try:
        file = bot.get_file(m.photo[-1].file_id)
        url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": [
                    {"type":"text","text":"این تصویر را تحلیل و توضیح بده."},
                    {"type":"image_url","image_url":{"url":url}}
                ]
            }]
        )
        ans = resp.choices[0].message.content
        bot.reply_to(m, f"🖼️ تحلیل تصویر:\n{ans}")
        cu["coins"] -= 1
        cu["last_ai"] = ans
        save_data(data)
    except Exception as e:
        bot.reply_to(m, f"❌ خطا در تحلیل تصویر:\n{e}")

# --------- پاسخ در گروه‌ها ---------
@bot.message_handler(func=lambda m: m.chat.type in ["group","supergroup"])
def group_ai(m):
    gid = str(m.chat.id)
    txt = (m.text or "").strip()
    if not txt: return

    # بررسی غیرفعال بودن گروه از پنل سودو
    if data["group_status"].get(gid) == "disabled":
        return

    if txt.startswith("ربات خاموش"):
        data["group_status"][gid] = "disabled"
        save_data(data)
        bot.reply_to(m, "⛔️ ربات در این گروه غیرفعال شد.")
        return

    if txt.startswith("ربات روشن"):
        if data["group_status"].get(gid) == "disabled":
            bot.reply_to(m, "⚠️ این گروه توسط سودو قفل شده و فقط سودو می‌تواند فعالش کند.")
            return
        data["group_status"][gid] = "active"
        save_data(data)
        bot.reply_to(m, "✅ ربات در این گروه فعال شد.")
        return

    # فقط وقتی از ربات خواسته شود
    want = False
    if txt.startswith("ربات "): want = True
    if bot.get_me().username and ("@" + bot.get_me().username.lower()) in txt.lower(): want = True
    if not want: return

    prompt = txt.replace("ربات ", "")
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role":"system","content":"You are a helpful AI that answers in Persian."},
                {"role":"user","content": prompt}
            ]
        )
        ans = resp.choices[0].message.content
        bot.reply_to(m, f"🤖 {ans}")
    except Exception as e:
        bot.reply_to(m, f"❌ خطا در پاسخ:\n{e}")

# --------- شروع ربات ---------
if __name__ == "__main__":
    print("🤖 Bot is running...")
    bot.infinity_polling(skip_pending=True, timeout=20)
