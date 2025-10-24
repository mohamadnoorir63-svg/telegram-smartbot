# 🎵 دانلود از لینک مستقیم (پشتیبانی از share.google, youtube, music.youtube و رفع Sign-in)
def download_from_link(url: str):
    import requests
    os.makedirs("downloads", exist_ok=True)

    # 1) Resolve redirect (share.google و لینک‌های کوتاه)
    try:
        r = requests.get(url, allow_redirects=True, timeout=8)
        final_url = r.url
        if any(x in final_url for x in ["youtube.com", "youtu.be", "music.youtube.com", "shorts.youtube.com"]):
            url = final_url
    except Exception as e:
        print(f"[Redirect Error] {e}")

    # 2) تنظیمات مقاوم yt-dlp + استفاده از cookies.txt اگر موجود باشد
    opts = {
        # چند فرمت fallback برای اطمینان
        "format": "bestaudio/best/b[ext=m4a]/bestaudio",
        "quiet": True,
        "noplaylist": True,
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        # پایداری بیشتر
        "ignoreerrors": True,
        "retries": 5,
        "fragment_retries": 5,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "concurrent_fragment_downloads": 4,
        "force_ipv4": True,
        # ↓ این ترفند معمولاً خطای «Sign in to confirm…» را دور می‌زند
        "extractor_args": {
            "youtube": {
                "player_client": ["android"]
            }
        },
    }

    cookiefile = "cookies.txt"
    if os.path.exists(cookiefile):
        opts["cookiefile"] = cookiefile

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # اگر لینک playlist بود، اولین آیتم را در نظر می‌گیریم
            if info and "entries" in info and info["entries"]:
                for e in info["entries"]:
                    if e:
                        info = e
                        break
            title = (info or {}).get("title", "audio")
            # مسیر فایل MP3 خروجی
            mp3_path = os.path.splitext(ydl.prepare_filename(info))[0] + ".mp3"
            if os.path.exists(mp3_path):
                return mp3_path, title
    except Exception as e:
        print(f"[YT Link Error] {e}")

    return None, None
