from pyrogram import Client, filters
import os, asyncio, yt_dlp, re

# ================== ⚙️ تنظیمات ==================
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION = os.getenv("SESSION_STRING", "")

app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)

DOWNLOAD_PATH = "downloads"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

# ================== 🎵 تابع دانلود از چند منبع ==================
def download_precise(query: str):
    os.makedirs(DOWNLOAD_PATH, exist_ok=True)

    opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "outtmpl": f"{DOWNLOAD_PATH}/%(title)s.%(ext)s",
        "retries": 3,
        "ignoreerrors": True,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    sources = [
        ("YouTube", f"ytsearch5:{query} audio"),
        ("YouTube Music", f"ytmusicsearch5:{query}"),
        ("SoundCloud", f"scsearch5:{query}"),
    ]

    for name, expr in sources:
        print(f"🔎 جستجو در {name} → {expr}")
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(expr, download=True)
                if "entries" in info and info["entries"]:
                    info = info["entries"][0]

                title = info.get("title", "audio")
                mp3_path = os.path.splitext(ydl.prepare_filename(info))[0] + ".mp3"

                if os.path.exists(mp3_path):
                    print(f"[✅ Downloaded] {title} ← {name}")
                    return mp3_path, title, name

        except Exception as e:
            print(f"[❌ {name} ERROR] {e}")
            continue

    return None, None, None


# ================== 💬 هندل پیام‌ها ==================
@app.on_message(filters.text)
async def on_message(client, message):
    text = (message.text or "").strip()
    print(f"📩 پیام از {message.from_user.first_name if message.from_user else 'ناشناس'}: {text}")

    if text.lower() == "ping":
        return await message.reply_text("✅ Userbot فعال است و کار می‌کند!")

    if text.startswith("آهنگ "):
        query = text.replace("آهنگ", "").strip()
        if not query:
            return await message.reply_text("❗ لطفاً بعد از 'آهنگ' نام آهنگ را بنویس.")

        m = await message.reply_text(f"🎧 در حال جستجو برای آهنگ: {query} ...")
        loop = asyncio.get_running_loop()
        file_path, title, source = await loop.run_in_executor(None, download_precise, query)

        if not file_path or not os.path.exists(file_path):
            return await m.edit("❌ هیچ نتیجه‌ای پیدا نشد یا دانلود ناموفق بود 😔")

        await message.reply_audio(
            audio=file_path,
            caption=f"🎶 {title}\n🌐 منبع: {source}"
        )
        await m.delete()

        try:
            os.remove(file_path)
        except:
            pass


# ================== 🚀 اجرای مستقیم ==================
async def main():
    print("🚀 Starting standalone Userbot...")
    await app.start()
    me = await app.get_me()
    print(f"✅ Logged in as: {me.first_name} ({me.id})")
    print("📢 آماده دریافت پیام از همه کاربران...")
    await asyncio.Future()  # نگه داشتن دائمی

if __name__ == "__main__":
    asyncio.run(main())
