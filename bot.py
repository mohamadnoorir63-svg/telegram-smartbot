from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp, asyncio, os

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH"))
SESSION_STRING = os.getenv("SESSION_STRING")

app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# ⬅️ سینک (بدون async)
def download_audio(query):
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

@app.on_message(filters.text & filters.group)
async def send_music(client, message):
    text = message.text.strip().lower()
    keys = ["آهنگ ", "/آهنگ ", "music ", "/music ", "song ", "/song ", "musik ", "/musik "]
    query = next((text[len(k):].strip() for k in keys if text.startswith(k)), None)
    if not query:
        return

    m = await message.reply("🎵 در حال جستجو و دانلود آهنگ...")

    try:
        # درست: چون download_audio سینک است
        file_path, title = await asyncio.to_thread(download_audio, query)
        await message.reply_audio(
            audio=file_path,
            caption=f"🎶 {title}",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("📺 YouTube", url=f"https://www.youtube.com/results?search_query={query.replace(' ','+')}")]]
            ),
        )
        await m.delete()
    except Exception as e:
        await m.edit(f"❌ خطا:\n`{e}`")

print("🎧 Music Sender Userbot Online...")
app.run()
