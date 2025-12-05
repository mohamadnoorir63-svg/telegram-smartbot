import os
from pyrogram import Client, filters
from player import Player
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

app = Client("musicbot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

player = Player(app)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("سلام! ربات موزیک پلیر آماده است 🎵")

@app.on_message(filters.command("play"))
async def play(client, message):
    if len(message.command) < 2:
        await message.reply_text("لطفاً نام یا لینک موزیک را ارسال کنید!")
        return
    query = message.text.split(None, 1)[1]
    await player.play(message.chat.id, query)

@app.on_message(filters.command("stop"))
async def stop(client, message):
    await player.stop(message.chat.id)
    await message.reply_text("پخش متوقف شد ⏹️")

app.run()
