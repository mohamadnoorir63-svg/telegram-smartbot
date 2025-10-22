from pyrogram import Client, filters
import os

# گرفتن api_id و api_hash از Config Vars
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

# اتصال با سشن ساخته‌شده
app = Client("userbot.session", api_id=API_ID, api_hash=API_HASH)

@app.on_message(filters.command("ping"))
def ping(_, msg):
    msg.reply_text("✅ ربات فعاله و آنلاین!")

print("✅ Bot is running...")
app.run()
