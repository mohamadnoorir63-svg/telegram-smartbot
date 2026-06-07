import os
import json
import uuid
import time
import asyncio
from html import escape

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_USERNAME = os.getenv("BOT_USERNAME", "YourBotUsername").replace("@", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8588347189"))

DATA_DIR = "data"
WHISPER_FILE = os.path.join(DATA_DIR, "whispers.json")
STATS_FILE = os.path.join(DATA_DIR, "stats.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
CHATS_FILE = os.path.join(DATA_DIR, "chats.json")

os.makedirs(DATA_DIR, exist_ok=True)


def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def make_token():
    return uuid.uuid4().hex[:12]


def register_user(user):
    if not user:
        return
    users = load_json(USERS_FILE, {})
    users[str(user.id)] = {
        "id": user.id,
        "first_name": user.first_name,
        "username": user.username,
        "last_seen": int(time.time()),
    }
    save_json(USERS_FILE, users)


def register_chat(chat):
    if not chat:
        return
    chats = load_json(CHATS_FILE, {})
    chats[str(chat.id)] = {
        "id": chat.id,
        "title": chat.title or chat.first_name or "Unknown",
        "type": chat.type,
        "last_seen": int(time.time()),
    }
    save_json(CHATS_FILE, chats)


def save_whisper(data):
    whispers = load_json(WHISPER_FILE, {})
    whispers[data["token"]] = data
    save_json(WHISPER_FILE, whispers)


def get_whisper(token):
    return load_json(WHISPER_FILE, {}).get(token)


def update_whisper(token, data):
    whispers = load_json(WHISPER_FILE, {})
    whispers[token] = data
    save_json(WHISPER_FILE, whispers)


def delete_whisper(token):
    whispers = load_json(WHISPER_FILE, {})
    if token in whispers:
        del whispers[token]
        save_json(WHISPER_FILE, whispers)


def add_stat(user_id):
    stats = load_json(STATS_FILE, {})
    uid = str(user_id)
    stats[uid] = stats.get(uid, 0) + 1
    save_json(STATS_FILE, stats)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    register_user(update.effective_user)
    register_chat(update.effective_chat)

    await update.message.reply_text(
        "💌 ربات نجوای پیشرفته\n\n"
        "روش استفاده در گروه:\n"
        "روی پیام یک نفر ریپلای کن و بنویس:\n"
        "/w متن نجوا\n\n"
        "ناشناس:\n"
        "/wa متن نجوا\n\n"
        "یک‌بارمصرف:\n"
        "/wo متن نجوا\n\n"
        "فقط فرستنده و گیرنده می‌توانند نجوا را ببینند."
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)


async def create_whisper(update: Update, context: ContextTypes.DEFAULT_TYPE, anonymous=False, once=False):
    register_user(update.effective_user)
    register_chat(update.effective_chat)

    msg = update.message

    if not msg.reply_to_message:
        return await msg.reply_text("❗ روی پیام شخص موردنظر ریپلای کن و بعد بنویس:\n/w متن نجوا")

    if not context.args:
        return await msg.reply_text("❗ متن نجوا را بنویس.\nمثال:\n/w سلام مخفی")

    target = msg.reply_to_message.from_user
    sender = msg.from_user

    if not target:
        return await msg.reply_text("❌ گیرنده پیدا نشد.")

    if target.id == sender.id:
        return await msg.reply_text("😂 به خودت نجوا نفرست.")

    text = " ".join(context.args).strip()
    token = make_token()

    data = {
        "token": token,
        "chat_id": msg.chat.id,
        "sender_id": sender.id,
        "sender_name": sender.first_name or "Unknown",
        "sender_username": sender.username,
        "target_id": target.id,
        "target_name": target.first_name or "Unknown",
        "target_username": target.username,
        "text": text,
        "anonymous": anonymous,
        "once": once,
        "created_at": int(time.time()),
        "views": 0,
    }

    save_whisper(data)
    add_stat(sender.id)

    target_name = f"@{target.username}" if target.username else escape(target.first_name or "کاربر")
    sender_name = "ناشناس 🕵️" if anonymous else (f"@{sender.username}" if sender.username else escape(sender.first_name or "کاربر"))

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👀 مشاهده نجوا", callback_data=f"open_w:{token}")],
        [InlineKeyboardButton("➕ راهنمای ساخت نجوا", callback_data="help_make")]
    ])

    once_text = "\n💣 این نجوا یک‌بارمصرف است." if once else ""

    await msg.reply_text(
        f"💌 یک نجوا برای {target_name}\n"
        f"👤 فرستنده: {sender_name}"
        f"{once_text}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    try:
        await msg.delete()
    except Exception:
        pass


async def whisper_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await create_whisper(update, context, anonymous=False, once=False)


async def anon_whisper_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await create_whisper(update, context, anonymous=True, once=False)


async def once_whisper_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await create_whisper(update, context, anonymous=False, once=True)


async def open_whisper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    register_user(cq.from_user)

    token = cq.data.replace("open_w:", "", 1)
    whisper = get_whisper(token)

    if not whisper:
        return await cq.answer("❌ این نجوا حذف شده یا وجود ندارد.", show_alert=True)

    user_id = cq.from_user.id

    if user_id not in [whisper["target_id"], whisper["sender_id"]]:
        return await cq.answer("⛔ این نجوا برای شما نیست.", show_alert=True)

    text = whisper.get("text", "بدون متن")
    sender = "ناشناس 🕵️" if whisper.get("anonymous") else whisper.get("sender_name", "Unknown")

    if len(text) > 160:
        text = text[:160] + "..."

    whisper["views"] = whisper.get("views", 0) + 1
    update_whisper(token, whisper)

    await cq.answer(
        f"💌 نجوا:\n\n{text}\n\n👤 فرستنده: {sender}",
        show_alert=True
    )

    if whisper.get("once"):
        delete_whisper(token)


async def help_make(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer(
        "برای ساخت نجوا داخل گروه روی پیام یک نفر ریپلای کن و بنویس:\n/w متن نجوا\n\nناشناس:\n/wa متن نجوا",
        show_alert=True
    )


async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = load_json(STATS_FILE, {})
    count = stats.get(str(update.effective_user.id), 0)
    await update.message.reply_text(f"📊 تعداد نجواهای شما: {count}")


async def top_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = load_json(STATS_FILE, {})
    if not stats:
        return await update.message.reply_text("هنوز آماری ثبت نشده.")

    top = sorted(stats.items(), key=lambda x: x[1], reverse=True)[:10]

    text = "🏆 برترین نجوافرست‌ها:\n\n"
    for i, (uid, count) in enumerate(top, 1):
        text += f"{i}. <code>{uid}</code> — {count} نجوا\n"

    await update.message.reply_text(text, parse_mode="HTML")


async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 آمار کلی", callback_data="admin_stats")],
        [InlineKeyboardButton("🧹 پاکسازی نجواهای قدیمی", callback_data="admin_cleanup")],
        [InlineKeyboardButton("📣 راهنمای ارسال همگانی", callback_data="admin_broadcast_help")],
    ])

    await update.message.reply_text("👑 پنل مدیریت ربات نجوا:", reply_markup=keyboard)


async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query

    if cq.from_user.id != ADMIN_ID:
        return await cq.answer("⛔ دسترسی نداری.", show_alert=True)

    await cq.answer()

    users = load_json(USERS_FILE, {})
    chats = load_json(CHATS_FILE, {})
    whispers = load_json(WHISPER_FILE, {})
    stats = load_json(STATS_FILE, {})

    if cq.data == "admin_stats":
        total_whispers = sum(stats.values()) if stats else 0
        await cq.message.reply_text(
            "📊 آمار کلی ربات:\n\n"
            f"👤 کاربران ثبت‌شده: {len(users)}\n"
            f"🏠 چت‌ها/گروه‌ها: {len(chats)}\n"
            f"💌 نجواهای فعال: {len(whispers)}\n"
            f"✉️ کل نجواهای ساخته‌شده: {total_whispers}"
        )

    elif cq.data == "admin_cleanup":
        now = int(time.time())
        new_data = {
            k: v for k, v in whispers.items()
            if now - v.get("created_at", now) < 86400
        }
        save_json(WHISPER_FILE, new_data)
        await cq.message.reply_text("🧹 نجواهای قدیمی‌تر از ۲۴ ساعت پاک شدند.")

    elif cq.data == "admin_broadcast_help":
        await cq.message.reply_text(
            "📣 ارسال همگانی:\n\n"
            "روی یک پیام ریپلای کن و بنویس:\n"
            "/broadcast\n\n"
            "یا متن مستقیم:\n"
            "/broadcast سلام به همه"
        )


async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    users = load_json(USERS_FILE, {})
    chats = load_json(CHATS_FILE, {})

    targets = set()
    for uid in users:
        targets.add(int(uid))
    for cid in chats:
        targets.add(int(cid))

    if update.message.reply_to_message:
        source = update.message.reply_to_message
        text = source.text or source.caption or ""
    else:
        text = " ".join(context.args).strip()

    if not text:
        return await update.message.reply_text("❗ متن ارسال همگانی خالی است.")

    sent = 0
    failed = 0

    msg = await update.message.reply_text("📣 ارسال همگانی شروع شد...")

    for chat_id in targets:
        try:
            await context.bot.send_message(chat_id=chat_id, text=text)
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1

    await msg.edit_text(
        "✅ ارسال همگانی تمام شد.\n\n"
        f"📤 موفق: {sent}\n"
        f"⚠️ ناموفق: {failed}"
    )


async def cleanup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    whispers = load_json(WHISPER_FILE, {})
    now = int(time.time())
    new_data = {
        k: v for k, v in whispers.items()
        if now - v.get("created_at", now) < 86400
    }

    save_json(WHISPER_FILE, new_data)
    await update.message.reply_text("🧹 پاکسازی انجام شد.")


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN تنظیم نشده.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))

    app.add_handler(CommandHandler(["w", "whisper"], whisper_cmd))
    app.add_handler(CommandHandler(["wa", "anon"], anon_whisper_cmd))
    app.add_handler(CommandHandler(["wo", "once"], once_whisper_cmd))

    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("top", top_cmd))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CommandHandler("cleanup", cleanup_cmd))

    app.add_handler(CallbackQueryHandler(open_whisper, pattern=r"^open_w:"))
    app.add_handler(CallbackQueryHandler(help_make, pattern=r"^help_make$"))
    app.add_handler(CallbackQueryHandler(admin_buttons, pattern=r"^admin_"))

    print("✅ Whisper bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
