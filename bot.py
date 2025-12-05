from pyrogram import Client, filters
import os

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
STRING_SESSION = os.getenv("STRING_SESSION")  # رشته session از تلگرام

app = Client(
    session=STRING_SESSION,  # <-- اینجا به جای session_name
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_message(filters.command("ping") & filters.private)
async def ping(client, message):
    await message.reply_text("من آنلاینم ✅")

app.run()
