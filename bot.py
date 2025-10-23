import os
from pyrogram import Client
import re

# ---------- ⚙️ تنظیمات ----------
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

# ---------- 📱 ساخت یوزربات ----------
app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# ---------- 📩 دریافت لینک و جوین ----------
@app.on_message()
async def join_from_message(client, message):
    if not message.text:
        return

    text = message.text.strip()
    links = re.findall(r"(https?://t\.me/[^\s]+|https?://telegram\.me/[^\s]+|@[\w\d_]+)", text)

    if not links:
        return  # اگر هیچ لینکی نبود، بی‌خیال شو

    for link in links:
        link = link.strip().replace("\u200c", "").replace("\u200b", "").replace(" ", "")

        try:
            # برای هر نوع لینک، join_chat خودش تشخیص می‌دهد
            await client.join_chat(link)
            await message.reply_text(f"✅ با موفقیت وارد شدم → {link}")
            print(f"✅ Joined successfully → {link}")

        except Exception as e:
            err = str(e)
            await message.reply_text(f"❌ خطا در جوین {link}:\n`{err}`")
            print(f"⚠️ Error joining {link}: {err}")

# ---------- 🚀 شروع ----------
print("🚀 ربات آماده است — فقط لینک بفرست تا وارد شود (هر نوع لینک پشتیبانی می‌شود)...")
app.run()
