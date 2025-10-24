from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests, os, random

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

os.makedirs("downloads", exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Connection": "keep-alive",
    "Referer": "https://google.com/"
}

def try_download(url, filename):
    """تلاش برای دانلود؛ اگر 403 بده None برمی‌گردونه"""
    path = os.path.join("downloads", filename)
    try:
        with requests.get(url, headers=HEADERS, stream=True, timeout=20) as r:
            if r.status_code == 403:
                return None
            r.raise_for_status()
            with open(path, "wb") as f:
                for chunk in r.iter_content(1024 * 64):
                    f.write(chunk)
        return path
    except Exception:
        return None

def get_music(query):
    """جست‌وجو بین منابع مختلف، تا یکی جواب بده"""
    query_encoded = query.replace(" ", "+")
    candidates = []

    # Deezer
    try:
        res = requests.get(f"https://api.deezer.com/search?q={query_encoded}", timeout=8)
        data = res.json().get("data", [])
        for d in data[:3]:
            candidates.append({
                "title": f"{d['artist']['name']} - {d['title']}",
                "url": d["preview"],
                "source": f"https://www.deezer.com/track/{d['id']}"
            })
    except:
        pass

    # Jamendo
    try:
        res = requests.get(
            "https://api.jamendo.com/v3.0/tracks/",
            params={
                "client_id": "ae1a3c56",
                "format": "json",
                "limit": 3,
                "search": query
            },
            timeout=8
        )
        data = res.json().get("results", [])
        for d in data:
            candidates.append({
                "title": f"{d['artist_name']} - {d['name']}",
                "url": d["audio"],
                "source": d["shareurl"]
            })
    except:
        pass

    # fallback های سالم از CDNهای عمومی
    fallback = [
        ("Random Vibe - Chillout", "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/Scott_Holmes_Music/Happy_Music/Scott_Holmes_Music_-_01_-_Happy_Music.mp3"),
        ("Relax Beat - FreeSound", "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/Komiku/It_Makes_Me_Happy/Komiku_-_01_-_Its_Gonna_Be_Okay.mp3"),
        ("Funny Loop", "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/Lobo_Loco/Sunny_Days/Lobo_Loco_-_02_-_Walking_Around_ID_1291.mp3"),
    ]
    for name, url in fallback:
        candidates.append({"title": name, "url": url, "source": "https://freemusicarchive.org"})

    # تلاش برای دانلود تا یکی جواب بده
    for c in candidates:
        filename = c["title"].replace("/", "_") + ".mp3"
        path = try_download(c["url"], filename)
        if path:
            return c, path

    raise Exception("هیچ فایل قابل دانلودی پیدا نشد (همه لینک‌ها مسدود بودن).")

@app.on_message(filters.text)
async def music_handler(client, message):
    text = message.text.strip()
    keys = ["آهنگ ", "/آهنگ ", "music ", "/music ", "song ", "/song "]
    query = next((text[len(k):].strip() for k in keys if text.lower().startswith(k)), None)
    if not query:
        return

    m = await message.reply("🎧 در حال جستجو بین منابع آزاد موسیقی...")

    try:
        info, path = get_music(query)
        await message.reply_audio(
            audio=path,
            caption=f"🎶 **{info['title']}**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌐 منبع", url=info['source'])]])
        )
        await m.delete()
        try:
            os.remove(path)
        except:
            pass
    except Exception as e:
        await m.edit(f"❌ خطا:\n`{e}`")

print("🎧 Universal Music Finder (No-403 Mode) Online...")
app.run()
