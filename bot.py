from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests, re, os, asyncio

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# 🔎 جستجو در سایت‌های ایرانی
def search_iranian_music(query):
    sources = [
        f"https://music-fa.com/?s={query.replace(' ', '+')}",
        f"https://upmusics.com/?s={query.replace(' ', '+')}",
        f"https://nava.ir/?s={query.replace(' ', '+')}"
    ]
    for site in sources:
        try:
            r = requests.get(site, timeout=10)
            links = re.findall(r'https://[^"\']+\.mp3', r.text)
            if links:
                return links[0]
        except Exception:
            continue
    return None

# 🎧 جستجو در منابع آزاد
def search_foreign_music(query):
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
            if "hits" in data and len(data["hits"]) > 0:
                return data["hits"][0]["audio"]
            if "results" in data and len(data["results"]) > 0:
                return data["results"][0]["audio"]
            if "data" in data and len(data["data"]) > 0:
                return data["data"][0]["preview"]
        except Exception:
            continue
    return None

@app.on_message(filters.text & (filters.private | filters.group))
async def send_music(client, message):
    text = message.text.strip().lower()
    keys = ["آهنگ ", "/آهنگ ", "music ", "/music ", "song ", "/song "]
    query = next((text[len(k):].strip() for k in keys if text.startswith(k)), None)
    if not query:
        return

    m = await message.reply("🎧 در حال جستجو برای آهنگ...")

    try:
        # جستجو در سایت‌های فارسی
        file_url = await asyncio.to_thread(search_iranian_music, query)
        if not file_url:
            # اگه پیدا نشد، برو سراغ منابع بین‌المللی
            file_url = await asyncio.to_thread(search_foreign_music, query)

        if not file_url:
            raise Exception(f"هیچ آهنگی برای '{query}' پیدا نشد 😔")

        await message.reply_audio(
            audio=file_url,
            caption=f"🎶 آهنگ درخواستی شما:\n**{query}**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🌐 منبع پخش", url=file_url)]
            ])
        )
        await m.delete()
    except Exception as e:
        await m.edit(f"❌ خطا:\n`{e}`")

print("🎧 MultiSource MusicBot Online...")
app.run()
