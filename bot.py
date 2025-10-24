from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests, re, os, asyncio

# 🔑 تنظیمات از Heroku config vars
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

# 🎧 شروع یوزربات
app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# ==================== جستجوی منابع ==================== #

# 🇮🇷 سایت‌های ایرانی
def search_iranian_music(query):
    sites = [
        f"https://music-fa.com/?s={query.replace(' ', '+')}",
        f"https://upmusics.com/?s={query.replace(' ', '+')}",
        f"https://nava.ir/?s={query.replace(' ', '+')}",
    ]
    for site in sites:
        try:
            r = requests.get(site, timeout=10)
            links = re.findall(r'https://[^"\']+\.mp3', r.text)
            if links:
                return links[0], site
        except:
            continue
    return None, None


# 🇦🇫 سایت‌های افغانی
def search_afghan_music(query):
    sites = [
        f"https://ahangbaz.com/?s={query.replace(' ', '+')}",
        f"https://afghan123.com/?s={query.replace(' ', '+')}",
        f"https://andamusic.com/?s={query.replace(' ', '+')}"
    ]
    for site in sites:
        try:
            r = requests.get(site, timeout=10)
            links = re.findall(r'https://[^"\']+\.mp3', r.text)
            if links:
                return links[0], site
        except:
            continue
    return None, None


# 🌍 منابع بین‌المللی آزاد
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

            # Pixabay
            if "hits" in data and len(data["hits"]) > 0:
                hit = data["hits"][0]
                return hit["audio"], "Pixabay"

            # Jamendo
            if "results" in data and len(data["results"]) > 0:
                song = data["results"][0]
                return song["audio"], "Jamendo"

            # Deezer
            if "data" in data and len(data["data"]) > 0:
                track = data["data"][0]
                return track["preview"], f"Deezer ({track['artist']['name']})"

        except Exception:
            continue
    return None, None


# ==================== هندل پیام ==================== #

@app.on_message(filters.text & (filters.private | filters.group))
async def send_music(client, message):
    text = message.text.strip().lower()
    keys = ["آهنگ ", "/آهنگ ", "music ", "/music ", "song ", "/song ", "musik ", "/musik "]
    query = next((text[len(k):].strip() for k in keys if text.startswith(k)), None)
    if not query:
        return

    m = await message.reply("🎧 در حال جستجو برای آهنگ... لطفاً صبر کنید 🎶")

    try:
        # جستجو در سایت‌های فارسی
        file_url, source = await asyncio.to_thread(search_iranian_music, query)
        if not file_url:
            # اگه فارسی نبود، سراغ افغانی
            file_url, source = await asyncio.to_thread(search_afghan_music, query)
        if not file_url:
            # اگه هیچ‌کدوم نبود، منابع بین‌المللی
            file_url, source = await asyncio.to_thread(search_foreign_music, query)

        if not file_url:
            raise Exception(f"هیچ آهنگی برای '{query}' پیدا نشد 😔")

        await message.reply_audio(
            audio=file_url,
            caption=f"🎶 آهنگ درخواستی شما:\n**{query}**\n\n🌐 منبع: {source}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎧 پخش آنلاین", url=file_url)]
            ])
        )
        await m.delete()

    except Exception as e:
        await m.edit(f"❌ خطا:\n`{e}`")


print("🎧 Global MusicBot (Iran | Afghan | World) Online...")
app.run()
