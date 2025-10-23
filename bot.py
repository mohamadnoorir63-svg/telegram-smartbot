from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests, os

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

def safe_json(resp):
    """برگشت داده‌ی json یا None اگر خطا بود"""
    try:
        return resp.json()
    except Exception:
        return None

def get_mp3_link(query):
    """جستجو در چند سرور و گرفتن mp3"""
    piped_servers = [
        "https://pipedapi.kavin.rocks",
        "https://pipedapi.syncpundit.io",
        "https://pipedapi.adminforge.de",
    ]
    video_id = None
    title = query
    for server in piped_servers:
        try:
            r = requests.get(f"{server}/search?q={query.replace(' ','+')}", timeout=10)
            data = safe_json(r)
            if data and "items" in data and data["items"]:
                video_url = data["items"][0]["url"]
                video_id = video_url.split("v=")[-1]
                title = data["items"][0]["title"]
                break
        except Exception:
            continue

    if not video_id:
        raise Exception("❌ نتوانستم ویدیو را پیدا کنم (همه سرورها خطا دادند).")

    # تلاش برای گرفتن لینک mp3 از چند منبع
    apis = [
        f"https://api.snappea.com/v1/video/details?url=https://www.youtube.com/watch?v={video_id}",
        f"https://api.y2mate.is/api/server/url?url=https://www.youtube.com/watch?v={video_id}",
    ]
    for api in apis:
        try:
            resp = requests.get(api, timeout=10)
            data = safe_json(resp)
            if not data:
                continue
            # Snappea
            if "videoInfo" in data and "audioStreams" in data["videoInfo"]:
                links = [x["url"] for x in data["videoInfo"]["audioStreams"] if "audio" in x.get("mimeType","")]
                if links:
                    return links[0], title
            # Y2Mate
            if "result" in data and "url" in data["result"]:
                return data["result"]["url"], title
        except Exception:
            continue

    raise Exception("هیچ لینک mp3 قابل استفاده پیدا نشد.")

@app.on_message(filters.text)
async def send_music(client, message):
    text = message.text.strip().lower()
    keys = ["آهنگ ", "/آهنگ ", "music ", "/music ", "song ", "/song ", "musik ", "/musik "]
    query = next((text[len(k):].strip() for k in keys if text.startswith(k)), None)
    if not query:
        return

    m = await message.reply("🎧 در حال جستجو برای آهنگ...")

    try:
        mp3_url, title = get_mp3_link(query)
        await message.reply_audio(
            audio=mp3_url,
            caption=f"🎶 آهنگ شما:\n**{title}**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎧 YouTube", url=f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}")]
            ])
        )
        await m.delete()
    except Exception as e:
        await m.edit(f"❌ خطا:\n`{e}`")

print("🎧 Music Downloader (Multi-API) Online...")
app.run()
