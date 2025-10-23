import os
import requests
from pyrogram import Client, filters

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH"))
SESSION_STRING = os.getenv("SESSION_STRING")

app = Client("music_userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

def search_song(query):
    """جستجو و دانلود MP3 از سایت API آزاد"""
    url = f"https://api-v2.musify.download/api/search?q={query}"
    r = requests.get(url)
    data = r.json()
    if not data or "songs" not in data or not data["songs"]:
        raise Exception("چیزی پیدا نشد 😢")
    song = data["songs"][0]
    title = song["title"]
    artist = song["artist"]["name"]
    dl = song["url"]
    mp3_url = dl.replace("/song/", "/download/")
    return mp3_url, f"{title} - {artist}"

@app.on_message(filters.text)
async def get_music(client, message):
    text = message.text.strip().lower()
    if text.startswith("آهنگ") or text.startswith("musik"):
        query = text.replace("آهنگ", "").replace("musik", "").strip()
        if not query:
            await message.reply_text("🎵 لطفاً بعد از کلمه آهنگ یا musik اسم آهنگ رو بنویس.")
            return

        await message.reply_text("🎧 در حال جستجو برای آهنگ...")

        try:
            mp3_url, title = search_song(query)
            await message.reply_audio(mp3_url, caption=f"🎶 {title}\n📀 درخواست‌شده توسط {message.from_user.first_name}")
        except Exception as e:
            await message.reply_text(f"❌ خطا:\n{str(e)[:300]}")

print("🎶 سارا موزیک‌بات فعال شد")
app.run()
