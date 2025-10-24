from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os, asyncio, yt_dlp, sys

# -------- ENV چک امن --------
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

# -------- دانلودگر با چند منبع داخلی yt-dlp --------
def download_by_query(query: str):
    """
    به ترتیب از این منابع امتحان می‌کند:
    1) scsearch1: (SoundCloud)
    2) ytmusicsearch1: (YouTube Music)
    3) ytsearch1: (YouTube)
    اگر cookies.txt در ریشه باشد، خودکار استفاده می‌شود.
    """
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
        # خطاها باعث توقف نشوند؛ می‌رویم سراغ منبع بعدی
        "ignoreerrors": True,
        "retries": 2,
        "fragment_retries": 2,
        "geo_bypass": True,
        "nocheckcertificate": True,
        # سرعت بهتر روی هرoku
        "concurrent_fragment_downloads": 3,
    }

    cookiefile = "cookies.txt"
    if os.path.exists(cookiefile):
        common_opts["cookiefile"] = cookiefile

    searches = [
        ("SoundCloud", f"scsearch1:{query}"),
        ("YouTube Music", f"ytmusicsearch1:{query}"),
        ("YouTube", f"ytsearch1:{query}"),
    ]

    last_error = None
    for source_name, expr in searches:
        try:
            with yt_dlp.YoutubeDL(common_opts) as ydl:
                info = ydl.extract_info(expr, download=True)
                # در حالت سرچ، info ممکن است playlist-info با entries باشد
                entry = None
                if info is None:
                    continue
                if "entries" in info and info["entries"]:
                    # اولین نتیجهٔ سالم
                    for e in info["entries"]:
                        if e:
                            entry = e
                            break
                else:
                    entry = info

                if not entry:
                    continue

                # مسیر فایل خروجی MP3 را حدس می‌زنیم
                # yt-dlp نام را بر اساس title می‌سازد
                title = entry.get("title", "audio")
                # چون پس‌پردازش MP3 انجام می‌دهیم، خروجی .mp3 است
                # ولی نام دقیق را با prepare_filename مطمئن‌تر می‌گیریم:
                # (حالت دانلود=True است، پس فایل باید روی دیسک باشد)
                # ترفند: دوباره یک بار با download=False فقط برای به‌دست‌آوردن نام:
                with yt_dlp.YoutubeDL({**common_opts, "download": False}) as y2:
                    prepared = y2.prepare_filename(entry)
                mp3_path = os.path.splitext(prepared)[0] + ".mp3"
                if os.path.exists(mp3_path):
                    return mp3_path, source_name
        except Exception as e:
            last_error = e
            continue

    # اگر هیچ‌کدام جواب نداد
    if last_error:
        print(f"[Downloader last error] {last_error}")
    return None, None

# -------- هندل پیام --------
@app.on_message(filters.text & (filters.private | filters.group))
async def handle_music(client, message):
    text = message.text.strip()
    if not text.startswith("آهنگ "):
        return
    query = text[6:].strip()
    if not query:
        return await message.reply("❗ بعد از «آهنگ» نام موزیک را بنویس.")

    m = await message.reply("🎧 در حال جستجو و دانلود...")

    try:
        file_path, source = await asyncio.to_thread(download_by_query, query)
        if not file_path or not os.path.exists(file_path):
            raise Exception("هیچ آهنگی پیدا نشد یا دانلود با خطا مواجه شد.")

        await message.reply_audio(
            audio=file_path,
            caption=f"🎶 آهنگ شما: **{query}**\n🌐 منبع: {source}",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("✅ OK", callback_data="ok")]]
            )
        )
        await m.delete()
        # پاکسازی تا فضای هرُوکو پر نشود
        try:
            os.remove(file_path)
        except Exception:
            pass

    except Exception as e:
        await m.edit(f"❌ خطا:\n`{e}`")
        print(f"[ERROR] {e}")

# دکمهٔ ساده
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
@app.on_callback_query()
async def cb(_, cq):
    await cq.answer("✅")

print("🎵 Multi-Search Music Bot (SC + YTMusic + YT) Online...")
app.run()
