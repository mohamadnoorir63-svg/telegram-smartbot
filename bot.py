from pyrogram import Client, filters
from pytgcalls import PyTgCalls, idle
from pytgcalls.types import AudioPiped
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
import asyncio
import os

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

app = Client("userbot", api_id=API_ID, api_hash=API_HASH)
call = PyTgCalls(app)

# 📥 دانلود آهنگ از یوتیوب
async def download_audio(query):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "quiet": True,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch1:{query}", download=True)["entries"][0]
        filename = ydl.prepare_filename(info)
    return filename, info["title"]

# 🎧 پخش آهنگ
@app.on_message(filters.text & filters.group)
async def play_music(client, message):
    text = message.text.lower().strip()
    query = None

    if text.startswith("آهنگ "):
        query = text[len("آهنگ "):].strip()
    elif text.startswith("music "):
        query = text[len("music "):].strip()
    elif text.startswith("musik "):
        query = text[len("musik "):].strip()

    if not query:
        return

    m = await message.reply("🎵 در حال جستجو و آماده‌سازی آهنگ...")

    try:
        file_path, title = await asyncio.to_thread(download_audio, query)
        await call.join_group_call(message.chat.id, AudioPiped(file_path))
        await m.delete()

        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("⏸ توقف", callback_data="pause"),
             InlineKeyboardButton("▶️ ادامه", callback_data="resume")],
            [InlineKeyboardButton("❌ خروج", callback_data="leave")]
        ])

        await message.reply_audio(
            audio=file_path,
            caption=f"🎶 اکنون در حال پخش: **{title}**",
            reply_markup=buttons
        )

    except Exception as e:
        await m.edit(f"❌ خطا در پخش آهنگ:\n`{e}`")

# 🎚 کنترل دکمه‌ها
@app.on_callback_query()
async def callbacks(client, callback_query):
    chat_id = callback_query.message.chat.id
    data = callback_query.data

    if data == "pause":
        await call.pause_stream(chat_id)
        await callback_query.answer("⏸ آهنگ متوقف شد.")
    elif data == "resume":
        await call.resume_stream(chat_id)
        await callback_query.answer("▶️ ادامه پخش.")
    elif data == "leave":
        await call.leave_group_call(chat_id)
        await callback_query.answer("❌ ربات از ویس خارج شد.")

print("🎧 VoiceChat Music Bot Online...")
app.start()
call.start()
idle()
