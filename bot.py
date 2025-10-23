import os
import asyncio
from pyrogram import Client

# خواندن مقادیر از Config Vars
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

# ساخت کلاینت
app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

async def main():
    print("🚀 در حال اتصال به تلگرام با session تنظیم‌شده در Heroku ...")
    async with app:
        print("✅ اتصال موفق! حالا لینک رو وارد کن (یا exit برای خروج):")
        while True:
            link = input("🔗 لینک: ").strip()
            if link.lower() in ["exit", "خروج", "quit"]:
                break
            if not link:
                continue
            try:
                await app.join_chat(link)
                print(f"🎉 با موفقیت جوین شدی: {link}")
            except Exception as e:
                print(f"❌ خطا در جوین {link}: {repr(e)}")

asyncio.run(main())
