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

if not BOT_TOKEN: raise SystemExit("BOT_TOKEN تعریف نشده است.")
if not OPENAI_API_KEY: raise SystemExit("OPENAI_API_KEY تعریف نشده است.")
if not ADMIN_ID: raise SystemExit("ADMIN_ID (عددی) تعریف نشده است.")

# --------- INIT ---------
bot = TeleBot(BOT_TOKEN, parse_mode="HTML")
client = OpenAI(api_key=OPENAI_API_KEY)
DATA_FILE = "data.json"
DEFAULT_FREE_COINS = 5

def now_ts(): return int(time.time())

def load_data():
    if not os.path.exists(DATA_FILE):
        d = {
            "users": {}, "banned": [], "muted": {},
            "groups": {}, "support_open": {},
            "admin_reply_to": None, "pending_broadcast": False,
            "instagram_pending": {}
        }
        save_data(d); return d
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        d = json.load(f)
    for k in ["users","banned","muted","groups","support_open","pending_broadcast","instagram_pending","admin_reply_to"]:
        d.setdefault(k, {} if k not in ["banned"] else [])
    return d

def save_data(d):
    with open(DATA_FILE,"w",encoding="utf-8") as f:
        json.dump(d,f,ensure_ascii=False,indent=2)

data = load_data()
def is_admin(uid): return int(uid)==int(ADMIN_ID)

def ensure_user(uid,name=""):
    suid=str(uid)
    if suid not in data["users"]:
        data["users"][suid]={"coins":DEFAULT_FREE_COINS,"active":True,"name":name or ""}
        save_data(data)

# --------- KEYBOARDS ---------
def kb_user(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("💡 راهنما", "🟩 شارژ مجدد")
    kb.row("☎️ پشتیبانی", "👤 سازنده")
    kb.row("➕ افزودن به گروه", "📱 دنبال کردم اینستاگرام")
    kb.row("🧠 روشن / خاموش")
    return kb

def kb_admin():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📊 آمار کاربران", "💰 شارژ کاربر")
    kb.row("🤐 سکوت کاربر", "🚫 بن کاربر")
    kb.row("🚫 لیست بن‌ها", "🤫 لیست سکوت‌ها")
    kb.row("📣 ارسال همگانی", "↩️ لفت بده")
    kb.row("بازگشت BACK")
    return kb

def ikb_support(uid):
    ik = types.InlineKeyboardMarkup()
    ik.add(
        types.InlineKeyboardButton("✉️ پاسخ به کاربر", callback_data=f"reply:{uid}"),
        types.InlineKeyboardButton("❌ بستن گفتگو", callback_data=f"close:{uid}")
    )
    return ik

def ikb_insta_approve(uid):
    ik = types.InlineKeyboardMarkup()
    ik.add(
        types.InlineKeyboardButton("✅ تأیید فالو", callback_data=f"insta_ok:{uid}"),
        types.InlineKeyboardButton("❌ رد فالو", callback_data=f"insta_no:{uid}")
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
        text = (
            f"سلام 👋 به <b>{BOT_NAME_FARSI}</b> خوش اومدی!\n"
            "اینجا می‌تونی با هوش مصنوعی حرف بزنی، عکس بفرستی تا تحلیل کنه، "
            "و از امکانات مدیریتی در گروه‌ها استفاده کنی.\n\n"
            f"🔹 هر کاربر {DEFAULT_FREE_COINS} پیام رایگان داره.\n"
            "برای سکه بیشتر، از «📱 دنبال کردم اینستاگرام» استفاده کن!\n\n"
            "📷 فالو کن و اسکرین بفرست تا بعد از تأیید، ۵ سکه هدیه بگیری 🎁\n\n"
            f"لینک اینستاگرام 👇\n<a href='https://www.instagram.com/pesar_rostayi'>instagram.com/pesar_rostayi</a>"
        )
        bot.reply_to(m, text, reply_markup=kb_user(uid))# ==========================
# --------- ADMIN PANEL ---------
# ==========================
@bot.message_handler(func=lambda m: m.chat.type == "private" and is_admin(m.from_user.id))
def admin_private(m):
    txt = (m.text or "").strip()

    # لغو ارسال همگانی
    if txt == "بازگشت BACK":
        data["pending_broadcast"] = False
        save_data(data)
        bot.reply_to(m, "✅ عملیات لغو شد.", reply_markup=kb_admin())
        return

    # شروع ارسال همگانی
    if txt == "ارسال همگانی 📣":
        data["pending_broadcast"] = True
        save_data(data)
        bot.reply_to(m, "✍️ پیام خود را ارسال کنید؛ برای لغو، «بازگشت BACK» را بفرستید.")
        return

    # ارسال همگانی در حال انجام
    if data.get("pending_broadcast"):
        ok, fail = 0, 0
        for suid in list(data["users"].keys()):
            try:
                bot.copy_message(int(suid), m.chat.id, m.message_id)
                ok += 1
            except:
                fail += 1
        data["pending_broadcast"] = False
        save_data(data)
        bot.reply_to(m, f"📢 پیام به همه ارسال شد.\nموفق: {ok} | ناموفق: {fail}")
        return

    # آمار کاربران
    if txt == "آمار کاربران 📊":
        total = len(data["users"])
        total_ban = len(data["banned"])
        total_mute = len([1 for _, v in data["muted"].items() if v > now_ts()])
        bot.reply_to(m, f"📈 کاربران: {total}\n🚫 بن‌شده: {total_ban}\n🤐 در سکوت: {total_mute}")
        return

    # دستورات تایپی ادمین
    parts = txt.split()
    if len(parts) == 0:
        return

    try:
        if parts[0] == "شارژ" and len(parts) == 3:
            uid = int(parts[1]); amount = int(parts[2])
            ensure_user(uid)
            data["users"][str(uid)]["coins"] += amount
            save_data(data)
            bot.reply_to(m, f"✅ {amount} سکه به کاربر {uid} اضافه شد.")
            bot.send_message(uid, f"💰 سکه‌های شما {amount} عدد شارژ شد.")
            return

        if parts[0] == "بن" and len(parts) == 2:
            uid = str(parts[1])
            if uid not in data["banned"]:
                data["banned"].append(uid)
                save_data(data)
            bot.reply_to(m, f"🚫 کاربر {uid} بن شد.")
            return

        if parts[0] == "حذف" and len(parts) == 3 and parts[1] == "بن":
            uid = str(parts[2])
            if uid in data["banned"]:
                data["banned"].remove(uid)
                save_data(data)
            bot.reply_to(m, f"✅ بن کاربر {uid} برداشته شد.")
            return

        if parts[0] == "سکوت" and len(parts) == 3:
            uid = str(parts[1]); hours = float(parts[2])
            expire = now_ts() + int(hours * 3600)
            data["muted"][uid] = expire
            save_data(data)
            bot.reply_to(m, f"🤐 کاربر {uid} به مدت {hours} ساعت در سکوت است.")
            return

        if parts[0] == "حذف" and len(parts) == 3 and parts[1] == "سکوت":
            uid = str(parts[2])
            data["muted"].pop(uid, None)
            save_data(data)
            bot.reply_to(m, f"✅ سکوت کاربر {uid} برداشته شد.")
            return

        if parts[0] == "لفت" and parts[1] == "بده":
            bot.leave_chat(m.chat.id)
            return
    except Exception as e:
        bot.reply_to(m, f"⚠️ خطا: {e}")

# ==========================
# --------- USER PANEL ---------
# ==========================
@bot.message_handler(func=lambda m: m.chat.type == "private" and not is_admin(m.from_user.id))
def user_private(m):
    uid = m.from_user.id
    ensure_user(uid, f"{m.from_user.first_name or ''} {m.from_user.last_name or ''}".strip())
    cu = data["users"][str(uid)]
    txt = (m.text or "").strip()

    # جلوگیری از بن یا سکوت
    if str(uid) in data["banned"]:
        return
    if str(uid) in data["muted"] and data["muted"][str(uid)] > now_ts():
        return

    # دستورات معمولی
    if txt == "راهنما 💡":
        bot.reply_to(m, "📘 راهنما:\nبا ارسال متن، پاسخ هوش مصنوعی را بگیر.\nبا ارسال عکس، تحلیل تصویر دریافت کن.\nاگر سکه تمام شد، از پشتیبانی بخواه شارژت کند.")
        return

    if txt == "سازنده 👤":
        bot.reply_to(m, f"👤 سازنده: {ADMIN_USERNAME}")
        return

    if txt == "افزودن به گروه ➕":
        bot.reply_to(m, "من را به گروه اضافه کنید و به من دسترسی پیام بدهید، سپس مدیر می‌تواند بنویسد: «شارژ گروه [روز]».")
        return

    if txt == "شارژ مجدد 🟩":
        bot.reply_to(m, "برای شارژ، به پشتیبانی پیام بده یا از لینک اینستاگرام استفاده کن:\n📸 [Instagram](https://www.instagram.com/pesar_rostayi)")
        return

    if txt == "پشتیبانی ☎️":
        data["support_open"][str(uid)] = True
        save_data(data)
        bot.reply_to(m, "📩 پشتیبانی فعال شد. هر پیامی بفرست به مدیر می‌رسد.\nبرای خروج بنویس: پایان پشتیبانی")
        bot.send_message(ADMIN_ID, f"📥 پیام جدید از کاربر {uid}")
        return

    if txt == "پایان پشتیبانی":
        data["support_open"][str(uid)] = False
        save_data(data)
        bot.reply_to(m, "✅ پشتیبانی بسته شد.")
        return

    if txt == "روشن / خاموش 🧠":
        cu["active"] = not cu.get("active", True)
        save_data(data)
        bot.reply_to(m, f"🧠 حالت گفتگو {'فعال' if cu['active'] else 'غیرفعال'} شد.")
        return

    # پاسخ هوش مصنوعی (متن)
    if cu.get("coins", 0) <= 0:
        bot.reply_to(m, "💸 موجودی سکه شما تمام شده.")
        return

    if cu.get("active", True) and txt:
        try:
            # اگر کاربر گفت "ادامه تحلیل" → از حافظه آخرین پاسخ استفاده کن
            if txt.startswith("ادامه تحلیل"):
                last = cu.get("last_prompt", "")
                if not last:
                    bot.reply_to(m, "🔹 هنوز تحلیلی برای ادامه وجود ندارد.")
                    return
                ask_text = f"{last}\n\n{txt.replace('ادامه تحلیل', '').strip()}"
            else:
                ask_text = txt
                cu["last_prompt"] = ask_text

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
            bot.reply_to(m, f"❌ خطا در پاسخ هوش مصنوعی:\n{e}")
        return

# ==========================
# --------- PHOTO AI ---------
# ==========================
@bot.message_handler(content_types=["photo"])
def handle_photo(m):
    uid = m.from_user.id
    ensure_user(uid)
    cu = data["users"][str(uid)]

    if cu.get("coins", 0) <= 0:
        return bot.reply_to(m, "💸 موجودی سکه تمام شده.")

    try:
        file_info = bot.get_file(m.photo[-1].file_id)
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user",
                 "content": [
                     {"type": "text", "text": "این تصویر را به فارسی تحلیل و توصیف کن."},
                     {"type": "image_url", "image_url": {"url": file_url}}
                 ]}
            ]
        )
        answer = resp.choices[0].message.content
        bot.reply_to(m, f"🖼️ تحلیل تصویر:\n{answer}")
        cu["coins"] -= 1
        save_data(data)
    except Exception as e:
        bot.reply_to(m, f"❌ خطا در تحلیل تصویر:\n{e}")

# ==========================
# --------- RUN BOT ---------
# ==========================
if __name__ == "__main__":
    print("🤖 Bot is running...")
    bot.infinity_polling(skip_pending=True, timeout=30)
