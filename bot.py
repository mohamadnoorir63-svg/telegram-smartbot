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

# تابع دانلود آهنگ
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

@app.on_message(filters.text & filters.group)
async def play_music(client, message):
    text = message.text.lower().strip()
    if text.startswith(("آهنگ ", "music ", "musik ", "/music")):
        query = text.split(" ", 1)[1] if " " in text else None
        if not query:
            await message.reply("❌ لطفاً بعد از دستور نام آهنگ رو بنویس.")
            return

        m = await message.reply("🎧 در حال جستجوی آهنگ...")

        try:
            file_path, title = await asyncio.to_thread(download_audio, query)
            await call.join_group_call(message.chat.id, AudioPiped(file_path))
            await m.delete()

            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("⏸ توقف", callback_data="pause"),
                 InlineKeyboardButton("▶️ پخش", callback_data="resume")],
                [InlineKeyboardButton("🔇 بی‌صدا", callback_data="mute"),
                 InlineKeyboardButton("🔊 صدا", callback_data="unmute")],
                [InlineKeyboardButton("❌ خروج", callback_data="leave")]
            ])

            await message.reply_audio(
                audio=file_path,
                caption=f"🎶 در حال پخش: **{title}**",
                reply_markup=buttons
            )

        except Exception as e:
            await m.edit(f"❌ خطا در پخش آهنگ:\n`{e}`")

# کنترل دکمه‌ها
@app.on_callback_query()
async def callbacks(client, callback_query):
    chat_id = callback_query.message.chat.id
    data = callback_query.data

    if data == "pause":
        await call.pause_stream(chat_id)
        await callback_query.answer("⏸ پخش متوقف شد.")
    elif data == "resume":
        await call.resume_stream(chat_id)
        await callback_query.answer("▶️ پخش ادامه یافت.")
    elif data == "mute":
        await call.mute_stream(chat_id)
        await callback_query.answer("🔇 بی‌صدا شد.")
    elif data == "unmute":
        await call.unmute_stream(chat_id)
        await callback_query.answer("🔊 صدا فعال شد.")
    elif data == "leave":
        await call.leave_group_call(chat_id)
        await callback_query.answer("❌ از ویس خارج شد.")
    else:
        await callback_query.answer("❓ دستور نامشخص.")

print("🎵 Voice Chat Music Bot Online...")
app.start()
call.start()
idle()
