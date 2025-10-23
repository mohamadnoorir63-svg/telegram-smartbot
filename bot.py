import os
from pyrogram import Client, filters

# ---------- ⚙️ تنظیمات ----------
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

# عدد آی‌دی خودت (از @userinfobot بگیر)
SUDO_USERS = [7089376754]

# ---------- 📱 ساخت یوزربات ----------
app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# ---------- 🧠 متغیرهای کمکی ----------
waiting_for_links = {}

# ---------- 🎯 فیلتر فقط برای خودت ----------
def is_sudo(_, __, message):
    return message.from_user and message.from_user.id in SUDO_USERS

sudo = filters.create(is_sudo)

# ---------- 🟢 وقتی روشن شد ----------
@app.on_message(filters.outgoing & filters.text & filters.regex("^/start$"))
async def start_message(client, message):
    await message.reply_text("✅ یوزربات روشن و آماده است!")

# ---------- 🟢 دستور: بیا ----------
@app.on_message(sudo & filters.text)
async def commands(client, message):
    text = message.text.strip().lower()
    chat_id = message.chat.id

    # ✅ بیا
    if text == "بیا":
        waiting_for_links[chat_id] = []
        await message.reply_text(
            "📎 لینک‌هاتو بفرست (هر کدوم در یک خط)\nوقتی تموم شد بنویس: پایان"
        )
        return

    # ✅ پایان
    if text == "پایان" and chat_id in waiting_for_links:
        links = waiting_for_links.pop(chat_id)
        if not links:
            await message.reply_text("⚠️ هیچ لینکی دریافت نشد.")
            return
        await message.reply_text(f"🔍 دارم {len(links)} تا لینک رو بررسی می‌کنم...")
        await join_links(client, message, links)
        return

    # ✅ برو بیرون
    if text == "برو بیرون":
        try:
            await client.leave_chat(message.chat.id)
            await message.reply_text("🚪 از گروه خارج شدم.")
        except Exception as e:
            await message.reply_text(f"⚠️ خطا هنگام خروج: {e}")
        return

    # ✅ لینک‌های در حال دریافت
    if chat_id in waiting_for_links:
        new_links = [line.strip() for line in text.splitlines() if line.strip()]
        waiting_for_links[chat_id].extend(new_links)
        await message.reply_text(f"✅ {len(new_links)} لینک جدید اضافه شد.")
        return


# ---------- 🤖 جوین شدن به لینک‌ها ----------
async def join_links(client, message, links):
    joined = 0
    failed = 0
    results = []

    for link in links:
        try:
            if link.startswith("https://t.me/") or link.startswith("http://t.me/"):
                await client.join_chat(link)
            elif link.startswith("@"):
                username = link.replace("@", "")
                await client.join_chat(username)
            else:
                results.append(f"⚠️ لینک نامعتبر: {link}")
                continue

            joined += 1
            results.append(f"✅ وارد شدم → {link}")

        except Exception as e:
            failed += 1
            results.append(f"❌ خطا برای {link}: {e}")

    result_text = "\n".join(results[-20:]) or "هیچ نتیجه‌ای ثبت نشد."
    await message.reply_text(f"📋 نتیجه نهایی:\n{result_text}\n\n✅ موفق: {joined} | ❌ خطا: {failed}")

# ---------- 🚀 شروع ----------
print("✅ یوزربات فارسی با موفقیت فعال شد و در حال اجراست...")
app.run()
