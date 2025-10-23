from pyrogram import Client, filters
from pyrogram.types import Message
import os
import asyncio

# ======= Environment Variables =======
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
SUDO_ID = int(os.getenv("SUDO_ID"))  # ID کاربر مدیر (تو)
# =====================================

# ایجاد کلاینت Pyrogram با session string
app = Client(
    name="userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING
)

# ===============================
#     دستورات مدیریتی اصلی
# ===============================

@app.on_message(filters.command("ping") & filters.user(SUDO_ID))
async def ping(_, message: Message):
    await message.reply_text("✅ Pong! Bot is alive.")


@app.on_message(filters.command("help") & filters.user(SUDO_ID))
async def help_cmd(_, message: Message):
    text = """
🤖 **Userbot Commands**

/ping - بررسی سلامت ربات  
/help - نمایش این منو  
/pm <user_id> <message> - ارسال پیام خصوصی  
/broadcast <message> - ارسال پیام همگانی به همه چت‌ها  
/leave - خروج از گروه فعلی  
"""
    await message.reply_text(text)


@app.on_message(filters.command("pm") & filters.user(SUDO_ID))
async def pm(_, message: Message):
    try:
        parts = message.text.split(" ", 2)
        if len(parts) < 3:
            return await message.reply_text("❌ فرمت نادرست است.\nمثال:\n`/pm 123456789 سلام!`")
        user_id = int(parts[1])
        msg = parts[2]
        await app.send_message(user_id, msg)
        await message.reply_text(f"✅ پیام به `{user_id}` ارسال شد.")
    except Exception as e:
        await message.reply_text(f"⚠️ خطا:\n`{e}`")


@app.on_message(filters.command("broadcast") & filters.user(SUDO_ID))
async def broadcast(_, message: Message):
    if len(message.text.split()) < 2:
        return await message.reply_text("❌ متن پیام را وارد کنید.")
    text = message.text.split(" ", 1)[1]
    count = 0
    async for dialog in app.get_dialogs():
        try:
            await app.send_message(dialog.chat.id, text)
            count += 1
            await asyncio.sleep(0.5)
        except:
            continue
    await message.reply_text(f"📢 پیام برای {count} چت ارسال شد.")


@app.on_message(filters.command("leave") & filters.user(SUDO_ID))
async def leave_chat(_, message: Message):
    try:
        chat_id = message.chat.id
        await app.leave_chat(chat_id)
        await message.reply_text("🚪 ربات از گروه خارج شد.")
    except Exception as e:
        await message.reply_text(f"⚠️ خطا در خروج:\n`{e}`")

# ===============================
#     اجرای ربات
# ===============================
print("✅ Userbot started successfully!")
app.run()
