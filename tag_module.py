import asyncio
from telethon import events

# دریافت کاربران آنلاین (فعال) یا آفلاین (غیرفعال)
async def get_active_users(client, chat_id):
    participants = await client.get_participants(chat_id)
    # می‌توانیم کاربران آنلاین را بر اساس status یا last_seen تشخیص دهیم
    active_users = [p for p in participants if getattr(p.status, 'was_online', None)]
    return active_users

async def get_admins(client, chat_id):
    participants = await client.get_participants(chat_id)
    admins = [p for p in participants if getattr(p, 'admin_rights', None)]
    return admins

async def tag_users(event, users, text_prefix="", delay=0.5):
    """تگ کردن کاربران با متن مشخص"""
    msg_text = text_prefix + "\n"
    for u in users:
        username = f"@{u.username}" if u.username else u.first_name or str(u.id)
        msg_text += f"{username} "
    msg = await event.reply(msg_text)
    await asyncio.sleep(delay)
    return msg

# دستورات آماده برای ثبت در client اصلی
def register_tag_commands(client):
    # تگ همه
    @client.on(events.NewMessage(pattern=r"(?i)^(?:تگ همه|tagall)$"))
    async def tag_all(event):
        participants = await event.client.get_participants(event.chat_id)
        await tag_users(event, participants, text_prefix="📢 تگ همه:")

    # تگ مدیران
    @client.on(events.NewMessage(pattern=r"(?i)^(?:تگ مدیران|tagadmins)$"))
    async def tag_admins(event):
        admins = await get_admins(event.client, event.chat_id)
        if not admins:
            await event.reply("❌ مدیر پیدا نشد!")
        else:
            await tag_users(event, admins, text_prefix="👑 تگ مدیران:")

    # تگ کاربران فعال
    @client.on(events.NewMessage(pattern=r"(?i)^(?:تگ فعال|tagactive)$"))
    async def tag_active(event):
        active = await get_active_users(event.client, event.chat_id)
        if not active:
            await event.reply("❌ کاربر فعالی پیدا نشد!")
        else:
            await tag_users(event, active, text_prefix="🟢 کاربران فعال:")

    # تگ کاربران غیر فعال
    @client.on(events.NewMessage(pattern=r"(?i)^(?:تگ غیرفعال|taginactive)$"))
    async def tag_inactive(event):
        participants = await event.client.get_participants(event.chat_id)
        active = await get_active_users(event.client, event.chat_id)
        inactive = [u for u in participants if u not in active]
        if not inactive:
            await event.reply("❌ کاربر غیرفعالی پیدا نشد!")
        else:
            await tag_users(event, inactive, text_prefix="⚪ کاربران غیرفعال:")
