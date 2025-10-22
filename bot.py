import os
import asyncio
import re
import random
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, UserPrivacyRestricted, ChatAdminRequired, UserNotMutualContact, UserAlreadyParticipant, UserBannedInChannel

# ---------- تنظیمات ----------
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
SUDO_USERS = [7089376754]  # آیدی عددی خودت
USERS_FILE = "users_list.txt"
GROUPS_FILE = "groups_list.txt"
GROUP_MESSAGES_INTERVAL = 1800  # نیم ساعت

# ---------- ساخت یوزربات ----------
app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

known_users = set()
known_groups = set()
private_replied_users = set()
last_group_message = {}

# ---------- فیلتر سودو ----------
def is_sudo(_, __, message):
    return message.from_user and message.from_user.id in SUDO_USERS

sudo_filter = filters.create(is_sudo)

# ---------- شروع ----------
@app.on_message(filters.me & filters.regex("^/start$"))
async def start_me(client, message):
    await message.reply_text("✅ یوزربات آنلاین است و آماده‌ی کار!")

# ---------- پاسخ خودکار ----------
@app.on_message(filters.text & ~filters.me)
async def auto_reply(client, message):
    user = message.from_user
    if not user:
        return

    # ثبت کاربر
    if user.id not in known_users:
        known_users.add(user.id)
        with open(USERS_FILE, "a", encoding="utf-8") as f:
            f.write(f"{user.first_name or 'Unknown'} ({user.id})\n")
        print(f"🆕 کاربر جدید ثبت شد: {user.first_name} ({user.id})")

    # فقط یک‌بار در پیوی جواب بده
    if message.chat.type == "private":
        if user.id not in private_replied_users:
            private_replied_users.add(user.id)
            await message.reply_text(random.choice(["سلام 👋", "درود 🌹", "خوبی؟ 😎"]))

    # در گروه هر نیم ساعت یک پیام تصادفی
    elif message.chat.type in ["supergroup", "group"]:
        now = datetime.now()
        if message.chat.id not in last_group_message or (now - last_group_message[message.chat.id]) > timedelta(seconds=GROUP_MESSAGES_INTERVAL):
            last_group_message[message.chat.id] = now
            await message.reply_text(random.choice(["سلام بچه‌ها 😄", "کسی هست؟ 😂", "حوصلم سر رفته 😅"]))

# ---------- دستور اد همه یا اد خاص ----------
@app.on_message(sudo_filter & filters.text & filters.regex(r"^اد($| )"))
async def add_users_to_group(client, message):
    if message.chat.type not in ["supergroup", "group"]:
        await message.reply_text("⚠️ فقط در گروه می‌تونی از این دستور استفاده کنی.")
        return

    # بررسی ادمین بودن
    member = await client.get_chat_member(message.chat.id, "me")
    if not member.privileges or not member.privileges.can_invite_users:
        await message.reply_text("🚫 من ادمین نیستم یا اجازه اد کردن ندارم!")
        return

    # خواندن کاربران ذخیره‌شده
    if not os.path.exists(USERS_FILE):
        await message.reply_text("⚠️ هنوز هیچ کاربری ذخیره نشده.")
        return

    with open(USERS_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # استخراج آیدی‌ها از فایل
    user_ids = []
    for line in lines:
        match = re.search(r"\((\d+)\)", line)
        if match:
            user_ids.append(int(match.group(1)))

    # دستور خاص: "اد @username"
    args = message.text.strip().split(maxsplit=1)
    if len(args) > 1 and args[1].startswith("@"):
        username = args[1].replace("@", "")
        try:
            user = await client.get_users(username)
            user_ids = [user.id]
        except Exception as e:
            await message.reply_text(f"❌ کاربر پیدا نشد:\n`{e}`")
            return

    await message.reply_text(f"👥 شروع اضافه کردن {len(user_ids)} کاربر... لطفاً صبر کن ⚙️")

    added, failed = 0, 0
    for user_id in user_ids:
        try:
            await client.add_chat_members(message.chat.id, user_id)
            added += 1
            await asyncio.sleep(random.uniform(3, 6))  # جلوگیری از Flood
        except (UserPrivacyRestricted, UserNotMutualContact, UserBannedInChannel, UserAlreadyParticipant):
            failed += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception as e:
            print(f"⚠️ خطا در افزودن {user_id}: {e}")
            failed += 1

    await message.reply_text(f"✅ عملیات اد تمام شد.\n👤 اضافه‌شده: {added}\n🚫 ناموفق: {failed}")

# ---------- لیست کاربران ----------
@app.on_message(sudo_filter & filters.regex(r"^لیست کاربران$"))
async def send_users_file(client, message):
    if os.path.exists(USERS_FILE):
        await message.reply_document(USERS_FILE, caption=f"👤 تعداد کاربران: {len(known_users)}")
    else:
        await message.reply_text("⚠️ هیچ کاربری ثبت نشده.")

print("✅ Userbot with auto-reply + add-users system started...")
app.run()
