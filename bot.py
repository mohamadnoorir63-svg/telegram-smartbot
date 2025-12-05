from pyrogram import Client
import os

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
STRING_SESSION = os.getenv("STRING_SESSION")  # session string از تلگرام بگیر

app = Client(
    session_name=STRING_SESSION,
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_message(filters.command("ping") & filters.private)
async def ping(client, message):
    await message.reply_text("من آنلاینم ✅")

app.run()
