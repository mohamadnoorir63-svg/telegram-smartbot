import os
from pyrogram import Client, filters

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SUDO_IDS = [8588347189]

app = Client(
    "music_bot",  # اسم محلی session (فقط برای Pyrogram)
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_message(filters.command("ping") & filters.user(SUDO_IDS))
async def ping(client, message):
    await message.reply_text("من آنلاینم ✅")

app.run()
