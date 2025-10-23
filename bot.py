from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests, os, random

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

def find_any_music(query):
    """جست‌وجوی آزاد بین چند سایت موسیقی"""
    query_encoded = query.replace(" ", "+")
    possible_results = []

    # 1️⃣ Deezer (پایگاه بزرگ جهانی)
    try:
        r = requests.get(f"https://api.deezer.com/search?q={query_encoded}", timeout=8)
        data = r.json().get("data", [])
        if data:
            track = random.choice(data)
            possible_results.append({
                "title": f"{track['artist']['name']} - {track['title']}",
                "url": track["preview"],  # فایل mp3 کوتاه ولی آزاد
                "source": f"https://www.deezer.com/track/{track['id']}"
            })
    except:
        pass

    # 2️⃣ Jamendo (موزیک‌های بدون حق کپی)
    try:
        r = requests.get(
            "https://api.jamendo.com/v3.0/tracks/",
            params={
                "client_id": "ae1a3c56",  # public ID
                "format": "json",
                "limit": 3,
                "search": query
            },
            timeout=8
        )
        data = r.json().get("results", [])
        if data:
            track = random.choice(data)
            possible_results.append({
                "title": f"{track['artist_name']} - {track['name']}",
                "url": track["audio"],
                "source": track["shareurl"]
            })
    except:
        pass

    # 3️⃣ اگر هیچ نتیجه‌ای نبود، یه آهنگ تصادفی بده
    if not possible_results:
        random_fallbacks = [
            ("Random Vibe - Chillout", "https://cdn.pixabay.com/download/audio/2022/03/15/audio_a7e6e7.mp3?filename=chillout-115546.mp3"),
            ("Relax Beat - FreeSound", "https://cdn.pixabay.com/download/audio/2022/10/19/audio_61e70a.mp3?filename=relax-beat-122870.mp3"),
            ("Funny Loop", "https://cdn.pixabay.com/download/audio/2021/09/02/audio_9c12ab.mp3?filename=funny-loop-110416.mp3")
        ]
        name, url = random.choice(random_fallbacks)
        possible_results.append({"title": name, "url": url, "source": "https://pixabay.com/music"})

    return random.choice(possible_results)

@app.on_message(filters.text)
async def send_music(client, message):
    text = message.text.strip()
    keys = ["آهنگ ", "/آهنگ ", "music ", "/music ", "song ", "/song "]
    query = next((text[len(k):].strip() for k in keys if text.lower().startswith(k)), None)
    if not query:
        return

    m = await message.reply("🎧 در حال جستجو و انتخاب آهنگ مناسب...")

    try:
        result = find_any_music(query)
        await message.reply_audio(
            audio=result["url"],
            caption=f"🎵 **{result['title']}**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🌐 منبع", url=result["source"])]
            ])
        )
        await m.delete()
    except Exception as e:
        await m.edit(f"❌ خطا:\n`{e}`")

print("🎧 Universal Music Finder Online...")
app.run()
