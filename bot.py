from pyrogram import Client, filters
from pyrogram.types import ChatPermissions
import os

# ----- تنظیمات اصلی -----
api_id = int(os.getenv("API_ID", 22825957))
api_hash = os.getenv("API_HASH", "bbb98a7a622f85a91a10865b6da75247")
session_name = "userbot.session"

bot = Client(session_name, api_id=api_id, api_hash=api_hash)

# فقط تو بتونی از دستورات مدیریتی استفاده کنی
OWNER_ID = 7089376754

def is_owner(func):
    async def wrapper(client, message):
        if message.from_user.id == OWNER_ID:
            return await func(client, message)
        else:
            await message.reply_text("❌ شما اجازه استفاده از این دستور را ندارید.")
    return wrapper

# ----- خوشامد -----
@bot.on_message(filters.new_chat_members)
async def welcome(client, message):
    for user in message.new_chat_members:
        await message.reply_text(f"👋 خوش اومدی {user.mention} به {message.chat.title}!")

# ----- قفل لینک -----
@bot.on_message(filters.regex("t.me/") & filters.group)
async def block_links(client, message):
    await message.delete()
    await message.reply_text("🚫 ارسال لینک در گروه ممنوع است!")

# ----- بن -----
@bot.on_message(filters.command("ban") & filters.group)
@is_owner
async def ban_user(client, message):
    if len(message.command) > 1:
        user = message.command[1]
        try:
            await message.chat.ban_member(user)
            await message.reply_text(f"🚫 کاربر {user} بن شد!")
        except Exception as e:
            await message.reply_text(f"❌ خطا: {e}")
    elif message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        await message.chat.ban_member(user_id)
        await message.reply_text("🚫 کاربر ریپلای‌شده بن شد!")
    else:
        await message.reply_text("⚠️ لطفاً آی‌دی یا ریپلای بده!")

# ----- کیک -----
@bot.on_message(filters.command("kick") & filters.group)
@is_owner
async def kick_user(client, message):
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        await message.chat.ban_member(user_id)
        await message.chat.unban_member(user_id)
        await message.reply_text("👢 کاربر با موفقیت اخراج شد!")
    else:
        await message.reply_text("⚠️ روی پیام کاربر ریپلای کن!")

# ----- تگ همه -----
@bot.on_message(filters.command("tagall") & filters.group)
@is_owner
async def tag_all(client, message):
    members = []
    async for m in client.get_chat_members(message.chat.id):
        members.append(m.user.mention)
    chunk_size = 10
    for i in range(0, len(members), chunk_size):
        await message.reply_text(" ".join(members[i:i+chunk_size]))

# ----- اجرای ربات -----
print("✅ Bot is running...")
bot.run()
