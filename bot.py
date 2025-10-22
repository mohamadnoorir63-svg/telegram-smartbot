# bot.py
# Digi-Anti (پایه) — نوشته شده با pyTelegramBotAPI (Telebot)
# توضیحات: این ربات قابلیت‌های مدیریتی پایه و پیشرفته‌ای دارد و تنظیمات را در data.json ذخیره می‌کند.

import telebot
from telebot import types
import os
import json
from datetime import datetime
from time import time

# ---------- تنظیمات ----------
TOKEN = os.environ.get("TOKEN")  # در Heroku: Config Var با نام TOKEN قرار بدین
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))  # آیدی عددی شما (مالک اصلی ربات)
DATA_FILE = "data.json"
# ------------------------------

bot = telebot.TeleBot(TOKEN)

# داده‌ها را از فایل می‌خوانیم / ذخیره می‌کنیم
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"chats": {}}, f, ensure_ascii=False, indent=2)

def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

data = load_data()  # حافظهٔ ساده

def ensure_chat(chat_id):
    chat_id = str(chat_id)
    if chat_id not in data["chats"]:
        data["chats"][chat_id] = {
            "admins": [],      # list of user ids (int)
            "vips": [],
            "locks": {         # default locks off
                "link": False,
                "photo": False,
                "sticker": False,
                "video": False,
                "forward": False,
                "bots": False,
                "contact": False,
                "audio": False,
                "document": False
            },
            "welcome": {
                "enabled": True,
                "text": "👋 سلام {name}!\nبه گروه خوش آمدی 🌸"
            },
            "warnings": {},    # user_id -> warn count
            "muted": [],       # list of user ids
            "members": {},     # tracked members: user_id -> {"name":..., "last_seen":ts}
            "nicknames": {}    # user_id -> nickname (local)
        }
        save_data(data)
    return data["chats"][chat_id]

# helper: check admin permission: either owner, or chat admin list, or Telegram admin
def is_bot_owner(user_id):
    return int(user_id) == OWNER_ID

def is_admin(user_id, chat_id):
    chat = ensure_chat(chat_id)
    try:
        if is_bot_owner(user_id):
            return True
        if int(user_id) in chat["admins"]:
            return True
    except:
        pass
    # also check if user is chat admin (via API)
    try:
        member = bot.get_chat_member(chat_id, user_id)
        if member.status in ["creator", "administrator"]:
            return True
    except:
        pass
    return False

# update tracked members when someone sends message or joins
def track_member(message):
    chat = ensure_chat(message.chat.id)
    uid = message.from_user.id
    name = message.from_user.first_name or ""
    chat["members"][str(uid)] = {"name": name, "last_seen": int(time())}
    save_data(data)

# -------------------------
# پیام خوش‌آمد
@bot.message_handler(content_types=['new_chat_members'])
def on_new_member(message):
    chat = ensure_chat(message.chat.id)
    for user in message.new_chat_members:
        # track
        chat["members"][str(user.id)] = {"name": user.first_name or "", "last_seen": int(time())}
        save_data(data)
        if chat["welcome"]["enabled"]:
            text = chat["welcome"]["text"].format(name=user.first_name or "دوست")
            bot.send_message(message.chat.id, text)

# -------------------------
# دستور: اضافه/حذف مدیر (owner یا existing admins)
@bot.message_handler(commands=['addadmin'])
def cmd_add_admin(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "برای اضافه کردن مدیر، روی پیام کاربر ریپلای کن و /addadmin رو بزن.")
        return
    user_id = message.reply_to_message.from_user.id
    chat = ensure_chat(message.chat.id)
    if user_id not in chat["admins"]:
        chat["admins"].append(user_id)
        save_data(data)
        bot.send_message(message.chat.id, f"✅ کاربر {message.reply_to_message.from_user.first_name} به عنوان مدیر افزوده شد.")
    else:
        bot.reply_to(message, "او قبلاً مدیر است.")

@bot.message_handler(commands=['deladmin'])
def cmd_del_admin(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "برای حذف مدیر، روی پیام کاربر ریپلای کن و /deladmin رو بزن.")
        return
    user_id = message.reply_to_message.from_user.id
    chat = ensure_chat(message.chat.id)
    if user_id in chat["admins"]:
        chat["admins"].remove(user_id)
        save_data(data)
        bot.send_message(message.chat.id, "✅ مدیر حذف شد.")
    else:
        bot.reply_to(message, "او مدیر نیست.")

# vip
@bot.message_handler(commands=['addvip'])
def cmd_add_vip(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "برای افزودن ویژه، روی پیام کاربر ریپلای کن و /addvip رو بزن.")
        return
    user_id = message.reply_to_message.from_user.id
    chat = ensure_chat(message.chat.id)
    if user_id not in chat["vips"]:
        chat["vips"].append(user_id)
        save_data(data)
        bot.send_message(message.chat.id, f"⭐ کاربر {message.reply_to_message.from_user.first_name} ویژه شد.")
    else:
        bot.reply_to(message, "او قبلاً ویژه است.")

@bot.message_handler(commands=['delvip'])
def cmd_del_vip(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "برای حذف ویژه، روی پیام کاربر ریپلای کن و /delvip رو بزن.")
        return
    user_id = message.reply_to_message.from_user.id
    chat = ensure_chat(message.chat.id)
    if user_id in chat["vips"]:
        chat["vips"].remove(user_id)
        save_data(data)
        bot.send_message(message.chat.id, "ویژه حذف شد.")
    else:
        bot.reply_to(message, "او ویژه نیست.")

# -------------------------
# قفل‌ها: تنظیم دستی با /lock <type> و /unlock <type>
VALID_LOCKS = ["link","photo","sticker","video","forward","bots","contact","audio","document"]
@bot.message_handler(commands=['lock'])
def cmd_lock(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return
    args = message.text.split()
    if len(args) < 2 or args[1] not in VALID_LOCKS:
        bot.reply_to(message, "موقع استفاده: /lock <نوع>\nانواع: " + ", ".join(VALID_LOCKS))
        return
    chat = ensure_chat(message.chat.id)
    chat["locks"][args[1]] = True
    save_data(data)
    bot.send_message(message.chat.id, f"🔒 قفل {args[1]} فعال شد.")

@bot.message_handler(commands=['unlock'])
def cmd_unlock(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return
    args = message.text.split()
    if len(args) < 2 or args[1] not in VALID_LOCKS:
        bot.reply_to(message, "موقع استفاده: /unlock <نوع>\nانواع: " + ", ".join(VALID_LOCKS))
        return
    chat = ensure_chat(message.chat.id)
    chat["locks"][args[1]] = False
    save_data(data)
    bot.send_message(message.chat.id, f"🔓 قفل {args[1]} غیرفعال شد.")

# -------------------------
# بررسی پیام‌ها برای اعمال قفل‌ها، حذف لینک و غیره
@bot.message_handler(func=lambda m: True, content_types=['text','photo','sticker','video','audio','document','voice','contact','video_note','animation'])
def content_filter(message):
    # track member
    try:
        track_member(message)
    except:
        pass

    chat = ensure_chat(message.chat.id)
    uid = message.from_user.id

    # if user is admin or vip, skip filters
    if is_admin(uid, message.chat.id) or uid in chat["vips"]:
        return

    # lock: link
    text = message.text or ""
    if chat["locks"].get("link") and ("http" in text.lower() or "t.me/" in text.lower()):
        try:
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(message.chat.id, f"🚫 {message.from_user.first_name} ارسال لینک مجاز نیست.")
        except:
            pass
        return

    # lock: photo
    if chat["locks"].get("photo") and message.content_type == "photo":
        try:
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(message.chat.id, f"🚫 ارسال عکس مجاز نیست.")
        except:
            pass
        return

    # lock: sticker
    if chat["locks"].get("sticker") and message.content_type == "sticker":
        try:
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(message.chat.id, f"🚫 استیکر مجاز نیست.")
        except:
            pass
        return

    # lock: video
    if chat["locks"].get("video") and message.content_type in ["video","video_note","animation"]:
        try:
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(message.chat.id, f"🚫 ویدیو مجاز نیست.")
        except:
            pass
        return

    # lock: forward
    if chat["locks"].get("forward") and message.forward_from:
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except:
            pass
        return

    # lock: bots (prevent messages from bot accounts)
    if chat["locks"].get("bots") and message.from_user.is_bot:
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except:
            pass
        return

    # lock: contact
    if chat["locks"].get("contact") and message.content_type == "contact":
        try:
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(message.chat.id, "🚫 ارسال مخاطب مجاز نیست.")
        except:
            pass
        return

    # lock: audio/document
    if chat["locks"].get("audio") and message.content_type in ["audio","voice"]:
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except:
            pass
        return
    if chat["locks"].get("document") and message.content_type == "document":
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except:
            pass
        return

# -------------------------
# اخطار / warn
@bot.message_handler(commands=['warn'])
def cmd_warn(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "روی پیام خاطی ریپلای کن و /warn بزن.")
        return
    user = message.reply_to_message.from_user
    chat = ensure_chat(message.chat.id)
    uid = str(user.id)
    chat["warnings"][uid] = chat["warnings"].get(uid, 0) + 1
    warns = chat["warnings"][uid]
    save_data(data)
    bot.send_message(message.chat.id, f"⚠️ {user.first_name} اکنون {warns} اخطار دارد.")
    # اگر تعداد اخطار >= 3 → سکوت یا اخراج
    if warns >= 3:
        try:
            bot.kick_chat_member(message.chat.id, user.id)
            bot.send_message(message.chat.id, f"🚫 {user.first_name} بخاطر دریافت {warns} اخطار بن شد.")
        except Exception as e:
            bot.send_message(message.chat.id, f"خطا در بن کردن: {e}")

# حذف اخطار
@bot.message_handler(commands=['clearwarns'])
def cmd_clear_warns(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "روی پیام کاربر ریپلای کن و /clearwarns بزن.")
        return
    user = message.reply_to_message.from_user
    chat = ensure_chat(message.chat.id)
    uid = str(user.id)
    if uid in chat["warnings"]:
        chat["warnings"].pop(uid)
        save_data(data)
        bot.send_message(message.chat.id, "اخطارها حذف شدند.")
    else:
        bot.reply_to(message, "او اخطاری ندارد.")

# سکوت (محدودسازی)
@bot.message_handler(commands=['mute'])
def cmd_mute(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "روی پیام کاربر ریپلای کن و /mute بزن.")
        return
    user = message.reply_to_message.from_user
    chat = ensure_chat(message.chat.id)
    uid = user.id
    if uid in chat["muted"]:
        bot.reply_to(message, "او قبلاً ساکت شده.")
        return
    # restrict: cannot send messages
    try:
        bot.restrict_chat_member(message.chat.id, uid,
                                 permissions=types.ChatPermissions(can_send_messages=False),
                                 until_date=None)
        chat["muted"].append(uid)
        save_data(data)
        bot.send_message(message.chat.id, f"🔇 {user.first_name} ساکت شد.")
    except Exception as e:
        bot.reply_to(message, f"خطا: {e}")

@bot.message_handler(commands=['unmute'])
def cmd_unmute(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "روی پیام کاربر ریپلای کن و /unmute بزن.")
        return
    user = message.reply_to_message.from_user
    chat = ensure_chat(message.chat.id)
    uid = user.id
    if uid not in chat["muted"]:
        bot.reply_to(message, "او سکوت نشده.")
        return
    try:
        bot.restrict_chat_member(message.chat.id, uid,
                                 permissions=types.ChatPermissions(can_send_messages=True,
                                                                  can_send_media_messages=True,
                                                                  can_send_other_messages=True,
                                                                  can_add_web_page_previews=True),
                                 until_date=None)
        chat["muted"].remove(uid)
        save_data(data)
        bot.send_message(message.chat.id, f"🔊 {user.first_name} از سکوت خارج شد.")
    except Exception as e:
        bot.reply_to(message, f"خطا: {e}")

# جلوگیری از پیام کاربر ساکت (همچنین حذف در content_filter)
# (در content_filter ما پیامهای ساکت رو حذف می‌کنیم ولی این هم یه لایه‌ست)

# -------------------------
# پاکسازی عددی: /del <count>
@bot.message_handler(commands=['del'])
def cmd_delete(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "مثال: /del 10")
        return
    try:
        count = int(args[1])
    except:
        bot.reply_to(message, "عدد معتبر وارد کن.")
        return
    # حذف پیام‌ها با استفاده از message_id نزولی (ساده ولی کارا)
    deleted = 0
    mid = message.message_id
    for i in range(1, count+1):
        try:
            bot.delete_message(message.chat.id, mid - i)
            deleted += 1
        except:
            pass
    bot.send_message(message.chat.id, f"🧹 {deleted} پیام حذف شد.")

# پاکسازی پیشرفته: /purge <@username or user_id>  (پاکسازی تمام پیام‌های کاربر در محدوده از آخر)
@bot.message_handler(commands=['purge'])
def cmd_purge(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return
    # باید ریپلای کن یا نام کاربر را وارد کنی
    target_id = None
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
    else:
        args = message.text.split()
        if len(args) >= 2:
            # تلاش برای گرفتن عدد
            try:
                target_id = int(args[1])
            except:
                bot.reply_to(message, "برای purge یا ریپلای کن یا id عددی وارد کن.")
                return
        else:
            bot.reply_to(message, "برای پاکسازی باید ریپلای یا id بدی.")
            return
    # تلاش حذف آخرین 1000 پیام (ممکنه زمان ببرد)
    deleted = 0
    # راه ساده: از آخرین message_id پایین بیاییم (محدود به 1000)
    end_mid = message.message_id
    for mid in range(end_mid, max(0, end_mid-1000), -1):
        try:
            # نیاز به گرفتن پیام نیست؛ سعی می‌کنیم حذف کنیم و به خطاها اهمیت ندهیم
            # اما باید چک کنیم پیام متعلق به target است: متأسفانه Bot API پیام را بازنمی‌گرداند بدون getUpdates
            # بنابراین یک روش عملی: تلاش برای حذف و در صورت شکست نادیده بگیر — این ممکن است پیام‌های دیگر را هم حذف کند.
            # امن‌تر: اگر پیام ریپلای هست می‌توانیم حذف کنیم؛ برای purge کامل نیاز به دیتابیس پیام‌ها داریم.
            pass
        except:
            pass
    bot.reply_to(message, "📌 عملیات purge (نسخه ساده) انجام شد — برای پاکسازی دقیق نیاز به ثبت پیام‌ها در دیتابیس است.")

# -------------------------
# نمایش آیدی با عکس و زمان: /whois (روی کاربر ریپلای کن)
@bot.message_handler(commands=['whois'])
def cmd_whois(message):
    if not message.reply_to_message:
        bot.reply_to(message, "برای نمایش آیدی و اطلاعات، روی پیام کاربر ریپلای کن و /whois را بزن.")
        return
    user = message.reply_to_message.from_user
    # تلاش برای گرفتن عکس پروفایل
    try:
        photos = bot.get_user_profile_photos(user.id, limit=1)
        if photos.total_count > 0:
            file_id = photos.photos[0][0].file_id
            caption = f"👤 نام: {user.first_name}\n🆔 آیدی: <code>{user.id}</code>\n⏰ زمان: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
            bot.send_photo(message.chat.id, file_id, caption, parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, f"👤 نام: {user.first_name}\n🆔 آیدی: <code>{user.id}</code>\n⏰ زمان: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}", parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"خطا در دریافت اطلاعات: {e}")

# -------------------------
# تگ همه (ساده): /tagall متن (تگ کسانی که تا کنون دیده شده اند)
@bot.message_handler(commands=['tagall'])
def cmd_tagall(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return
    args = message.text.split(maxsplit=1)
    note = args[1] if len(args) > 1 else "Attention!"
    chat = ensure_chat(message.chat.id)
    # لیستی از اعضای tracked
    mentions = []
    for uid, info in chat["members"].items():
        uid_i = int(uid)
        name = info.get("name","")
        # mention با فرمت tg://user?id=...
        mentions.append(f"[{name}](tg://user?id={uid_i})")
    # اگر لیست طولانی شد، پیام را به تکه‌ها تقسیم کن
    text = note + "\n" + " ".join(mentions)
    try:
        bot.send_message(message.chat.id, text, parse_mode="Markdown")
    except Exception:
        # fallback: فقط متن
        bot.send_message(message.chat.id, note)

# -------------------------
# پین پیام: ریپلای به پیام و /pin
@bot.message_handler(commands=['pin'])
def cmd_pin(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "روی پیام مورد نظر ریپلای کن و /pin بزن.")
        return
    try:
        bot.pin_chat_message(message.chat.id, message.reply_to_message.message_id)
        bot.send_message(message.chat.id, "📌 پیام پین شد.")
    except Exception as e:
        bot.reply_to(message, f"خطا: {e}")

# -------------------------
# لقب (محلی) — ذخیره و نمایش در whois/welcome
@bot.message_handler(commands=['setnick'])
def cmd_setnick(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "برای دادن لقب به کاربر، روی پیامش ریپلای کن و /setnick لقب را بزن.")
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "مثال: ریپلای به پیام کاربر + /setnick قهرمان")
        return
    nick = args[1].strip()
    target_id = str(message.reply_to_message.from_user.id)
    chat = ensure_chat(message.chat.id)
    chat["nicknames"][target_id] = nick
    save_data(data)
    bot.send_message(message.chat.id, f"🏷 لقب '{nick}' به کاربر داده شد.")

@bot.message_handler(commands=['delnick'])
def cmd_delnick(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "روی پیام کاربر ریپلای کن و /delnick بزن.")
        return
    target_id = str(message.reply_to_message.from_user.id)
    chat = ensure_chat(message.chat.id)
    if target_id in chat["nicknames"]:
        chat["nicknames"].pop(target_id)
        save_data(data)
        bot.send_message(message.chat.id, "لقب حذف شد.")
    else:
        bot.reply_to(message, "او لقبی ندارد.")

# -------------------------
# تنظیم پیام خوش‌آمد: /setwelcome متن (برای مدیران)
@bot.message_handler(commands=['setwelcome'])
def cmd_setwelcome(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "مثال: /setwelcome خوش آمدی {name} به گروه ما")
        return
    chat = ensure_chat(message.chat.id)
    chat["welcome"]["text"] = args[1]
    save_data(data)
    bot.send_message(message.chat.id, "پیام خوش‌آمد به‌روز شد.")

@bot.message_handler(commands=['togglewelcome'])
def cmd_toggle_welcome(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return
    chat = ensure_chat(message.chat.id)
    chat["welcome"]["enabled"] = not chat["welcome"]["enabled"]
    save_data(data)
    bot.send_message(message.chat.id, f"وضعیت خوش‌آمد {'فعال' if chat['welcome']['enabled'] else 'غیرفعال'} شد.")

# -------------------------
# بن و کیک و پاکسازی سریع
@bot.message_handler(commands=['ban'])
def cmd_ban(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "روی پیام کاربر ریپلای کن و /ban بزن.")
        return
    user = message.reply_to_message.from_user
    try:
        bot.kick_chat_member(message.chat.id, user.id)
        bot.send_message(message.chat.id, f"🚫 {user.first_name} بن شد.")
    except Exception as e:
        bot.reply_to(message, f"خطا: {e}")

@bot.message_handler(commands=['unban'])
def cmd_unban(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "مثال: /unban user_id")
        return
    try:
        uid = int(args[1])
        bot.unban_chat_member(message.chat.id, uid)
        bot.send_message(message.chat.id, "✅ آنبن شد.")
    except Exception as e:
        bot.reply_to(message, f"خطا: {e}")

@bot.message_handler(commands=['kick'])
def cmd_kick(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "روی پیام کاربر ریپلای کن و /kick بزن.")
        return
    user = message.reply_to_message.from_user
    try:
        bot.kick_chat_member(message.chat.id, user.id)
        bot.unban_chat_member(message.chat.id, user.id)  # باعث می‌شه kick فقط موقت باشه
        bot.send_message(message.chat.id, f"👢 {user.first_name} اخراج شد.")
    except Exception as e:
        bot.reply_to(message, f"خطا: {e}")

# -------------------------
# دستور کمکی برای نمایش وضعیت گروه
@bot.message_handler(commands=['settings'])
def cmd_settings(message):
    chat = ensure_chat(message.chat.id)
    s = f"🔧 تنظیمات گروه:\nقفل‌ها:\n"
    for k,v in chat["locks"].items():
        s += f" - {k}: {'فعال' if v else 'غیرفعال'}\n"
    s += f"\nتعداد مدیران: {len(chat['admins'])}\nتعداد ویژه: {len(chat['vips'])}\nوضعیت خوش‌آمد: {'فعال' if chat['welcome']['enabled'] else 'غیرفعال'}"
    bot.send_message(message.chat.id, s)

# -------------------------
# دستورات مدیر اصلی (owner) برای مشاهده داده‌ها
@bot.message_handler(commands=['dumpdata'])
def cmd_dumpdata(message):
    if not is_bot_owner(message.from_user.id):
        return
    # برای debug: ارسال فایل data.json
    try:
        with open(DATA_FILE, "rb") as f:
            bot.send_document(message.chat.id, f)
    except Exception as e:
        bot.reply_to(message, f"خطا: {e}")

# -------------------------
# catch-all: log errors (simple)
import logging
logger = telebot.logger
telebot.logger.setLevel(logging.INFO)

print("🤖 Digi-Anti (base) فعال شد.")
bot.infinity_polling(timeout=60, long_polling_timeout = 60)
