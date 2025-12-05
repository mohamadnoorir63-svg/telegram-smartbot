import os
import asyncio
from pyrogram import Client, filters
from yt_dlp import YoutubeDL

# اطلاعات ربات از محیط Heroku
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SESSION_STRING = os.getenv("SESSION_STRING")

# پوشه موقت برای دانلود فایل‌ها
DOWNLOAD_PATH = "/tmp/downloads"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

app = Client(
    name="music_bot",
    session_string=SESSION_STRING,
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workdir="/tmp"
)

# پاسخ خودکار به هر پیام برای تست آنلاین بودن
@app.on_message(filters.private & ~filters.command(["music"]))
async def online_check(client, message):
    await message.reply_text("من آنلاینم ✅")

# دانلود موزیک و ارسال
@app.on_message(filters.private & filters.text)
async def music_handler(client, message):
    query = message.text.strip()
    if not query:
        await message.reply_text("نام آهنگ را وارد کنید")
        return

    await message.reply_text(f"در حال جستجو و دانلود: {query} ... 🎵")

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
        await message.reply_text(f"خطا در دانلود موزیک: {e}")

# اجرای ربات
if __name__ == "__main__":
    asyncio.run(app.start())
    print("ربات آنلاین شد ✅")
    asyncio.get_event_loop().run_forever()
