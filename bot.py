from pyrogram import Client, filters
import os, yt_dlp, asyncio

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

async def download_audio(query):
    os.makedirs("downloads", exist_ok=True)
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "quiet": True,
        "noplaylist": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch1:{query}", download=True)["entries"][0]
        filename = os.path.splitext(ydl.prepare_filename(info))[0] + ".mp3"
    return filename, info["title"]

@app.on_message(filters.text)
async def debug(client, message):
    print(f"📩 پیام جدید: {message.text}")
    if any(message.text.lower().startswith(x) for x in ["آهنگ", "/music", "music", "/song", "song"]):
        await message.reply("🎵 دارم می‌فرستم، صبر کن...")
        try:
            file_path, title = await asyncio.to_thread(download_audio, message.text.split(' ', 1)[1])
            await message.reply_audio(audio=file_path, caption=f"🎶 {title}")
        except Exception as e:
            await message.reply(f"❌ خطا:\n{e}")

print("🚀 Bot Running...")
app.run()
