import os
from pyrogram import Client, filters
from pytgcalls import PyTgCalls, idle
from pytgcalls.types.input_stream import AudioPiped
import yt_dlp

# ---------------- تنظیمات ----------------
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

# ساخت کلاینت و اتصال صوتی
app = Client("music_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
call = PyTgCalls(app)

# ---------------- پخش موزیک ----------------
@app.on_message(filters.command("play", prefixes=["/"]))
async def play_music(client, message):
    if len(message.command) < 2:
        await message.reply_text("🎵 لطفاً نام آهنگ یا لینک یوتیوب رو بعد از /play بنویس.")
        return

    query = " ".join(message.command[1:])
    msg = await message.reply_text(f"🎧 در حال جستجو برای: {query}")

    try:
        ydl_opts = {"format": "bestaudio/best", "quiet": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)["entries"][0]
            url = info["url"]
            title = info["title"]

        chat_id = message.chat.id
        await call.join_group_call(chat_id, AudioPiped(url))
        await msg.edit_text(f"▶️ پخش: **{title}**")

    except Exception as e:
        await msg.edit_text(f"❌ خطا در پخش: {e}")

# ---------------- توقف پخش ----------------
@app.on_message(filters.command("stop", prefixes=["/"]))
async def stop_music(client, message):
    try:
        await call.leave_group_call(message.chat.id)
        await message.reply_text("⏹ پخش متوقف شد.")
    except Exception as e:
        await message.reply_text(f"⚠️ خطا در توقف: {e}")

# ---------------- شروع ----------------
@call.on_stream_end()
async def on_end(_, update):
    chat_id = update.chat_id
    await call.leave_group_call(chat_id)

print("🎤 MusicBot gestartet!")
app.start()
call.start()
idle()
