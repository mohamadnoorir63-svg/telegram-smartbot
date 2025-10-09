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
            "users": {},              # uid -> {coins, active, name, last_photo_desc}
            "banned": [],             # [uid]
            "muted": {},              # uid -> expire_ts
            "groups": {},             # gid -> {expires, active}
            "support_open": {},       # uid -> True/False
            "admin_reply_to": None,   # uid (در حالت پاسخ پشتیبانی)
            "pending_broadcast": False
        }
        save_data(data)
        return data
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        d = json.load(f)
    # در صورت نبود کلیدها
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
        data["users"][suid] = {
            "coins": DEFAULT_FREE_COINS,
            "active": True,
            "name": name or "",
            "last_photo_desc": ""
        }
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
        bot.reply_to(m, f"👑 سلام رئیس! وارد پنل مدیریتی شدی.", reply_markup=kb_admin())
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
    if txt == "ارسال همگانی 📣":
        data["pending_broadcast"] = True
        save_data(data)
        bot.reply_to(m, "✍️ پیام خود را بفرست تا برای همه کاربران و گروه‌ها ارسال شود.\n(لغو با: «بازگشت BACK»)")
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

    if txt == "بازگشت BACK":
        bot.reply_to(m,
            "دستورات سودو (فقط خصوصی):\n"
            "• شارژ [uid] [تعداد]\n"
            "• بن [uid] | حذف بن [uid]\n"
            "• سکوت [uid] [ساعت] | حذف سکوت [uid]\n"
            "• در گروه: شارژ گروه [روز] | لفت بده\n"
            "• لیست بن‌ها | لیست سکوت‌ها",
            reply_markup=kb_admin())
        return

    parts = txt.replace("‌"," ").split()
    if not parts: return

    try:
        if parts[0] == "شارژ" and len(parts) == 3:
            uid = int(parts[1]); count = int(parts[2])
            ensure_user(uid)
            data["users"][str(uid)]["coins"] += count
            save_data(data)
            bot.reply_to(m, f"✅ {count} سکه به کاربر {uid} اضافه شد.")
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

# --------- USER PANEL ---------
@bot.message_handler(func=lambda m: m.chat.type=="private" and not is_admin(m.from_user.id))
def user_private(m):
    uid = m.from_user.id
    ensure_user(uid)
    cu = data["users"][str(uid)]
    txt = (m.text or "").strip()

    if str(uid) in data["banned"]: return
    if str(uid) in data["muted"] and data["muted"][str(uid)] > now_ts(): return

    # ادامه در بخش بعد 👇# ===== دکمه‌ها =====
    if txt == "راهنما 💡":
        bot.reply_to(m,
            "📘 راهنما:\n"
            "• با ارسال متن، جواب هوش مصنوعی رو می‌گیری.\n"
            "• با ارسال عکس، تحلیل تصویری دریافت می‌کنی.\n"
            f"• هر پیام ۱ سکه مصرف می‌کند (موجودی: <b>{cu['coins']}</b>).\n"
            "• برای ادامه یک تحلیل قبلی، بنویس: «ادامه تحلیل».\n"
            "• پشتیبانی برای ارتباط مستقیم با مدیر است.")
        return

    if txt == "سازنده 👤":
        bot.reply_to(m, f"سازنده: {ADMIN_USERNAME}")
        return

    if txt == "افزودن به گروه ➕":
        bot.reply_to(m, "برای افزودن من به گروه، فقط منو به گروه اضافه کن و دسترسی ارسال پیام بده.\nسپس مدیر می‌تونه بنویسه:\n<b>شارژ گروه [روز]</b>")
        return

    if txt == "شارژ مجدد 🟩":
        bot.reply_to(m, "برای شارژ سکه با «پشتیبانی ☎️» تماس بگیر.")
        return

    if txt == "پشتیبانی ☎️":
        data["support_open"][str(uid)] = True
        save_data(data)
        bot.reply_to(m, "✉️ گفتگوی پشتیبانی باز شد. هر پیامی بفرستی برای سازنده ارسال می‌شود.\nبرای خروج: «پایان پشتیبانی»")
        try:
            bot.send_message(ADMIN_ID, f"📥 پیام جدید از کاربر {uid}")
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
        bot.reply_to(m,
            "✅ حالت گفتگو فعال شد." if cu["active"] else "⛔️ گفتگو با هوش غیرفعال شد.",
            reply_markup=kb_user(uid))
        return

    # اگر در حالت پشتیبانی است → ارسال به ادمین
    if data["support_open"].get(str(uid)):
        try:
            bot.copy_message(ADMIN_ID, m.chat.id, m.message_id, reply_markup=ikb_support(uid))
            bot.reply_to(m, "📨 پیام به پشتیبانی ارسال شد.")
        except Exception as e:
            bot.reply_to(m, f"❌ خطا در ارسال به پشتیبانی: {e}")
        return

    # حالت غیرفعال یا بدون سکه
    if not cu.get("active", True):
        bot.reply_to(m, "⏸ حالت گفتگو غیرفعال است.")
        return
    if cu.get("coins", 0) <= 0:
        bot.reply_to(m, "💸 سکه شما تمام شده است.")
        return

    # ---- حالت "ادامه تحلیل" ----
    if txt.startswith("ادامه تحلیل"):
        last_desc = cu.get("last_photo_desc")
        if not last_desc:
            bot.reply_to(m, "❗ تحلیلی برای ادامه وجود ندارد. ابتدا عکسی ارسال کن یا موضوعی بنویس.")
            return
        prompt = txt.replace("ادامه تحلیل", "").strip() or "ادامه بده"
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful AI that continues previous Persian analysis."},
                    {"role": "user", "content": f"{last_desc}\n\nادامه و گسترش بر اساس: {prompt}"}
                ]
            )
            answer = resp.choices[0].message.content
            bot.reply_to(m, f"🔁 ادامه تحلیل:\n{answer}")
            cu["coins"] -= 1
            save_data(data)
        except Exception as e:
            bot.reply_to(m, f"❌ خطا در ادامه تحلیل: {e}")
        return

    # ---- حالت عادی: متن به هوش مصنوعی ----
    if m.content_type == "text" and (m.text or "").strip():
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
            bot.reply_to(m, f"❌ خطایی در پاسخ هوش مصنوعی رخ داد.\n{e}")
        return

# --------- PHOTO → VISION ---------
@bot.message_handler(content_types=["photo"])
def handle_photo(m):
    uid = m.from_user.id
    ensure_user(uid)
    cu = data["users"][str(uid)]

    if str(uid) in data["banned"]: return
    if str(uid) in data["muted"] and data["muted"][str(uid)] > now_ts(): return

    if m.chat.type == "private" and data["support_open"].get(str(uid)):
        try:
            bot.copy_message(ADMIN_ID, m.chat.id, m.message_id, reply_markup=ikb_support(uid))
            bot.reply_to(m, "📨 عکس به پشتیبانی ارسال شد.")
        except Exception as e:
            bot.reply_to(m, f"❌ خطا در ارسال عکس به پشتیبانی:\n{e}")
        return

    if m.chat.type == "private":
        if not cu.get("active", True):
            return bot.reply_to(m, "⏸ حالت گفتگو غیرفعال است.")
        if cu.get("coins", 0) <= 0:
            return bot.reply_to(m, "💸 سکه شما تمام شده است.")

        try:
            file_info = bot.get_file(m.photo[-1].file_id)
            file_url  = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type":"text","text":"این تصویر را توصیف و تحلیل کن."},
                        {"type":"image_url","image_url":{"url": file_url}}
                    ]
                }]
            )
            answer = resp.choices[0].message.content
            cu["last_photo_desc"] = answer  # ذخیره تحلیل برای ادامه
            save_data(data)
            bot.reply_to(m, f"🖼️ تحلیل تصویر:\n{answer}")
            cu["coins"] -= 1
            save_data(data)
        except Exception as e:
            bot.reply_to(m, f"❌ خطا در تحلیل تصویر:\n{e}")

# --------- پشتیبانی (ادمین ↔ کاربر) ---------
@bot.callback_query_handler(func=lambda c: c.data and (c.data.startswith("reply:") or c.data.startswith("close:")))
def cb_support(c):
    if not is_admin(c.from_user.id):
        return bot.answer_callback_query(c.id, "فقط مدیر.")
    try:
        action, raw = c.data.split(":", 1)
        uid = int(raw)
        if action == "reply":
            data["admin_reply_to"] = uid
            save_data(data)
            bot.answer_callback_query(c.id, "✅ حالت پاسخ فعال شد.")
            bot.send_message(c.message.chat.id, f"اکنون هر پیامی بفرستید برای کاربر {uid} ارسال می‌شود.\nبرای بستن: «پایان {uid}»")
        elif action == "close":
            data["support_open"][str(uid)] = False
            if data.get("admin_reply_to") == uid:
                data["admin_reply_to"] = None
            save_data(data)
            bot.answer_callback_query(c.id, "🔒 گفتگو بسته شد.")
            try: bot.send_message(uid, "🔒 گفتگوی پشتیبانی بسته شد.")
            except: pass
    except Exception as e:
        bot.answer_callback_query(c.id, f"خطا: {e}")

@bot.message_handler(func=lambda m: m.chat.type=="private" and is_admin(m.from_user.id) and data.get("admin_reply_to"))
def admin_replying(m):
    target = data.get("admin_reply_to")
    try:
        bot.copy_message(target, m.chat.id, m.message_id)
        bot.reply_to(m, f"✅ ارسال شد برای {target}")
    except Exception as e:
        bot.reply_to(m, f"❌ خطا در ارسال: {e}")

@bot.message_handler(func=lambda m: m.chat.type=="private" and is_admin(m.from_user.id))
def admin_close_cmd(m):
    txt = (m.text or "").strip()
    parts = txt.split()
    if len(parts)==2 and parts[0]=="پایان":
        uid = int(parts[1])
        data["support_open"][str(uid)] = False
        if data.get("admin_reply_to") == uid:
            data["admin_reply_to"] = None
        save_data(data)
        bot.reply_to(m, f"🔒 گفتگوی کاربر {uid} بسته شد.")

# --------- پاسخ به گروه ---------
@bot.message_handler(func=lambda m: m.chat.type in ["group","supergroup"])
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
            bot.reply_to(m, "⛔️ شارژ گروه تمام شده. بنویس: «شارژ گروه [روز]».")
        return
    if g.get("active") is False: return

    prompt = text.replace("ربات ","").strip() or text
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
        if is_admin(uid): bot.reply_to(m, f"❌ خطا: {e}")

# --------- RUN ---------
if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling(skip_pending=True, timeout=20)
