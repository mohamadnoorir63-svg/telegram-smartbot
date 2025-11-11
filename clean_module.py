import asyncio
from telethon import events

# -------------------- توابع کمکی --------------------
async def send_temp_msg(event, text, seconds=10):
    """ارسال پیام و حذف خودکار"""
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

# -------------------- ثبت دستورات پاکسازی --------------------
def register_clean_commands(client, SUDO_USERS):
    async def check_permission(event):
        sender = event.sender_id
        participants = await event.client.get_participants(event.chat_id)
        admins = [p.id for p in participants if getattr(p, 'admin_rights', None)]
        return sender in admins or sender in SUDO_USERS

    @client.on(events.NewMessage(pattern=r"(?i)^(?:پاکسازی|clean)(?:\s+(.+))?$"))
    async def clean_messages(event):
        lang = detect_lang(event.raw_text)
        if not await check_permission(event):
            return await send_temp_msg(event, "❌ شما اجازه دسترسی به این دستور را ندارید." if lang=="fa" else "❌ You don't have permission.")

        arg = event.pattern_match.group(1)
        reply = await event.get_reply_message()
        messages_to_delete = []

        try:
            # اگر عدد داده شده
            number = int(arg)
            if number > 10000:  # محدودیت
                number = 10000
            async for msg in event.client.iter_messages(event.chat_id, limit=number):
                messages_to_delete.append(msg)
        except:
            # اگر ریپلای باشد پاک کردن پیام‌های کاربر
            if reply:
                user_id = reply.sender_id
                async for msg in event.client.iter_messages(event.chat_id, limit=10000):
                    if msg.sender_id == user_id:
                        messages_to_delete.append(msg)
            else:
                # پاکسازی کل گروه
                async for msg in event.client.iter_messages(event.chat_id, limit=10000):
                    messages_to_delete.append(msg)

        if not messages_to_delete:
            return await send_temp_msg(event, "❌ هیچ پیامی برای حذف یافت نشد." if lang=="fa" else "❌ No messages found to delete.")

        # حذف پیام‌ها با سرعت کنترل شده
        count = 0
        for m in messages_to_delete:
            try:
                await m.delete()
                count += 1
            except:
                pass
            if count % 50 == 0:
                await asyncio.sleep(1)

        sender_name = (await event.get_sender()).first_name
        command_used = event.raw_text
        report_text = (
            f"✅ دستور پاکسازی اجرا شد!\n"
            f"👤 دستور دهنده: {sender_name}\n"
            f"💬 دستور: {command_used}\n"
            f"🗑️ تعداد پیام‌های پاک شده: {count}"
            if lang=="fa" else
            f"✅ Clean command executed!\n"
            f"👤 Executor: {sender_name}\n"
            f"💬 Command: {command_used}\n"
            f"🗑️ Messages deleted: {count}"
        )

        await send_temp_msg(event, report_text, seconds=10)

    @client.on(events.NewMessage(pattern=r"(?i)^(?:حذف|delete)(?:\s+(.+))?$"))
    async def delete_number(event):
        lang = detect_lang(event.raw_text)
        if not await check_permission(event):
            return await send_temp_msg(event, "❌ شما اجازه دسترسی به این دستور را ندارید." if lang=="fa" else "❌ You don't have permission.")

        arg = event.pattern_match.group(1)
        if not arg:
            return await send_temp_msg(event, "❌ لطفا تعداد پیام‌ها برای حذف را مشخص کنید." if lang=="fa" else "❌ Please specify number of messages to delete.")

        try:
            number = int(arg)
            if number > 10000:
                number = 10000
        except:
            return await send_temp_msg(event, "❌ مقدار عددی معتبر وارد کنید." if lang=="fa" else "❌ Please provide a valid number.")

        messages_to_delete = []
        async for msg in event.client.iter_messages(event.chat_id, limit=number):
            messages_to_delete.append(msg)

        if not messages_to_delete:
            return await send_temp_msg(event, "❌ هیچ پیامی برای حذف یافت نشد." if lang=="fa" else "❌ No messages found to delete.")

        count = 0
        for m in messages_to_delete:
            try:
                await m.delete()
                count += 1
            except:
                pass
            if count % 50 == 0:
                await asyncio.sleep(1)

        sender_name = (await event.get_sender()).first_name
        command_used = event.raw_text
        report_text = (
            f"✅ دستور حذف اجرا شد!\n"
            f"👤 دستور دهنده: {sender_name}\n"
            f"💬 دستور: {command_used}\n"
            f"🗑️ تعداد پیام‌های حذف شده: {count}"
            if lang=="fa" else
            f"✅ Delete command executed!\n"
            f"👤 Executor: {sender_name}\n"
            f"💬 Command: {command_used}\n"
            f"🗑️ Messages deleted: {count}"
        )

        await send_temp_msg(event, report_text, seconds=10)
