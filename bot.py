from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests, re, os, yt_dlp, asyncio

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

def is_persian(text):
    """اگر متن شامل حروف فارسی باشد، یعنی آهنگ ایرانی است"""
    return bool(re.search(r'[\u0600-\u06FF]', text))

def search_iranian_music(query):
    """از سایت‌های ایرانی mp3 بگیر"""
    sources = [
        f"https://music-fa.com/?s={query.replace(' ', '+')}",
        f"https://upmusics.com/?s={query.replace(' ', '+')}",
        f"https://nava.ir/?s={query.replace(' ', '+')}",
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

def search_foreign_music(query):
    """از Deezer بگیر"""
    url = f"https://api.deezer.com/search?q={query}"
    r = requests.get(url)
    if r.status_code != 200:
        raise Exception("ارتباط با سرور Deezer برقرار نشد.")
    data = r.json().get("data", [])
    if not data:
        return None
    track = data[0]
    return track["preview"], f"{track['artist']['name']} - {track['title']}"

@app.on_message(filters.text & filters.group)
async def send_music(client, message):
    text = message.text.strip().lower()
    keys = ["آهنگ ", "/آهنگ ", "music ", "/music ", "song ", "/song ", "musik ", "/musik "]
    query = next((text[len(k):].strip() for k in keys if text.startswith(k)), None)
    if not query:
        return

    m = await message.reply("🎧 در حال جستجو برای آهنگ...")

    try:
        if is_persian(query):
            mp3_url = search_iranian_music(query)
            if not mp3_url:
                raise Exception(f"هیچ آهنگ فارسی برای '{query}' پیدا نشد.")
            await message.reply_audio(
                audio=mp3_url,
                caption=f"🎵 آهنگ ایرانی مورد نظر:\n**{query}**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🌐 منبع", url=mp3_url)]
                ])
            )
        else:
            result = search_foreign_music(query)
            if not result:
                raise Exception(f"هیچ آهنگ خارجی برای '{query}' پیدا نشد.")
            file_url, title = result
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
