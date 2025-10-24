from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests, re, os, asyncio, yt_dlp, sys

# ⚙️ تنظیم متغیرها
def safe_env(var, required=False):
    val = os.getenv(var)
    if not val:
        msg = f"[⚠️ Missing ENV] {var} not found."
        print(msg)
        if required:
            raise SystemExit(msg)
        return None
    return val

try:
    API_ID = int(safe_env("API_ID", required=True))
    API_HASH = safe_env("API_HASH", required=True)
    SESSION_STRING = safe_env("SESSION_STRING", required=True)
except Exception as e:
    print(f"❌ ENV Error: {e}")
    sys.exit(1)

app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# ==================== 🎧 جستجوی آهنگ ==================== #
def find_music(query):
    q = query.replace(" ", "+")
    sources = [
        ("Music-fa", f"https://music-fa.com/?s={q}"),
        ("Ahangbaz", f"https://ahangbaz.ir/?s={q}"),
        ("Nex1music", f"https://nex1music.ir/?s={q}")
    ]

    # منابع ایرانی
    for name, site in sources:
        try:
            html = requests.get(site, timeout=10).text
            links = re.findall(r'https?://[^\s"\']+\.mp3', html)
            if links:
                for link in links:
                    r = requests.head(link, timeout=5)
                    if r.status_code == 200 and "audio" in r.headers.get("Content-Type", ""):
                        return link, name
        except Exception:
            continue

    # Jamendo
    try:
        r = requests.get(
            f"https://api.jamendo.com/v3.0/tracks/?client_id=49a8a3cf&format=jsonpretty&limit=1&namesearch={q}",
            timeout=10
        )
        results = r.json().get("results", [])
        if results:
            return results[0]["audio"], "Jamendo"
    except Exception:
        pass

    # MP3Clan
    try:
        r = requests.get(f"https://mp3clan.top/search/{q}", timeout=10)
        links = re.findall(r'https?://[^"\']+\.mp3', r.text)
        if links:
            return links[0], "MP3Clan"
    except Exception:
        pass

    # FreeSound
    try:
        fs = requests.get(f"https://freesound.org/apiv2/search/text/?query={q}&token=L9jPaePcZsYhzbtGcQq2zdYz6m1a2fbC8WeAtu0e", timeout=10)
        results = fs.json().get("results", [])
        if results:
            return results[0]["previews"]["preview-hq-mp3"], "FreeSound"
    except Exception:
        pass

    # YouTube fallback
    try:
        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)["entries"][0]
            return info["url"], "YouTube"
    except Exception:
        pass

    return None, None


# ==================== 📥 دانلود فایل ==================== #
def download_audio(url):
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
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            mp3 = os.path.splitext(file_path)[0] + ".mp3"
            return mp3
    except Exception as e:
        print(f"[yt_dlp Error] {e}")
        return None


# ==================== 💬 دستور "آهنگ" ==================== #
@app.on_message(filters.text & (filters.private | filters.group))
async def music_handler(client, message):
    text = message.text.strip()
    if not text.startswith("آهنگ "):
        return
    query = text[len("آهنگ "):].strip()

    m = await message.reply("🎧 در حال جستجوی آهنگ...")
    try:
        url, source = await asyncio.to_thread(find_music, query)
        if not url:
            raise Exception("هیچ منبعی برای این آهنگ پیدا نشد 😔")

        file_path = await asyncio.to_thread(download_audio, url)
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
        print(f"[Error] {e}")

print("🎧 Universal Music Bot Online...")
app.run()
