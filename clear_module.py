# clear_module.py
import asyncio
from telethon import events

def register_clear_commands(client, SUDO_USERS):
    
    async def is_admin_or_sudo(event):
        if event.sender_id in SUDO_USERS:
            return True
        if not event.is_group:
            return False
        try:
            perm = await event.client.get_permissions(event.chat_id, event.sender_id)
            return perm.is_admin
        except:
            return False

    async def send_temp_msg(event, text, seconds=10):
        msg = await event.reply(text)
        await asyncio.sleep(seconds)
        try:
            await msg.delete()
        except:
            pass
        return msg

    async def get_user_from_input(event, input_str):
        s = input_str.strip() if input_str else ""
        try:
            if s.startswith("@"):
                ent = await event.client.get_entity(s)
                return ent.id
            if s.isdigit() or (s.startswith("-") and s[1:].isdigit()):
                return int(s)
        except:
            return None
        reply = await event.get_reply_message()
        if reply:
            return reply.sender_id
        return None

    # حذف پیام‌ها
    @client.on(events.NewMessage(pattern=r"(?i)^(?:پاکسازی|clear)(?:\s+(.+))?$"))
    async def clear_messages(event):
        lang = "fa" if any("\u0600" <= c <= "\u06FF" for c in event.raw_text) else "en"
        if not await is_admin_or_sudo(event):
            return await send_temp_msg(event, "❌ شما اجازه دسترسی ندارید." if lang=="fa" else "❌ You don't have permission.")
        
        arg = event.pattern_match.group(1)
        limit = 100  # پیشفرض تعداد پیام
        target_user = None

        if arg:
            if arg.isdigit():
                limit = int(arg)
            else:
                target_user = await get_user_from_input(event, arg)
        count = 0
        async for msg in event.client.iter_messages(event.chat_id, limit=limit):
            if target_user:
                if msg.sender_id != target_user:
                    continue
            if msg.is_self or msg.out or msg.sender_id == target_user:
                try:
                    await msg.delete()
                    count += 1
                except:
                    pass
            else:
                try:
                    await msg.delete()
                    count += 1
                except:
                    pass

        text = (f"🗑 دستور پاکسازی اجرا شد!\n"
                f"دستور دهنده: {event.sender_id}\n"
                f"تعداد پیام پاک شده: {count}") if lang=="fa" else (
                f"🗑 Clear command executed!\n"
                f"Invoker: {event.sender_id}\n"
                f"Messages deleted: {count}")
        await send_temp_msg(event, text, seconds=10)
