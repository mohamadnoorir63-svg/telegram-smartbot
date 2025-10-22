import os
from pyrogram import Client, filters

# ---------- تنظیمات ----------
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

# آی‌دی عددی خودت
SUDO_USERS = [7089376754]  # عدد خودت رو بذار اینجا

app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

waiting_for_links = {}

# فیلتر سودو
def is_sudo(_, __, message):
    return message.from_user and message.from_user.id in SUDO_USERS

sudo_filter = filters.create(is_sudo)


# ---------- وقتی ربات روشن شد ----------
@app.on_message(filters.me & filters.regex("^/start$"))
async def start_me(client, message):
    await message.reply_text("✅ یوزربات روشن و آنلاین است!")


# ---------- دستور: بیا ----------
@app.on_message(sudo_filter & filters.text & filters.regex(r"^بیا$"))
async def ask_for_links(client, message):
    waiting_for_links[message.chat.id] = []
    await message.reply_text(
        "📎 لینک‌ها رو بفرست (هر کدوم در یک خط)\nوقتی تموم شد بنویس: **پایان**"
    )


# ---------- دریافت لینک‌ها ----------
@app.on_message(sudo_filter & filters.text)
async def handle_links(client, message):
    chat_id = message.chat.id
    text = message.text.strip()

    # اگر در حالت انتظار لینک نیست
    if chat_id not in waiting_for_links:
        return

    # پایان مرحله دریافت لینک
    if text == "پایان":
        links = waiting_for_links.pop(chat_id)
        if not links:
            await message.reply_text("⚠️ هیچ لینکی دریافت نشد.")
            return
        await message.reply_text(f"🔍 دارم {len(links)} تا لینک رو بررسی می‌کنم...")
        await join_links(client, message, links)
        return

    # اضافه کردن لینک‌ها
    new_links = [line.strip() for line in text.splitlines() if line.strip()]
    waiting_for_links[chat_id].extend(new_links)
    await message.reply_text(f"✅ {len(new_links)} لینک جدید اضافه شد.")


# ---------- جوین شدن به گروه‌ها ----------
async def join_links(client, message, links):
    joined = 0
    failed = 0
    results = []

    for link in links:
        try:
            if link.startswith("https://t.me/"):
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
            results.append(f"❌ خطا برای {link}: {e}")

    text = "\n".join(results[-30:])  # فقط آخرین ۳۰ خط
    await message.reply_text(f"📋 نتیجه نهایی:\n{text}\n\n✅ موفق: {joined} | ❌ خطا: {failed}")


# ---------- خروج از گروه ----------
@app.on_message(sudo_filter & filters.regex(r"^برو بیرون$"))
async def leave_group(client, message):
    try:
        await client.leave_chat(message.chat.id)
        await message.reply_text("🚪 از گروه خارج شدم.")
    except Exception as e:
        await message.reply_text(f"⚠️ خطا هنگام خروج: {e}")


# ---------- شروع ----------
print("✅ Userbot started successfully and is online.")
app.run()
