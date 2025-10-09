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
            "users": {},          # uid -> {coins, active, name}
            "banned": [],         # [uid]
            "muted": {},          # uid -> expire_ts
            "groups": {},         # gid -> {expires, active}
            "support_open": {},   # uid -> True/False
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

# --------- ADMIN PANEL BUTTONS ---------
@bot.message_handler(func=lambda m: m.chat.type == "private" and is_admin(m.from_user.id))
def admin_private(m):
    txt = (m.text or "").strip()
    
    # ارسال همگانی
    if txt == "ارسال همگانی 📣":
        data["pending_broadcast"] = True
        save_data(data)
        bot.reply_to(m, "✍️ پیام خود را همینجا بفرست تا برای همه ارسال شود.\n(برای انصراف: «بازگشت BACK»)")
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
        total_mute = len([1 for k, v in data["muted"].items() if v > now_ts()])
        bot.reply_to(m, f"📈 کاربران: {total}\n🚫 بن‌شده: {total_ban}\n🤐 در سکوت: {total_mute}")
        return# دستورات نوشتاری سودو
    parts = txt.replace("‌", " ").split()
    if not parts: 
        return
    try:
        if parts[0] == "شارژ" and len(parts) == 3:
            uid = int(parts[1]); count = int(parts[2])
            ensure_user(uid)
            data["users"][str(uid)]["coins"] += count
            save_data(data)
            bot.reply_to(m, f"✅ به کاربر {uid} تعداد {count} سکه اضافه شد.")
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

# --------- GROUP ADMIN COMMANDS ---------
@bot.message_handler(func=lambda m: m.chat.type in ["group","supergroup"] and is_admin(m.from_user.id))
def admin_in_group(m):
    txt = (m.text or "").strip()
    parts = txt.split()
    if txt == "لفت بده":
        try:
            bot.reply_to(m, "👋 خداحافظ! از گروه خارج شدم.")
            bot.leave_chat(m.chat.id)
        except Exception as e:
            bot.reply_to(m, f"❌ خطا در خروج از گروه.\n{e}")
        return
    if len(parts) == 3 and parts[0] == "شارژ" and parts[1] == "گروه":
        days = int(parts[2])
        gid = str(m.chat.id)
        until = now_ts() + days * 86400
        data["groups"].setdefault(gid, {"expires": 0, "active": True})
        data["groups"][gid]["expires"] = until
        save_data(data)
        bot.reply_to(m, f"✅ گروه به مدت {days} روز شارژ شد.")
        return

# --------- USER PANEL (PRIVATE) ---------
@bot.message_handler(func=lambda m: m.chat.type == "private" and not is_admin(m.from_user.id))
def user_private(m):
    uid = m.from_user.id
    ensure_user(uid, f"{m.from_user.first_name or ''} {m.from_user.last_name or ''}".strip())
    txt = (m.text or "").strip()

    # بن / سکوت
    if str(uid) in data["banned"]: return
    if str(uid) in data["muted"] and data["muted"][str(uid)] > now_ts(): return

    # دکمه‌ها
    if txt == "راهنما 💡":
        bot.reply_to(m,
            "📘 راهنما:\n"
            "• با ارسال متن، پاسخ هوش مصنوعی را می‌گیری.\n"
            "• با ارسال عکس، تحلیل تصویری می‌گیری.\n"
            f"• هر پیام ۱ سکه مصرف می‌کند. موجودی فعلی: <b>{data['users'][str(uid)]['coins']}</b>\n"
            "• برای خاموش/روشن کردن، از دکمه «روشن / خاموش 🧠» استفاده کن.")
        return

    if txt == "سازنده 👤":
        bot.reply_to(m, f"سازنده: {ADMIN_USERNAME}")
        return

    if txt == "افزودن به گروه ➕":
        bot.reply_to(m, "من را به گروه اضافه کنید و مدیر بگویید «شارژ گروه [روز]» تا فعال شوم.")
        return

    if txt == "شارژ مجدد 🟩":
        bot.reply_to(m, "برای شارژ سکه با پشتیبانی تماس بگیر: «پشتیبانی ☎️»")
        return

    if txt == "پشتیبانی ☎️":
        data["support_open"][str(uid)] = True
        save_data(data)
        bot.reply_to(m, "✉️ گفتگوی پشتیبانی باز شد. پیام بده تا به سازنده برسد. برای خروج: «پایان پشتیبانی»")
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
        cu = data["users"][str(uid)]
        cu["active"] = not cu["active"]
        save_data(data)
        msg = "✅ حالت گفتگو با هوش فعال شد." if cu["active"] else "⛔️ حالت گفتگو غیرفعال شد."
        bot.reply_to(m, msg, reply_markup=kb_user(uid))
        return

    # پشتیبانی فعال؟
    if data["support_open"].get(str(uid)):
        try:
            bot.copy_message(ADMIN_ID, m.chat.id, m.message_id, reply_markup=ikb_support(uid))
            bot.reply_to(m, "📨 پیام به پشتیبانی ارسال شد.")
        except Exception as e:
            bot.reply_to(m, f"❌ خطا در ارسال به پشتیبانی:\n{e}")
        return

    # فعال بودن هوش و سکه
    cu = data["users"][str(uid)]
    if not cu.get("active", True):
        return bot.reply_to(m, "⏸ حالت گفتگو غیرفعال است.")
    if cu.get("coins", 0) <= 0:
        return bot.reply_to(m, "💸 سکه شما تمام شده است. با «پشتیبانی ☎️» شارژ کن.")

    # 🧠 متنی → GPT-4o
    if m.content_type == "text" and (m.text or "").strip():
        ask_text = (m.text or "").strip()
        try:
            resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful Persian-speaking AI assistant."},
                    {"role": "user", "content": ask_text}
                ]
            )
            answer = resp.choices[0].message.content
            bot.reply_to(m, f"🤖 {answer}")
            cu["coins"] -= 1
            save_data(data)
        except Exception as e:
            bot.reply_to(m, f"❌ خطا در پاسخ هوش مصنوعی:\n{e}")
        return


# --------- PHOTO → GPT-4o Vision ---------
@bot.message_handler(content_types=["photo"])
def handle_photo(m):
    uid = m.from_user.id
    ensure_user(uid)
    if str(uid) in data["banned"]: return
    if str(uid) in data["muted"] and data["muted"][str(uid)] > now_ts(): return

    # پشتیبانی باز؟
    if m.chat.type == "private" and data["support_open"].get(str(uid)):
        try:
            bot.copy_message(ADMIN_ID, m.chat.id, m.message_id, reply_markup=ikb_support(uid))
            bot.reply_to(m, "📨 عکس به پشتیبانی ارسال شد.")
        except Exception as e:
            bot.reply_to(m, f"❌ خطا در ارسال:\n{e}")
        return

    cu = data["users"][str(uid)]
    if not cu.get("active", True):
        return bot.reply_to(m, "⏸ حالت گفتگو غیرفعال است.")
    if cu.get("coins", 0) <= 0:
        return bot.reply_to(m, "💸 سکه شما تمام شده است.")

    try:
        file_info = bot.get_file(m.photo[-1].file_id)
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "این تصویر را به‌طور کامل توصیف و تحلیل کن."},
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


# --------- GROUP AI (mention / 'ربات ') ---------
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
            bot.reply_to(m, "⛔️ شارژ گروه تمام شده. مدیر باید «شارژ گروه [روز]» بزند.")
        return
    if g.get("active") is False: return

    prompt = text.replace("ربات ", "").strip() or text
    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful AI that replies in Persian."},
                {"role": "user", "content": prompt}
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
