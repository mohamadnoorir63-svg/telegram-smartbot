from pyrogram import Client, filters
import os
import yt_dlp
import asyncio

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

app = Client("userbot", api_id=API_ID, api_hash=API_HASH)

@app.on_message(filters.command("music"))
async def music_downloader(client, message):
    if len(message.command) < 2:
        await message.reply_text("❌ لطفاً نام آهنگ یا لینک رو بنویس:\nمثلاً: `/music Arash Broken Angel`")
        return

    query = " ".join(message.command[1:])
    m = await message.reply_text(f"🎧 در حال جستجو برای آهنگ `{query}` ...")

    if not os.path.exists("downloads"):
        os.mkdir("downloads")

    # تابع کمکی برای دانلود از یک منبع خاص
    async def try_download(source):
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
            return ydl.prepare_filename(info), info

    try:
        try:
            file_path, info = await asyncio.to_thread(try_download, "youtube")
        except Exception:
            await m.edit_text("⚠️ یوتیوب اجازه نداد، دارم از SoundCloud امتحان می‌کنم...")
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": "downloads/%(title)s.%(ext)s",
                "quiet": True,
                "noplaylist": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"scsearch1:{query}", download=True)['entries'][0]
                file_path = ydl.prepare_filename(info)

        title = info.get("title", "Unknown Title")
        artist = info.get("uploader", "Unknown Artist")

        await m.edit_text(f"📤 در حال ارسال آهنگ `{title}` ...")
        await message.reply_audio(
            audio=file_path,
            title=title,
            performer=artist,
            caption=f"🎶 {title}\n👤 {artist}\n\nدانلود شده توسط 🎧 *خنگول موزیک بات*",
        )
        os.remove(file_path)
        await m.delete()
    except Exception as e:
        await m.edit_text(f"❌ خطا در دریافت آهنگ:\n`{e}`")

print("🎧 Music Bot Online...")
app.run()
