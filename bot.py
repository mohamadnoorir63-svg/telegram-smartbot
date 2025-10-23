import os, asyncio, aiohttp
from pyrogram import Client, filters

# ===== 🌍 Environment =====
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
SUDO_ID = int(os.getenv("SUDO_ID"))
# ===========================

app = Client("sara_userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# 🎵 سرچ موزیک با API عمومی Saavn/Deezer
async def search_music(query):
    url = f"https://saavn.me/search/songs?query={query}"
    async with aiohttp.ClientSession() as ses:
        async with ses.get(url) as resp:
            data = await resp.json()
            songs = data.get("data", {}).get("results", [])
            if not songs:
                raise Exception("چیزی پیدا نشد.")
            first = songs[0]
            return {
                "title": first["title"],
                "artist": first["primaryArtists"],
                "mp3": first["downloadUrl"][-1]["link"],  # لینک کیفیت 320kbps
                "image": first["image"][-1]["link"],
            }

@app.on_message(filters.me & filters.regex(r"^موزیک (.+)"))
async def send_music(client, message):
    query = message.matches[0].group(1).strip()
    msg = await message.reply_text(f"🎧 درحال جست‌وجوی موزیک: <b>{query}</b>", parse_mode="html")

    try:
        info = await search_music(query)
        await msg.edit_text(
            f"🎵 <b>{info['title']}</b>\n👤 {info['artist']}\n\n📤 درحال ارسال فایل MP3 ...",
            parse_mode="html"
        )
        await message.reply_audio(
            info["mp3"],
            title=info["title"],
            performer=info["artist"],
            thumb=info["image"]
        )
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ خطا یا موزیک یافت نشد.\n{e}", parse_mode="html")

if __name__ == "__main__":
    print("✅ Sara Music (API Version) started.")
    app.run()
