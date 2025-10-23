import os, asyncio
from pyrogram import Client, filters
import yt_dlp
import aiohttp

# ===== 🌍 Environment =====
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
SUDO_ID = int(os.getenv("SUDO_ID"))
# ===========================

app = Client("sara_userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# 🎧 دستور: موزیک ...
@app.on_message(filters.me & filters.regex(r"^موزیک (.+)"))
async def send_music(client, message):
    query = message.matches[0].group(1).strip()
    msg = await message.reply_text(f"🎧 در حال جست‌وجوی موزیک برای: <b>{query}</b>", parse_mode="HTML")

    async def from_youtube(q):
        ydl_opts = {
            "format": "bestaudio/best",
            "noplaylist": True,
            "quiet": True,
            "outtmpl": "%(title)s.%(ext)s",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{q}", download=True)
            if not info or not info.get("entries"):
                raise Exception("در یوتیوب چیزی پیدا نشد.")
            entry = info["entries"][0]
            filename = ydl.prepare_filename(entry).rsplit(".", 1)[0] + ".mp3"
            title = entry["title"]
            return filename, title

    async def from_soundcloud(q):
        client_id = os.getenv("YOUR_CLIENT_ID")
        if not client_id:
            raise Exception("⚠️ SoundCloud Client ID تنظیم نشده.")
        async with aiohttp.ClientSession() as ses:
            async with ses.get(f"https://api-v2.soundcloud.com/search/tracks?q={q}&client_id={client_id}") as resp:
                js = await resp.json()
                if "collection" not in js or not js["collection"]:
                    raise Exception("در SoundCloud چیزی پیدا نشد.")
                track = js["collection"][0]
                title = track["title"]
                permalink = track["permalink_url"]
                return permalink, title

    try:
        try:
            # 🎬 دانلود از یوتیوب
            filename, title = await asyncio.to_thread(from_youtube, query)
            await msg.edit_text(f"✅ از YouTube پیدا شد: {title}\n📤 درحال ارسال فایل MP3 ...")
            await message.reply_audio(filename, title=title, performer="YouTube 🎧")
            os.remove(filename)
            await msg.delete()

        except Exception as e1:
            print("YouTube failed:", e1)
            await msg.edit_text("⚠️ یوتیوب در دسترس نیست، تلاش از SoundCloud ...")

            try:
                url, title = await from_soundcloud(query)
                await msg.edit_text(f"🎶 از SoundCloud پیدا شد:\n<b>{title}</b>\n🔗 {url}", parse_mode="HTML")
            except Exception as e2:
                await msg.edit_text(f"❌ هیچ منبعی پیدا نشد.\n\nYouTube: {e1}\nSoundCloud: {e2}")

    except Exception as e:
        await msg.edit_text(f"❌ خطا: {e}")

if __name__ == "__main__":
    print("✅ Sara Music Downloader started.")
    app.run()
