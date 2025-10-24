from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests, os, random

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

os.makedirs("downloads", exist_ok=True)

def find_any_music(query):
    """جست‌وجوی آزاد بین چند سایت موسیقی"""
    query_encoded = query.replace(" ", "+")
    possible_results = []

    # 1️⃣ Deezer (آهنگ‌های جهانی)
    try:
        r = requests.get(f"https://api.deezer.com/search?q={query_encoded}", timeout=8)
        data = r.json().get("data", [])
        if data:
            track = random.choice(data)
            possible_results.append({
                "title": f"{track['artist']['name']} - {track['title']}",
                "url": track["preview"],  # لینک mp3 کوتاه
                "source": f"https://www.deezer.com/track/{track['id']}"
            })
    except:
        pass

    # 2️⃣ Jamendo (موزیک آزاد)
    try:
        r = requests.get(
            "https://api.jamendo.com/v3.0/tracks/",
            params={
                "client_id": "ae1a3c56",
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

    # 3️⃣ آهنگ تصادفی در صورت نبود نتیجه
    if not possible_results:
        random_fallbacks = [
            ("Random Vibe - Chillout", "https://cdn.pixabay.com/download/audio/2022/03/15/audio_a7e6e7.mp3?filename=chillout-115546.mp3"),
            ("Relax Beat - FreeSound", "https://cdn.pixabay.com/download/audio/2022/10/19/audio_61e70a.mp3?filename=relax-beat-122870.mp3"),
            ("Funny Loop", "https://cdn.pixabay.com/download/audio/2021/09/02/audio_9c12ab.mp3?filename=funny-loop-110416.mp3")
        ]
        name, url = random.choice(random_fallbacks)
        possible_results.append({"title": name, "url": url, "source": "https://pixabay.com/music"})

    return random.choice(possible_results)

def download_file(url, filename):
    """دانلود فایل MP3"""
    path = os.path.join("downloads", filename)
    with requests.get(url, stream=True, timeout=20) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(1024 * 64):
                f.write(chunk)
    return path

@app.on_message(filters.text)
async def send_music(client, message):
    text = message.text.strip()
    keys = ["آهنگ ", "/آهنگ ", "music ", "/music ", "song ", "/song "]
    query = next((text[len(k):].strip() for k in keys if text.lower().startswith(k)), None)
    if not query:
        return

    m = await message.reply("🎧 در حال جستجو و دانلود آهنگ...")

    try:
        result = find_any_music(query)
        filename = result["title"].replace("/", "_") + ".mp3"
        filepath = download_file(result["url"], filename)

        await message.reply_audio(
            audio=filepath,
            caption=f"🎵 **{result['title']}**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🌐 منبع", url=result["source"])]
            ])
        )

        await m.delete()

        # پاک کردن بعد از ارسال
        try:
            os.remove(filepath)
        except:
            pass

    except Exception as e:
        await m.edit(f"❌ خطا:\n`{e}`")

print("🎧 Universal Music Finder (Local Upload) Online...")
app.run()
