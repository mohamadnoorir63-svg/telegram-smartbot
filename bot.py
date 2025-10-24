from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls import GroupCallFactory
from pytgcalls.types import AudioPiped
import requests, re, os, asyncio, yt_dlp

# 🧩 متغیرهای محیطی Heroku
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

# 🎧 راه‌اندازی Pyrogram و تماس صوتی
app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
call = GroupCallFactory(app).get_file_group_call()

# ==================== 🎵 جستجوی آهنگ از منابع آزاد ==================== #
def search_sources(query):
    query_enc = query.replace(" ", "+")
    sources = [
        f"https://api.deezer.com/search?q={query_enc}",
        f"https://api.jamendo.com/v3.0/tracks/?client_id=49a8a3cf&format=jsonpretty&limit=1&namesearch={query_enc}",
        f"https://pixabay.com/api/audio/?key=40177437-bd6bffea2e3a4ef7e50e0f9e4&q={query_enc}"
    ]

    for url in sources:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                continue
            data = r.json()

            # Deezer
            if "data" in data and data["data"]:
                track = data["data"][0]
                return track["preview"], f"Deezer ({track['artist']['name']})"

            # Jamendo
            if "results" in data and data["results"]:
                song = data["results"][0]
                return song["audio"], "Jamendo"

            # Pixabay
            if "hits" in data and data["hits"]:
                hit = data["hits"][0]
                return hit["audio"], "Pixabay"

        except Exception as e:
            print(f"⚠️ خطا در منبع {url}: {e}")
            continue

    return None, None

# ==================== 📥 دانلود آهنگ برای پخش ==================== #
def download_audio(url):
    os.makedirs("downloads", exist_ok=True)
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "downloads/song.%(ext)s",
        "quiet": True,
        "noplaylist": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    for file in os.listdir("downloads"):
        if file.endswith(".mp3"):
            return os.path.join("downloads", file)
    return None

# ==================== 🎧 هندل پیام پخش آهنگ ==================== #
@app.on_message(filters.text & (filters.private | filters.group))
async def play_music(client, message):
    text = message.text.strip().lower()
    keys = ["آهنگ ", "/آهنگ ", "music ", "/music ", "song ", "/song "]
    query = next((text[len(k):].strip() for k in keys if text.startswith(k)), None)
    if not query:
        return

    m = await message.reply("🎵 در حال جستجو برای آهنگ... لطفاً صبر کنید 🎶")

    try:
        file_url, source = await asyncio.to_thread(search_sources, query)
        if not file_url:
            raise Exception(f"هیچ آهنگی برای '{query}' پیدا نشد 😔")

        file_path = await asyncio.to_thread(download_audio, file_url)
        if not file_path:
            raise Exception("خطا در دانلود فایل mp3")

        # ارسال آهنگ
        await message.reply_audio(
            audio=file_path,
            caption=f"🎶 آهنگ درخواستی شما:\n**{query}**\n🌐 منبع: {source}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎧 پخش در ویس‌چت", callback_data=f"play|{file_path}")],
                [InlineKeyboardButton("❌ خروج از ویس", callback_data="leave")]
            ])
        )
        await m.delete()

    except Exception as e:
        await m.edit(f"❌ خطا:\n`{e}`")

# ==================== 🎛 کنترل دکمه‌های پخش ==================== #
@app.on_callback_query()
async def callbacks(client, callback_query):
    data = callback_query.data
    chat_id = callback_query.message.chat.id

    if data.startswith("play|"):
        file_path = data.split("|", 1)[1]
        await call.join_group_call(chat_id, AudioPiped(file_path))
        await callback_query.answer("🎧 در حال پخش در ویس‌چت...")

    elif data == "leave":
        await call.leave_group_call(chat_id)
        await callback_query.answer("❌ ربات از ویس‌چت خارج شد.")

print("🎧 VoiceChat MusicBot Online...")
app.run()
