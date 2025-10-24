from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests, re, os, asyncio, yt_dlp, sys

# ========== ⚙️ تنظیمات محیطی ========== #
def safe_get_env(var_name, required=False):
    value = os.getenv(var_name)
    if not value:
        msg = f"[⚠️ Missing ENV] {var_name} not found."
        print(msg)
        if required:
            raise SystemExit(msg)
        return None
    return value

try:
    API_ID = int(safe_get_env("API_ID", required=True))
    API_HASH = safe_get_env("API_HASH", required=True)
    SESSION_STRING = safe_get_env("SESSION_STRING", required=True)
except Exception as e:
    print(f"❌ Configuration Error: {e}")
    sys.exit(1)

app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# ========== 🔍 جستجو در چند منبع ========== #
def search_music(query):
    q = query.replace(" ", "+")
    sources = [
        f"https://music-fa.com/?s={q}",
        f"https://ahangbaz.ir/?s={q}",
        f"https://nex1music.ir/?s={q}",
    ]

    for site in sources:
        try:
            html = requests.get(site, timeout=10).text
            mp3_links = re.findall(r'https?://[^\s"\']+\.mp3', html)
            if mp3_links:
                return mp3_links[0], site
        except Exception:
            continue

    # Jamendo
    try:
        r = requests.get(
            f"https://api.jamendo.com/v3.0/tracks/?client_id=49a8a3cf&format=jsonpretty&limit=1&namesearch={q}",
            timeout=10,
        )
        results = r.json().get("results", [])
        if results:
            return results[0]["audio"], "Jamendo"
    except Exception:
        pass

    # MP3Clan (منبع عمومی)
    try:
        r = requests.get(f"https://mp3clan.top/search/{q}", timeout=10)
        links = re.findall(r'https?://[^"\']+\.mp3', r.text)
        if links:
            return links[0], "MP3Clan"
    except Exception:
        pass

    # YouTube fallback
    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "noplaylist": True,
            "quiet": True,
            "outtmpl": "downloads/%(title)s.%(ext)s",
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)["entries"][0]
            return info["url"], "YouTube"
    except Exception:
        pass

    return None, None

# ========== 📥 دانلود آهنگ ========== #
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
            mp3_path = os.path.splitext(file_path)[0] + ".mp3"
            return mp3_path
    except Exception as e:
        print(f"[yt_dlp Error] {e}")
        return None

# ========== 💬 دستور "آهنگ ..." ========== #
@app.on_message(filters.text & (filters.private | filters.group))
async def send_music(client, message):
    text = message.text.strip()
    if not text.startswith("آهنگ "):
        return

    query = text[len("آهنگ "):].strip()
    if not query:
        return await message.reply("❗ لطفاً بعد از 'آهنگ' نام آهنگ را بنویس.")

    m = await message.reply("🎧 در حال جستجو برای آهنگ...")

    try:
        url, source = await asyncio.to_thread(search_music, query)
        if not url:
            raise Exception(f"هیچ آهنگی برای '{query}' پیدا نشد 😔")

        file_path = await asyncio.to_thread(download_audio, url)
        if not file_path or not os.path.exists(file_path):
            raise Exception("دانلود فایل با خطا مواجه شد یا لینک خراب بود.")

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

print("🎵 Global Music Downloader Bot Online...")
app.run()
