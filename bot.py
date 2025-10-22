from pyrogram import Client, filters
from pyrogram.errors import UserAlreadyParticipant

import os

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")  # از Pyrogram بگیر

app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

@app.on_message(filters.text)
async def join_leave_handler(client, message):
    text = message.text.lower().strip()
    chat = message.chat

    # ✅ وقتی بنویسی "بیا" → ربات جوین میشه
    if text == "بیا":
        if message.chat.username:
            link = f"https://t.me/{message.chat.username}"
        else:
            link = message.invite_link if hasattr(message, "invite_link") else None

        try:
            await client.join_chat(link or chat.id)
            await message.reply_text("✅ اومدم داخل گروه 😎")
        except UserAlreadyParticipant:
            await message.reply_text("من از قبل توی گروه بودم 😅")
        except Exception as e:
            await message.reply_text(f"❌ نتونستم بیام:\n`{e}`")

    # ❌ وقتی بنویسی "برو بیرون" → ربات لفت میده
    elif text == "برو بیرون":
        try:
            await message.reply_text("🫡 چشم، دارم میرم...")
            await client.leave_chat(chat.id)
        except Exception as e:
            await message.reply_text(f"❌ نتونستم برم:\n`{e}`")

print("✅ Userbot آماده‌ست ...")
app.run()
