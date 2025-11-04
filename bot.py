# ============================================================
# 🤖 BOT SYSTEM – نسخه‌ی کامل مرحله 1
# 🔒 شامل قفل‌ها (۲۵ نوع) + مدیریت ذخیره + بررسی مدیران
# ============================================================

import os, json, re, asyncio
from datetime import datetime
from telegram import Update, ChatPermissions, MessageEntity
from telegram.ext import ContextTypes

# ============================================================
# 📁 فایل‌های ذخیره‌سازی
# ============================================================

GROUP_CTRL_FILE = "group_control.json"
BACKUP_DIR = "backups"

if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

# -------------------- ذخیره و بارگذاری JSON --------------------
def _load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ خطا در بارگذاری {path}: {e}")
    return default

def _save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        bkp = os.path.join(BACKUP_DIR, f"backup_{os.path.basename(path)}")
        with open(bkp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ خطا در ذخیره {path}: {e}")

# داده‌ی اصلی گروه‌ها
group_data = _load_json(GROUP_CTRL_FILE, {})

# ============================================================
# 👑 سودوها (مدیران کل)
# ============================================================
SUDO_IDS = [8588347189]  # شناسه‌ی مدیر کل

# ============================================================
# 🔐 بررسی دسترسی مدیر / سودو
# ============================================================
async def _is_admin_or_sudo_uid(context, chat_id: int, user_id: int) -> bool:
    if user_id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except:
        return False

async def is_authorized(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return False
    if user.id in SUDO_IDS:
        return True
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status in ("administrator", "creator")
    except:
        return False

# ============================================================
# 🔒 سیستم قفل‌ها (۲۵ نوع قفل)
# ============================================================

LOCK_TYPES = {
    "links": "ارسال لینک",
    "photos": "ارسال عکس",
    "videos": "ارسال ویدیو",
    "files": "ارسال فایل",
    "voices": "ارسال ویس",
    "vmsgs": "ارسال ویدیو مسیج",
    "stickers": "ارسال استیکر",
    "gifs": "ارسال گیف",
    "media": "ارسال همه رسانه‌ها",
    "forward": "ارسال فوروارد",
    "ads": "ارسال تبلیغ/تبچی",
    "usernames": "ارسال یوزرنیم/تگ",
    "mention": "منشن با @",
    "bots": "افزودن ربات",
    "join": "ورود عضو جدید",
    "tgservices": "پیام‌های سیستمی تلگرام",
    "joinmsg": "پیام ورود",
    "arabic": "حروف عربی (غیر فارسی)",
    "english": "حروف انگلیسی",
    "text": "ارسال پیام متنی",
    "audio": "ارسال آهنگ/موسیقی",
    "emoji": "پیام فقط ایموجی",
    "caption": "ارسال کپشن",
    "edit": "ویرایش پیام",
    "reply": "ریپلای/پاسخ",
    "all": "قفل کلی"
}

# نگاشت فارسی به کلید اصلی
PERSIAN_TO_KEY = {
    "لینک": "links",
    "عکس": "photos", "تصویر": "photos",
    "ویدیو": "videos", "فیلم": "videos",
    "فایل": "files",
    "ویس": "voices",
    "ویدیو مسیج": "vmsgs", "ویدیو مسج": "vmsgs",
    "استیکر": "stickers",
    "گیف": "gifs",
    "رسانه": "media",
    "فوروارد": "forward",
    "تبچی": "ads", "تبلیغ": "ads",
    "یوزرنیم": "usernames", "تگ": "usernames",
    "منشن": "mention",
    "ربات": "bots",
    "ورود": "join",
    "سرویس": "tgservices",
    "پیام ورود": "joinmsg",
    "عربی": "arabic",
    "انگلیسی": "english",
    "متن": "text",
    "آهنگ": "audio", "موزیک": "audio",
    "ایموجی": "emoji",
    "کپشن": "caption",
    "ویرایش": "edit",
    "ریپلای": "reply",
    "کلی": "all"
}

# ------------------------------------------------------------
# 🧱 توابع کمکی قفل
# ------------------------------------------------------------
def _locks_get(chat_id: int) -> dict:
    return group_data.get(str(chat_id), {}).get("locks", {})

def _locks_set(chat_id: int, key: str, status: bool):
    cid = str(chat_id)
    g = group_data.get(cid, {})
    locks = g.get("locks", {})
    locks[key] = bool(status)
    g["locks"] = locks
    group_data[cid] = g
    _save_json(GROUP_CTRL_FILE, group_data)

# ------------------------------------------------------------
# 🔒 فعال‌سازی قفل
# ------------------------------------------------------------
async def handle_lock(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    if key not in LOCK_TYPES:
        return await update.message.reply_text("⚠️ همچین قفلی وجود ندارد.")
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")
    chat = update.effective_chat
    if _locks_get(chat.id).get(key):
        return await update.message.reply_text(f"⚠️ قفل {LOCK_TYPES[key]} از قبل فعال است.")
    _locks_set(chat.id, key, True)
    await update.message.reply_text(f"🔒 قفل <b>{LOCK_TYPES[key]}</b> فعال شد.", parse_mode="HTML")

# ------------------------------------------------------------
# 🔓 باز کردن قفل
# ------------------------------------------------------------
async def handle_unlock(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    if key not in LOCK_TYPES:
        return await update.message.reply_text("⚠️ همچین قفلی وجود ندارد.")
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")
    chat = update.effective_chat
    if not _locks_get(chat.id).get(key):
        return await update.message.reply_text(f"🔓 قفل {LOCK_TYPES[key]} از قبل باز بوده.")
    _locks_set(chat.id, key, False)
    await update.message.reply_text(f"🔓 قفل <b>{LOCK_TYPES[key]}</b> باز شد.", parse_mode="HTML")

# ------------------------------------------------------------
# 📋 نمایش وضعیت قفل‌ها
# ------------------------------------------------------------
async def handle_locks_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    locks = _locks_get(update.effective_chat.id)
    if not locks:
        return await update.message.reply_text("🔓 هیچ قفلی فعال نیست.", parse_mode="HTML")

    text = "🧱 <b>وضعیت قفل‌های گروه:</b>\n\n"
    for k, d in LOCK_TYPES.items():
        text += f"▫️ {d}: {'🔒 فعال' if locks.get(k) else '🔓 غیرفعال'}\n"
    await update.message.reply_text(text, parse_mode="HTML")

# ------------------------------------------------------------
# 🧠 پشتیبانی از فارسی «قفل لینک» و «بازکردن لینک»
# ------------------------------------------------------------
_lock_cmd_regex = re.compile(r"^(قفل|باز ?کردن)\s+(.+)$")

def _map_persian_to_key(name: str) -> str | None:
    name = name.strip()
    if name in PERSIAN_TO_KEY:
        return PERSIAN_TO_KEY[name]
    for fa, key in PERSIAN_TO_KEY.items():
        if fa in name:
            return key
    for key in LOCK_TYPES:
        if key in name:
            return key
    return None

async def handle_locks_with_alias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    tx = update.message.text.strip().lower()
    m = _lock_cmd_regex.match(tx)
    if not m:
        return
    action, rest = m.groups()
    key = _map_persian_to_key(rest)
    if not key:
        return await update.message.reply_text("⚠️ نام قفل نامعتبر است.")
    if action.startswith("قفل"):
        return await handle_lock(update, context, key)
    else:
        return await handle_unlock(update, context, key)

# ============================================================
# ✅ پایان مرحله ۱
# تا اینجا فقط قفل‌ها و سیستم ذخیره آماده شدند.
# ============================================================
# ============================================================
# 🛡️ مرحله ۲ — مدیریت قفل گروه و زمان‌بندی خودکار
# ============================================================

from datetime import datetime, time as _t

# ------------------------------------------------------------
# 🔒 قفل کامل گروه
# ------------------------------------------------------------
async def handle_lockgroup(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند گروه را قفل کنند!")

    chat = update.effective_chat
    try:
        # قفل کامل برای اعضای عادی
        await context.bot.set_chat_permissions(
            chat.id,
            ChatPermissions(can_send_messages=False)
        )

        await update.message.reply_text(
            f"🔒 <b>گروه قفل شد!</b>\n📅 {datetime.now().strftime('%H:%M - %d/%m/%Y')}\n👑 {update.effective_user.first_name}",
            parse_mode="HTML"
        )

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در قفل گروه:\n<code>{e}</code>", parse_mode="HTML")


# ------------------------------------------------------------
# 🔓 باز کردن کامل گروه
# ------------------------------------------------------------
async def handle_unlockgroup(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند گروه را باز کنند!")

    chat = update.effective_chat
    try:
        await context.bot.set_chat_permissions(
            chat.id,
            ChatPermissions(can_send_messages=True)
        )

        await update.message.reply_text(
            f"🔓 <b>گروه باز شد!</b>\n📅 {datetime.now().strftime('%H:%M - %d/%m/%Y')}\n👑 {update.effective_user.first_name}",
            parse_mode="HTML"
        )

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در بازکردن گروه:\n<code>{e}</code>", parse_mode="HTML")


# ------------------------------------------------------------
# 🕒 تنظیم قفل خودکار گروه
# مثال استفاده:
# قفل خودکار گروه 23:00 07:00
# ------------------------------------------------------------
async def handle_auto_lockgroup(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    chat_id = str(update.effective_chat.id)
    args = context.args

    if len(args) != 2:
        return await update.message.reply_text("🕒 استفاده صحیح:\n`قفل خودکار گروه 23:00 07:00`", parse_mode="HTML")

    start, end = args
    g = group_data.get(chat_id, {})
    g["auto_lock"] = {"enabled": True, "start": start, "end": end}
    group_data[chat_id] = g
    _save_json(GROUP_CTRL_FILE, group_data)

    await update.message.reply_text(
        f"✅ قفل خودکار فعال شد.\n⏰ هر روز از {start} تا {end}",
        parse_mode="HTML"
    )


# ------------------------------------------------------------
# ❌ غیرفعال کردن قفل خودکار گروه
# ------------------------------------------------------------
async def handle_disable_auto_lock(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    chat_id = str(update.effective_chat.id)
    g = group_data.get(chat_id, {})

    if "auto_lock" not in g or not g["auto_lock"].get("enabled"):
        return await update.message.reply_text("ℹ️ قفل خودکار فعال نیست.")

    g["auto_lock"]["enabled"] = False
    group_data[chat_id] = g
    _save_json(GROUP_CTRL_FILE, group_data)

    await update.message.reply_text("❌ قفل خودکار غیرفعال شد.")


# ------------------------------------------------------------
# 🧭 زمان‌بندی خودکار قفل گروه (اجرای خودکار با JobQueue)
# ------------------------------------------------------------
async def auto_group_lock_scheduler(context):
    now = datetime.now().time()
    for chat_id, data in list(group_data.items()):
        auto = data.get("auto_lock", {})
        if not auto.get("enabled"):
            continue

        try:
            s = datetime.strptime(auto["start"], "%H:%M").time()
            e = datetime.strptime(auto["end"], "%H:%M").time()
        except:
            continue

        try:
            # بررسی بازه شبانه (مثلاً 23:00 تا 07:00)
            if s > e:
                in_lock = now >= s or now <= e
            else:
                in_lock = s <= now <= e

            cid = int(chat_id)
            await context.bot.set_chat_permissions(
                cid,
                ChatPermissions(can_send_messages=not in_lock)
            )
        except Exception as ex:
            print(f"auto lock error {chat_id}: {ex}")

# ============================================================
# ✅ پایان مرحله ۲
# تا اینجا کنترل قفل کامل گروه و قفل خودکار تنظیم شد.
# ============================================================
# ============================================================
# ⚔️ مرحله ۳ — مدیریت کاربران (بن / سکوت / اخطار)
# ============================================================

# ✅ بن کردن کاربر
async def handle_ban(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند کاربر را بن کنند!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("⚠️ برای بن، باید روی پیام کاربر ریپلای کنید.")

    target = update.message.reply_to_message.from_user
    chat = update.effective_chat

    try:
        await context.bot.ban_chat_member(chat.id, target.id)
        await update.message.reply_text(f"⛔️ <b>{target.first_name}</b> از گروه بن شد.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در بن:\n<code>{e}</code>", parse_mode="HTML")


# ✅ حذف بن کاربر
async def handle_unban(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها می‌توانند آزاد کنند!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("⚠️ برای آزادسازی باید روی پیام کاربر ریپلای کنید.")

    target = update.message.reply_to_message.from_user
    chat = update.effective_chat

    try:
        await context.bot.unban_chat_member(chat.id, target.id)
        await update.message.reply_text(f"✅ <b>{target.first_name}</b> از بن خارج شد.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در حذف بن:\n<code>{e}</code>", parse_mode="HTML")


# ✅ سکوت کاربر
async def handle_mute(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("⚠️ برای سکوت باید روی پیام کاربر ریپلای کنید.")

    target = update.message.reply_to_message.from_user
    chat = update.effective_chat

    try:
        await context.bot.restrict_chat_member(
            chat.id,
            target.id,
            ChatPermissions(can_send_messages=False)
        )
        await update.message.reply_text(f"🔇 <b>{target.first_name}</b> در سکوت قرار گرفت.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در سکوت:\n<code>{e}</code>", parse_mode="HTML")


# ✅ حذف سکوت کاربر
async def handle_unmute(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("⚠️ برای حذف سکوت باید ریپلای کنید.")

    target = update.message.reply_to_message.from_user
    chat = update.effective_chat

    try:
        await context.bot.restrict_chat_member(
            chat.id,
            target.id,
            ChatPermissions(can_send_messages=True)
        )
        await update.message.reply_text(f"🔊 سکوت از <b>{target.first_name}</b> برداشته شد.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در حذف سکوت:\n<code>{e}</code>", parse_mode="HTML")


# ✅ سیستم اخطار
WARN_FILE = "warns.json"
warns_db = _load_json(WARN_FILE, {})  # {"chat_id": {"user_id": count}}

def _save_warns():
    _save_json(WARN_FILE, warns_db)

async def handle_warn(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("⚠️ برای اخطار باید روی پیام کاربر ریپلای کنید.")

    target = update.message.reply_to_message.from_user
    chat_id = str(update.effective_chat.id)
    uid = str(target.id)

    warns_db.setdefault(chat_id, {})
    warns_db[chat_id][uid] = warns_db[chat_id].get(uid, 0) + 1
    _save_warns()

    count = warns_db[chat_id][uid]
    await update.message.reply_text(f"⚠️ به <b>{target.first_name}</b> اخطار داده شد. (تعداد: {count})", parse_mode="HTML")

    # سه اخطار → سکوت
    if count >= 3:
        try:
            await context.bot.restrict_chat_member(
                int(chat_id), target.id,
                ChatPermissions(can_send_messages=False)
            )
            await update.message.reply_text(f"🚫 <b>{target.first_name}</b> به‌دلیل ۳ اخطار در سکوت قرار گرفت.", parse_mode="HTML")
        except Exception as e:
            await update.message.reply_text(f"⚠️ خطا در اعمال سکوت:\n<code>{e}</code>", parse_mode="HTML")

async def handle_unwarn(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("⚠️ باید روی پیام کاربر ریپلای کنید.")

    target = update.message.reply_to_message.from_user
    chat_id = str(update.effective_chat.id)
    uid = str(target.id)

    if warns_db.get(chat_id, {}).get(uid, 0) == 0:
        return await update.message.reply_text("ℹ️ این کاربر هیچ اخطاری ندارد.")

    warns_db[chat_id][uid] = max(0, warns_db[chat_id][uid] - 1)
    _save_warns()
    await update.message.reply_text(f"✅ یک اخطار از <b>{target.first_name}</b> حذف شد.", parse_mode="HTML")

async def handle_list_warns(update, context):
    chat_id = str(update.effective_chat.id)
    warns = warns_db.get(chat_id, {})
    if not warns:
        return await update.message.reply_text("ℹ️ هیچ کاربری اخطار ندارد.")

    text = "⚠️ <b>لیست اخطارها:</b>\n"
    for uid, count in warns.items():
        text += f"• <a href='tg://user?id={uid}'>کاربر {uid}</a> → {count} اخطار\n"

    await update.message.reply_text(text, parse_mode="HTML")

# ============================================================
# ✅ پایان مرحله ۳
# تا اینجا مدیریت کامل کاربران ساخته شد.
# ============================================================
# ============================================================
# 💎 مرحله ۴ — لقب‌ها (Nicknames) و اصل‌ها (Origins)
# ============================================================

# فایل‌های ذخیره
NICKS_FILE = "nicks.json"
ORIGINS_FILE = "origins.json"

nicks_db = _load_json(NICKS_FILE, {})       # {"chat_id": {"user_id": "nickname"}}
origins_db = _load_json(ORIGINS_FILE, {})   # {"chat_id": {"origins": {user_id: "origin"}}}

# ----------------------------- لقب‌ها -----------------------------

async def handle_set_nick(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    if len(context.args) < 1 or not update.message.reply_to_message:
        return await update.message.reply_text("⚠️ استفاده:\n`ثبت لقب <لقب>` (روی پیام کاربر ریپلای کنید)", parse_mode="HTML")

    target = update.message.reply_to_message.from_user
    chat_id = str(update.effective_chat.id)
    nickname = " ".join(context.args)

    nicks_db.setdefault(chat_id, {})
    nicks_db[chat_id][str(target.id)] = nickname
    _save_json(NICKS_FILE, nicks_db)

    await update.message.reply_text(f"✅ لقب <b>{nickname}</b> برای <b>{target.first_name}</b> ثبت شد.", parse_mode="HTML")


async def handle_show_nick(update, context):
    user = update.effective_user
    chat_id = str(update.effective_chat.id)
    nick = nicks_db.get(chat_id, {}).get(str(user.id))
    if not nick:
        return await update.message.reply_text("ℹ️ شما هیچ لقبی ثبت نکرده‌اید.")
    await update.message.reply_text(f"🏷️ لقب شما: <b>{nick}</b>", parse_mode="HTML")


async def handle_del_nick(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("⚠️ برای حذف لقب باید روی پیام کاربر ریپلای کنید.")

    target = update.message.reply_to_message.from_user
    chat_id = str(update.effective_chat.id)

    if str(target.id) not in nicks_db.get(chat_id, {}):
        return await update.message.reply_text("ℹ️ این کاربر لقبی ندارد.")

    del nicks_db[chat_id][str(target.id)]
    _save_json(NICKS_FILE, nicks_db)
    await update.message.reply_text(f"❌ لقب <b>{target.first_name}</b> حذف شد.", parse_mode="HTML")


async def handle_list_nicks(update, context):
    chat_id = str(update.effective_chat.id)
    nicks = nicks_db.get(chat_id, {})
    if not nicks:
        return await update.message.reply_text("ℹ️ هیچ لقبی در این گروه ثبت نشده.")
    text = "🏷️ <b>لیست لقب‌های گروه:</b>\n\n"
    for uid, name in nicks.items():
        text += f"• <a href='tg://user?id={uid}'>{name}</a>\n"
    await update.message.reply_text(text, parse_mode="HTML")

# ----------------------------- اصل‌ها -----------------------------

async def handle_set_origin(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    if len(context.args) < 1 or not update.message.reply_to_message:
        return await update.message.reply_text("⚠️ استفاده:\n`ثبت اصل <متن>` (روی پیام کاربر ریپلای کنید)", parse_mode="HTML")

    target = update.message.reply_to_message.from_user
    chat_id = str(update.effective_chat.id)
    origin = " ".join(context.args)

    origins_db.setdefault(chat_id, {}).setdefault("origins", {})
    origins_db[chat_id]["origins"][str(target.id)] = origin
    _save_json(ORIGINS_FILE, origins_db)

    await update.message.reply_text(f"✅ اصل <b>{origin}</b> برای <b>{target.first_name}</b> ثبت شد.", parse_mode="HTML")


async def handle_show_origin(update, context):
    user = update.effective_user
    chat_id = str(update.effective_chat.id)
    user_origin = origins_db.get(chat_id, {}).get("origins", {}).get(str(user.id))
    if not user_origin:
        return await update.message.reply_text("ℹ️ شما هیچ اصلی ثبت نکرده‌اید.")
    await update.message.reply_text(f"🌿 اصل شما: <b>{user_origin}</b>", parse_mode="HTML")


async def handle_del_origin(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("⚠️ برای حذف اصل باید ریپلای کنید.")

    target = update.message.reply_to_message.from_user
    chat_id = str(update.effective_chat.id)

    if str(target.id) not in origins_db.get(chat_id, {}).get("origins", {}):
        return await update.message.reply_text("ℹ️ این کاربر اصلی ثبت نکرده.")

    del origins_db[chat_id]["origins"][str(target.id)]
    _save_json(ORIGINS_FILE, origins_db)
    await update.message.reply_text(f"❌ اصل <b>{target.first_name}</b> حذف شد.", parse_mode="HTML")


async def handle_list_origins(update, context):
    chat_id = str(update.effective_chat.id)
    origins = origins_db.get(chat_id, {}).get("origins", {})
    if not origins:
        return await update.message.reply_text("ℹ️ هیچ اصلی در گروه ثبت نشده.")
    text = "🌿 <b>لیست اصل‌های گروه:</b>\n\n"
    for uid, val in origins.items():
        text += f"• <a href='tg://user?id={uid}'>{val}</a>\n"
    await update.message.reply_text(text, parse_mode="HTML")

# ============================================================
# ✅ پایان مرحله ۴
# لقب‌ها و اصل‌ها کامل شد.
# ============================================================
# ============================================================
# 🧠 مرحله ۵ — مدیران، سودوها و فیلتر کلمات
# ============================================================

# فایل‌ها
ADMINS_FILE = "admins.json"
SUDOS_FILE = "sudos.json"
FILTER_FILE = "filters.json"

admins_db = _load_json(ADMINS_FILE, {})   # {"chat_id": [uid, uid, ...]}
sudos_db = _load_json(SUDOS_FILE, {"8588347189": True})  # پیش‌فرض سودو اصلی
filters_db = _load_json(FILTER_FILE, {})  # {"chat_id": ["کلمه۱", "کلمه۲", ...]}


# ============================================================
# 👑 مدیران گروه
# ============================================================

async def handle_addadmin(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("⚠️ باید روی پیام کاربر ریپلای کنید.")

    target = update.message.reply_to_message.from_user
    chat_id = str(update.effective_chat.id)

    admins_db.setdefault(chat_id, [])
    if str(target.id) in admins_db[chat_id]:
        return await update.message.reply_text("ℹ️ این کاربر از قبل مدیر است.")

    admins_db[chat_id].append(str(target.id))
    _save_json(ADMINS_FILE, admins_db)
    await update.message.reply_text(f"👑 {target.first_name} به مدیران اضافه شد.", parse_mode="HTML")


async def handle_removeadmin(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("⚠️ باید روی پیام کاربر ریپلای کنید.")

    target = update.message.reply_to_message.from_user
    chat_id = str(update.effective_chat.id)

    if str(target.id) not in admins_db.get(chat_id, []):
        return await update.message.reply_text("ℹ️ این کاربر مدیر نیست.")

    admins_db[chat_id].remove(str(target.id))
    _save_json(ADMINS_FILE, admins_db)
    await update.message.reply_text(f"❌ {target.first_name} از مدیران حذف شد.", parse_mode="HTML")


async def handle_admins(update, context):
    chat_id = str(update.effective_chat.id)
    admins = admins_db.get(chat_id, [])
    if not admins:
        return await update.message.reply_text("ℹ️ هیچ مدیری در این گروه ثبت نشده.")
    text = "👑 <b>مدیران گروه:</b>\n\n"
    for uid in admins:
        text += f"• <a href='tg://user?id={uid}'>مدیر</a>\n"
    await update.message.reply_text(text, parse_mode="HTML")


async def handle_clearadmins(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    chat_id = str(update.effective_chat.id)
    if chat_id not in admins_db or not admins_db[chat_id]:
        return await update.message.reply_text("ℹ️ لیست مدیران خالی است.")
    admins_db[chat_id] = []
    _save_json(ADMINS_FILE, admins_db)
    await update.message.reply_text("🧹 تمام مدیران پاک شدند.")


# ============================================================
# 🧑‍💻 مدیریت سودوها (دسترسی کل ربات)
# ============================================================

async def handle_addsudo(update, context):
    user = update.effective_user
    if user.id != 8588347189:  # فقط سودوی اصلی می‌تواند
        return await update.message.reply_text("🚫 فقط سودوی اصلی مجاز است!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("⚠️ باید روی پیام کاربر ریپلای کنید.")

    target = update.message.reply_to_message.from_user
    sudos_db[str(target.id)] = True
    _save_json(SUDOS_FILE, sudos_db)
    await update.message.reply_text(f"🧠 {target.first_name} به سودوها اضافه شد.", parse_mode="HTML")


async def handle_delsudo(update, context):
    user = update.effective_user
    if user.id != 8588347189:
        return await update.message.reply_text("🚫 فقط سودوی اصلی مجاز است!")

    if not update.message.reply_to_message:
        return await update.message.reply_text("⚠️ باید روی پیام کاربر ریپلای کنید.")

    target = update.message.reply_to_message.from_user
    if str(target.id) not in sudos_db:
        return await update.message.reply_text("ℹ️ این کاربر سودو نیست.")

    del sudos_db[str(target.id)]
    _save_json(SUDOS_FILE, sudos_db)
    await update.message.reply_text(f"❌ {target.first_name} از سودوها حذف شد.", parse_mode="HTML")


async def handle_listsudos(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    if not sudos_db:
        return await update.message.reply_text("ℹ️ هیچ سودویی ثبت نشده.")

    text = "🧠 <b>سودوهای ربات:</b>\n\n"
    for uid in sudos_db.keys():
        text += f"• <a href='tg://user?id={uid}'>سودو</a>\n"
    await update.message.reply_text(text, parse_mode="HTML")


# ============================================================
# 🚫 فیلتر کلمات (کلمات ممنوعه در گروه)
# ============================================================

async def handle_addfilter(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    if len(context.args) < 1:
        return await update.message.reply_text("⚠️ استفاده:\n`افزودن فیلتر <کلمه>`", parse_mode="HTML")

    chat_id = str(update.effective_chat.id)
    word = " ".join(context.args).lower()

    filters_db.setdefault(chat_id, [])
    if word in filters_db[chat_id]:
        return await update.message.reply_text("ℹ️ این کلمه از قبل فیلتر است.")

    filters_db[chat_id].append(word)
    _save_json(FILTER_FILE, filters_db)
    await update.message.reply_text(f"🚫 کلمه <b>{word}</b> به فیلترها اضافه شد.", parse_mode="HTML")


async def handle_delfilter(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    if len(context.args) < 1:
        return await update.message.reply_text("⚠️ استفاده:\n`حذف فیلتر <کلمه>`", parse_mode="HTML")

    chat_id = str(update.effective_chat.id)
    word = " ".join(context.args).lower()

    if word not in filters_db.get(chat_id, []):
        return await update.message.reply_text("ℹ️ چنین کلمه‌ای در فیلتر نیست.")

    filters_db[chat_id].remove(word)
    _save_json(FILTER_FILE, filters_db)
    await update.message.reply_text(f"✅ کلمه <b>{word}</b> از فیلترها حذف شد.", parse_mode="HTML")


async def handle_filters(update, context):
    chat_id = str(update.effective_chat.id)
    words = filters_db.get(chat_id, [])
    if not words:
        return await update.message.reply_text("ℹ️ هیچ کلمه‌ای فیلتر نشده.")
    text = "🚫 <b>لیست کلمات فیلترشده:</b>\n\n" + "\n".join(f"• {w}" for w in words)
    await update.message.reply_text(text, parse_mode="HTML")

# ============================================================
# ✅ پایان مرحله ۵
# مدیریت مدیران، سودوها و فیلتر کلمات تکمیل شد.
# ============================================================
# ============================================================
# 🎛️ مرحله ۶ — پنل، خوش‌آمدگویی و تگ کاربران
# ============================================================

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

WELCOME_FILE = "welcome.json"
welcome_db = _load_json(WELCOME_FILE, {})  # {"chat_id": "message text"}


# 🟢 تنظیم پیام خوش‌آمد (فقط مدیر یا سودو)
async def handle_set_welcome(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    if len(context.args) < 1:
        return await update.message.reply_text("⚠️ استفاده:\n`تنظیم خوشامد [متن]`", parse_mode="HTML")

    chat_id = str(update.effective_chat.id)
    text = " ".join(context.args)

    welcome_db[chat_id] = text
    _save_json(WELCOME_FILE, welcome_db)
    await update.message.reply_text("✅ پیام خوش‌آمد ثبت شد.")


# 🟡 حذف پیام خوش‌آمد
async def handle_del_welcome(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    chat_id = str(update.effective_chat.id)
    if chat_id not in welcome_db:
        return await update.message.reply_text("ℹ️ هیچ پیام خوش‌آمدی تنظیم نشده.")
    del welcome_db[chat_id]
    _save_json(WELCOME_FILE, welcome_db)
    await update.message.reply_text("❌ پیام خوش‌آمد حذف شد.")


# 🟢 اجرای پیام خوش‌آمد هنگام ورود عضو جدید
async def handle_new_member(update, context):
    msg = update.message
    chat_id = str(msg.chat.id)
    if not msg.new_chat_members:
        return
    text = welcome_db.get(chat_id, "🎉 خوش آمدی {name} 🌿")
    for member in msg.new_chat_members:
        try:
            formatted = text.replace("{name}", member.first_name)
            await msg.reply_text(formatted, parse_mode="HTML")
        except:
            pass


# 🧾 نمایش پنل وضعیت گروه
async def handle_panel(update, context):
    if not await is_authorized(update, context):
        return await update.message.reply_text("🚫 فقط مدیران یا سودوها مجازند!")

    chat = update.effective_chat
    locks = _locks_get(chat.id)
    lock_count = sum(1 for k, v in locks.items() if v)
    total = len(LOCK_TYPES)

    text = (
        f"📊 <b>پنل مدیریت گروه</b>\n\n"
        f"👥 گروه: {chat.title}\n"
        f"🔒 قفل‌های فعال: {lock_count}/{total}\n"
        f"🧹 مدیران: {len(admins_db.get(str(chat.id), []))}\n"
        f"🧠 سودوها: {len(sudos_db)}\n"
        f"🚫 فیلترها: {len(filters_db.get(str(chat.id), []))}\n\n"
        f"📘 برای مشاهده لیست قفل‌ها بنویس: وضعیت قفل"
    )

    buttons = [
        [InlineKeyboardButton("🧱 وضعیت قفل‌ها", callback_data="locks")],
        [InlineKeyboardButton("📋 فیلترها", callback_data="filters")],
        [InlineKeyboardButton("👑 مدیران", callback_data="admins")],
    ]
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(buttons))


# 🧩 هندلر دکمه‌ها
async def handle_callback(update, context):
    query = update.callback_query
    data = query.data
    chat_id = query.message.chat_id
    await query.answer()

    if data == "locks":
        locks = _locks_get(chat_id)
        txt = "🧱 <b>وضعیت قفل‌ها:</b>\n\n"
        for k, name in LOCK_TYPES.items():
            txt += f"• {name}: {'🔒 فعال' if locks.get(k) else '🔓 آزاد'}\n"
        await query.edit_message_text(txt, parse_mode="HTML")

    elif data == "filters":
        lst = filters_db.get(str(chat_id), [])
        if not lst:
            return await query.edit_message_text("ℹ️ هیچ کلمه‌ای فیلتر نشده.")
        await query.edit_message_text("🚫 <b>فیلترها:</b>\n\n" + "\n".join(lst), parse_mode="HTML")

    elif data == "admins":
        lst = admins_db.get(str(chat_id), [])
        if not lst:
            return await query.edit_message_text("ℹ️ هیچ مدیری ثبت نشده.")
        txt = "👑 <b>مدیران:</b>\n" + "\n".join([f"• <a href='tg://user?id={uid}'>مدیر</a>" for uid in lst])
        await query.edit_message_text(txt, parse_mode="HTML")
        # ============================================================
# ⚙️ تابع مدیریت دستورات فارسی گروه
# ============================================================

async def group_command_handler(update, context):
    """تمام دستورات فارسی را به توابع مربوطه وصل می‌کند."""
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip().lower()

    # قفل کامل گروه
    if text.startswith("قفل گروه"):
        return await handle_lockgroup(update, context)
    elif text.startswith("باز کردن گروه") or text.startswith("بازکردن گروه"):
        return await handle_unlockgroup(update, context)

    # قفل خودکار
    elif text.startswith("قفل خودکار گروه"):
        return await handle_auto_lockgroup(update, context)
    elif text.startswith("غیرفعال قفل خودکار") or text.startswith("لغو قفل خودکار"):
        return await handle_disable_auto_lock(update, context)

    # مدیریت کاربران
    elif text.startswith("بن "):
        return await handle_ban(update, context)
    elif text.startswith("آزاد "):
        return await handle_unban(update, context)
    elif text.startswith("سکوت "):
        return await handle_mute(update, context)
    elif text.startswith("حذف سکوت"):
        return await handle_unmute(update, context)

    elif text.startswith("اخطار"):
        return await handle_warn(update, context)
    elif text.startswith("حذف اخطار"):
        return await handle_unwarn(update, context)
    elif text.startswith("اخطارها"):
        return await handle_list_warns(update, context)

    # لقب و اصل
    elif text.startswith("ثبت لقب"):
        return await handle_set_nick(update, context)
    elif text.startswith("لقب من"):
        return await handle_show_nick(update, context)
    elif text.startswith("حذف لقب"):
        return await handle_del_nick(update, context)
    elif text.startswith("لیست لقب"):
        return await handle_list_nicks(update, context)

    elif text.startswith("ثبت اصل"):
        return await handle_set_origin(update, context)
    elif text.startswith("اصل من"):
        return await handle_show_origin(update, context)
    elif text.startswith("حذف اصل"):
        return await handle_del_origin(update, context)
    elif text.startswith("لیست اصل"):
        return await handle_list_origins(update, context)

    # فیلترها
    elif text.startswith("افزودن فیلتر"):
        return await handle_addfilter(update, context)
    elif text.startswith("حذف فیلتر"):
        return await handle_delfilter(update, context)
    elif text.startswith("فیلترها"):
        return await handle_filters(update, context)

    # مدیران
    elif text.startswith("افزودن مدیر"):
        return await handle_addadmin(update, context)
    elif text.startswith("حذف مدیر"):
        return await handle_removeadmin(update, context)
    elif text.startswith("مدیران"):
        return await handle_admins(update, context)
    elif text.startswith("پاکسازی مدیران"):
        return await handle_clearadmins(update, context)

    # سودو
    elif text.startswith("افزودن سودو"):
        return await handle_addsudo(update, context)
    elif text.startswith("حذف سودو"):
        return await handle_delsudo(update, context)
    elif text.startswith("سودوها"):
        return await handle_listsudos(update, context)

    # خوشامد
    elif text.startswith("تنظیم خوشامد"):
        return await handle_set_welcome(update, context)
    elif text.startswith("حذف خوشامد"):
        return await handle_del_welcome(update, context)

    # پنل
    elif text.startswith("پنل"):
        return await handle_panel(update, context)
        # ============================================================
# 🚫 بررسی پیام‌ها با قفل‌ها و فیلترها
# ============================================================

async def check_message_locks(update, context):
    """بررسی همه پیام‌ها برای تشخیص نقض قفل‌ها و فیلترها"""
    msg = update.message
    if not msg or not msg.chat or not msg.from_user:
        return

    chat_id = str(msg.chat.id)
    user = msg.from_user

    # اجازه برای مدیران و سودوها
    if await _is_admin_or_sudo_uid(context, msg.chat.id, user.id):
        return

    locks = _locks_get(msg.chat.id)
    filters_list = filters_db.get(chat_id, [])

    # --------------------------------------------
    # 🔤 بررسی فیلتر کلمات
    # --------------------------------------------
    if msg.text:
        text_lower = msg.text.lower()
        for word in filters_list:
            if word in text_lower:
                try:
                    await msg.delete()
                    await context.bot.send_message(
                        chat_id,
                        f"🚫 پیام <b>{user.first_name}</b> به‌دلیل استفاده از کلمهٔ فیلترشده حذف شد.",
                        parse_mode="HTML",
                    )
                    return
                except:
                    return

    # --------------------------------------------
    # 🧱 بررسی انواع قفل‌ها
    # --------------------------------------------
    for key, active in locks.items():
        if not active:
            continue

        try:
            # قفل لینک‌ها
            if key == "links" and msg.entities:
                for e in msg.entities:
                    if e.type in ["url", "text_link"]:
                        await msg.delete()
                        return

            # قفل عکس
            elif key == "photos" and msg.photo:
                await msg.delete()
                return

            # قفل ویدیو
            elif key == "videos" and msg.video:
                await msg.delete()
                return

            # قفل فایل‌ها
            elif key == "files" and msg.document:
                await msg.delete()
                return

            # قفل ویس
            elif key == "voices" and msg.voice:
                await msg.delete()
                return

            # قفل ویدیو مسیج
            elif key == "vmsgs" and msg.video_note:
                await msg.delete()
                return

            # قفل استیکر
            elif key == "stickers" and msg.sticker:
                await msg.delete()
                return

            # قفل گیف
            elif key == "gifs" and msg.animation:
                await msg.delete()
                return

            # قفل فوروارد
            elif key == "forward" and msg.forward_date:
                await msg.delete()
                return

            # قفل تبلیغات (تشخیص با لینک + کلمه تبلیغ)
            elif key == "ads" and msg.text and any(x in msg.text.lower() for x in ["join", "channel", "تبچی", "تبلیغ"]):
                await msg.delete()
                return

            # قفل یوزرنیم/تگ
            elif key == "usernames" and msg.text and "@" in msg.text:
                await msg.delete()
                return

            # قفل عربی
            elif key == "arabic" and msg.text and re.search(r"[\u0600-\u06FF]", msg.text):
                await msg.delete()
                return

            # قفل انگلیسی
            elif key == "english" and msg.text and re.search(r"[a-zA-Z]", msg.text):
                await msg.delete()
                return

            # قفل ایموجی (پیام‌هایی که فقط شامل ایموجی هستند)
            elif key == "emoji" and msg.text and re.fullmatch(r"[\U0001F600-\U0001F64F\s]+", msg.text):
                await msg.delete()
                return

            # قفل کپشن
            elif key == "caption" and getattr(msg, "caption", None):
                await msg.delete()
                return

            # قفل ویرایش
            elif key == "edit" and msg.edit_date:
                await msg.delete()
                return

            # قفل ریپلای
            elif key == "reply" and msg.reply_to_message:
                await msg.delete()
                return

            # قفل کلی (حذف هر نوع پیام)
            elif key == "all":
                await msg.delete()
                return

        except Exception as e:
            print(f"lock check error: {e}")
            return
            
# ============================================================
# ⚙️ تابع مدیریت دستورات فارسی گروه
# ============================================================

async def group_command_handler(update, context):
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip().lower()

    # قفل کامل گروه
    if text.startswith("قفل گروه"):
        return await handle_lockgroup(update, context)
    elif text.startswith("باز کردن گروه") or text.startswith("بازکردن گروه"):
        return await handle_unlockgroup(update, context)

    # قفل خودکار
    elif text.startswith("قفل خودکار گروه"):
        return await handle_auto_lockgroup(update, context)
    elif text.startswith("غیرفعال قفل خودکار") or text.startswith("لغو قفل خودکار"):
        return await handle_disable_auto_lock(update, context)

    # مدیریت کاربران
    elif text.startswith("بن"):
        return await handle_ban(update, context)
    elif text.startswith("آزاد"):
        return await handle_unban(update, context)
    elif text.startswith("سکوت"):
        return await handle_mute(update, context)
    elif text.startswith("حذف سکوت"):
        return await handle_unmute(update, context)
    elif text.startswith("اخطار"):
        return await handle_warn(update, context)
    elif text.startswith("حذف اخطار"):
        return await handle_unwarn(update, context)
    elif text.startswith("اخطارها"):
        return await handle_list_warns(update, context)

    # لقب و اصل
    elif text.startswith("ثبت لقب"):
        return await handle_set_nick(update, context)
    elif text.startswith("لقب من"):
        return await handle_show_nick(update, context)
    elif text.startswith("حذف لقب"):
        return await handle_del_nick(update, context)
    elif text.startswith("لیست لقب"):
        return await handle_list_nicks(update, context)
    elif text.startswith("ثبت اصل"):
        return await handle_set_origin(update, context)
    elif text.startswith("اصل من"):
        return await handle_show_origin(update, context)
    elif text.startswith("حذف اصل"):
        return await handle_del_origin(update, context)
    elif text.startswith("لیست اصل"):
        return await handle_list_origins(update, context)

    # فیلتر کلمات
    elif text.startswith("افزودن فیلتر"):
        return await handle_addfilter(update, context)
    elif text.startswith("حذف فیلتر"):
        return await handle_delfilter(update, context)
    elif text.startswith("فیلترها"):
        return await handle_filters(update, context)

    # مدیران و سودوها
    elif text.startswith("افزودن مدیر"):
        return await handle_addadmin(update, context)
    elif text.startswith("حذف مدیر"):
        return await handle_removeadmin(update, context)
    elif text.startswith("مدیران"):
        return await handle_admins(update, context)
    elif text.startswith("پاکسازی مدیران"):
        return await handle_clearadmins(update, context)
    elif text.startswith("افزودن سودو"):
        return await handle_addsudo(update, context)
    elif text.startswith("حذف سودو"):
        return await handle_delsudo(update, context)
    elif text.startswith("سودوها"):
        return await handle_listsudos(update, context)

    # خوش‌آمد
    elif text.startswith("تنظیم خوشامد"):
        return await handle_set_welcome(update, context)
    elif text.startswith("حذف خوشامد"):
        return await handle_del_welcome(update, context)

    # پنل
    elif text.startswith("پنل"):
        return await handle_panel(update, context)
        # ============================================================
# 🚫 بررسی پیام‌ها با قفل‌ها و فیلترها
# ============================================================

async def check_message_locks(update, context):
    msg = update.message
    if not msg or not msg.chat or not msg.from_user:
        return

    chat_id = str(msg.chat.id)
    user = msg.from_user

    # مدیران و سودوها مستثنی‌اند
    if await _is_admin_or_sudo_uid(context, msg.chat.id, user.id):
        return

    locks = _locks_get(msg.chat.id)
    filters_list = filters_db.get(chat_id, [])

    # --- فیلتر کلمات ---
    if msg.text:
        text_lower = msg.text.lower()
        for word in filters_list:
            if word in text_lower:
                try:
                    await msg.delete()
                    await context.bot.send_message(
                        chat_id,
                        f"🚫 پیام {user.first_name} به‌دلیل استفاده از کلمه‌ی فیلترشده حذف شد."
                    )
                    return
                except:
                    return

    # --- بررسی انواع قفل ---
    for key, active in locks.items():
        if not active:
            continue
        try:
            if key == "links" and msg.entities:
                for e in msg.entities:
                    if e.type in ["url", "text_link"]:
                        await msg.delete()
                        return
            elif key == "photos" and msg.photo:
                await msg.delete(); return
            elif key == "videos" and msg.video:
                await msg.delete(); return
            elif key == "files" and msg.document:
                await msg.delete(); return
            elif key == "stickers" and msg.sticker:
                await msg.delete(); return
            elif key == "gifs" and msg.animation:
                await msg.delete(); return
            elif key == "voices" and msg.voice:
                await msg.delete(); return
            elif key == "vmsgs" and msg.video_note:
                await msg.delete(); return
            elif key == "forward" and msg.forward_date:
                await msg.delete(); return
            elif key == "arabic" and msg.text and re.search(r"[\u0600-\u06FF]", msg.text):
                await msg.delete(); return
            elif key == "english" and msg.text and re.search(r"[a-zA-Z]", msg.text):
                await msg.delete(); return
            elif key == "emoji" and msg.text and re.fullmatch(r"[\U0001F600-\U0001F64F\s]+", msg.text):
                await msg.delete(); return
            elif key == "all":
                await msg.delete(); return
        except Exception as e:
            print(f"lock check error: {e}")
            return
# ============================================================
# ✅ پایان مرحله ۶
# پنل + خوش‌آمد + دکمه‌های کنترلی کامل شد.
# ============================================================
# ============================================================
# 🚀 مرحله ۷ — اجرای نهایی ربات
# ============================================================

from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    filters,
)

# توکن ربات (از @BotFather بگیر)
BOT_TOKEN = "8465442140:AAHdWrgiTtMl_WuoAdPfEnPFoKfAyxJyNNg"

# ساخت اپلیکیشن
app = ApplicationBuilder().token(BOT_TOKEN).build()

# ============================================================
# 📌 ثبت همه‌ی هندلرها
# ============================================================

# --- خوش‌آمد و رویدادها ---
app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_member))

# --- دستورات اصلی فارسی (بن، سکوت، قفل گروه، اخطار، لقب و...) ---
app.add_handler(MessageHandler(filters.TEXT, group_command_handler))

# --- قفل‌ها (فقط "قفل لینک" و "بازکردن لینک" و امثال آن) ---
app.add_handler(MessageHandler(filters.Regex(r"^(قفل|باز ?کردن)\s+"), handle_locks_with_alias))

# --- پنل و دکمه‌ها ---
app.add_handler(MessageHandler(filters.Regex("^پنل$"), handle_panel))
app.add_handler(CallbackQueryHandler(handle_callback))

# --- بررسی قفل‌ها و فیلترها روی پیام‌ها ---
app.add_handler(MessageHandler(filters.ALL, check_message_locks))
 

# ============================================================
# 🎯 شروع اجرای ربات
# ============================================================

if __name__ == "__main__":
    print("🤖 Bot is running... Made by NoorBotSystem")
    app.run_polling()
