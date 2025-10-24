from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os, asyncio, yt_dlp, sys, re, requests

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
    print(e)
    sys.exit(1)

app = Client("music_userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)


# 🎧 تابع اصلی دانلود آهنگ (اولویت: YouTube → YouTube Music → SoundCloud)
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
        ("YouTube", f"ytsearch1:{query}"),
        ("YouTube Music", f"ytmusicsearch1:{query}"),
        ("SoundCloud", f"scsearch1:{query}"),
    ]

    for source_name, expr in sources:
        try:
            with yt_dlp.YoutubeDL(common_opts) as ydl:
                info = ydl.extract_info(expr, download=True)
                if not info:
                    continue

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


# 🎵 دانلود از لینک مستقیم (پشتیبانی کامل از share.google, youtube, music.youtube و رفع خطای Sign-in)
def download_from_link(url: str):
    import requests
    os.makedirs("downloads", exist_ok=True)

    # 🔁 بررسی redirect
    try:
        r = requests.get(url, allow_redirects=True, timeout=10)
        if any(x in r.url for x in ["youtube.com", "youtu.be", "music.youtube.com", "shorts.youtube.com"]):
            url = r.url
    except Exception as e:
        print(f"[Redirect Error] {e}")

    # ⚙️ تنظیمات yt-dlp با پایداری بالا
    opts = {
        "format": "bestaudio/best/b[ext=m4a]/bestaudio",
        "quiet": True,
        "noplaylist": True,
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "ignoreerrors": True,
        "retries": 5,
        "fragment_retries": 5,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "concurrent_fragment_downloads": 4,
        "force_ipv4": True,
        # ✅ مهم: استفاده از client اندروید برای دور زدن کپچا
        "extractor_args": {
            "youtube": {
                "player_client": ["android"]
            }
        },
    }

    # اگر cookies.txt موجود است، استفاده شود
    cookiefile = "cookies.txt"
    if os.path.exists(cookiefile):
        opts["cookiefile"] = cookiefile

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)

            # اگر playlist بود، فقط اولین آهنگ را بگیرد
            if info and "entries" in info and info["entries"]:
                for e in info["entries"]:
                    if e:
                        info = e
                        break

            title = (info or {}).get("title", "audio")
            mp3_path = os.path.splitext(ydl.prepare_filename(info))[0] + ".mp3"

            if os.path.exists(mp3_path):
                print(f"[✅ Download Success] {title}")
                return mp3_path, title

    except Exception as e:
        print(f"[YT Link Error] {e}")

    return None, None


# 💬 پاسخ به پیام‌ها (کار می‌کند در PV و گروه)
@app.on_message(filters.text)
async def handle_music(client, message):
    text = message.text.strip()

    # 🎯 شناسایی هر نوع لینک یوتیوب / موزیک / share.google
    yt_match = re.search(r"(https?://)?(www\.)?(youtube\.com|youtu\.be|music\.youtube\.com|share\.google|shorts\.youtube\.com)/[^\s]+", text)
    if yt_match:
        url = yt_match.group(0)
        m = await message.reply("🎧 در حال دانلود MP3 از لینک YouTube...")
        try:
            file_path, title = await asyncio.to_thread(download_from_link, url)
            if not file_path:
                raise Exception("دانلود از لینک انجام نشد 😔")

            await message.reply_audio(
                audio=file_path,
                caption=f"🎶 از لینک YouTube:\n**{title}**",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔗 لینک", url=url)]])
            )
            await m.delete()
            os.remove(file_path)
        except Exception as e:
            await m.edit(f"❌ خطا در دانلود:\n`{e}`")
        return

    # 🎵 حالت دستور متنی: آهنگ ...
    if not text.startswith("آهنگ "):
        return

    query = text[len("آهنگ "):].strip()
    if not query:
        return await message.reply("❗ لطفاً بعد از 'آهنگ' نام آهنگ را بنویس.")

    m = await message.reply("🎧 در حال جستجو در YouTube و SoundCloud...")

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
        os.remove(file_path)

    except Exception as e:
        await m.edit(f"❌ خطا:\n`{e}`")
        print(f"[ERROR] {e}")


@app.on_callback_query()
async def cb(_, cq):
    await cq.answer("✅")


print("🎵 YouTube + Redirect + Text Search Music Bot Online...")
app.run()
