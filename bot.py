from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import yt_dlp
import asyncio

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

app = Client("userbot", api_id=API_ID, api_hash=API_HASH)


@app.on_message(filters.text)
async def music_downloader(client, message):
    text = (message.text or "").strip()

    # تشخیص دستور کاربر
    if text.startswith("/music") or text.startswith("!music"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            await message.reply_text("❌ لطفاً نام آهنگ یا لینک رو بنویس:\nمثلاً: `/music Arash Broken Angel`")
            return
        query = parts[1].strip()
    elif text.lower().startswith("آهنگ "):
        query = text[len("آهنگ "):].strip()
    elif text.lower().startswith("music "):
        query = text[len("music "):].strip()
    elif text.lower().startswith("musik "):
        query = text[len("musik "):].strip()
    else:
        return

    m = await message.reply_text(f"🎧 در حال جستجو برای آهنگ `{query}` ...")

    if not os.path.exists("downloads"):
        os.mkdir("downloads")

    # تابع دانلود آهنگ
    async def try_download():
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
                info = ydl.extract_info(f"ytsearch1:{query}", download=True)["entries"][0]
            return ydl.prepare_filename(info), info

    try:
        file_path, info = await asyncio.to_thread(try_download)
        title = info.get("title", "Unknown Title")
        artist = info.get("uploader", "Unknown Artist")
        url = info.get("webpage_url", "https://youtube.com")

        # 🎵 دکمه‌های زیبا زیر آهنگ
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎧 لینک آهنگ", url=url)],
            [InlineKeyboardButton("🤖 ساخت ربات مشابه", url=f"https://t.me/{client.me.username}")]
        ])

        await m.edit_text(f"📤 در حال ارسال آهنگ `{title}` ...")

        await message.reply_audio(
            audio=file_path,
            title=title,
            performer=artist,
            caption=f"🎶 {title}\n👤 {artist}\n\nدانلود شده توسط 🎧 *خنگول موزیک بات*",
            reply_markup=buttons
        )

        os.remove(file_path)
        await m.delete()

    except Exception as e:
        await m.edit_text(f"❌ خطا در دریافت آهنگ:\n`{e}`")


print("🎧 Music Bot Online...")
app.run()
