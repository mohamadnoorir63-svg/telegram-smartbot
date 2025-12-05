import os
from pyrogram import Client, filters
from yt_dlp import YoutubeDL

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

DOWNLOAD_PATH = "/tmp"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

app = Client("music_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# دستور Ping
@app.on_message(filters.command("ping") & filters.private)
async def ping_handler(client, message):
    await message.reply_text("من آنلاینم ✅")

# دستور دانلود موزیک
@app.on_message(filters.command("music") & filters.private)
async def music_handler(client, message):
    if len(message.command) < 2:
        await message.reply_text("لطفاً نام آهنگ را بعد از /music وارد کنید")
        return

    query = " ".join(message.command[1:])
    await message.reply_text(f"در حال جستجو و دانلود '{query}' ... ⏳")

    ydl_opts = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "default_search": "ytsearch",
        "outtmpl": f"{DOWNLOAD_PATH}/%(title)s.%(ext)s",
        "quiet": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)
            file_path = ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".m4a", ".mp3")

        await message.reply_audio(audio=file_path, title=info.get("title", "Music"))
        os.remove(file_path)

    except Exception as e:
        await message.reply_text(f"خطا در دانلود: {e}")

app.run()
