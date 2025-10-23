import os
import yt_dlp
import asyncio
from pyrogram import Client, filters
from pytgcalls import PyTgCalls, idle
from pytgcalls.types import AudioPiped
from pytgcalls.types.input_stream import InputAudioStream

# ====== ⚙️ تنظیمات ======
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

# ساخت یوزربات
app = Client("music_voice_userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
pytg = PyTgCalls(app)

# پوشه آهنگ‌ها
if not os.path.exists("downloads"):
    os.mkdir("downloads")

# ====== 🎶 دانلود آهنگ ======
async def download_audio(query):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "quiet": True,
        "noplaylist": True,
    }

    loop = asyncio.get_event_loop()
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        def _download():
            if "http" in query:
                return ydl.extract_info(query, download=True)
            else:
                return ydl.extract_info(f"ytsearch1:{query}", download=True)["entries"][0]
        info = await loop.run_in_executor(None, _download)
        filename = ydl.prepare_filename(info)
    return filename, info.get("title", "Unknown")

# ====== 🎧 شروع پخش آهنگ ======
@app.on_message(filters.text & filters.regex(r"^(\/play|\/music|آهنگ)"))
async def play_music(client, message):
    chat_id = message.chat.id
    text = message.text.strip()

    # دریافت نام یا لینک آهنگ
    query = text.replace("/play", "").replace("/music", "").replace("آهنگ", "").strip()
    if not query:
        await message.reply_text("🎵 لطفاً نام آهنگ یا لینک یوتیوب را بنویس.\nمثلاً:\n`/play Arash Broken Angel`")
        return

    msg = await message.reply_text(f"🎧 در حال دریافت آهنگ **{query}** ...")
    try:
        file_path, title = await download_audio(query)
        await msg.edit_text(f"🎶 در حال پخش: **{title}**")

        # وصل شدن به ویس و پخش آهنگ
        await pytg.join_group_call(
            chat_id,
            AudioPiped(file_path, stream_type=InputAudioStream),
        )

        await message.reply_text(f"✅ پخش آغاز شد: **{title}**")

    except Exception as e:
        await msg.edit_text(f"❌ خطا در پخش:\n`{e}`")

# ====== ⏹ توقف پخش ======
@app.on_message(filters.text & filters.regex(r"^(\/stop|\/leave|توقف|خروج)$"))
async def stop_music(client, message):
    chat_id = message.chat.id
    try:
        await pytg.leave_group_call(chat_id)
        await message.reply_text("⏹ پخش متوقف شد و از ویس خارج شدم.")
    except Exception as e:
        await message.reply_text(f"⚠️ خطا هنگام توقف:\n`{e}`")

# ====== 🚀 شروع ======
@pytg.on_stream_end()
async def stream_ended(_, update):
    chat_id = update.chat_id
    await app.send_message(chat_id, "🎵 آهنگ تموم شد!")

async def main():
    await app.start()
    await pytg.start()
    print("🎤 Voice MusicBot gestartet!")
    await idle()

if __name__ == "__main__":
    asyncio.run(main())
