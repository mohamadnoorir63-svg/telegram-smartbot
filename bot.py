from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests, os, asyncio, yt_dlp, sys

# ⚙️ گرفتن تنظیمات محیطی
def get_env(var, required=False):
    val = os.getenv(var)
    if not val and required:
        raise SystemExit(f"[❌ Missing ENV] {var} not found.")
    return val

try:
    API_ID = int(get_env("API_ID", True))
    API_HASH = get_env("API_HASH", True)
    SESSION_STRING = get_env("SESSION_STRING", True)
except Exception as e:
    print(f"⚠️ Config Error: {e}")
    sys.exit(1)

app = Client("music_userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# ==================== 🌍 جستجوی آهنگ ==================== #
def global_search(query):
    q = query.replace(" ", "+")
    
    # Jamendo API
    try:
        jam = requests.get(
            f"https://api.jamendo.com/v3.0/tracks/?client_id=49a8a3cf&format=jsonpretty&limit=1&namesearch={q}",
            timeout=5,
        ).json()
        res = jam.get("results", [])
        if res:
            audio = res[0]["audio"]
            name = res[0]["artist_name"] + " - " + res[0]["name"]
            return audio, f"Jamendo ({name})"
    except Exception:
        pass

    # FreeSound API
    try:
        free = requests.get(
            f"https://freesound.org/apiv2/search/text/?query={q}&token=L9jPaePcZsYhzbtGcQq2zdYz6m1a2fbC8WeAtu0e",
            timeout=5,
        ).json()
        results = free.get("results", [])
        if results:
            link = results[0]["previews"]["preview-hq-mp3"]
            return link, "FreeSound"
    except Exception:
        pass

    # YouTube fallback
    try:
        ydl_opts = {"format": "bestaudio/best", "noplaylist": True, "quiet": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)["entries"][0]
            return info["url"], "YouTube"
    except Exception:
        pass

    return None, None

# ==================== 📥 دانلود آهنگ ==================== #
def download_mp3(url):
    os.makedirs("downloads", exist_ok=True)
    opts = {
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
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
            mp3 = os.path.splitext(path)[0] + ".mp3"
            return mp3
    except Exception as e:
        print(f"[yt_dlp Error] {e}")
        return None

# ==================== 💬 پیام "آهنگ ..." ==================== #
@app.on_message(filters.text & (filters.private | filters.group))
async def handle_music(client, message):
    text = message.text.strip()
    if not text.startswith("آهنگ "):
        return

    query = text[len("آهنگ "):].strip()
    m = await message.reply("🎧 در حال جستجوی سریع برای آهنگ...")

    try:
        url, source = await asyncio.to_thread(global_search, query)
        if not url:
            raise Exception("هیچ آهنگی پیدا نشد 😔")

        file_path = await asyncio.to_thread(download_mp3, url)
        if not file_path or not os.path.exists(file_path):
            raise Exception("دانلود فایل با خطا مواجه شد.")

        await message.reply_audio(
            audio=file_path,
            caption=f"🎶 آهنگ شما: **{query}**\n🌐 منبع: {source}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌍 منبع", url=url)]])
        )

        await m.delete()
        os.remove(file_path)

    except Exception as e:
        await m.edit(f"❌ خطا:\n`{e}`")
        print(f"[ERROR] {e}")

print("🎵 Fast Global Music Bot Online...")
app.run()
