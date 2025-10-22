import os
from pyrogram import Client, filters

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

# 👇 آی‌دی عددی اکانت سودو (خودت) — بعد از اجرا یک بار از @userinfobot بگیر
SUDO_USERS = [7089376754]  # عدد آی‌دی خودت رو اینجا بذار

app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

waiting_for_link = {}

def is_sudo(_, __, message):
    return message.from_user and message.from_user.id in SUDO_USERS

sudo_filter = filters.create(is_sudo)

@app.on_message(sudo_filter & filters.text & filters.regex(r"^بیا$"))
async def ask_for_link(client, message):
    waiting_for_link[message.chat.id] = message.from_user.id
    await message.reply_text("📎 لطفاً لینک گروه رو بفرست تا واردش بشم!")

@app.on_message(sudo_filter & filters.text)
async def join_when_link_sent(client, message):
    chat_id = message.chat.id
    if waiting_for_link.get(chat_id) == message.from_user.id:
        text = message.text.strip()
        if text.startswith("https://t.me/") or text.startswith("@"):
            try:
                link = text.replace("https://t.me/", "").replace("@", "")
                await client.join_chat(link)
                await message.reply_text(f"✅ با موفقیت وارد گروه [{link}](https://t.me/{link}) شدم!")
            except Exception as e:
                await message.reply_text(f"❌ خطا هنگام ورود:\n`{e}`")
            waiting_for_link.pop(chat_id)
        else:
            await message.reply_text("⚠️ لینک معتبر بفرست (مثل https://t.me/examplegroup)")

@app.on_message(sudo_filter & filters.regex(r"^برو بیرون$"))
async def leave_group(client, message):
    try:
        await client.leave_chat(message.chat.id)
    except Exception as e:
        await message.reply_text(f"خطا هنگام خروج: {e}")

print("✅ Userbot with sudo control started...")
app.run()
