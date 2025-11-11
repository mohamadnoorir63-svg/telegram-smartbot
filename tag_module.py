import asyncio
from telethon import events

# -------------------- توابع کمکی --------------------
async def get_active_users(client, chat_id):
    participants = await client.get_participants(chat_id)
    active_users = [p for p in participants if getattr(p.status, '__class__', None).__name__ in ('UserStatusOnline', 'UserStatusRecently')]
    return active_users

async def get_admins(client, chat_id):
    participants = await client.get_participants(chat_id)
    admins = [p for p in participants if getattr(p, 'admin_rights', None)]
    return admins

async def send_temp_msg(event, text, seconds=10):
    """ارسال پیام و حذف خودکار بعد از مدت زمان"""
    msg = await event.reply(text)
    await asyncio.sleep(seconds)
    try:
        await msg.delete()
    except:
        pass
    return msg

def detect_lang(text):
    """تشخیص فارسی یا انگلیسی"""
    if any("\u0600" <= c <= "\u06FF" for c in text):
        return "fa"
    return "en"

async def tag_users(event, users, SUDO_USERS, text_prefix="", chunk_size=20):
    """تگ کردن کاربران با متن مشخص و تقسیم پیام‌ها"""
    # فقط مدیر یا سودو مجاز
    sender = event.sender_id
    participants = await event.client.get_participants(event.chat_id)
    admins = [p.id for p in participants if getattr(p, 'admin_rights', None)]
    if sender not in admins and sender not in SUDO_USERS:
        return await send_temp_msg(event, "❌ شما اجازه دسترسی به این دستور را ندارید.")

    if not users:
        return await send_temp_msg(event, "❌ کاربری برای تگ پیدا نشد!")

    lines = [text_prefix]
    count = 0
    for u in users:
        username = f"@{u.username}" if u.username else u.first_name or str(u.id)
        lines.append(username)
        count += 1
        # ارسال هر chunk_size نفر
        if count % chunk_size == 0 or count == len(users):
            msg_text = "\n".join(lines)
            await event.reply(msg_text)
            lines = [text_prefix]  # reset
            # جلوگیری از اسپم: کمی تأخیر
            await asyncio.sleep(1)

# -------------------- ثبت دستورات --------------------
def register_tag_commands(client, SUDO_USERS):
    # تگ همه
    @client.on(events.NewMessage(pattern=r"(?i)^(?:تگ همه|tagall)$"))
    async def tag_all(event):
        lang = detect_lang(event.raw_text)
        participants = await event.client.get_participants(event.chat_id)
        prefix = "📢 تگ همه:" if lang=="fa" else "📢 Tag all:"
        await tag_users(event, participants, SUDO_USERS, text_prefix=prefix, chunk_size=20)

    # تگ مدیران
    @client.on(events.NewMessage(pattern=r"(?i)^(?:تگ مدیران|tagadmins)$"))
    async def tag_admins(event):
        lang = detect_lang(event.raw_text)
        admins = await get_admins(event.client, event.chat_id)
        prefix = "👑 تگ مدیران:" if lang=="fa" else "👑 Tag admins:"
        await tag_users(event, admins, SUDO_USERS, text_prefix=prefix, chunk_size=20)

    # تگ کاربران فعال
    @client.on(events.NewMessage(pattern=r"(?i)^(?:تگ فعال|tagactive)$"))
    async def tag_active(event):
        lang = detect_lang(event.raw_text)
        active = await get_active_users(event.client, event.chat_id)
        prefix = "🟢 کاربران فعال:" if lang=="fa" else "🟢 Active users:"
        await tag_users(event, active, SUDO_USERS, text_prefix=prefix, chunk_size=20)

    # تگ کاربران غیرفعال
    @client.on(events.NewMessage(pattern=r"(?i)^(?:تگ غیرفعال|taginactive)$"))
    async def tag_inactive(event):
        lang = detect_lang(event.raw_text)
        participants = await event.client.get_participants(event.chat_id)
        active = await get_active_users(event.client, event.chat_id)
        inactive = [u for u in participants if u not in active]
        prefix = "⚪ کاربران غیرفعال:" if lang=="fa" else "⚪ Inactive users:"
        await tag_users(event, inactive, SUDO_USERS, text_prefix=prefix, chunk_size=20)
