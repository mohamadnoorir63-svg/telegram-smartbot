import os
import yt_dlp
from pyrogram import Client, filters

# ---------- ⚙️ تنظیمات ----------
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

# ---------- 🎧 ساخت یوزربات ----------
app = Client("music_userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# ---------- 🎵 تابع دانلود آهنگ ----------
def download_song(query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'song.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=True)
        filename = ydl.prepare_filename(info)
        mp3_path = os.path.splitext(filename)[0] + ".mp3"
        title = info.get("title", "Unknown Title")
        duration = info.get("duration")
        minutes = duration // 60 if duration else 0
        seconds = duration % 60 if duration else 0
        length = f"{minutes}:{seconds:02d}" if duration else "نامشخص"
        return mp3_path, title, length

# ---------- 💬 پاسخ به درخواست آهنگ ----------
# ---------- 💬 پاسخ به درخواست آهنگ ----------
@app.on_message(filters.text)
async def handle_music(client, message):
    text = message.text.lower().strip()

    if text.startswith("آهنگ") or text.startswith("musik"):
        query = text.replace("آهنگ", "").replace("musik", "").strip()

        if not query:
            await message.reply_text("🎵 لطفاً بعد از کلمه 'آهنگ' یا 'musik' اسم آهنگ رو بنویس.")
            return

        await message.reply_text("🎧 در حال جست‌وجو و دانلود آهنگ... لطفاً صبر کن 🔎")

        try:
            path, title, length = download_song(query)
            caption = f"🎶 {title}\n🕒 مدت: {length}\n📀 درخواست‌شده: {message.from_user.first_name}"
            await message.reply_audio(audio=path, caption=caption)
            os.remove(path)
        except Exception as e:
            await message.reply_text(f"❌ خطا در دانلود آهنگ:\n`{e}`")

# ---------- 🚀 شروع ----------
print("🎵 Music Userbot (Sara) started and ready.")
app.run()
