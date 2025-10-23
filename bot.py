from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp, asyncio, os

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# 📥 تابع دانلود آهنگ از سایت‌های آزاد (غیر YouTube)
def download_audio(query):
    os.makedirs("downloads", exist_ok=True)
    # جستجو در چند منبع مختلف
    search_sites = [
        f"ytsearch1:{query} audio -youtube",  # به yt_dlp بگو یوتیوب رو نادیده بگیره
        f"scsearch1:{query}",  # SoundCloud
        f"mixcloud:{query}",   # MixCloud
        f"ytsearchmusic1:{query}",  # فقط موزیک‌های باز
    ]

    last_error = None
    for site in search_sites:
        try:
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": "downloads/%(title)s.%(ext)s",
                "quiet": True,
                "noplaylist": True,
                "ignoreerrors": True,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(site, download=True)
                # در بعضی سایت‌ها "entries" وجود داره
                if "entries" in info:
                    info = info["entries"][0]
                filename = os.path.splitext(ydl.prepare_filename(info))[0] + ".mp3"
                return filename, info.get("title", "Unknown title")
        except Exception as e:
            last_error = e
            continue
    raise Exception(f"❌ هیچ منبع آزادی پیدا نشد یا خطا رخ داد:\n{last_error}")

@app.on_message(filters.text & filters.group)
async def send_music(client, message):
    text = message.text.strip().lower()
    keys = ["آهنگ ", "/آهنگ ", "music ", "/music ", "song ", "/song ", "musik ", "/musik "]
    query = next((text[len(k):].strip() for k in keys if text.startswith(k)), None)
    if not query:
        return

    m = await message.reply("🎧 در حال جستجو در منابع آزاد و دانلود آهنگ...")

    try:
        file_path, title = await asyncio.to_thread(download_audio, query)
        await message.reply_audio(
            audio=file_path,
            caption=f"🎶 آهنگ شما آماده است:\n**{title}**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🌐 منبع", url=f"https://www.google.com/search?q={query.replace(' ','+')}+mp3")]
            ])
        )
        await m.delete()
    except Exception as e:
        await m.edit(f"❌ خطا:\n`{e}`")

print("🎧 Music Sender Userbot Online...")
app.run()
