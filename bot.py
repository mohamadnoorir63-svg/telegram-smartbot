import os, re, json, asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from clear_module import register_clear_commands

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# -------------------- دیتاست‌ها --------------------
warns = {}       # اخطارها
banned = set()   # لیست بن
muted = set()    # لیست سکوت

# load sudo list
SUDO_FILE = "sudo.json"
if os.path.exists(SUDO_FILE):
    with open(SUDO_FILE, "r", encoding="utf-8") as f:
        try:
            sudo_data = json.load(f)
            SUDO_USERS = set(sudo_data.get("sudo_users", []))
        except:
            SUDO_USERS = set()
else:
    SUDO_USERS = set()

# -------------------- اعتبارسنجی --------------------
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

async def check_protection(event, target_user_id, lang="fa"):
    me_id = (await event.client.get_me()).id
    if target_user_id in SUDO_USERS:
        text = "❌ این کاربر سودو است و نمی‌توان او را مدیریت کرد." if lang=="fa" else "❌ This user is a sudo and cannot be managed."
        await send_temp_msg(event, text)
        return False
    if target_user_id == me_id:
        text = "❌ شما نمی‌توانید خود ربات را مدیریت کنید!" if lang=="fa" else "❌ You cannot manage me!"
        await send_temp_msg(event, text)
        return False
    if event.is_group:
        try:
            perm = await event.client.get_permissions(event.chat_id, target_user_id)
            if perm.is_admin:
                text = "❌ این کاربر مدیر گروه است و نمی‌توان او را مدیریت کرد." if lang=="fa" else "❌ This user is an admin and cannot be managed."
                await send_temp_msg(event, text)
                return False
        except:
            pass
    return True

async def send_temp_msg(event, text, seconds=10):
    """ارسال پیام و حذف خودکار بعد از مدت زمان"""
    msg = await event.reply(text)
    await asyncio.sleep(seconds)
    try:
        await msg.delete()
    except:
        pass
    return msg

# -------------------- helper: گرفتن کاربر --------------------
async def get_user_from_input(event, input_str):
    if input_str:
        s = input_str.strip()
    else:
        s = ""
    try:
        if re.match(r"^@[\w\d_]+$", s):
            ent = await event.client.get_entity(s)
            return ent.id
        if re.match(r"^\-?\d+$", s):
            return int(s)
    except:
        return None
    reply = await event.get_reply_message()
    if reply:
        return reply.sender_id
    return None

async def safe_action(event, func, target_user_id, lang="fa", **kwargs):
    if not await check_protection(event, target_user_id, lang):
        return False
    try:
        if event.is_group:
            participants = await event.client.get_participants(event.chat_id)
            if target_user_id not in [p.id for p in participants]:
                text = "❌ این کاربر در گروه نیست، الکی اعمال نشد!" if lang=="fa" else "❌ This user is not in the group, action ignored!"
                await send_temp_msg(event, text)
                return False
        await func(event.chat_id, target_user_id, **kwargs)
        return True
    except Exception as e:
        await send_temp_msg(event, f"❌ خطا: {e}" if lang=="fa" else f"❌ Error: {e}")
        return False

async def get_user_info_text(user_id):
    try:
        user = await client.get_entity(user_id)
        name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        username = f"@{user.username}" if user.username else "NoUsername"
        return f"{name} ({username}, {user_id})"
    except:
        return str(user_id)

def detect_lang(text):
    """تشخیص فارسی یا انگلیسی"""
    if any("\u0600" <= c <= "\u06FF" for c in text):
        return "fa"
    return "en"

# -------------------- مدیریت دستورات --------------------
# BAN
@client.on(events.NewMessage(pattern=r"(?i)^(?:بن|ban)(?:\s+(.+))?$"))
async def ban_user(event):
    lang = detect_lang(event.raw_text)
    if not await is_admin_or_sudo(event):
        return await send_temp_msg(event, "❌ شما اجازه دسترسی ندارید." if lang=="fa" else "❌ You don't have permission.")
    arg = event.pattern_match.group(1)
    user = await get_user_from_input(event, arg)
    if not user:
        return await send_temp_msg(event, "❌ کاربر یافت نشد!" if lang=="fa" else "❌ User not found!")
    if await safe_action(event, client.edit_permissions, user, view_messages=False, lang=lang):
        banned.add(user)
        info = await get_user_info_text(user)
        await send_temp_msg(event, f"🚫 کاربر {info} بن شد." if lang=="fa" else f"🚫 User {info} banned.")

# UNBAN
@client.on(events.NewMessage(pattern=r"(?i)^(?:حذف بن|unban)(?:\s+(.+))?$"))
async def unban_user(event):
    lang = detect_lang(event.raw_text)
    if not await is_admin_or_sudo(event):
        return await send_temp_msg(event, "❌ شما اجازه دسترسی ندارید." if lang=="fa" else "❌ You don't have permission.")
    arg = event.pattern_match.group(1)
    user = await get_user_from_input(event, arg)
    if not user:
        return await send_temp_msg(event, "❌ کاربر یافت نشد!" if lang=="fa" else "❌ User not found!")
    if await safe_action(event, client.edit_permissions, user, view_messages=True, lang=lang):
        banned.discard(user)
        info = await get_user_info_text(user)
        await send_temp_msg(event, f"✅ کاربر {info} از بن خارج شد." if lang=="fa" else f"✅ User {info} unbanned.")

# MUTE
@client.on(events.NewMessage(pattern=r"(?i)^(?:سکوت|mute)(?:\s+(.+))?$"))
async def mute_user(event):
    lang = detect_lang(event.raw_text)
    if not await is_admin_or_sudo(event):
        return await send_temp_msg(event, "❌ شما اجازه دسترسی ندارید." if lang=="fa" else "❌ You don't have permission.")
    arg = event.pattern_match.group(1)
    user = await get_user_from_input(event, arg)
    if not user:
        return await send_temp_msg(event, "❌ کاربر یافت نشد!" if lang=="fa" else "❌ User not found!")
    if await safe_action(event, client.edit_permissions, user, send_messages=False, lang=lang):
        muted.add(user)
        info = await get_user_info_text(user)
        await send_temp_msg(event, f"🔇 کاربر {info} سکوت شد." if lang=="fa" else f"🔇 User {info} muted.")

# UNMUTE
@client.on(events.NewMessage(pattern=r"(?i)^(?:حذف سکوت|unmute)(?:\s+(.+))?$"))
async def unmute_user(event):
    lang = detect_lang(event.raw_text)
    if not await is_admin_or_sudo(event):
        return await send_temp_msg(event, "❌ شما اجازه دسترسی ندارید." if lang=="fa" else "❌ You don't have permission.")
    arg = event.pattern_match.group(1)
    user = await get_user_from_input(event, arg)
    if not user:
        return await send_temp_msg(event, "❌ کاربر یافت نشد!" if lang=="fa" else "❌ User not found!")
    if await safe_action(event, client.edit_permissions, user, send_messages=True, lang=lang):
        muted.discard(user)
        info = await get_user_info_text(user)
        await send_temp_msg(event, f"🔊 کاربر {info} از سکوت خارج شد." if lang=="fa" else f"🔊 User {info} unmuted.")

# WARN
@client.on(events.NewMessage(pattern=r"(?i)^(?:اخطار|warn)(?:\s+(.+))?$"))
async def warn_user(event):
    lang = detect_lang(event.raw_text)
    if not await is_admin_or_sudo(event):
        return await send_temp_msg(event, "❌ شما اجازه دسترسی ندارید." if lang=="fa" else "❌ You don't have permission.")
    arg = event.pattern_match.group(1)
    user = await get_user_from_input(event, arg)
    if not user:
        return await send_temp_msg(event, "❌ کاربر یافت نشد!" if lang=="fa" else "❌ User not found!")
    warns[user] = warns.get(user,0)+1
    info = await get_user_info_text(user)
    if event.is_group:
        participants = await event.client.get_participants(event.chat_id)
        if user not in [p.id for p in participants]:
            text = "❌ این کاربر در گروه نیست، اخطار ثبت نشد!" if lang=="fa" else "❌ This user is not in the group, warn ignored!"
            return await send_temp_msg(event, text)
    if warns[user]>=3:
        if await safe_action(event, client.edit_permissions, user, view_messages=False, lang=lang):
            banned.add(user)
            await send_temp_msg(event, f"🚫 کاربر {info} سه اخطار گرفت و بن شد." if lang=="fa" else f"🚫 User {info} got 3 warns and banned.")
    else:
        await send_temp_msg(event, f"⚠️ اخطار {warns[user]} برای کاربر {info} ثبت شد." if lang=="fa" else f"⚠️ Warn {warns[user]} for user {info} registered.")

# UNWARN
@client.on(events.NewMessage(pattern=r"(?i)^(?:حذف اخطار|unwarn)(?:\s+(.+))?$"))
async def unwarn_user(event):
    lang = detect_lang(event.raw_text)
    if not await is_admin_or_sudo(event):
        return await send_temp_msg(event, "❌ شما اجازه دسترسی ندارید." if lang=="fa" else "❌ You don't have permission.")
    arg = event.pattern_match.group(1)
    user = await get_user_from_input(event, arg)
    if not user:
        return await send_temp_msg(event, "❌ کاربر یافت نشد!" if lang=="fa" else "❌ User not found!")
    warns[user] = 0
    info = await get_user_info_text(user)
    await send_temp_msg(event, f"✅ اخطارهای کاربر {info} پاک شد." if lang=="fa" else f"✅ User {info} warns cleared.")

# -------------------- لیست‌ها --------------------
@client.on(events.NewMessage(pattern=r"(?i)^(?:لیست بن|banlist)$"))
async def banlist(event):
    lang = detect_lang(event.raw_text)
    if banned:
        lines = []
        participants = await event.client.get_participants(event.chat_id)
        members = {p.id: p for p in participants}
        for uid in banned:
            if uid in members:
                lines.append(f"{await get_user_info_text(uid)}")
            else:
                lines.append(f"{uid} (خارج از گروه)")
        text = "📛 لیست بن‌شده‌ها:\n" + "\n".join(lines) if lang=="fa" else "📛 Banned list:\n" + "\n".join(lines)
    else:
        text = "✅ لیست بن خالی است." if lang=="fa" else "✅ Banned list is empty."
    await send_temp_msg(event, text)

@client.on(events.NewMessage(pattern=r"(?i)^(?:لیست سکوت|mutelist)$"))
async def mutelist(event):
    lang = detect_lang(event.raw_text)
    if muted:
        lines = []
        participants = await event.client.get_participants(event.chat_id)
        members = {p.id: p for p in participants}
        for uid in muted:
            if uid in members:
                lines.append(f"{await get_user_info_text(uid)}")
            else:
                lines.append(f"{uid} (خارج از گروه)")
        text = "🔇 لیست سکوت‌شده‌ها:\n" + "\n".join(lines) if lang=="fa" else "🔇 Muted list:\n" + "\n".join(lines)
    else:
        text = "✅ لیست سکوت خالی است." if lang=="fa" else "✅ Muted list is empty."
    await send_temp_msg(event, text)

@client.on(events.NewMessage(pattern=r"(?i)^(?:لیست اخطار|warnlist)$"))
async def warnlist(event):
    lang = detect_lang(event.raw_text)
    if warns:
        lines = [f"{await get_user_info_text(uid)}: {count}" for uid,count in warns.items()]
        text = "⚠️ لیست اخطارها:\n" + "\n".join(lines) if lang=="fa" else "⚠️ Warn list:\n" + "\n".join(lines)
    else:
        text = "✅ لیست اخطارها خالی است." if lang=="fa" else "✅ Warn list is empty."
    await send_temp_msg(event, text)

# -------------------- پاکسازی لیست‌ها --------------------
@client.on(events.NewMessage(pattern=r"(?i)^(?:پاکسازی بن|clearban)$"))
async def clearban(event):
    lang = detect_lang(event.raw_text)
    if not await is_admin_or_sudo(event):
        return await send_temp_msg(event, "❌ شما اجازه دسترسی ندارید." if lang=="fa" else "❌ You don't have permission.")
    banned.clear()
    await send_temp_msg(event, "✅ لیست بن پاک شد." if lang=="fa" else "✅ Banned list cleared.")

@client.on(events.NewMessage(pattern=r"(?i)^(?:پاکسازی سکوت|clearmute)$"))
async def clearmute(event):
    lang = detect_lang(event.raw_text)
    if not await is_admin_or_sudo(event):
        return await send_temp_msg(event, "❌ شما اجازه دسترسی ندارید." if lang=="fa" else "❌ You don't have permission.")
    muted.clear()
    await send_temp_msg(event, "✅ لیست سکوت پاک شد." if lang=="fa" else "✅ Muted list cleared.")

@client.on(events.NewMessage(pattern=r"(?i)^(?:پاکسازی اخطار|clearwarn)$"))
async def clearwarn(event):
    lang = detect_lang(event.raw_text)
    if not await is_admin_or_sudo(event):
        return await send_temp_msg(event, "❌ شما اجازه دسترسی ندارید." if lang=="fa" else "❌ You don't have permission.")
    warns.clear()
    await send_temp_msg(event, "✅ لیست اخطارها پاک شد." if lang=="fa" else "✅ Warn list cleared.")

# -------------------- دستورات سودو --------------------
@client.on(events.NewMessage(pattern=r"(?i)^(?:افزودن سودو|addsudo)(?:\s+(.+))?$"))
async def addsudo(event):
    lang = detect_lang(event.raw_text)
    if event.sender_id not in SUDO_USERS:
        return await send_temp_msg(event, "❌ شما اجازه دسترسی ندارید.")
    arg = event.pattern_match.group(1)
    user = await get_user_from_input(event, arg)
    if not user:
        return await send_temp_msg(event, "❌ کاربر یافت نشد!")
    SUDO_USERS.add(user)
    with open(SUDO_FILE, "w", encoding="utf-8") as f:
        json.dump({"sudo_users": list(SUDO_USERS)}, f, ensure_ascii=False)
    info = await get_user_info_text(user)
    await send_temp_msg(event, f"✅ کاربر {info} به سودو اضافه شد.")

@client.on(events.NewMessage(pattern=r"(?i)^(?:حذف سودو|remsudo)(?:\s+(.+))?$"))
async def remsudo(event):
    lang = detect_lang(event.raw_text)
    if event.sender_id not in SUDO_USERS:
        return await send_temp_msg(event, "❌ شما اجازه دسترسی ندارید.")
    arg = event.pattern_match.group(1)
    user = await get_user_from_input(event, arg)
    if not user:
        return await send_temp_msg(event, "❌ کاربر یافت نشد!")
    SUDO_USERS.discard(user)
    with open(SUDO_FILE, "w", encoding="utf-8") as f:
        json.dump({"sudo_users": list(SUDO_USERS)}, f, ensure_ascii=False)
    info = await get_user_info_text(user)
    await send_temp_msg(event, f"✅ کاربر {info} از سودو حذف شد.")

@client.on(events.NewMessage(pattern=r"(?i)^(?:لیست سودو|sudolist)$"))
async def sudolist(event):
    if not SUDO_USERS:
        return await send_temp_msg(event, "✅ لیست سودو خالی است.")
    lines = [f"{await get_user_info_text(uid)}" for uid in SUDO_USERS]
    text = "👑 لیست سودوها:\n" + "\n".join(lines)
    await send_temp_msg(event, text)

# -------------------- ثبت دستورات تگ --------------------
from tag_module import register_tag_commands
register_tag_commands(client, SUDO_USERS)

register_clear_commands(client, SUDO_USERS)
# -------------------- اجرای اصلی --------------------
with client:
    print("✅ Userbot فعال و آماده مدیریت گروه‌هاست...")
    client.run_until_disconnected()
