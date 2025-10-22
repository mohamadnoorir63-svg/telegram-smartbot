from pyrogram import Client, filters
from pytgcalls import PyTgCalls, idle
from pytgcalls.types import AudioPiped
import yt_dlp
import os
import asyncio

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH"))

app = Client("userbot", api_id=API_ID, api_hash=API_HASH)
call = PyTgCalls(app)

@app.on_message(filters.text)
async def play_music(client, message):
    text = message.text.strip()

    # تشخیص دستورات
    if text.startswith("/music") or text.startswith("!music"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            await message.reply_text("❌ لطفاً نام آهنگ را بنویس:\nمثلاً: `/music Arash Broken Angel`")
            return
        query = parts[1]
    elif text.lower().startswith(("music ", "musik ", "آهنگ ")):
        query = text.split(" ", 1)[1]
    else:
        return

    msg = await message.reply_text(f"🎧 در حال جستجوی آهنگ `{query}` ...")

    if not os.path.exists("downloads"):
        os.mkdir("downloads")

    # دانلود از یوتیوب یا ساندکلاود
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "quiet": True,
        "noplaylist": True,
    }

    try:
        def download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch1:{query}", download=True)['entries'][0]
                return ydl.prepare_filename(info), info
        file_path, info = await asyncio.to_thread(download)
    except Exception as e:
        await msg.edit_text(f"⚠️ خطا در دریافت آهنگ:\n`{e}`")
        return

    title = info.get("title", "Unknown Title")
    artist = info.get("uploader", "Unknown Artist")

    await msg.edit_text(f"🎵 در حال پخش `{title}` ...")

    try:
        chat_id = message.chat.id
        await call.join_group_call(chat_id, AudioPiped(file_path))
        await message.reply_audio(
            audio=file_path,
            title=title,
            performer=artist,
            caption=f"🎶 {title}\n👤 {artist}\n🎧 *در حال پخش در ویس‌کال گروه*"
        )
        os.remove(file_path)
    except Exception as e:
        await msg.edit_text(f"❌ خطا در پخش ویس‌کال:\n`{e}`")

print("🎧 Music Bot Ready — connecting to Telegram...")
app.start()
call.start()
idle()
