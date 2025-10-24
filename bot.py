from pyrogram import Client, filters
import yt_dlp, os, asyncio, re

# ------------------ ⚙️ تنظیمات اصلی ------------------
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION_STRING = os.getenv("SESSION_STRING", "")

app = Client("userbot_test", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
DOWNLOAD_PATH = "downloads"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)


# ------------------ 🎵 تابع دانلود موزیک ------------------
def download_music(query: str):
    """دانلود آهنگ از YouTube، YT Music یا SoundCloud"""
    sources = [
        ("YouTube", f"ytsearch5:{query}"),
        ("YouTube Music", f"ytmusicsearch5:{query}"),
        ("SoundCloud", f"scsearch5:{query}")
    ]

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": False,
        "noplaylist": True,
        "outtmpl": f"{DOWNLOAD_PATH}/%(title)s.%(ext)s",
        "retries": 3,
        "fragment_retries": 3,
        "ignoreerrors": True,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "concurrent_fragment_downloads": 3,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    for name, expr in sources:
        print(f"🔎 Searching in {name} → {expr}")
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(expr, download=True)
                if "entries" in info and info["entries"]:
                    info = info["entries"][0]
                if not info:
                    continue

                title = info.get("title", "audio")
                file_path = os.path.splitext(ydl.prepare_filename(info))[0] + ".mp3"
                if os.path.exists(file_path):
                    print(f"✅ Downloaded: {title} ({name})")
                    return file_path, title, name
        except Exception as e:
            print(f"[{name} ERROR] {e}")
    return None, None, None


# ------------------ 💬 هندل پیام‌ها ------------------
@app.on_message(filters.text & (filters.private | filters.me))
async def music_handler(client, message):
    text = message.text.strip()

    if text.lower() == "ping":
        return await message.reply("✅ Userbot آماده‌ست!")

    if text.startswith("آهنگ "):
        query = text.replace("آهنگ", "").strip()
        if not query:
            return await message.reply("❗ لطفاً بعد از 'آهنگ' اسم آهنگ رو بنویس.")

        m = await message.reply(f"🎧 در حال جستجو برای آهنگ: {query} ...")

        loop = asyncio.get_running_loop()
        file_path, title, source = await loop.run_in_executor(None, download_music, query)

        if not file_path:
            return await m.edit("❌ متأسفم! نتونستم آهنگی با این نام پیدا کنم 😔")

        await message.reply_audio(
            audio=file_path,
            caption=f"🎶 {title}\n🌐 منبع: {source}"
        )
        await m.delete()

        try:
            os.remove(file_path)
        except:
            pass


# ------------------ 🚀 اجرای یوزربات ------------------
async def main():
    print("🚀 Starting standalone userbot music tester...")
    async with app:
        me = await app.get_me()
        print(f"✅ Logged in as: {me.first_name} ({me.id})")
        print("🎵 آماده دریافت دستورات مثل: آهنگ love story")
        await asyncio.Future()  # برای همیشه فعال بمونه

if __name__ == "__main__":
    asyncio.run(main())
