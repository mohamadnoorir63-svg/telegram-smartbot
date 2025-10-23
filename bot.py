from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests, os

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

def search_jamendo(query):
    r = requests.get(
        "https://api.jamendo.com/v3.0/tracks/",
        params={
            "client_id": "ae1a3c56",   # شناسه‌ی عمومی Jamendo
            "format": "json",
            "limit": 1,
            "search": query,
        },
        timeout=10,
    )
    data = r.json().get("results", [])
    if not data:
        raise Exception("هیچ آهنگی پیدا نشد.")
    track = data[0]
    return track["audio"], f"{track['artist_name']} - {track['name']}"

@app.on_message(filters.text)
async def handler(client, message):
    text = message.text.strip().lower()
    keys = ["آهنگ ", "/آهنگ ", "music ", "/music ", "song ", "/song "]
    query = next((text[len(k):].strip() for k in keys if text.startswith(k)), None)
    if not query:
        return
    m = await message.reply("🎧 در حال جست‌وجوی آهنگ آزاد...")
    try:
        url, title = search_jamendo(query)
        await message.reply_audio(
            audio=url,
            caption=f"🎶 {title}",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🌐 منبع", url=url)]]
            ),
        )
        await m.delete()
    except Exception as e:
        await m.edit(f"❌ {e}")

print("🎧 Free-Music Bot Online...")
app.run()
