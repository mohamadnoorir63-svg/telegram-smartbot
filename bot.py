from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests, re, os, asyncio

# 🔑 متغیرهای Heroku
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# 🎵 توابع جستجو از منابع آزاد
def search_music_sources(query):
    # منابع آزاد MP3
    sources = [
        f"https://pixabay.com/api/audio/?key=40177437-bd6bffea2e3a4ef7e50e0f9e4&q={query.replace(' ', '+')}",
        f"https://api.jamendo.com/v3.0/tracks/?client_id=49a8a3cf&format=jsonpretty&limit=1&namesearch={query.replace(' ', '+')}",
        f"https://api.deezer.com/search?q={query.replace(' ', '+')}"
    ]

    for url in sources:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                continue
            data = r.json()

            # Pixabay
            if "hits" in data and len(data["hits"]) > 0:
                hit = data["hits"][0]
                return hit["audio"], hit["tags"]

            # Jamendo
            if "results" in data and len(data["results"]) > 0:
                song = data["results"][0]
                return song["audio"], song["name"]

            # Deezer
            if "data" in data and len(data["data"]) > 0:
                track = data["data"][0]
                return track["preview"], f"{track['artist']['name']} - {track['title']}"

        except Exception as e:
            print("❌ خطا در منبع:", e)
            continue

    return None, None


@app.on_message(filters.text & (filters.private | filters.group))
async def send_music(client, message):
    text = message.text.strip().lower()
    keys = ["آهنگ ", "/آهنگ ", "music ", "/music ", "song ", "/song ", "musik ", "/musik "]
    query = next((text[len(k):].strip() for k in keys if text.startswith(k)), None)
    if not query:
        return

    m = await message.reply("🎧 در حال جستجو برای آهنگ...")

    try:
        file_url, title = await asyncio.to_thread(search_music_sources, query)
        if not file_url:
            raise Exception("هیچ فایل قابل دانلودی پیدا نشد 😔")

        await message.reply_audio(
            audio=file_url,
            caption=f"🎶 آهنگ شما:\n**{title}**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🌐 منبع پخش", url=file_url)]
            ])
        )
        await m.delete()

    except Exception as e:
        await m.edit(f"❌ خطا:\n`{e}`")


print("🎧 Universal Music Sender Online...")
app.run()
