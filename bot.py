import os
import json
import uuid
import time
from html import escape

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8588347189"))
BOT_USERNAME = os.getenv("BOT_USERNAME", "YourBotUsername")

DATA_DIR = "data"
WHISPER_FILE = os.path.join(DATA_DIR, "whispers.json")
STATS_FILE = os.path.join(DATA_DIR, "stats.json")

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
    args = context.args

    if args and args[0].startswith("w_"):
        token = args[0].replace("w_", "", 1)
        whisper = get_whisper(token)

        if not whisper:
            return await update.message.reply_text("❌ این نجوا حذف شده یا وجود ندارد.")

        if update.effective_user.id not in [whisper["target_id"], whisper["sender_id"]]:
            return await update.message.reply_text("⛔ این نجوا برای شما نیست.")

        text = whisper.get("text", "بدون متن")
        await update.message.reply_text(f"💌 نجوای مخفی:\n\n{text}")

        if whisper.get("once"):
            delete_whisper(token)

        return

    await update.message.reply_text(
        "💌 ربات نجوای پیشرفته\n\n"
        "در گروه روی پیام یک نفر ریپلای کن و بنویس:\n"
        "/w متن نجوا\n\n"
        "یا:\n"
        "/wa متن نجوا ناشناس\n\n"
        "فقط گیرنده می‌تواند نجوا را ببیند."
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 راهنما:\n\n"
        "روی پیام کاربر ریپلای کن:\n"
        "/w سلام مخفیانه\n"
        "/wa نجوای ناشناس\n"
        "/wo نجوای یک‌بارمصرف\n\n"
        "دستورات:\n"
        "/stats آمار شما\n"
        "/top برترین‌ها"
    )


async def create_whisper(update: Update, context: ContextTypes.DEFAULT_TYPE, anonymous=False, once=False):
    msg = update.message

    if not msg.reply_to_message:
        return await msg.reply_text("❗ روی پیام شخص موردنظر ریپلای کن و بعد نجوا بفرست.")

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

    button = InlineKeyboardMarkup([
        [InlineKeyboardButton("👀 مشاهده نجوا", callback_data=f"open_w:{token}")],
        [InlineKeyboardButton("➕ ساخت نجوا", url=f"https://t.me/{BOT_USERNAME}?start=start")]
    ])

    once_text = "\n💣 این نجوا یک‌بارمصرف است." if once else ""

    await msg.reply_text(
        f"💌 یک نجوا برای {target_name}\n"
        f"👤 فرستنده: {sender_name}"
        f"{once_text}",
        reply_markup=button,
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
    await cq.answer()

    token = cq.data.replace("open_w:", "", 1)
    whisper = get_whisper(token)

    if not whisper:
        return await cq.answer("❌ این نجوا حذف شده یا منقضی شده.", show_alert=True)

    user_id = cq.from_user.id

    if user_id not in [whisper["target_id"], whisper["sender_id"]]:
        start_link = f"https://t.me/{BOT_USERNAME}?start=w_{token}"
        return await cq.answer(
            "⛔ این نجوا برای شما نیست.",
            show_alert=True
        )

    text = whisper.get("text", "بدون متن")
    sender = "ناشناس 🕵️" if whisper.get("anonymous") else whisper.get("sender_name", "Unknown")

    whisper["views"] = whisper.get("views", 0) + 1
    update_whisper(token, whisper)

    await cq.answer(
        f"💌 نجوا:\n\n{text}\n\n👤 فرستنده: {sender}",
        show_alert=True
    )

    if whisper.get("once"):
        delete_whisper(token)


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
    await update.message.reply_text("🧹 نجواهای قدیمی پاک شدند.")


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN تنظیم نشده.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))

    app.add_handler(CommandHandler(["w", "whisper", "نجوا"], whisper_cmd))
    app.add_handler(CommandHandler(["wa", "anon", "ناشناس"], anon_whisper_cmd))
    app.add_handler(CommandHandler(["wo", "once"], once_whisper_cmd))

    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("top", top_cmd))
    app.add_handler(CommandHandler("cleanup", cleanup_cmd))

    app.add_handler(CallbackQueryHandler(open_whisper, pattern=r"^open_w:"))

    print("✅ Whisper bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
