from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp, asyncio, os

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# 📥 دانلود از YouTube به MP3
def download_audio(query):
    os.makedirs("downloads", exist_ok=True)
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "noplaylist": True,
        "quiet": True,
        "geo_bypass": True,
        "age_limit": 0,
        "extract_flat": False,
        "default_search": "ytsearch1",  # جستجوی خودکار در یوتیوب
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=True)
        if "entries" in info:
            info = info["entries"][0]
        filename = os.path.splitext(ydl.prepare_filename(info))[0] + ".mp3"
        abs_path = os.path.abspath(filename)
    return abs_path, info.get("title", "Unknown Title")

# 🎧 پاسخ به همه (گروه + پیوی)
@app.on_message(filters.text)
async def send_music(client, message):
    text = message.text.strip().lower()
    keys = ["آهنگ ", "/آهنگ ", "music ", "/music ", "song ", "/song ", "musik ", "/musik "]
    query = next((text[len(k):].strip() for k in keys if text.startswith(k)), None)
    if not query:
        return

    m = await message.reply("🎵 در حال جستجو و دانلود آهنگ از YouTube...")

    try:
        file_path, title = await asyncio.to_thread(download_audio, query)

        await message.reply_audio(
            audio=file_path,
            caption=f"🎶 آهنگ شما آماده است:\n**{title}**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎧 منبع", url=f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}")]
            ])
        )
        await m.delete()

        # پاک‌کردن فایل بعد از ارسال (برای جلوگیری از پر شدن حافظه Heroku)
        try:
            os.remove(file_path)
        except:
            pass

    except Exception as e:
        await m.edit(f"❌ خطا در دانلود:\n`{e}`")

print("🎧 Universal Music Bot Online...")
app.run()
