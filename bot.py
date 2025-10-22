from pyrogram import Client, filters

# از همون فایل session استفاده کن
app = Client("userbot.session")

@app.on_message(filters.command("ping"))
def ping(_, msg):
    msg.reply_text("✅ ربات فعاله!")

print("✅ Bot is running...")
app.run()
