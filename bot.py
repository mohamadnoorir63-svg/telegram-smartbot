from pyrogram import Client, filters
import yt_dlp, os, asyncio, re

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION_STRING = os.getenv("SESSION_STRING", "")

app = Client("userbot_test", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
DOWNLOAD_PATH = "downloads"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

@app.on_message(filters.text & (filters.private | filters.me))
async def handler(client, message):
    print(f"📩 Message received: {message.text}")
    if message.text.lower() == "ping":
        await message.reply("✅ Userbot آماده‌ست!")
    elif message.text.startswith("آهنگ "):
        await message.reply("🎵 دریافت شد، ولی فعلاً در حالت تست هستم.")

async def main():
    print("🚀 Starting userbot...")
    try:
        await app.start()
        me = await app.get_me()
        print(f"✅ Logged in as: {me.first_name} ({me.id})")
        print("📢 منتظر پیام هستم...")
        await asyncio.Future()
    except Exception as e:
        print(f"❌ Error starting userbot: {e}")

if __name__ == "__main__":
    asyncio.run(main())
