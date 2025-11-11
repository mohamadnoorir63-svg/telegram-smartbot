import os
from telethon import TelegramClient, events
from telethon.sessions import StringSession

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

@client.on(events.NewMessage)
async def handler(event):
    text = event.raw_text.lower()
    
    if "سلام" in text:
        await event.reply("سلام 🌷 خوش اومدی!")
    elif text == "/ping":
        await event.reply("✅ Userbot فعاله!")
    elif text.startswith("/ban") and event.is_group:
        if event.sender_id == (await event.client.get_me()).id:
            await event.reply("من ادمین نیستم 😅")
        else:
            try:
                user = await event.get_reply_message()
                if user:
                    await event.client.edit_permissions(event.chat_id, user.sender_id, view_messages=False)
                    await event.reply("🚫 کاربر بن شد.")
                else:
                    await event.reply("باید روی پیام کاربر ریپلای کنی.")
            except Exception as e:
                await event.reply(f"خطا: {e}")

with client:
    print("✅ Userbot در حال اجراست ...")
    client.run_until_disconnected()
