import os
import re
import asyncio
from pyrogram import Client, filters
from pyrogram.errors import FloodWait

# ---------- ⚙️ تنظیمات ----------
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

# ---------- 📱 ساخت یوزربات ----------
app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# ---------- 🧠 تابع بررسی عضویت ----------
async def is_joined(client, chat_id):
    try:
        me = await client.get_me()
        member = await client.get_chat_member(chat_id, me.id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False


# ---------- 🔁 تابع جوین با بررسی واقعی ----------
async def safe_join(client, link):
    try:
        chat = await client.join_chat(link)
        await asyncio.sleep(2)
        if await is_joined(client, chat.id):
            print(f"✅ Joined successfully: {link}")
            return True
        else:
            print(f"❌ Not actually joined: {link}")
            return False
    except FloodWait as e:
        print(f"⏳ FloodWait: {e.value}s for {link}")
        await asyncio.sleep(e.value)
        return await safe_join(client, link)
    except Exception as e:
        print(f"⚠️ Error joining {link}: {e}")
        return False


# ---------- 🤖 تابع اصلی جوین ----------
async def smart_join(client, message, raw_link):
    link = re.sub(r"[\u200b\u200c\uFEFF\s]+", "", raw_link).strip()
    if not link:
        return

    try:
        joined = await safe_join(client, link)
        if joined:
            await message.reply_text(f"✅ با موفقیت عضو شدم:\n`{link}`")
        else:
            await message.reply_text(f"❌ نتونستم وارد بشم:\n`{link}`")

    except Exception as e:
        err = str(e)
        msg = f"❌ خطا در جوین:\n`{err}`\n\n🔗 `{link}`"
        await message.reply_text(msg)


# ---------- 📩 فقط پیوی و کانال ----------
@app.on_message((filters.private | filters.channel) & filters.text)
async def handle_links(client, message):
    text = message.text.strip()
    links = re.findall(r"(https?://t\.me/[^\s]+|https?://telegram\.me/[^\s]+|@[\w\d_]+)", text)

    if not links:
        if message.chat.type == "private":
            await message.reply_text("📎 لینک تلگرام بفرست تا امتحان کنم جوین شم.")
        return

    for link in links:
        await smart_join(client, message, link)


# ---------- 🚫 نادیده گرفتن گروه‌ها ----------
@app.on_message(filters.group)
async def ignore_groups(client, message):
    return


# ---------- 🚀 شروع ----------
print("🚀 ربات آماده است — فقط از پیوی یا کانال لینک‌ها را بررسی می‌کند...")
app.run()
