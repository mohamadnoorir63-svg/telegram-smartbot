from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp, asyncio, os

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

def download_audio(query):
    os.makedirs("downloads", exist_ok=True)
    search_sites = [
        f"scsearch1:{query}",
        f"ytsearchmusic1:{query}",
        f"mixcloud:{query}",
        f"ytsearch1:{query} audio -youtube"
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
                # گاهی info خالی یا None میاد
                if not info:
                    continue
                if "entries" in info:
                    entries = [e for e in info.get("entries", []) if e]
                    if not entries:
                        continue
                    info = entries[0]
                filename = os.path.splitext(ydl.prepare_filename(info))[0] + ".mp3"
                abs_path = os.path.abspath(filename)
                if os.path.exists(abs_path):
                    return abs_path, info.get("title", query)
        except Exception as e:
            last_error = e
            continue
    raise Exception(f"هیچ آهنگی برای '{query}' پیدا نشد یا همه منابع خطا دادن.\n{last_error}")

@app.on_message(filters.text & filters.group)
async def send_music(client, message):
    text = message.text.strip().lower()
    keys = ["آهنگ ", "/آهنگ ", "music ", "/music ", "song ", "/song ", "musik ", "/musik "]
    query = next((text[len(k):].strip() for k in keys if text.startswith(k)), None)
    if not query:
        return

    m = await message.reply("🎧 در حال جست‌وجو در منابع آزاد و دانلود آهنگ...")

    try:
        file_path, title = await asyncio.to_thread(download_audio, query)
        await message.reply_audio(
            audio=file_path,
            caption=f"🎶 آهنگ شما آماده است:\n**{title}**",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🌐 جستجو در گوگل", url=f"https://www.google.com/search?q={query.replace(' ','+')}+mp3")]]
            ),
        )
        await m.delete()
        try:
            os.remove(file_path)
        except:
            pass
    except Exception as e:
        await m.edit(f"❌ خطا:\n`{e}`")

print("🎧 Music Sender Userbot Online...")
app.run()
