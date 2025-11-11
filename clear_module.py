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

    def detect_lang(text):
        if any("\u0600" <= c <= "\u06FF" for c in text):
            return "fa"
        return "en"

    @client.on(events.NewMessage(pattern=r"(?i)^(?:پاکسازی|clear)(?:\s+(\d+|@\w+))?$"))
    async def clear_messages(event):
        lang = detect_lang(event.raw_text)
        if not await is_admin_or_sudo(event):
            return await send_temp_msg(event, "❌ شما اجازه دسترسی ندارید." if lang=="fa" else "❌ You don't have permission.")

        arg = event.pattern_match.group(1)
        me = await event.client.get_me()
        chat_id = event.chat_id
        deleted_count = 0

        # تعیین هدف پاکسازی
        target_user = None
        limit = 100  # پیش فرض حداکثر ۱۰۰ پیام اگر عدد داده نشده

        if arg:
            if arg.isdigit():
                limit = int(arg)
            elif arg.startswith("@"):
                try:
                    entity = await event.client.get_entity(arg)
                    target_user = entity.id
                except:
                    return await send_temp_msg(event, "❌ کاربر یافت نشد!" if lang=="fa" else "❌ User not found!")
            else:
                # ممکنه ID داده شده باشه
                try:
                    target_user = int(arg)
                except:
                    return await send_temp_msg(event, "❌ ورودی نامعتبر!" if lang=="fa" else "❌ Invalid input!")

        # گرفتن پیام‌ها
        messages = await event.client.get_messages(chat_id, limit=limit)

        for msg in messages:
            try:
                if target_user:
                    if msg.sender_id != target_user:
                        continue
                else:
                    # پاک کردن پیام‌های ربات و خود فردی که دستور داد
                    if msg.sender_id != me.id and msg.sender_id != event.sender_id:
                        continue
                await msg.delete()
                deleted_count += 1
            except:
                pass

        info_sender = await event.client.get_entity(event.sender_id)
        sender_name = f"{info_sender.first_name or ''} {info_sender.last_name or ''}".strip()
        # متن گزارش
        report_text = f"🧹 دستور پاکسازی توسط {sender_name} اجرا شد.\n✅ تعداد پیام‌های پاک شده: {deleted_count}"
        if target_user:
            info_target = await event.client.get_entity(target_user)
            target_name = f"{info_target.first_name or ''} {info_target.last_name or ''}".strip()
            report_text += f"\n👤 پیام‌های پاک شده مربوط به: {target_name}"

        await send_temp_msg(event, report_text, seconds=10)
