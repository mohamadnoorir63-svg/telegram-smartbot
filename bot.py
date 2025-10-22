from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import os
import yt_dlp
import asyncio

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

app = Client("userbot.session", api_id=API_ID, api_hash=API_HASH)


@app.on_message(filters.text)
async def music_downloader(client, message):
    text = (message.text or "").strip()

    # تشخیص دستورات کاربر
    if text.startswith("/music") or text.startswith("!music"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            await message.reply_text("❌ لطفاً نام آهنگ یا لینک رو بنویس:\nمثلاً: `/music Arash Broken Angel`")
            return
        query = parts[1].strip()
    elif text.lower().startswith("آهنگ "):
        query = text[len("آهنگ "):].strip()
    elif text.lower().startswith("music "):
        query = text[len("music "):].strip()
    elif text.lower().startswith("musik "):
        query = text[len("musik "):].strip()
    else:
        return

    m = await message.reply_text(f"🎧 در حال جستجو برای آهنگ `{query}` ...")

    if not os.path.exists("downloads"):
        os.mkdir("downloads")

    # تابع برای دانلود آهنگ
    async def try_download():
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": "downloads/%(title)s.%(ext)s",
            "quiet": True,
            "noplaylist": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if "http" in query:
                info = ydl.extract_info(query, download=True)
            else:
                info = ydl.extract_info(f"ytsearch1:{query}", download=True)["entries"][0]
            return ydl.prepare_filename(info), info

    try:
        file_path, info = await asyncio.to_thread(try_download)
        title = info.get("title", "Unknown Title")
        artist = info.get("uploader", "Unknown Artist")
        url = info.get("webpage_url", "")

        # دکمه‌های زیر آهنگ
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🎧 لینک آهنگ", url=url if url else "https://www.youtube.com"),
                InlineKeyboardButton("🔁 دانلود دوباره", callback_data=f"redownload|{query}")
            ],
            [
                InlineKeyboardButton("🎵 آهنگ بعدی", callback_data="next_song"),
                InlineKeyboardButton("❌ حذف پیام", callback_data="delete_msg")
            ]
        ])

        await m.edit_text(f"📤 در حال ارسال آهنگ `{title}` ...")

        await message.reply_audio(
            audio=file_path,
            title=title,
            performer=artist,
            caption=f"🎶 {title}\n👤 {artist}\n\nارسال شده توسط 🤖 *خنگول موزیک بات*",
            reply_markup=buttons
        )

        os.remove(file_path)
        await m.delete()

    except Exception as e:
        await m.edit_text(f"❌ خطا در دریافت آهنگ:\n`{e}`")


# 🎛 پاسخ به دکمه‌ها
@app.on_callback_query()
async def callback_handler(client, query):
    data = query.data or ""
    if data.startswith("delete_msg"):
        await query.message.delete()
        await query.answer("🗑️ پیام حذف شد", show_alert=False)
    elif data.startswith("redownload"):
        q = data.split("|", 1)[1] if "|" in data else None
        if not q:
            await query.answer("❌ خطا در دریافت متن", show_alert=True)
            return
        await query.message.reply_text(f"🔁 در حال دانلود مجدد آهنگ: {q}")
        await music_downloader(client, type("msg", (), {"text": q, "reply_text": query.message.reply_text}))
        await query.answer("✅ درخواست مجدد ثبت شد", show_alert=False)
    elif data == "next_song":
        await query.answer("🎶 آهنگ بعدی هنوز فعال نشده 😉", show_alert=True)
    else:
        await query.answer("⛔ دکمه ناشناخته", show_alert=True)


print("🎧 Music Bot Online with Buttons...")
app.run()
