import os
import yt_dlp
from pyrogram import Client, filters

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

app = Client("music_userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# 🎧 تابع دانلود هوشمند
def smart_download(query):
    sources = [
        f"ytsearch:{query}",          # YouTube
        f"scsearch:{query}",          # SoundCloud
        f"dzsearch:{query}",          # Deezer
    ]
    for src in sources:
        try:
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": "song.%(ext)s",
                "quiet": True,
                "noplaylist": True,
                "default_search": "auto",
                "geo_bypass": True,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(src, download=True)
                filename = ydl.prepare_filename(info)
                path = os.path.splitext(filename)[0] + ".mp3"
                title = info.get("title", "Unknown")
                duration = info.get("duration", 0)
                m, s = divmod(duration, 60)
                length = f"{m}:{s:02d}" if duration else "نامشخص"
                return path, title, length
        except Exception as e:
            print(f"⚠️ خطا در {src}: {e}")
            continue
    raise Exception("هیچ منبع قابل دانلودی پیدا نشد ❌")


# 🎵 هندل پیام‌ها
@app.on_message(filters.text)
async def play_music(client, message):
    text = message.text.lower().strip()
    if text.startswith("آهنگ") or text.startswith("musik"):
        query = text.replace("آهنگ", "").replace("musik", "").strip()
        if not query:
            await message.reply_text("🎵 لطفاً بعد از کلمه 'آهنگ' یا 'musik' اسم آهنگ رو بنویس.")
            return

        await message.reply_text(f"🔎 در حال جست‌وجوی {query} ...")

        try:
            path, title, length = smart_download(query)
            caption = f"🎶 {title}\n🕒 مدت: {length}\n📀 درخواست‌شده توسط: {message.from_user.first_name}"
            await message.reply_audio(audio=path, caption=caption)
            os.remove(path)
        except Exception as e:
            await message.reply_text(f"❌ خطا در دانلود آهنگ:\n`{str(e)[:400]}`")


print("🎧 سارا موزیک‌بات بدون کوکی آماده است 🎶")
app.run()
