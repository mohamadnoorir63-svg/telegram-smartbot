import os
from pyrogram import Client, filters

# اطلاعات از Config Vars هروکو گرفته می‌شن
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

# ساخت یوزربات
app = Client(name="userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# دستور "بیا"
@app.on_message(filters.me & filters.regex(r"^بیا"))
async def join_group(client, message):
    try:
        text = message.text.split(" ", 1)
        if len(text) == 1:
            await message.reply_text("❗ لطفاً لینک یا یوزرنیم گروه رو هم بنویس.\nمثال:\nبیا https://t.me/examplegroup")
            return

        link = text[1].strip()
        if link.startswith("https://t.me/"):
            link = link.replace("https://t.me/", "").replace("@", "")

        await client.join_chat(link)
        await message.reply_text(f"✅ با موفقیت وارد گروه {link} شدم!")
    except Exception as e:
        await message.reply_text(f"❌ نتونستم بیام:\n`{e}`")

# دستور "برو بیرون"
@app.on_message(filters.me & filters.regex(r"^برو بیرون"))
async def leave_group(client, message):
    try:
        await client.leave_chat(message.chat.id)
    except Exception as e:
        await message.reply_text(f"خطا هنگام خروج: {e}")

# شروع برنامه
print("✅ Userbot started successfully!")
app.run()
