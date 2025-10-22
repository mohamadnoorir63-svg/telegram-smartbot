from pyrogram import Client, filters
import os
import yt_dlp
import asyncio

# 📌 مقداردهی از Config Vars
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

# 📁 سشن userbot
app = Client("userbot", api_id=API_ID, api_hash=API_HASH)

# 📥 دستور دانلود آهنگ
@app.on_message(filters.command("music"))
async def music_downloader(client, message):
    if len(message.command) < 2:
        await message.reply_text("❌ لطفاً نام آهنگ یا لینک یوتیوب رو بنویس:\nمثلاً: `/music Arash Broken Angel`")
        return

    query = " ".join(message.command[1:])
    m = await message.reply_text(f"🎧 در حال جستجو برای آهنگ: `{query}` ...")

    # مسیر دانلود
    if not os.path.exists("downloads"):
        os.mkdir("downloads")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "quiet": True,
        "noplaylist": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=True)['entries'][0]
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

# 📡 شروع ربات
print("🎧 Music Bot Online...")
app.run()
