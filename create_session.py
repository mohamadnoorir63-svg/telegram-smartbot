from pyrogram import Client

api_id = 22825957
api_hash = "bbb98a7a622f85a91a10865b6da75247"

app = Client("userbot", api_id=api_id, api_hash=api_hash)
app.start()
print("✅ فایل سشن ساخته شد و در userbot.session ذخیره شد.")
app.stop()
