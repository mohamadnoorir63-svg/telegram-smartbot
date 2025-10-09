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
INSTAGRAM_LINK = os.getenv("INSTAGRAM_LINK") or "https://www.instagram.com/pesar_rostayi"

if not BOT_TOKEN:
    raise SystemExit("❌ BOT_TOKEN تعریف نشده است.")
if not ADMIN_ID:
    raise SystemExit("❌ ADMIN_ID (عددی) تعریف نشده است.")
if not OPENAI_API_KEY:
    raise SystemExit("❌ OPENAI_API_KEY تعریف نشده است.")

# --------- INIT ---------
bot = TeleBot(BOT_TOKEN, parse_mode="HTML")
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
            "pending_broadcast": False,
            "ig_pending": {}
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
    d.setdefault("ig_pending", {})
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
    kb.row(types.KeyboardButton("افزودن به گروه ➕"), types.KeyboardButton("دنبال کردم اینستاگرام 📲"))
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

# --------- START COMMAND ---------
@bot.message_handler(commands=["start"])
def start_cmd(m):
    uid = m.from_user.id
    ensure_user(uid, f"{m.from_user.first_name or ''} {m.from_user.last_name or ''}".strip())

    if is_admin(uid):
        bot.reply_to(m, "👑 سلام رئیس! وارد پنل مدیریتی شدی.", reply_markup=kb_admin())
    else:
        bot.reply_to(
            m,
            f"👋 سلام! به <b>{BOT_NAME_FARSI}</b> خوش اومدی!\n"
            "اینجا می‌تونی با هوش مصنوعی چت کنی یا عکس بفرستی تا تحلیل کنه.\n"
            f"هر کاربر {DEFAULT_FREE_COINS} پیام رایگان داره؛ بعدش با «شارژ مجدد 🟩» ادامه بده.\n\n"
            f"📷 اگه صفحهٔ اینستاگرام ما رو دنبال کردی، دکمهٔ «دنبال کردم اینستاگرام 📲» رو بزن تا ۵ سکهٔ هدیه بگیری 🎁\n"
            f"🔗 <a href='{INSTAGRAM_LINK}'>صفحهٔ اینستاگرام ما</a>",
            reply_markup=kb_user(uid)
        )

# --------- ADMIN PANEL ---------
@bot.message_handler(func=lambda m: m.chat.type == "private" and is_admin(m.from_user.id))
def admin_private(m):
    txt = (m.text or "").strip()

    # ارسال همگانی
    if txt == "ارسال همگانی 📣":
        data["pending_broadcast"] = True
        save_data(data)
        bot.reply_to(m, "✍️ پیام خود را بفرست تا برای همه کاربران و گروه‌ها ارسال شود. (برای لغو: BACK)")
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
        bot.reply_to(m, f"📣 ارسال شد ✅ موفق: {ok} | ❌ ناموفق: {fail}")
        return

    # آمار
    if txt == "آمار کاربران 📊":
        total = len(data["users"])
        total_ban = len(data["banned"])
        total_mute = len([1 for k, v in data["muted"].items() if v > now_ts()])
        bot.reply_to(m, f"📈 کاربران: {total}\n🚫 بن‌شده: {total_ban}\n🤐 در سکوت: {total_mute}")
        return

    # برگشت راهنما
    if txt == "بازگشت BACK":
        bot.reply_to(m,
                     "دستورات سودو:\n"
                     "• شارژ [uid] [تعداد]\n"
                     "• بن [uid] | حذف بن [uid]\n"
                     "• سکوت [uid] [ساعت] | حذف سکوت [uid]\n"
                     "• شارژ گروه [روز] | لفت بده\n"
                     "• لیست بن‌ها | لیست سکوت‌ها",
                     reply_markup=kb_admin())
        return# --------- USER COMMANDS ---------
@bot.message_handler(func=lambda m: m.chat.type == "private" and not is_admin(m.from_user.id))
def user_private(m):
    uid = m.from_user.id
    ensure_user(uid)
    txt = (m.text or "").strip()
    suid = str(uid)

    # راهنما
    if txt == "راهنما 💡":
        bot.reply_to(m,
                     "📘 راهنما:\n"
                     "1️⃣ برای چت، پیام یا سوال خود را بنویسید.\n"
                     "2️⃣ برای ارسال عکس جهت تحلیل، فقط عکس را بفرستید.\n"
                     "3️⃣ برای ارتباط با پشتیبانی، روی ☎️ پشتیبانی بزنید.\n"
                     "4️⃣ با دنبال کردن اینستاگرام، ۵ سکه هدیه بگیرید 🎁.",
                     reply_markup=kb_user(uid))
        return

    # لینک سازنده
    if txt == "سازنده 👤":
        bot.reply_to(m, f"👑 سازنده: {ADMIN_USERNAME}\n💬 هر پیشنهاد یا باگ را اطلاع دهید.")
        return

    # افزودن به گروه
    if txt == "افزودن به گروه ➕":
        bot.reply_to(m,
                     f"برای افزودن من به گروه، لینک زیر را بزن:\n\n"
                     f"https://t.me/{bot.get_me().username}?startgroup=new\n\n"
                     "بعد از افزودن، ادمین گروه باید دستور «شارژ گروه [روز]» را بزند.")
        return

    # دکمه دنبال کردم اینستاگرام 📲
    if txt == "دنبال کردم اینستاگرام 📲":
        data["ig_pending"][suid] = True
        save_data(data)
        bot.reply_to(m,
                     "📸 لطفاً از صفحهٔ فالو گرفته‌شده (که نشون بده فالو کردی) اسکرین بفرست.\n"
                     "ادمین بررسی می‌کنه و بعد از تأیید، ۵ سکه بهت هدیه داده میشه 🎁.")
        return

    # سکوت، شارژ، یا خطا
    if suid in data["banned"]:
        bot.reply_to(m, "🚫 شما بن شدید. دسترسی شما مسدود است.")
        return
    if suid in data["muted"] and data["muted"][suid] > now_ts():
        left = (data["muted"][suid] - now_ts()) // 60
        bot.reply_to(m, f"🤫 شما در حالت سکوت هستید ({left} دقیقه باقی‌مانده).")
        return

    # اگر در پشتیبانی هست
    if suid in data["support_open"]:
        bot.forward_message(ADMIN_ID, m.chat.id, m.message_id)
        bot.reply_to(m, "📩 پیام شما برای پشتیبانی ارسال شد.")
        return

    # روشن / خاموش هوش
    if txt == "روشن / خاموش 🧠":
        u = data["users"][suid]
        u["active"] = not u.get("active", True)
        save_data(data)
        bot.reply_to(m, "✅ هوش فعال شد." if u["active"] else "⛔ هوش غیرفعال شد.")
        return

    # اگر کاربر سکه ندارد
    coins = data["users"][suid]["coins"]
    if coins <= 0:
        bot.reply_to(m, "❌ موجودی شما تمام شده.\nبا «شارژ مجدد 🟩» ادامه دهید.")
        return

    # تشخیص ادامه تحلیل
    if txt.startswith("ادامه تحلیل"):
        prev_msg = txt.replace("ادامه تحلیل", "").strip()
        prompt = f"تحلیل را ادامه بده و توضیح تکمیلی ارائه کن برای:\n{prev_msg}"
    else:
        prompt = txt

    # درخواست به GPT با پشتیبانی از متن
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "شما یک دستیار فارسی حرفه‌ای هستید."},
                {"role": "user", "content": prompt}
            ]
        )
        answer = response.choices[0].message.content
        bot.reply_to(m, answer)
        data["users"][suid]["coins"] -= 1
        save_data(data)
    except Exception as e:
        bot.reply_to(m, f"⚠️ خطا در پاسخ: {e}")

# --------- عکس ---------
@bot.message_handler(content_types=["photo"])
def photo_analyze(m):
    uid = m.from_user.id
    ensure_user(uid)
    suid = str(uid)

    # اگر سکه ندارد
    if data["users"][suid]["coins"] <= 0:
        bot.reply_to(m, "❌ موجودی شما تمام شده.\nبا «شارژ مجدد 🟩» ادامه دهید.")
        return

    # اگر در انتظار تأیید اینستا است
    if suid in data["ig_pending"] and data["ig_pending"][suid]:
        bot.send_message(ADMIN_ID, f"📥 عکس اثبات فالو از {m.from_user.first_name} دریافت شد.", reply_to_message_id=None)
        bot.forward_message(ADMIN_ID, m.chat.id, m.message_id)
        bot.send_message(ADMIN_ID, f"تأیید می‌کنی فالو کرده؟ /approve_{uid} یا /reject_{uid}")
        bot.reply_to(m, "📤 تصویر ارسال شد. ادمین بررسی می‌کنه و نتیجه اعلام میشه.")
        return

    # تحلیل تصویر با GPT-4o
    file_info = bot.get_file(m.photo[-1].file_id)
    file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "تصویر را تحلیل کن و توضیح فارسی ارائه بده."},
                {"role": "user", "content": [{"type": "image_url", "image_url": {"url": file_url}}]}
            ]
        )
        answer = res.choices[0].message.content
        bot.reply_to(m, f"🖼 تحلیل تصویر:\n{answer}")
        data["users"][suid]["coins"] -= 1
        save_data(data)
    except Exception as e:
        bot.reply_to(m, f"❌ خطا در تحلیل تصویر: {e}")

# --------- تأیید یا رد فالو اینستا ---------
@bot.message_handler(commands=["approve", "reject"])
def approve_reject_instagram(m):
    if not is_admin(m.from_user.id):
        return
    try:
        cmd, uid = m.text.split("_")
        uid = int(uid)
    except:
        bot.reply_to(m, "فرمت اشتباه است. مثال: /approve_12345")
        return

    suid = str(uid)
    if suid not in data["ig_pending"]:
        bot.reply_to(m, "درخواستی از این کاربر وجود ندارد.")
        return

    if cmd.startswith("/approve"):
        data["users"][suid]["coins"] += 5
        bot.send_message(uid, "✅ فالو تأیید شد! ۵ سکه به حسابت اضافه شد 🎁.")
        bot.reply_to(m, f"تأیید شد ✅ برای {uid}")
    else:
        bot.send_message(uid, "❌ فالو تأیید نشد. لطفاً عکس واضح‌تر بفرست.")
        bot.reply_to(m, f"رد شد ❌ برای {uid}")

    del data["ig_pending"][suid]
    save_data(data)

# --------- پشتیبانی ---------
@bot.message_handler(func=lambda m: m.text == "پشتیبانی ☎️")
def support_request(m):
    uid = m.from_user.id
    suid = str(uid)
    ensure_user(uid)
    if suid in data["support_open"]:
        del data["support_open"][suid]
        bot.reply_to(m, "📪 پشتیبانی بسته شد.", reply_markup=kb_user(uid))
    else:
        data["support_open"][suid] = True
        bot.reply_to(m, "📨 پیام خود را بنویسید. برای بستن، دوباره روی ☎️ پشتیبانی بزنید.")
    save_data(data)

# --------- گروه ---------
@bot.my_chat_member_handler()
def added_to_group(update):
    chat = update.chat
    if update.new_chat_member.status == "member":
        data["groups"][str(chat.id)] = {"title": chat.title, "join_time": now_ts()}
        save_data(data)
        bot.send_message(ADMIN_ID, f"📢 ربات به گروه جدیدی اضافه شد:\n📛 {chat.title}\n🆔 {chat.id}")

# --------- RUN ---------
print("🤖 Bot is running with GPT-4o-mini ...")
bot.infinity_polling(skip_pending=True)
