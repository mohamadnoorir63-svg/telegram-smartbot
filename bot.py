from pyrogram import Client, filters
from gorghan import search_music
from player import join_and_play
import requests

app = Client("music_bot")

@app.on_message(filters.command("start"))
async def start(_, message):
    await message.reply_text("سلام! ربات موزیک پلیر آماده است 🎵")

@app.on_message(filters.command("play"))
async def play(_, message):
    query = " ".join(message.command[1:])
    results = search_music(query)
    if not results:
        await message.reply_text("موزیک پیدا نشد ❌")
        return
    
    # دانلود اولین نتیجه
    r = requests.get(results[0]["link"])
    file_path = f"temp.mp3"
    with open(file_path, "wb") as f:
        f.write(r.content)
    
    join_and_play(message.chat.id, file_path)
    await message.reply_text(f"در حال پخش: {results[0]['title']} 🎶")

@app.on_message(filters.command("stop"))
async def stop(_, message):
    vc.leave_group_call(message.chat.id)
    await message.reply_text("پخش متوقف شد ⏹️")

app.run()
