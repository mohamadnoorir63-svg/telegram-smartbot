import os
import re
from telethon import TelegramClient, events
from telethon.sessions import StringSession

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

warns = {}  # برای ذخیره اخطارها

# ==================== دستورات مدیریتی ====================

@client.on(events.NewMessage(pattern=r"(?i)^(?:/ban|بن)\s+(.*)"))
async def ban_user(event):
    if not event.is_group:
        return await event.reply("این دستور فقط در گروه‌ها کار می‌کند.")
    user = await get_user_from_input(event, event.pattern_match.group(1))
    if not user:
        return await event.reply("کاربر یافت نشد ❌")

    try:
        await event.client.edit_permissions(event.chat_id, user, view_messages=False)
        await event.reply(f"🚫 کاربر [{user}] بن شد.")
    except Exception as e:
        await event.reply(f"خطا در بن کردن: {e}")

@client.on(events.NewMessage(pattern=r"(?i)^(?:/unban|حذف بن)\s+(.*)"))
async def unban_user(event):
    user = await get_user_from_input(event, event.pattern_match.group(1))
    if not user:
        return await event.reply("کاربر یافت نشد ❌")
    try:
        await event.client.edit_permissions(event.chat_id, user, view_messages=True)
        await event.reply(f"✅ کاربر [{user}] از بن خارج شد.")
    except Exception as e:
        await event.reply(f"خطا در حذف بن: {e}")

@client.on(events.NewMessage(pattern=r"(?i)^(?:/mute|سکوت)\s+(.*)"))
async def mute_user(event):
    user = await get_user_from_input(event, event.pattern_match.group(1))
    if not user:
        return await event.reply("کاربر یافت نشد ❌")
    try:
        await event.client.edit_permissions(event.chat_id, user, send_messages=False)
        await event.reply(f"🔇 کاربر [{user}] در حالت سکوت قرار گرفت.")
    except Exception as e:
        await event.reply(f"خطا در سکوت: {e}")

@client.on(events.NewMessage(pattern=r"(?i)^(?:/unmute|حذف سکوت)\s+(.*)"))
async def unmute_user(event):
    user = await get_user_from_input(event, event.pattern_match.group(1))
    if not user:
        return await event.reply("کاربر یافت نشد ❌")
    try:
        await event.client.edit_permissions(event.chat_id, user, send_messages=True)
        await event.reply(f"🔊 کاربر [{user}] از حالت سکوت خارج شد.")
    except Exception as e:
        await event.reply(f"خطا در حذف سکوت: {e}")

@client.on(events.NewMessage(pattern=r"(?i)^(?:/warn|اخطار)\s+(.*)"))
async def warn_user(event):
    user = await get_user_from_input(event, event.pattern_match.group(1))
    if not user:
        return await event.reply("کاربر یافت نشد ❌")

    warns[user] = warns.get(user, 0) + 1
    if warns[user] >= 3:
        await event.client.edit_permissions(event.chat_id, user, view_messages=False)
        await event.reply(f"🚫 کاربر [{user}] سه اخطار گرفت و بن شد.")
    else:
        await event.reply(f"⚠️ اخطار {warns[user]} برای [{user}] ثبت شد.")

@client.on(events.NewMessage(pattern=r"(?i)^(?:/unwarn|حذف اخطار)\s+(.*)"))
async def unwarn_user(event):
    user = await get_user_from_input(event, event.pattern_match.group(1))
    if not user:
        return await event.reply("کاربر یافت نشد ❌")

    warns[user] = 0
    await event.reply(f"✅ اخطارهای [{user}] پاک شدند.")

# ==================== توابع کمکی ====================

async def get_user_from_input(event, input_str):
    """پیدا کردن کاربر از @ یا ID"""
    input_str = input_str.strip()
    user = None
    try:
        if re.match(r"^@\w+", input_str):
            user = await event.client.get_entity(input_str)
            return user.id
        elif re.match(r"^\d+$", input_str):
            return int(input_str)
        else:
            reply = await event.get_reply_message()
            if reply:
                return reply.sender_id
    except:
        pass
    return None

# =====================================================

with client:
    print("✅ Userbot فعال و آماده مدیریت گروه‌هاست...")
    client.run_until_disconnected()
