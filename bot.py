from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests, os

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

def search_deezer(query):
    url = f"https://api.deezer.com/search?q={query}"
    r = requests.get(url)
    if r.status_code != 200:
        raise Exception("ارتباط با سرور Deezer برقرار نشد.")
    data = r.json().get("data", [])
    if not data:
        raise Exception(f"هیچ آهنگی برای '{query}' پیدا نشد.")
    track = data[0]
    title = track["title"]
    artist = track["artist"]["name"]
    preview = track["preview"]  # لینک mp3 کوتاه (۳۰ ثانیه‌ای ولی آزاد)
    return preview, f"{artist} - {title}"

@app.on_message(filters.text & filters.group)
async def send_music(client, message):
    text = message.text.strip().lower()
    keys = ["آهنگ ", "/آهنگ ", "music ", "/music ", "song ", "/song ", "musik ", "/musik "]
    query = next((text[len(k):].strip() for k in keys if text.startswith(k)), None)
    if not query:
        return

    m = await message.reply("🎧 در حال جستجو در Deezer...")

    try:
        file_url, title = search_deezer(query)
        await message.reply_audio(
            audio=file_url,
            caption=f"🎶 آهنگ شما:\n**{title}**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎧 پخش در Deezer", url=f"https://www.deezer.com/search/{query.replace(' ', '+')}")]
            ])
        )
        await m.delete()
    except Exception as e:
        await m.edit(f"❌ خطا:\n`{e}`")

print("🎧 Music Sender Userbot Online...")
app.run()
