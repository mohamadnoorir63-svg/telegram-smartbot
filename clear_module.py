# clear_module.py
import asyncio
from telethon import events
from datetime import datetime

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

    async def batch_delete(client, messages):
        tasks = []
        for msg in messages:
            tasks.append(msg.delete())
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return sum(1 for r in results if r is None)

    @client.on(events.NewMessage(pattern=r"(?i)^(?:پاکسازی|clear)(?:\s+(.+))?$"))
    async def clear_messages(event):
        lang = detect_lang(event.raw_text)
        if not await is_admin_or_sudo(event):
            return await send_temp_msg(event, "❌ شما اجازه دسترسی ندارید." if lang=="fa" else "❌ You don't have permission.")

        arg = event.pattern_match.group(1)
        me = await event.client.get_me()
        chat_id = event.chat_id
        deleted_count = 0
        target_user = None
        limit = None  # None = پاکسازی کل گروه

        # تعیین هدف پاکسازی
        if arg:
            if arg.isdigit():
                limit = int(arg)
            elif arg.startswith("@"):
                try:
                    entity = await event.client.get_entity(arg)
                    target_user = entity.id
                except:
                    return await send_temp_msg(event, "❌ کاربر یا ربات یافت نشد!" if lang=="fa" else "❌ User/robot not found!")
            else:
                try:
                    target_user = int(arg)
                except:
                    return await send_temp_msg(event, "❌ ورودی نامعتبر!" if lang=="fa" else "❌ Invalid input!")

        # اگر روی پیام ریپلای شده زده شود
        reply = await event.get_reply_message()
        if reply:
            target_user = reply.sender_id

        batch_size = 500  # تعداد پیام در هر batch
        while True:
            fetch_limit = batch_size if not limit else min(batch_size, limit - deleted_count)
            messages = await event.client.get_messages(chat_id, limit=fetch_limit)
            if not messages:
                break

            to_delete = []
            for msg in messages:
                try:
                    # حذف پیام‌ها بر اساس هدف
                    if target_user:
                        if msg.sender_id != target_user:
                            continue
                    else:
                        # پاکسازی پیام‌های خود ربات، دستور دهنده، و سایر ربات‌ها
                        if not (msg.sender_id == me.id or msg.sender_id == event.sender_id):
                            # برای ربات‌ها، sender.bot = True
                            if not getattr(msg.sender, 'bot', False):
                                continue
                    to_delete.append(msg)
                except:
                    continue

            if not to_delete:
                break

            deleted = await batch_delete(event.client, to_delete)
            deleted_count += deleted

            # محدودیت تعداد
            if limit and deleted_count >= limit:
                break
            # اگر کمتر از batch_size پیام پیدا شد، پایان
            if len(to_delete) < fetch_limit:
                break

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        info_sender = await event.client.get_entity(event.sender_id)
        sender_name = f"{info_sender.first_name or ''} {info_sender.last_name or ''}".strip()

        report_text = f"🧹 دستور پاکسازی توسط {sender_name} اجرا شد.\n🕒 زمان: {now}\n✅ تعداد پیام‌های پاک شده: {deleted_count}"
        if target_user:
            info_target = await event.client.get_entity(target_user)
            target_name = f"{info_target.first_name or ''} {info_target.last_name or ''}".strip()
            report_text += f"\n👤 پیام‌های پاک شده مربوط به: {target_name}"

        await send_temp_msg(event, report_text, seconds=10)
