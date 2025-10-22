from pyrogram import Client, filters
import os
import yt_dlp
import asyncio
import re

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

app = Client("userbot", api_id=API_ID, api_hash=API_HASH)

async def download_music(query):
    if not os.path.exists("downloads"):
        os.mkdir("downloads")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "quiet": True,
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        if "http" in query:
            info = ydl.extract_info(query, download=True)
        else:
            info = ydl.extract_info(f"ytsearch1:{query}", download=True)['entries'][0]
        file_path = ydl.prepare_filename(info)
    return file_path, info


# 🟢 اینجا فقط filters.text استفاده شده (بدون edited)
@app.on_message(filters.text)
async def detect_music_request(client, message):
    text = message.text.lower().strip()

    # اگر پیام با یکی از کلیدواژه‌ها شروع شد
    if text.startswith("آهنگ ") or text.startswith("music ") or text.startswith("musik "):
        query = re.sub(r"^(آهنگ|music|musik)\s+", "", text).strip()
        if not query:
            await message.reply_text("🎧 لطفاً بعد از 'آهنگ' یا 'music' اسم آهنگ رو بنویس.")
            return

        m = await message.reply_text(f"🎶 در حال جستجو برای: `{query}` ...")

        try:
            file_path, info = await asyncio.to_thread(download_music, query)
            title = info.get("title", "Unknown Title")
            artist = info.get("uploader", "Unknown Artist")

            await m.edit_text(f"📤 در حال ارسال آهنگ `{title}` ...")

            await message.reply_audio(
                audio=file_path,
                title=title,
                performer=artist,
                caption=f"🎵 {title}\n👤 {artist}\n\nارسال توسط 🤖 *ربات خنگول موزیک*"
            )

            os.remove(file_path)
            await m.delete()
        except Exception as e:
            await m.edit_text(f"❌ خطا در دریافت آهنگ:\n`{e}`")

print("🎧 Music Bot Online...")
app.run()
