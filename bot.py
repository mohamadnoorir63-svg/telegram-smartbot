# -*- coding: utf-8 -*-
import os, json, time, datetime
from telebot import TeleBot, types
from openai import OpenAI

# --------- ENV ---------
BOT_TOKEN        = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
ADMIN_ID         = int(os.getenv("ADMIN_ID") or "0")  # عددی
ADMIN_USERNAME   = os.getenv("ADMIN_USERNAME") or "@NOORI_NOOR"  # برای دکمه سازنده/پشتیبانی
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
    # ساخت فایل پایه + اطمینان از کلیدها
    base = {
        "users": {},              # uid -> {coins, active, name}
        "banned": [],             # [uid(str)]
        "muted": {},              # uid(str) -> expire_ts
        "groups": {},             # gid(str) -> {expires, active}
        "support_open": {},       # uid(str) -> True/False
        "admin_reply_to": None,   # uid یا None
        "pending_broadcast": False
    }
    if not os.path.exists(DATA_FILE):
        save_data(base)
        return base
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        d = json.load(f)
    # تکمیل کلیدهای جاافتاده
    for k, v in base.items():
        if k not in d:
            d[k] = v
    # تکمیل ساختارهای داخلی
    if not isinstance(d.get("users"), dict): d["users"] = {}
    if not isinstance(d.get("banned"), list): d["banned"] = []
    if not isinstance(d.get("muted"), dict): d["muted"] = {}
    if not isinstance(d.get("groups"), dict): d["groups"] = {}
    if not isinstance(d.get("support_open"), dict): d["support_open"] = {}
    if "admin_reply_to" not in d: d["admin_reply_to"] = None
    if "pending_broadcast" not in d: d["pending_broadcast"] = False
    save_data(d)
    return d

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

data = load_data()

def is_admin(uid): 
    try: 
        return int(uid) == int(ADMIN_ID)
    except:
        return False

def ensure_user(uid, name=""):
    suid = str(uid)
    if suid not in data["users"]:
        data["users"][suid] = {"coins": DEFAULT_FREE_COINS, "active": True, "name": name or ""}
        save_data(data)

def get_bot_username():
    try:
        return bot.get_me().username or "NoorirSmartBot"
    except:
        return "NoorirSmartBot"

def get_bot_id():
    try:
        return bot.get_me().id
    except:
        return None

# --------- KEYBOARDS ---------
def kb_user(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(types.KeyboardButton("راهنما 💡"), types.KeyboardButton("شارژ مجدد 🟩"))
    kb.row(types.KeyboardButton("پشتیبانی ☎️"), types.KeyboardButton("سازنده 👤"))
    kb.row(types.KeyboardButton("افزودن به گروه ➕"))
    kb.row(types.KeyboardButton("روشن / خاموش 🧠"))
    return kb

def ikb_user_deeplink():
    ik = types.InlineKeyboardMarkup()
    bot_un = get_bot_username()
    add_url = f"https://t.me/{bot_un}?startgroup=add"
    # سازنده/پشتیبانی مستقیم
    admin_user = ADMIN_USERNAME.replace("@","")
    support_url = f"https://t.me/{admin_user}"
    ik.add(types.InlineKeyboardButton("➕ افزودن به گروه", url=add_url))
    ik.add(types.InlineKeyboardButton("ارتباط مستقیم با سازنده", url=support_url))
    return ik

def kb_admin():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(types.KeyboardButton("آمار کاربران 📊"), types.KeyboardButton("ارسال همگانی 📣"))
    kb.row(types.KeyboardButton("سکوت کاربر 🤐"), types.KeyboardButton("بن کاربر 🚫"))
    kb.row(types.KeyboardButton("لیست بن‌ها 🚫"), types.KeyboardButton("لیست سکوت‌ها 🤫"))
    kb.row(types.KeyboardButton("راهنمای سودو 📘"), types.KeyboardButton("لفت بده ↩️"))
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
            "👑 سلام رئیس! این پنل مدیریت شماست.\n"
            "پیام همگانی، سکوت/بن، و شارژ گروه را از اینجا مدیریت کن.",
            reply_markup=kb_admin())
    else:
        bot.reply_to(
            m,
            f"سلام! 👋 به <b>{BOT_NAME_FARSI}</b> خوش اومدی.\n"
            "• با ارسال متن یا عکس در پی‌وی، پاسخ هوش مصنوعی می‌گیری.\n"
            f"• هر کاربر <b>{DEFAULT_FREE_COINS}</b> پیام رایگان دارد، بعدش «شارژ مجدد 🟩» را بزن.\n"
            "• برای فعال/غیرفعال: «روشن / خاموش 🧠».",
            reply_markup=kb_user(uid)
        )
        # دکمه‌های بالایی (inline) برای افزودن به گروه و تماس مستقیم با سازنده
        try:
            bot.send_message(uid, "می‌تونی از این دکمه‌ها استفاده کنی:", reply_markup=ikb_user_deeplink())
        except: pass

# --------- ADMIN REPLY MODE (باید بالاتر از هندلرِ ادمین پرایوت باشد) ---------
@bot.message_handler(func=lambda m: m.chat.type=="private" and is_admin(m.from_user.id) and data.get("admin_reply_to"))
def admin_replying(m):
    target = data.get("admin_reply_to")
    try:
        bot.copy_message(target, m.chat.id, m.message_id)
        bot.reply_to(m, f"✅ ارسال شد برای {target}")
    except Exception as e:
        bot.reply_to(m, f"❌ خطا در ارسال: {e}")

# بستن گفتگو از سمت ادمین: «پایان [uid]»
@bot.message_handler(func=lambda m: m.chat.type=="private" and is_admin(m.from_user.id))
def admin_close_cmd(m):
    txt = (m.text or "").strip()
    parts = txt.split()
    if len(parts)==2 and parts[0]=="پایان":
        try:
            uid = int(parts[1])
            data["support_open"][str(uid)] = False
            if data.get("admin_reply_to") == uid:
                data["admin_reply_to"] = None
            save_data(data)
            bot.reply_to(m, f"🔒 گفتگوی کاربر {uid} بسته شد.")
        except:
            pass

# --------- ADMIN PANEL BUTTONS (خصوصی) ---------
@bot.message_handler(func=lambda m: m.chat.type == "private" and is_admin(m.from_user.id))
def admin_private(m):
    txt = (m.text or "").strip()

    # ارسال همگانی
    if txt == "ارسال همگانی 📣":
        data["pending_broadcast"] = True
        save_data(data)
        bot.reply_to(m, "✍️ پیام خود را همینجا بفرست؛ همان پیام برای همهٔ کاربران و گروه‌ها کپی می‌شود.\n(برای انصراف: «لغو»)")
        return

    if data.get("pending_broadcast"):
        if txt == "لغو":
            data["pending_broadcast"] = False
            save_data(data)
            bot.reply_to(m, "ارسال همگانی لغو شد.")
            return
        ok, fail = 0, 0
        # ارسال به همه کاربران
        for suid in list(data["users"].keys()):
            try:
                bot.copy_message(int(suid), m.chat.id, m.message_id)
                ok += 1
            except:
                fail += 1
        # ارسال به همه گروه‌ها
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
        total_mute = len([1 for _,t in data["muted"].items() if t > now_ts()])
        total_groups = len(data["groups"])
        bot.reply_to(m, f"📈 کاربران: {total}\n👥 گروه‌ها: {total_groups}\n🚫 بن‌شده: {total_ban}\n🤐 در سکوت: {total_mute}")
        return

    # راهنما
    if txt == "راهنمای سودو 📘":
        bot.reply_to(m,
            "دستورات تایپی سودو (خصوصی):\n"
            "• شارژ [uid] [تعداد]\n"
            "• بن [uid] | حذف بن [uid]\n"
            "• سکوت [uid] [ساعت] | حذف سکوت [uid]\n"
            "• لفت گروه [آیدی] | لفت همه گروه‌ها\n"
            "— داخل گروه: شارژ گروه [روز] | لفت بده")
        return

    # راهنمای دکمه‌ها
    if txt == "بن کاربر 🚫":
        bot.reply_to(m, "✅ بن: «بن [uid]» | رفع: «حذف بن [uid]»")
        return
    if txt == "سکوت کاربر 🤐":
        bot.reply_to(m, "✅ سکوت: «سکوت [uid] [ساعت]» | رفع: «حذف سکوت [uid]»")
        return
    if txt == "لیست بن‌ها 🚫":
        if not data["banned"]:
            bot.reply_to(m, "📜 لیست بن‌ها خالی است.")
        else:
            bot.reply_to(m, "📜 لیست بن‌ها:\n" + "\n".join([f"• {u}" for u in data["banned"]]))
        return
    if txt == "لیست سکوت‌ها 🤫":
        alive = [f"{u} (تا {datetime.datetime.fromtimestamp(t)})"
                 for u,t in data["muted"].items() if t > now_ts()]
        if not alive:
            bot.reply_to(m, "📜 لیست سکوت‌ها خالی است.")
        else:
            bot.reply_to(m, "📜 لیست سکوت‌ها:\n" + "\n".join([f"• {x}" for x in alive]))
        return
    if txt == "لفت بده ↩️":
        bot.reply_to(m, "این دستور را داخل گروه بزن تا از همان گروه خارج شوم: «لفت بده»\nاز راه دور: «لفت گروه [آیدی]»")
        return

    # دستورات نوشتاری سودو (خصوصی)
    parts = txt.replace("‌"," ").split()
    if not parts: return

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

        if parts[0] == "لیست" and len(parts) == 2 and parts[1] in ["بن‌ها","بنها"]:
            if not data["banned"]:
                bot.reply_to(m, "📜 لیست بن‌ها خالی است.")
            else:
                bot.reply_to(m, "📜 لیست بن‌ها:\n" + "\n".join([f"• {u}" for u in data["banned"]]))
            return

        if parts[0] == "لیست" and len(parts) == 2 and parts[1] in ["سکوت‌ها","سکوتها"]:
            alive = [f"{u} (تا {datetime.datetime.fromtimestamp(t)})"
                     for u,t in data["muted"].items() if t > now_ts()]
            if not alive:
                bot.reply_to(m, "📜 لیست سکوت‌ها خالی است.")
            else:
                bot.reply_to(m, "📜 لیست سکوت‌ها:\n" + "\n".join([f"• {x}" for x in alive]))
            return

        # از راه دور: لفت گروه [آیدی]
        if parts[0] == "لفت" and len(parts) == 3 and parts[1] == "گروه":
            gid = int(parts[2])
            try:
                bot.send_message(gid, "👋 ربات به درخواست ادمین از گروه خارج می‌شود. خداحافظ 🌸")
            except:
                pass
            try:
                bot.leave_chat(gid)
                bot.reply_to(m, f"✅ از گروه <code>{gid}</code> خارج شدم.")
            except Exception as e:
                bot.reply_to(m, f"❗ خطا در خروج از گروه:\n{e}")
            return

        # لفت همه گروه‌ها
        if txt == "لفت همه گروه‌ها":
            left, fail = 0, 0
            for gid in list(data["groups"].keys()):
                try:
                    bot.leave_chat(int(gid))
                    left += 1
                except:
                    fail += 1
            bot.reply_to(m, f"↩️ خارج شدم از {left} گروه | ناموفق: {fail}")
            return

    except Exception as e:
        bot.reply_to(m, f"❌ خطا: {e}")

# --------- ADDED TO GROUP (خوش‌آمد + اطلاع به ادمین) ---------
@bot.message_handler(content_types=["new_chat_members"])
def greet_on_add(m):
    try:
        bot_id = get_bot_id()
        if not bot_id: 
            return
        # اگر خودِ ربات عضو جدید است
        for u in m.new_chat_members:
            if u.id == bot_id:
                gid = str(m.chat.id)
                # ثبت گروه با وضعیت غیرفعال تا شارژ شود
                data["groups"].setdefault(gid, {"expires": 0, "active": True})
                save_data(data)
                # پیام در گروه
                bot.send_message(m.chat.id,
                    "سلام! من اضافه شدم 🌸\n"
                    "برای فعال‌سازی پاسخ هوش مصنوعی در این گروه، مدیر بنویسد:\n"
                    "• «شارژ گروه 1» (یک روز)\n"
                    "سپس در پیام‌ها با پیشوند «ربات ...» از من چیزی بخواهید.")
                # اطلاع به ادمین
                try:
                    bot.send_message(ADMIN_ID, f"➕ ربات به گروه جدید اضافه شد:\n"
                                               f"عنوان: {m.chat.title}\n"
                                               f"آیدی: <code>{m.chat.id}</code>")
                except: pass
                break
    except:
        pass

# همچنین اگر از نوع my_chat_member هم بیاید:
try:
    @bot.my_chat_member_handler(func=lambda upd: True)
    def on_my_status(upd):
        try:
            bot_id = get_bot_id()
            if not bot_id: return
            if upd.new_chat_member and upd.new_chat_member.user and upd.new_chat_member.user.id == bot_id:
                if upd.new_chat_member.status in ("member", "administrator"):
                    gid = str(upd.chat.id)
                    data["groups"].setdefault(gid, {"expires": 0, "active": True})
                    save_data(data)
                    # خوش آمد مختصر
                    try:
                        bot.send_message(upd.chat.id,
                            "سلام! برای فعال‌سازی، مدیر بنویسد: «شارژ گروه 1» 🌟")
                    except: pass
                    try:
                        bot.send_message(ADMIN_ID, f"➕ اضافه شدم به گروه:\n"
                                                   f"عنوان: {upd.chat.title}\n"
                                                   f"آیدی: <code>{upd.chat.id}</code>")
                    except: pass
        except:
            pass
except:
    pass

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

    # شارژ گروه [روز]
    if len(parts) == 3 and parts[0] == "شارژ" and parts[1] == "گروه":
        try:
            days = int(parts[2])
        except:
            return bot.reply_to(m, "⚠️ فرمت درست: «شارژ گروه 1» (یک روز)")

        gid = str(m.chat.id)
        until = now_ts() + days*86400
        data["groups"].setdefault(gid, {"expires":0,"active":True})
        data["groups"][gid]["expires"] = until
        data["groups"][gid]["active"]  = True
        save_data(data)
        bot.reply_to(m, f"✅ گروه به مدت {days} روز شارژ شد. از این پس با «ربات …» پاسخ می‌دهم.")
        return

# --------- USER PANEL (PRIVATE) ---------
@bot.message_handler(func=lambda m: m.chat.type=="private" and not is_admin(m.from_user.id))
def user_private(m):
    uid = m.from_user.id
    ensure_user(uid, f"{m.from_user.first_name or ''} {m.from_user.last_name or ''}".strip())
    txt = (m.text or "").strip()

    # بن / سکوت
    if str(uid) in data["banned"]:
        return
    if str(uid) in data["muted"] and data["muted"][str(uid)] > now_ts():
        return

    # دکمه‌ها
    if txt == "راهنما 💡":
        bot.reply_to(m,
            "راهنما:\n"
            "• با ارسال «متن»، پاسخ هوش مصنوعی می‌گیری.\n"
            "• با ارسال «عکس»، تحلیل تصویری می‌گیری.\n"
            f"• هر پیام 1 سکه مصرف می‌کند. موجودی فعلی: <b>{data['users'][str(uid)]['coins']}</b>\n"
            "• دکمه «روشن / خاموش 🧠» فقط برای خودت است.\n"
            "• برای شارژ: «پشتیبانی ☎️».")
        return

    if txt == "سازنده 👤":
        bot.reply_to(m, f"سازنده: {ADMIN_USERNAME}")
        return

    if txt == "افزودن به گروه ➕":
        # ارسال Deep-link واقعی
        bot_un = get_bot_username()
        add_url = f"https://t.me/{bot_un}?startgroup=add"
        ik = types.InlineKeyboardMarkup()
        ik.add(types.InlineKeyboardButton("➕ افزودن به گروه", url=add_url))
        bot.reply_to(m, "برای افزودن، روی دکمه زیر بزنید:", reply_markup=ik)
        return

    if txt == "شارژ مجدد 🟩":
        bot.reply_to(m, "برای شارژ سکه با پشتیبانی تماس بگیر: «پشتیبانی ☎️»")
        return

    if txt == "پشتیبانی ☎️":
        data["support_open"][str(uid)] = True
        save_data(data)
        bot.reply_to(m, "✉️ گفتگوی پشتیبانی باز شد. پیام بده؛ به سازنده وصل می‌شود. برای خروج: «پایان پشتیبانی»")
        try:
            bot.send_message(ADMIN_ID, f"📥 پیام جدید از کاربر {uid} — {m.from_user.first_name or ''} {m.from_user.last_name or ''}".strip())
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
        if cu["active"]:
            bot.reply_to(m, "✅ حالت گفتگو با هوش فعال شد.", reply_markup=kb_user(uid))
        else:
            bot.reply_to(m, "⛔️ حالت گفتگو با هوش غیرفعال شد.", reply_markup=kb_user(uid))
        return

    # اگر پشتیبانی باز است: هر پیام به ادمین ارسال شود
    if data["support_open"].get(str(uid)):
        try:
            bot.copy_message(ADMIN_ID, m.chat.id, m.message_id, reply_markup=ikb_support(uid))
            bot.reply_to(m, "📨 پیام به پشتیبانی ارسال شد.")
        except Exception as e:
            bot.reply_to(m, f"❌ خطا در ارسال به پشتیبانی:\n{e}")
        return

    # پیام برای هوش مصنوعی (در صورت فعال بودن و داشتن سکه)
    cu = data["users"][str(uid)]
    if not cu.get("active", True):
        bot.reply_to(m, "⏸ حالت گفتگو غیرفعال است. «روشن / خاموش 🧠» را بزن.")
        return
    if cu.get("coins", 0) <= 0:
        bot.reply_to(m, "💸 سکه شما تمام شده است. با «پشتیبانی ☎️» شارژ کن.")
        return

    # متنی → Chat
    if m.content_type == "text" and (m.text or "").strip():
        ask_text = (m.text or "").strip()
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful AI that answers in Persian."},
                    {"role": "user", "content": ask_text}
   
