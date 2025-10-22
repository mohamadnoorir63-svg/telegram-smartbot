
import os
from pyrogram import Client, filters
import re
import random

# ---------- تنظیمات ----------
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
SUDO_USERS = [7089376754]  # آی‌دی عددی خودت

# ---------- یوزربات ----------
app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
waiting_for_links = {}

# ---------- پاسخ‌های خودکار ----------
auto_replies = [
    "سلام 👋",
    "سلام، خوبی؟ 😊",
    "درود! 🌹",
    "هستم 😎",
    "سلام! آنلاینم ✅"
]

# ---------- فیلتر سودو ----------
def is_sudo(_, __, message):
    return message.from_user and message.from_user.id in SUDO_USERS

sudo_filter = filters.create(is_sudo)

# ---------- وقتی روشن میشه ----------
@app.on_message(filters.me & filters.regex("^/start$"))
async def start_me(client, message):
    await message.reply_text("✅ یوزربات روشن و آنلاین است!")

# ---------- دستور بیا ----------
@app.on_message(sudo_filter & filters.text & filters.regex(r"^بیا$"))
async def ask_for_links(client, message):
    waiting_for_links[message.chat.id] = []
    await message.reply_text("📎 لینک‌ها رو بفرست (هر خط یک لینک)\nوقتی تموم شد بنویس: **پایان**")

# ---------- پردازش پیام‌های سودو و لینک‌ها ----------
@app.on_message(sudo_filter & filters.text)
async def handle_links(client, message):
    text = message.text.strip()
    chat_id = message.chat.id

    # حالت منتظر لینک
    if chat_id in waiting_for_links:
        if text == "پایان":
            links = waiting_for_links.pop(chat_id)
            if links:
                await message.reply_text(f"🔍 دارم {len(links)} تا لینک رو جوین می‌کنم...")
                await join_links(client, message, links)
            else:
                await message.reply_text("⚠️ هیچ لینکی دریافت نشد.")
            return

        links = extract_links(text)
        waiting_for_links[chat_id].extend(links)
        await message.reply_text(f"✅ {len(links)} لینک جدید اضافه شد.")
        return

    # حالت خودکار — هر پیام شامل لینک
    links = extract_links(text)
    if links:
        await message.reply_text(f"🔗 {len(links)} لینک شناسایی شد — دارم جوین می‌شم...")
        await join_links(client, message, links)

# ---------- پاسخ خودکار به هر پیام (از هرکسی) ----------
@app.on_message(filters.text & ~filters.me)
async def auto_reply(client, message):
    # اگر لینک داشت، خودش در بخش بالا هندل میشه — اینجا فقط چت معمولی
    if not extract_links(message.text):
        reply = random.choice(auto_replies)
        await message.reply_text(reply)

# ---------- خروج ----------
@app.on_message(sudo_filter & filters.regex(r"^برو بیرون$"))
async def leave_group(client, message):
    try:
        await client.leave_chat(message.chat.id)
        await message.reply_text("🚪 از گروه خارج شدم.")
    except Exception as e:
        await message.reply_text(f"⚠️ خطا هنگام خروج: {e}")

# ---------- استخراج لینک ----------
def extract_links(text: str):
    pattern = r"(https?://t\.me/[^\s]+|@[\w\d_]+)"
    return re.findall(pattern, text)

# ---------- جوین شدن ----------
async def join_links(client, message, links):
    joined = 0
    failed = 0
    results = []

    for link in links:
        try:
            if link.startswith("https://t.me/") or link.startswith("http://t.me/"):
                await client.join_chat(link)
            elif link.startswith("@"):
                await client.join_chat(link.replace("@", ""))
            else:
                results.append(f"⚠️ لینک نامعتبر: {link}")
                continue

            joined += 1
            results.append(f"✅ Joined → {link}")

        except Exception as e:
            failed += 1
            err = str(e)
            if "USER_ALREADY_PARTICIPANT" in err:
                results.append(f"⏭ قبلاً عضو بودم: {link}")
            else:
                results.append(f"❌ خطا برای {link}: {err}")

    summary = f"📋 نتیجه:\n" + "\n".join(results[-30:])
    await message.reply_text(f"{summary}\n\n✅ موفق: {joined} | ❌ خطا: {failed}")

# ---------- شروع ----------
print("✅ Userbot started successfully and is online.")
app.run()
