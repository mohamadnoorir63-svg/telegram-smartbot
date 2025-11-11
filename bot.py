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
    """بررسی اینکه کاربر محافظت شده نباشد"""
    me_id = (await event.client.get_me()).id
    if target_user_id in SUDO_USERS:
        await event.reply("❌ این کاربر سودو است و نمی‌توان او را مدیریت کرد.")
        return False
    if target_user_id == me_id:
        await event.reply("❌ شما نمی‌توانید خود من را مدیریت کنید!")
        return False
    if event.is_group:
        try:
            perm = await event.client.get_permissions(event.chat_id, target_user_id)
            if perm.is_admin:
                await event.reply("❌ این کاربر مدیر گروه است و نمی‌توان او را مدیریت کرد.")
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

# -------------------- مدیریت دستورات --------------------
async def safe_action(event, func, target_user_id, **kwargs):
    if not await check_protection(event, target_user_id):
        return False
    try:
        await func(event.chat_id, target_user_id, **kwargs)
        return True
    except Exception as e:
        await event.reply(f"خطا: {e}")
        return False

# ---------- BAN ----------
@client.on(events.NewMessage(pattern=r"(?i)^(?:/ban|بن)(?:\s+(.+))?$"))
async def ban_user(event):
    if not await is_admin_or_sudo(event):
        return await event.reply("❌ شما اجازه دسترسی ندارید.")
    arg = event.pattern_match.group(1)
    user = await get_user_from_input(event, arg)
    if not user:
        return await event.reply("کاربر یافت نشد!")
    if await safe_action(event, client.edit_permissions, user, view_messages=False):
        banned.add(user)
        await event.reply(f"🚫 کاربر [{user}] بن شد.")

@client.on(events.NewMessage(pattern=r"(?i)^(?:/unban|حذف بن)(?:\s+(.+))?$"))
async def unban_user(event):
    if not await is_admin_or_sudo(event):
        return await event.reply("❌ شما اجازه دسترسی ندارید.")
    arg = event.pattern_match.group(1)
    user = await get_user_from_input(event, arg)
    if not user:
        return await event.reply("کاربر یافت نشد!")
    if await safe_action(event, client.edit_permissions, user, view_messages=True):
        banned.discard(user)
        await event.reply(f"✅ کاربر [{user}] از بن خارج شد.")

# ---------- MUTE ----------
@client.on(events.NewMessage(pattern=r"(?i)^(?:/mute|سکوت)(?:\s+(.+))?$"))
async def mute_user(event):
    if not await is_admin_or_sudo(event):
        return await event.reply("❌ شما اجازه دسترسی ندارید.")
    arg = event.pattern_match.group(1)
    user = await get_user_from_input(event, arg)
    if not user:
        return await event.reply("کاربر یافت نشد!")
    if await safe_action(event, client.edit_permissions, user, send_messages=False):
        muted.add(user)
        await event.reply(f"🔇 کاربر [{user}] سکوت شد.")

@client.on(events.NewMessage(pattern=r"(?i)^(?:/unmute|حذف سکوت)(?:\s+(.+))?$"))
async def unmute_user(event):
    if not await is_admin_or_sudo(event):
        return await event.reply("❌ شما اجازه دسترسی ندارید.")
    arg = event.pattern_match.group(1)
    user = await get_user_from_input(event, arg)
    if not user:
        return await event.reply("کاربر یافت نشد!")
    if await safe_action(event, client.edit_permissions, user, send_messages=True):
        muted.discard(user)
        await event.reply(f"🔊 کاربر [{user}] از سکوت خارج شد.")

# ---------- WARN ----------
@client.on(events.NewMessage(pattern=r"(?i)^(?:/warn|اخطار)(?:\s+(.+))?$"))
async def warn_user(event):
    if not await is_admin_or_sudo(event):
        return await event.reply("❌ شما اجازه دسترسی ندارید.")
    arg = event.pattern_match.group(1)
    user = await get_user_from_input(event, arg)
    if not user:
        return await event.reply("کاربر یافت نشد!")
    warns[user] = warns.get(user,0)+1
    if warns[user]>=3:
        if await safe_action(event, client.edit_permissions, user, view_messages=False):
            banned.add(user)
            await event.reply(f"🚫 کاربر [{user}] سه اخطار گرفت و بن شد.")
    else:
        await event.reply(f"⚠️ اخطار {warns[user]} برای [{user}] ثبت شد.")

@client.on(events.NewMessage(pattern=r"(?i)^(?:/unwarn|حذف اخطار)(?:\s+(.+))?$"))
async def unwarn_user(event):
    if not await is_admin_or_sudo(event):
        return await event.reply("❌ شما اجازه دسترسی ندارید.")
    arg = event.pattern_match.group(1)
    user = await get_user_from_input(event, arg)
    if not user:
        return await event.reply("کاربر یافت نشد!")
    warns[user]=0
    await event.reply(f"✅ اخطارهای [{user}] پاک شدند.")

# -------------------- لیست‌ها --------------------
@client.on(events.NewMessage(pattern=r"(?i)^/banlist$"))
async def banlist(event):
    if banned:
        await event.reply("📛 لیست بن‌شده‌ها:\n" + "\n".join(str(u) for u in banned))
    else:
        await event.reply("✅ لیست بن خالی است.")

@client.on(events.NewMessage(pattern=r"(?i)^/mutelist$"))
async def mutelist(event):
    if muted:
        await event.reply("🔇 لیست سکوت‌شده‌ها:\n" + "\n".join(str(u) for u in muted))
    else:
        await event.reply("✅ لیست سکوت خالی است.")

@client.on(events.NewMessage(pattern=r"(?i)^/warnlist$"))
async def warnlist(event):
    if warns:
        await event.reply("⚠️ لیست اخطارها:\n" + "\n".join(f"{u}: {c}" for u,c in warns.items()))
    else:
        await event.reply("✅ لیست اخطارها خالی است.")

# -------------------- پاکسازی لیست‌ها --------------------
@client.on(events.NewMessage(pattern=r"(?i)^/clearban$"))
async def clearban(event):
    if not await is_admin_or_sudo(event):
        return await event.reply("❌ شما اجازه دسترسی ندارید.")
    banned.clear()
    await event.reply("✅ لیست بن پاک شد.")

@client.on(events.NewMessage(pattern=r"(?i)^/clearmute$"))
async def clearmute(event):
    if not await is_admin_or_sudo(event):
        return await event.reply("❌ شما اجازه دسترسی ندارید.")
    muted.clear()
    await event.reply("✅ لیست سکوت پاک شد.")

@client.on(events.NewMessage(pattern=r"(?i)^/clearwarn$"))
async def clearwarn(event):
    if not await is_admin_or_sudo(event):
        return await event.reply("❌ شما اجازه دسترسی ندارید.")
    warns.clear()
    await event.reply("✅ لیست اخطارها پاک شد.")

# -------------------- اجرای اصلی --------------------
with client:
    print("✅ Userbot فعال و آماده مدیریت گروه‌هاست...")
    client.run_until_disconnected()
