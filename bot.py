import os
import yt_dlp
from pyrogram import Client, filters

# ---------- تنظیمات ----------
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH"))
SESSION_STRING = os.getenv("SESSION_STRING")

# ساخت یوزربات
app = Client("music_userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# ---------- تابع دانلود آهنگ ----------
def download_song(query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'song.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',  # کیفیت خوب
        }],
        'default_search': 'ytsearch',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=True)
        filename = ydl.prepare_filename(info)
        mp3_path = os.path.splitext(filename)[0] + ".mp3"
        return mp3_path, info.get("title", "بدون عنوان")

# ---------- پاسخ به پیام‌هایی با آهنگ یا musik ----------
@app.on_message(filters.text & ~filters.edited)
async def handle_music_request(client, message):
    text = message.text.lower().strip()

    if text.startswith("آهنگ") or text.startswith("musik"):
        query = text.replace("آهنگ", "").replace("musik", "").strip()
        if not query:
            await message.reply_text("🎵 لطفاً بعد از کلمه آهنگ یا musik اسم آهنگ رو بنویس.")
            return

        await message.reply_text("⏳ دارم دنبالش می‌گردم، صبر کن...")

        try:
            path, title = download_song(query)
            await message.reply_audio(audio=path, caption=f"🎧 {title}")
            os.remove(path)
        except Exception as e:
            await message.reply_text(f"❌ خطا در دانلود آهنگ:\n`{e}`")

# ---------- شروع ----------
print("🎶 Music downloader userbot started.")
app.run()
