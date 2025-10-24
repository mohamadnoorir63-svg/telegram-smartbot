from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os, asyncio, yt_dlp, sys

# ✅ متغیرهای محیطی
def need(name):
    v = os.getenv(name)
    if not v:
        raise SystemExit(f"[❌ Missing ENV] {name}")
    return v

try:
    API_ID = int(need("API_ID"))
    API_HASH = need("API_HASH")
    SESSION_STRING = need("SESSION_STRING")
except Exception as e:
    print(e); sys.exit(1)

app = Client("music_userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# 🎧 تابع اصلی دانلود آهنگ
def download_precise(query: str):
    os.makedirs("downloads", exist_ok=True)
    common_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "ignoreerrors": True,
        "retries": 2,
        "fragment_retries": 2,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "concurrent_fragment_downloads": 3,
    }

    cookiefile = "cookies.txt"
    if os.path.exists(cookiefile):
        common_opts["cookiefile"] = cookiefile

    sources = [
        ("YouTube Music", f"ytmusicsearch1:{query}"),
        ("SoundCloud", f"scsearch1:{query}"),
        ("YouTube", f"ytsearch1:{query}"),
    ]

    for source_name, expr in sources:
        try:
            with yt_dlp.YoutubeDL(common_opts) as ydl:
                info = ydl.extract_info(expr, download=True)
                if not info:
                    continue

                # پیدا کردن آهنگ واقعی
                entry = None
                if "entries" in info and info["entries"]:
                    for e in info["entries"]:
                        if e:
                            entry = e
                            break
                else:
                    entry = info

                if not entry:
                    continue

                # مسیر فایل MP3
                title = entry.get("title", "audio")
                with yt_dlp.YoutubeDL({**common_opts, "download": False}) as y2:
                    prepared = y2.prepare_filename(entry)
                mp3_path = os.path.splitext(prepared)[0] + ".mp3"

                if os.path.exists(mp3_path):
                    return mp3_path, title, source_name

        except Exception as e:
            print(f"[{source_name} ERROR] {e}")
            continue

    return None, None, None

# 💬 دریافت پیام‌ها
@app.on_message(filters.text & (filters.private | filters.group))
async def handle_music(client, message):
    text = message.text.strip()
    if not text.startswith("آهنگ "):
        return

    query = text[len("آهنگ "):].strip()
    if not query:
        return await message.reply("❗ لطفاً بعد از 'آهنگ' نام آهنگ را بنویس.")

    m = await message.reply("🎧 در حال جستجوی دقیق برای آهنگ...")

    try:
        file_path, title, source = await asyncio.to_thread(download_precise, query)
        if not file_path:
            raise Exception("هیچ آهنگی پیدا نشد 😔")

        await message.reply_audio(
            audio=file_path,
            caption=f"🎶 آهنگ شما:\n**{title}**\n🌐 منبع: {source}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎵 منبع", callback_data="ok")]])
        )

        await m.delete()
        try:
            os.remove(file_path)
        except Exception:
            pass

    except Exception as e:
        await m.edit(f"❌ خطا:\n`{e}`")
        print(f"[ERROR] {e}")

@app.on_callback_query()
async def cb(_, cq):
    await cq.answer("✅")

print("🎵 Precise YouTube Music Bot Online...")
app.run()
