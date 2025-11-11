import os, re, json
from telethon import TelegramClient, events
from telethon.sessions import StringSession

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

async def check_protection(event, target_user_id):
    me_id = (await event.client.get_me()).id
    if target_user_id in SUDO_USERS:
        await event.reply("❌ این کاربر سودو است و نمی‌توان او را مدیریت کرد.\n❌ This user is a sudo and cannot be managed.")
        return False
    if target_user_id == me_id:
        await event.reply("❌ شما نمی‌توانید خود ربات را مدیریت کنید!\n❌ You cannot manage me!")
        return False
    if event.is_group:
        try:
            perm = await event.client.get_permissions(event.chat_id, target_user_id)
            if perm.is_admin:
                await event.reply("❌ این کاربر مدیر گروه است و نمی‌توان او را مدیریت کرد.\n❌ This user is an admin and cannot be managed.")
                return False
        except:
            pass
    return True

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

# -------------------- اجرای ایمن --------------------
async def safe_action(event, func, target_user_id, **kwargs):
    if not await check_protection(event, target_user_id):
        return False
    try:
        participants = await event.client.get_participants(event.chat_id)
        if target_user_id not in [p.id for p in participants]:
            await event.reply("❌ این کاربر در گروه نیست، الکی اعمال نشد!\n❌ This user is not in the group, action ignored!")
            return False
        await func(event.chat_id, target_user_id, **kwargs)
        return True
    except Exception as e:
        await event.reply(f"❌ خطا: {e}\n❌ Error: {e}")
        return False

# -------------------- مدیریت دستورات --------------------
async def get_user_info_text(user_id):
    try:
        user = await client.get_entity(user_id)
        name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        username = f"@{user.username}" if user.username else "NoUsername"
        return f"{name} ({username}, {user_id})"
    except:
        return str(user_id)

# BAN
@client.on(events.NewMessage(pattern=r"(?i)^(?:بن|ban)(?:\s+(.+))?$"))
async def ban_user(event):
    if not await is_admin_or_sudo(event):
        return await event.reply("❌ شما اجازه دسترسی ندارید.\n❌ You don't have permission.")
    arg = event.pattern_match.group(1)
    user = await get_user_from_input(event, arg)
    if not user:
        return await event.reply("❌ کاربر یافت نشد!\n❌ User not found!")
    if await safe_action(event, client.edit_permissions, user, view_messages=False):
        banned.add(user)
        info = await get_user_info_text(user)
        await event.reply(f"🚫 کاربر {info} بن شد.\n🚫 User {info} banned.")

@client.on(events.NewMessage(pattern=r"(?i)^(?:حذف بن|unban)(?:\s+(.+))?$"))
async def unban_user(event):
    if not await is_admin_or_sudo(event):
        return await event.reply("❌ شما اجازه دسترسی ندارید.\n❌ You don't have permission.")
    arg = event.pattern_match.group(1)
    user = await get_user_from_input(event, arg)
    if not user:
        return await event.reply("❌ کاربر یافت نشد!\n❌ User not found!")
    if await safe_action(event, client.edit_permissions, user, view_messages=True):
        banned.discard(user)
        info = await get_user_info_text(user)
        await event.reply(f"✅ کاربر {info} از بن خارج شد.\n✅ User {info} unbanned.")

# MUTE
@client.on(events.NewMessage(pattern=r"(?i)^(?:سکوت|mute)(?:\s+(.+))?$"))
async def mute_user(event):
    if not await is_admin_or_sudo(event):
        return await event.reply("❌ شما اجازه دسترسی ندارید.\n❌ You don't have permission.")
    arg = event.pattern_match.group(1)
    user = await get_user_from_input(event, arg)
    if not user:
        return await event.reply("❌ کاربر یافت نشد!\n❌ User not found!")
    if await safe_action(event, client.edit_permissions, user, send_messages=False):
        muted.add(user)
        info = await get_user_info_text(user)
        await event.reply(f"🔇 کاربر {info} سکوت شد.\n🔇 User {info} muted.")

@client.on(events.NewMessage(pattern=r"(?i)^(?:حذف سکوت|unmute)(?:\s+(.+))?$"))
async def unmute_user(event):
    if not await is_admin_or_sudo(event):
        return await event.reply("❌ شما اجازه دسترسی ندارید.\n❌ You don't have permission.")
    arg = event.pattern_match.group(1)
    user = await get_user_from_input(event, arg)
    if not user:
        return await event.reply("❌ کاربر یافت نشد!\n❌ User not found!")
    if await safe_action(event, client.edit_permissions, user, send_messages=True):
        muted.discard(user)
        info = await get_user_info_text(user)
        await event.reply(f"✅ کاربر {info} از سکوت خارج شد.\n✅ User {info} unmuted.")

# WARN
@client.on(events.NewMessage(pattern=r"(?i)^(?:اخطار|warn)(?:\s+(.+))?$"))
async def warn_user(event):
    if not await is_admin_or_sudo(event):
        return await event.reply("❌ شما اجازه دسترسی ندارید.\n❌ You don't have permission.")
    arg = event.pattern_match.group(1)
    user = await get_user_from_input(event, arg)
    if not user:
        return await event.reply("❌ کاربر یافت نشد!\n❌ User not found!")
    warns[user] = warns.get(user,0)+1
    info = await get_user_info_text(user)
    if warns[user]>=3:
        if await safe_action(event, client.edit_permissions, user, view_messages=False):
            banned.add(user)
            await event.reply(f"🚫 کاربر {info} سه اخطار گرفت و بن شد.\n🚫 User {info} got 3 warns and was banned.")
    else:
        await event.reply(f"⚠️ اخطار {warns[user]} برای کاربر {info} ثبت شد.\n⚠️ Warn {warns[user]} for user {info} registered.")

@client.on(events.NewMessage(pattern=r"(?i)^(?:حذف اخطار|unwarn)(?:\s+(.+))?$"))
async def unwarn_user(event):
    if not await is_admin_or_sudo(event):
        return await event.reply("❌ شما اجازه دسترسی ندارید.\n❌ You don't have permission.")
    arg = event.pattern_match.group(1)
    user = await get_user_from_input(event, arg)
    if not user:
        return await event.reply("❌ کاربر یافت نشد!\n❌ User not found!")
    warns[user]=0
    info = await get_user_info_text(user)
    await event.reply(f"✅ اخطارهای کاربر {info} پاک شد.\n✅ User {info} warns cleared.")

# -------------------- لیست‌ها --------------------
async def show_list(event, user_set, title_fa, title_en, is_warn=False):
    if not user_set:
        await event.reply(f"✅ {title_fa} خالی است.\n✅ {title_en} is empty.")
        return
    text = f"{title_fa} (نام + یوزرنیم + آیدی):\n"
    for u in user_set if not is_warn else user_set.keys():
        try:
            user = await event.client.get_entity(u)
            name = f"{user.first_name or ''} {user.last_name or ''}".strip()
            username = f"@{user.username}" if user.username else "NoUsername"
            if is_warn:
                count = user_set[u]
                text += f"- {name} ({username}, {u}): {count}\n"
            else:
                text += f"- {name} ({username}, {u})\n"
        except:
            text += f"- {u}\n"
    await event.reply(text)

@client.on(events.NewMessage(pattern=r"(?i)^(?:لیست بن|banlist)$"))
async def banlist(event):
    await show_list(event, banned, "لیست بن", "Ban list")

@client.on(events.NewMessage(pattern=r"(?i)^(?:لیست سکوت|mutelist)$"))
async def mutelist(event):
    await show_list(event, muted, "لیست سکوت", "Mute list")

@client.on(events.NewMessage(pattern=r"(?i)^(?:لیست اخطار|warnlist)$"))
async def warnlist(event):
    await show_list(event, warns, "لیست اخطارها", "Warn list", is_warn=True)

# -------------------- پاکسازی لیست‌ها --------------------
@client.on(events.NewMessage(pattern=r"(?i)^(?:پاکسازی بن|clearban)$"))
async def clearban(event):
    if not await is_admin_or_sudo(event):
        return await event.reply("❌ شما اجازه دسترسی ندارید.\n❌ You don't have permission.")
    banned.clear()
    await event.reply("✅ لیست بن پاک شد.\n✅ Ban list cleared.")

@client.on(events.NewMessage(pattern=r"(?i)^(?:پاکسازی سکوت|clearmute)$"))
async def clearmute(event):
    if not await is_admin_or_sudo(event):
        return await event.reply("❌ شما اجازه دسترسی ندارید.\n❌ You don't have permission.")
    muted.clear()
    await event.reply("✅ لیست سکوت پاک شد.\n✅ Mute list cleared.")

@client.on(events.NewMessage(pattern=r"(?i)^(?:پاکسازی اخطار|clearwarn)$"))
async def clearwarn(event):
    if not await is_admin_or_sudo(event):
        return await event.reply("❌ شما اجازه دسترسی ندارید.\n❌ You don't have permission.")
    warns.clear()
    await event.reply("✅ لیست اخطارها پاک شد.\n✅ Warn list cleared.")

# -------------------- اجرای اصلی --------------------
with client:
    print("✅ Userbot فعال و آماده مدیریت گروه‌هاست...")
    client.run_until_disconnected()
