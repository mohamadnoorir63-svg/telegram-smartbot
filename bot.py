import os
from pyrogram import Client

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

    # فقط اگر پیام شامل لینک t.me یا @username باشد
    if "t.me/" in text or "telegram.me/" in text or text.startswith("@"):
        try:
            await client.join_chat(text)
            await message.reply_text(f"🎉 با موفقیت جوین شدم → {text}")
            print(f"✅ Joined successfully → {text}")
        except Exception as e:
            err = str(e)
            await message.reply_text(f"❌ خطا در جوین:\n`{err}`")
            print(f"⚠️ Error joining {text}: {err}")

# ---------- 🚀 شروع ----------
print("✅ ربات آماده است. فقط لینک بفرست تا جوین شود...")
app.run()
