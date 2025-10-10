# -*- coding: utf-8 -*-
import os, json, time, datetime
from telebot import TeleBot, types
from openai import OpenAI

# ───── تنظیمات محیطی ─────
BOT_TOKEN        = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
ADMIN_ID         = 7089376754
ADMIN_USERNAME   = "NOORI_NOOR"
BOT_NAME_FARSI   = "Openai"

if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN تعریف نشده است.")
if not ADMIN_ID:
    raise SystemExit("ADMIN_ID (عددی) تعریف نشده است.")
if not OPENAI_API_KEY:
    raise SystemExit("OPENAI_API_KEY تعریف نشده است.")

# ───── شروع تنظیمات ─────
bot    = TeleBot(BOT_TOKEN, parse_mode="HTML")
client = OpenAI(api_key=OPENAI_API_KEY)

DATA_FILE = "data.json"
DEFAULT_FREE_COINS = 5

def now_ts():
    return int(time.time())

def load_data():
    if not os.path.exists(DATA_FILE):
        data = {
            "users": {}, "banned": [], "muted": {},
            "groups": {}, "support_open": {},
            "admin_reply_to": None, "pending_broadcast": False,
            "group_disabled": []  # گروه‌هایی که ربات در آن‌ها خاموش است
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
    d.setdefault("group_disabled", [])
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

# ───── کیبوردها ─────
def kb_user(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("راهنما 💡", "شارژ مجدد 🟩")
    kb.row("پشتیبانی ☎️", "سازنده 👤")
    kb.row("افزودن به گروه ➕", "روشن / خاموش 🧠")
    return kb

def kb_admin():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("آمار کاربران 📊", "شارژ کاربر 💰")
    kb.row("سکوت کاربر 🤐", "بن کاربر 🚫")
    kb.row("لیست بن‌ها 🚫", "لیست سکوت‌ها 🤫")
    kb.row("ارسال همگانی 📣", "لفت بده ↩️")
    kb.row("خاموش/روشن گروه ⚙️", "بازگشت BACK")
    return kb

def ikb_support(uid):
    ik = types.InlineKeyboardMarkup()
    ik.add(
        types.InlineKeyboardButton("پاسخ ✉️", callback_data=f"reply:{uid}"),
        types.InlineKeyboardButton("بستن ❌", callback_data=f"close:{uid}")
    )
    return ik

# ───── شروع ربات ─────
@bot.message_handler(commands=["start"])
def start_cmd(m):
    uid = m.from_user.id
    ensure_user(uid, f"{m.from_user.first_name or ''} {m.from_user.last_name or ''}".strip())
    if is_admin(uid):
        bot.reply_to(m, "👑 سلام رئیس! وارد پنل مدیریتی شدی.", reply_markup=kb_admin())
    else:
        bot.reply_to(m,
            f"👋 سلام به <b>{BOT_NAME_FARSI}</b> خوش اومدی!\n"
            "من یه هوش مصنوعی هستم که هم با متن و هم عکس کار می‌کنم 🤖\n"
            f"هر کاربر {DEFAULT_FREE_COINS} پیام رایگان داره. بعدش با «شارژ مجدد 🟩» ادامه بده.\n"
            "🌐 برای دریافت ۵ سکه رایگان دیگه صفحه‌ی اینستاگرام منو دنبال کن:\n"
            "<a href='https://www.instagram.com/pesar_rostayi'>instagram.com/pesar_rostayi</a>",
            reply_markup=kb_user(uid)
        )

# ───── پنل مدیر ─────
@bot.message_handler(func=lambda m: m.chat.type=="private" and is_admin(m.from_user.id))
def admin_panel(m):
    txt = (m.text or "").strip()

    if txt == "بازگشت BACK":
        return bot.reply_to(m, "پنل مدیریتی باز شد ✅", reply_markup=kb_admin())

    if txt == "آمار کاربران 📊":
        bot.reply_to(m, f"📊 کاربران: {len(data['users'])}\n🚫 بن‌شده: {len(data['banned'])}\n🤐 در سکوت: {len(data['muted'])}")
        return

    if txt == "خاموش/روشن گروه ⚙️":
        bot.reply_to(m, "دستور: «خاموش گروه [id]» یا «روشن گروه [id]» را بفرست.")
        return

    if txt == "ارسال همگانی 📣":
        data["pending_broadcast"] = True
        save_data(data)
        return bot.reply_to(m, "پیام خود را بنویس تا برای همه ارسال شود.")

    if data.get("pending_broadcast"):
        data["pending_broadcast"] = False
        save_data(data)
        ok = 0
        for suid in data["users"]:
            try: bot.copy_message(int(suid), m.chat.id, m.message_id); ok+=1
            except: pass
        bot.reply_to(m, f"📣 پیام برای {ok} کاربر ارسال شد.")
        return

    parts = txt.split()
    try:
        if parts[0] == "شارژ" and len(parts)==3:
            uid = int(parts[1]); coins = int(parts[2])
            ensure_user(uid)
            data["users"][str(uid)]["coins"] += coins
            save_data(data)
            bot.reply_to(m, f"✅ {coins} سکه به کاربر {uid} اضافه شد.")
            return
        if parts[0] == "بن" and len(parts)==2:
            uid = str(parts[1])
            if uid not in data["banned"]:
                data["banned"].append(uid)
                save_data(data)
            bot.reply_to(m, f"🚫 کاربر {uid} بن شد.")
            return
        if parts[0] == "حذف" and len(parts)==3 and parts[1]=="بن":
            uid = str(parts[2])
            if uid in data["banned"]:
                data["banned"].remove(uid)
                save_data(data)
            bot.reply_to(m, f"✅ بن {uid} برداشته شد.")
            return
        if parts[0] == "خاموش" and parts[1]=="گروه":
            gid = parts[2]
            if gid not in data["group_disabled"]:
                data["group_disabled"].append(gid)
                save_data(data)
            bot.reply_to(m, f"⛔ گروه {gid} خاموش شد.")
            return
        if parts[0] == "روشن" and parts[1]=="گروه":
            gid = parts[2]
            if gid in data["group_disabled"]:
                data["group_disabled"].remove(gid)
                save_data(data)
            bot.reply_to(m, f"✅ گروه {gid} روشن شد.")
            return
    except Exception as e:
        bot.reply_to(m, f"⚠️ خطا: {e}")

# ───── کاربران ─────
@bot.message_handler(func=lambda m: m.chat.type=="private" and not is_admin(m.from_user.id))
def user_panel(m):
    uid = m.from_user.id
    ensure_user(uid)
    cu = data["users"][str(uid)]
    txt = (m.text or "").strip()

    if str(uid) in data["banned"]: return
    if str(uid) in data["muted"] and data["muted"][str(uid)] > now_ts(): return

    if txt == "راهنما 💡":
        bot.reply_to(m, "📘 راهنما:\n• ارسال متن = پاسخ متنی\n• ارسال عکس = تحلیل تصویر\n• هر پیام ۱ سکه مصرف می‌کند.")
        return
    if txt == "سازنده 👤":
        bot.reply_to(m, f"🧑‍💻 @{ADMIN_USERNAME}")
        return
    if txt == "پشتیبانی ☎️":
        data["support_open"][str(uid)] = True
        save_data(data)
        bot.reply_to(m, "✉️ پشتیبانی فعال شد. برای خروج: «پایان پشتیبانی»")
        bot.send_message(ADMIN_ID, f"📥 پیام جدید از {uid}")
        return
    if txt == "پایان پشتیبانی":
        data["support_open"][str(uid)] = False
        save_data(data)
        bot.reply_to(m, "✅ گفتگو بسته شد.")
        return
    if txt == "روشن / خاموش 🧠":
        cu["active"] = not cu["active"]
        save_data(data)
        return bot.reply_to(m, "✅ فعال شد." if cu["active"] else "⛔ غیرفعال شد.")
    if txt == "افزودن به گروه ➕":
        return bot.reply_to(m, "من را به گروه اضافه کنید و مدیر داخل گروه بنویسد:\n«شارژ گروه [روز]»")

    # اگر در پشتیبانی است
    if data["support_open"].get(str(uid)):
        bot.copy_message(ADMIN_ID, uid, m.message_id, reply_markup=ikb_support(uid))
        return

    if not cu["active"]:
        return bot.reply_to(m, "⏸ گفتگو غیرفعال است.")
    if cu["coins"] <= 0:
        return bot.reply_to(m, "💸 سکه تمام شده. از پشتیبانی شارژ بگیر.")

    # متن → GPT پاسخ
    if m.content_type == "text":
        ask = m.text.strip()
        try:
            resp = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role":"system","content":"You are a helpful AI that responds in Persian."},
                    {"role":"user","content": ask}
                ]
            )
            ans = resp.choices[0].message.content
            bot.reply_to(m, f"🤖 {ans}")
            cu["coins"] -= 1
            save_data(data)
        except Exception as e:
            bot.reply_to(m, f"⚠️ خطا در پاسخ: {e}")

# ───── عکس → GPT Vision ─────
@bot.message_handler(content_types=["photo"])
def photo_ai(m):
    uid = m.from_user.id
    ensure_user(uid)
    cu = data["users"][str(uid)]
    if cu["coins"] <= 0: return bot.reply_to(m, "💸 سکه تمام شده.")

    file_info = bot.get_file(m.photo[-1].file_id)
    file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": [
                    {"type":"text","text":"این تصویر را تحلیل کن و نتیجه را به فارسی توضیح بده."},
                    {"type":"image_url","image_url":{"url": file_url}}
                ]
            }]
        )
        ans = resp.choices[0].message.content
        bot.reply_to(m, f"🖼️ {ans}")
        cu["coins"] -= 1
        save_data(data)
    except Exception as e:
        bot.reply_to(m, f"⚠️ خطا در پردازش تصویر:\n{e}")

# ───── گفتگو در گروه ─────
@bot.message_handler(func=lambda m: m.chat.type in ["group","supergroup"])
def group_ai(m):
    gid = str(m.chat.id)
    uid = m.from_user.id
    txt = (m.text or "").strip()
    if gid in data["group_disabled"]: return
    if not txt: return

    want = False
    if txt.startswith("ربات "): want = True
    if bot.get_me().username.lower() in txt.lower(): want = True
    if m.reply_to_message and m.reply_to_message.from_user.id == bot.get_me().id: want = True
    if not want: return

    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role":"system","content":"You are a Persian assistant."},
                {"role":"user","content": txt}
            ]
        )
        ans = resp.choices[0].message.content
        bot.reply_to(m, ans)
    except Exception as e:
        bot.reply_to(m, f"⚠️ خطا: {e}")

# ───── پشتیبانی ─────
@bot.callback_query_handler(func=lambda c: c.data.startswith("reply:") or c.data.startswith("close:"))
def support_cb(c):
    if not is_admin(c.from_user.id): return
    action, uid = c.data.split(":")
    uid = int(uid)
    if action=="reply":
        data["admin_reply_to"]=uid; save_data(data)
        bot.send_message(ADMIN_ID, f"✍️ در حالت پاسخ به {uid}")
    else:
        data["support_open"][str(uid)] = False
        data["admin_reply_to"]=None
        save_data(data)
        bot.send_message(uid,"🔒 گفتگو بسته شد.")
        bot.send_message(ADMIN_ID,"✅ بسته شد.")

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and data.get("admin_reply_to"))
def admin_reply(m):
    target = data["admin_reply_to"]
    try:
        bot.copy_message(target, m.chat.id, m.message_id)
        bot.reply_to(m, f"📤 ارسال شد به {target}")
    except Exception as e:
        bot.reply_to(m, f"⚠️ خطا: {e}")

# ───── اجرای نهایی ─────
if __name__ == "__main__":
    print("🤖 Bot is running...")
    bot.infinity_polling(skip_pending=True, timeout=20)
