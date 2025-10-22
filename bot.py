from pyrogram import Client, filters
import os

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

# فقط نام سشن بدون پسوند .session
app = Client("userbot", api_id=API_ID, api_hash=API_HASH)

@app.on_message(filters.command("ping"))
def ping(_, msg):
    msg.reply_text("✅ ربات فعاله و آنلاین!")

print("✅ Bot is running...")
app.run()
