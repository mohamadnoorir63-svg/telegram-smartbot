from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests, re, os, asyncio

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# ========================= منابع مختلف ========================= #

def search_sources(query):
    query_enc = query.replace(" ", "+")
    sources = [
        # 🎵 Deezer
        f"https://api.deezer.com/search?q={query_enc}",
        # 🎵 Jamendo
        f"https://api.jamendo.com/v3.0/tracks/?client_id=49a8a3cf&format=jsonpretty&limit=1&namesearch={query_enc}",
        # 🎵 Pixabay
        f"https://pixabay.com/api/audio/?key=40177437-bd6bffea2e3a4ef7e50e0f9e4&q={query_enc}",
        # 🎵 JioSaavn غیررسمی
        f"https://saavn.me/search/songs?query={query_enc}",
        # 🎵 mp3Quack
        f"https://mp3-juices.nu/api/search.php?q={query_enc}"
    ]

    for url in sources:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                continue

            data = r.json() if r.text.strip().startswith("{") or r.text.strip().startswith("[") else None

            # Deezer
            if "data" in (data or {}):
                track = data["data"][0]
                return track["preview"], f"Deezer ({track['artist']['name']})"

            # Jamendo
            if "results" in (data or {}):
                song = data["results"][0]
                return song["audio"], f"Jamendo ({song['artist_name']})"

            # Pixabay
            if "hits" in (data or {}):
                hit = data["hits"][0]
                return hit["audio"], "Pixabay"

            # Saavn
            if "data" in (data or {}):
                for item in data["data"]["results"]:
                    if "downloadUrl" in item and item["downloadUrl"]:
                        return item["downloadUrl"][0]["link"], "Saavn"

            # mp3-juices
            links = re.findall(r'https://[^"\']+\.mp3', r.text)
            if links:
                return links[0], "mp3Juices"

        except Exception as e:
            print(f"⚠️ خطا در منبع: {url} → {e}")
            continue

    return None, None

# ========================= هندل پیام ========================= #

@app.on_message(filters.text & (filters.private | filters.group))
async def send_music(client, message):
    text = message.text.strip().lower()
    keys = ["آهنگ ", "/آهنگ ", "music ", "/music ", "song ", "/song "]
    query = next((text[len(k):].strip() for k in keys if text.startswith(k)), None)
    if not query:
        return

    m = await message.reply("🎧 در حال جستجو برای آهنگ... لطفاً صبر کنید 🎵")

    try:
        file_url, source = await asyncio.to_thread(search_sources, query)
        if not file_url:
            raise Exception(f"هیچ آهنگی برای '{query}' پیدا نشد 😔")

        await message.reply_audio(
            audio=file_url,
            caption=f"🎶 آهنگ درخواستی شما:\n**{query}**\n\n🌐 منبع: {source}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎧 پخش آنلاین", url=file_url)]
            ])
        )
        await m.delete()

    except Exception as e:
        await m.edit(f"❌ خطا:\n`{e}`")

print("🎧 Global MultiSource MusicBot Online...")
app.run()
