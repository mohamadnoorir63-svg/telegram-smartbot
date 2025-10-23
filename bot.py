from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests, os, re

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

def get_mp3_link(query):
    """دریافت لینک MP3 از API آزاد"""
    search_url = f"https://ytsearch.ai/api/search?q={query.replace(' ', '+')}"
    try:
        res = requests.get(search_url, timeout=10)
        data = res.json().get("data", [])
        if not data:
            raise Exception("هیچ نتیجه‌ای پیدا نشد.")
        video_id = data[0]["id"]
        title = data[0]["title"]

        # گرفتن لینک دانلود mp3 از سایت SnapSave
        api_url = f"https://api.snappea.com/v1/video/details?url=https://www.youtube.com/watch?v={video_id}"
        info = requests.get(api_url, timeout=10).json()
        links = info.get("videoInfo", {}).get("audioStreams", [])
        mp3_links = [x["url"] for x in links if "audio" in x.get("mimeType", "")]

        if not mp3_links:
            raise Exception("هیچ لینک mp3 موجود نیست.")

        return mp3_links[0], title
    except Exception as e:
        raise Exception(f"خطا در دریافت آهنگ: {e}")

@app.on_message(filters.text)
async def send_music(client, message):
    text = message.text.strip().lower()
    keys = ["آهنگ ", "/آهنگ ", "music ", "/music ", "song ", "/song ", "musik ", "/musik "]
    query = next((text[len(k):].strip() for k in keys if text.startswith(k)), None)
    if not query:
        return

    m = await message.reply("🎧 در حال جستجو و آماده‌سازی آهنگ...")

    try:
        mp3_url, title = get_mp3_link(query)

        await message.reply_audio(
            audio=mp3_url,
            caption=f"🎶 آهنگ شما:\n**{title}**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎧 منبع", url=f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}")]
            ])
        )

        await m.delete()

    except Exception as e:
        await m.edit(f"❌ خطا:\n`{e}`")

print("🎧 Music Downloader (API Mode) Online...")
app.run()
