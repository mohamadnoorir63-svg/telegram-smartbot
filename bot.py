import os
import asyncio
import random
from pyrogram import Client, filters
from pyrogram.errors import FloodWait

# 🔧 تنظیمات اصلی
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

SUDO_USERS = [7089376754]  # آیدی عددی خودت
CHECK_INTERVAL = 5  # هر چند دقیقه فایل لینک چک بشه
GROUP_MESSAGE_INTERVAL = 20 * 60  # هر ۲۰ دقیقه در گروه پیام بده
LINKS_FILE = "links.txt"

# 📦 داده‌ها
joined_links = set()
saved_users = set()
waiting_for_links = {}
groups_joined = set()

# پیام‌های خودکار در گروه‌ها
auto_messages = [
    "سلام بچه‌ها 👋",
    "عه بازم کسی نیست؟ 😅",
    "سارا اومده ببینه کی آنلاینه 💫",
    "بیاین حرف بزنیم دیگه، حوصلم سر رفته 😄",
    "یه آهنگ گوش کنیم؟ 🎧",
    "بچه‌ها کسی دلش تنگ من نشده؟ 💖"
]

# 🌸 ساخت یوزربات
app = Client("sarabot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
sudo_filter = filters.user(SUDO_USERS)

# ──────── پیام شروع ────────
@app.on_message(filters.me & filters.command("start", prefixes=["/", "!", ""]))
async def start_msg(client, message):
    await message.reply_text("💖 سارا بات فعال شد و آماده‌ست 💫")

# ──────── ذخیره کاربران ────────
@app.on_message(filters.private)
async def save_user(client, message):
    user = message.from_user
    if user:
        saved_users.add(user.id)
        if message.text and "سلام" in message.text:
            await message.reply_text("سلام 🌹 خوش اومدی 🩷")

# ──────── پیام‌های خودکار گروه ────────
async def group_auto_chat():
    while True:
        try:
            for group_id in list(groups_joined):
                msg = random.choice(auto_messages)
                try:
                    await app.send_message(group_id, msg)
                    await asyncio.sleep(1)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                except Exception:
                    pass
            await asyncio.sleep(GROUP_MESSAGE_INTERVAL)
        except Exception:
            await asyncio.sleep(30)

# ──────── دستور: بیا ────────
@app.on_message(sudo_filter & filters.text & filters.regex(r"^بیا$"))
async def ask_for_links(client, message):
    waiting_for_links[message.chat.id] = True
    await message.reply_text(
        "📎 لینک‌ها رو بفرست (هر کدوم در یک خط) یا فایل txt بفرست.\n"
        "وقتی تموم شد بنویس: **پایان**"
    )

# ──────── دریافت لینک‌ها ────────
@app.on_message(sudo_filter & filters.text)
async def handle_links(client, message):
    chat_id = message.chat.id
    if not waiting_for_links.get(chat_id):
        return

    text = message.text.strip()
    if text == "پایان":
        waiting_for_links[chat_id] = False
        await message.reply_text("✅ دریافت لینک‌ها تموم شد — دارم پردازش می‌کنم...")
        return

    links = [line.strip() for line in text.splitlines() if line.strip()]
    await join_multiple(client, message, links)

# ──────── فایل txt ────────
@app.on_message(sudo_filter & filters.document)
async def handle_file(client, message):
    mime = (message.document.mime_type or "").lower()
    name = (message.document.file_name or "").lower()
    if "text" in mime or name.endswith(".txt"):
        file_path = await message.download()
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                links = [line.strip() for line in f if line.strip()]
            await join_multiple(client, message, links)
        finally:
            os.remove(file_path)
    else:
        await message.reply_text("❗ فایل txt بفرست لطفاً.")

# ──────── تابع ورود به لینک ────────
async def try_join(bot, link):
    if link.startswith(("https://t.me/joinchat/", "https://t.me/+")):
        chat = await bot.join_chat(link)
    elif link.startswith(("https://t.me/", "@")):
        username = link.replace("https://t.me/", "").replace("@", "")
        chat = await bot.join_chat(username)
    else:
        raise ValueError("لینک معتبر نیست")
    groups_joined.add(chat.id)

# ──────── جوین چند لینک ────────
async def join_multiple(client, message, links):
    results = []
    for link in links:
        if link in joined_links:
            results.append(f"⏭ قبلاً عضو بودم: {link}")
            continue
        try:
            await try_join(app, link)
            joined_links.add(link)
            results.append(f"✅ Joined: {link}")
        except Exception as e:
            results.append(f"❌ خطا برای {link}: {e}")
    await message.reply_text("\n".join(results[-30:]))

# ──────── آمار ────────
@app.on_message(sudo_filter & filters.regex(r"^آمار$"))
async def stats(client, message):
    await message.reply_text(
        f"📊 **آمار سارا بات**:\n\n"
        f"👥 کاربران ذخیره‌شده: {len(saved_users)}\n"
        f"👩‍💻 گروه‌های جوین‌شده: {len(groups_joined)}\n"
        f"🔗 لینک‌های پردازش‌شده: {len(joined_links)}"
    )

# ──────── خروج ────────
@app.on_message(sudo_filter & filters.regex(r"^برو بیرون$"))
async def leave_group(client, message):
    try:
        await client.leave_chat(message.chat.id)
        await message.reply_text("🚪 از گروه خارج شدم.")
    except Exception as e:
        await message.reply_text(f"⚠️ خطا: {e}")

# ──────── شروع و اجرای همزمان ────────
async def main():
    await app.start()
    print("💖 سارا بات فعال شد و در حال اجراست...")
    asyncio.create_task(group_auto_chat())
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
