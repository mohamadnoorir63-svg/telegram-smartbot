from pyrogram import Client, filters
from pyrogram.types import Message
import os
import asyncio
import re
import json

# ======= Environment Variables =======
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
SUDO_ID = int(os.getenv("SUDO_ID"))  # ID کاربر مدیر (تو)
# =====================================

# ایجاد کلاینت Pyrogram با session string
app = Client(
    name="userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING
)

# ===============================
#     توابع کمکی
# ===============================

def load_json(filename):
    if not os.path.exists(filename):
        return {}
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# فایل‌ها برای ذخیره کاربران و لینک‌ها
if not os.path.exists("data"):
    os.mkdir("data")
users_file = "data/users.json"
links_file = "data/links.json"
users_data = load_json(users_file)
links_data = load_json(links_file)

# ===============================
#     دستورات مدیریتی اصلی
# ===============================

@app.on_message(filters.command("ping") & filters.user(SUDO_ID))
async def ping(_, message: Message):
    await message.reply_text("✅ Pong! Bot is alive.")


@app.on_message(filters.command("help") & filters.user(SUDO_ID))
async def help_cmd(_, message: Message):
    text = """
🤖 **Userbot Commands**

/ping - بررسی سلامت ربات  
/help - نمایش این منو  
/pm <user_id> <message> - ارسال پیام خصوصی  
/broadcast <message> - ارسال پیام همگانی  
/send_groups <message> - ارسال فقط برای گروه‌ها  
/send_users <message> - ارسال فقط برای کاربران خصوصی  
/leave - خروج از گروه فعلی  
/stats - نمایش آمار کامل گروه‌ها و کاربران  
"""
    await message.reply_text(text)

# ===============================
#   ارسال پیام به گروه‌ها و کاربران
# ===============================

@app.on_message(filters.command("send_groups") & filters.user(SUDO_ID))
async def send_groups(_, message: Message):
    if len(message.text.split()) < 2:
        return await message.reply_text("❌ لطفاً متن پیام را وارد کنید.\nمثال:\n`/send_groups سلام گروهی‌ها!`")
    
    text = message.text.split(" ", 1)[1]
    sent, failed = 0, 0

    async for dialog in app.get_dialogs():
        if dialog.chat.type in ["group", "supergroup"]:
            try:
                await app.send_message(dialog.chat.id, text)
                sent += 1
                await asyncio.sleep(0.5)
            except Exception as e:
                failed += 1
                print(f"⚠️ ارسال به {dialog.chat.id} ناموفق بود: {e}")
    
    await message.reply_text(f"📢 پیام برای {sent} گروه ارسال شد. ❌ خطا در {failed} مورد.")


@app.on_message(filters.command("send_users") & filters.user(SUDO_ID))
async def send_users(_, message: Message):
    if len(message.text.split()) < 2:
        return await message.reply_text("❌ لطفاً متن پیام را وارد کنید.\nمثال:\n`/send_users سلام دوست من!`")
    
    text = message.text.split(" ", 1)[1]
    sent, failed = 0, 0

    async for dialog in app.get_dialogs():
        if dialog.chat.type == "private":
            try:
                await app.send_message(dialog.chat.id, text)
                sent += 1
                await asyncio.sleep(0.5)
            except Exception as e:
                failed += 1
                print(f"⚠️ ارسال به {dialog.chat.id} ناموفق بود: {e}")
    
    await message.reply_text(f"📬 پیام برای {sent} کاربر خصوصی ارسال شد. ❌ خطا در {failed} مورد.")

# ===============================
#   پاسخ خودکار + ذخیره کاربران خصوصی (فقط یک‌بار)
# ===============================

@app.on_message(filters.private & ~filters.me)
async def auto_reply_and_save(_, message: Message):
    try:
        user = message.from_user
        user_id = str(user.id)
        text = message.text.lower() if message.text else ""

        # ذخیره کاربر در فایل JSON
        if user_id not in users_data:
            users_data[user_id] = {
                "first_name": user.first_name or "",
                "last_name": user.last_name or "",
                "replied": False
            }
            save_json(users_file, users_data)

        # فقط یک بار جواب بده
        if "سلام" in text and not users_data[user_id]["replied"]:
            await message.reply_text("سلام بفرما؟ 😊")
            users_data[user_id]["replied"] = True
            save_json(users_file, users_data)

    except Exception as e:
        print(f"⚠️ خطا در پاسخ خودکار یا ذخیره: {e}")

# ===============================
#   جوین خودکار در لینک‌ها (حتی فوروارد شده‌ها)
# ===============================

@app.on_message((filters.text | filters.caption) & ~filters.me)
async def auto_join_links(_, message: Message):
    try:
        text = message.text or message.caption or ""
        links = re.findall(r"(https?://t\.me/(?:joinchat/|\+)?[A-Za-z0-9_\-]+)", text)

        if not links:
            return

        joined = 0
        failed = 0

        for link in links:
            if link in links_data:
                continue
            try:
                await app.join_chat(link)
                joined += 1
                links_data[link] = True
                save_json(links_file, links_data)
                await asyncio.sleep(2)
            except Exception as e:
                failed += 1
                print(f"⚠️ خطا در جوین به {link}: {e}")
                await app.send_message(SUDO_ID, f"⚠️ خطا در جوین:\n{link}\n`{e}`")

        if joined > 0:
            await app.send_message(SUDO_ID, f"✅ با موفقیت به {joined} لینک جدید جوین شدم!")
        elif failed > 0:
            await app.send_message(SUDO_ID, f"❌ نتوانستم به {failed} لینک جوین شوم.")
    except Exception as e:
        print(f"❌ خطای کلی در بررسی لینک‌ها: {e}")
        await app.send_message(SUDO_ID, f"⚠️ خطای کلی در بررسی لینک‌ها:\n`{e}`")

# ===============================
#     آمار کامل (Stats)
# ===============================

@app.on_message(filters.command("stats") & filters.user(SUDO_ID))
async def stats(_, message: Message):
    try:
        # فقط در پیوی اجرا شه
        if message.chat.type != "private":
            return await message.reply_text("⚠️ لطفاً این دستور را فقط در پیوی ارسال کنید.")

        print("📊 اجرای دستور /stats ...")

        dialogs = [d async for d in app.get_dialogs()]
        privates = sum(1 for d in dialogs if d.chat.type == "private")
        groups = sum(1 for d in dialogs if d.chat.type == "group")
        supergroups = sum(1 for d in dialogs if d.chat.type == "supergroup")
        channels = sum(1 for d in dialogs if d.chat.type == "channel")

        me = await app.get_me()
        sudo_name = f"{me.first_name or ''} {me.last_name or ''}".strip()

        total_users = len(users_data)
        total_links = len(links_data)

        text = f"""
📊 **آمار دقیق ربات:**

👤 کاربران خصوصی: `{privates}`
👥 گروه‌ها: `{groups}`
🏛️ سوپرگروه‌ها: `{supergroups}`
📢 کانال‌ها: `{channels}`
💾 کاربران ذخیره‌شده: `{total_users}`
🔗 لینک‌های جوین‌شده: `{total_links}`

👑 مدیر فعلی سشن: `{sudo_name}` (`{me.id}`)
⚙️ مدیریت تنظیم‌شده در ENV: `{SUDO_ID}`
"""
        await message.reply_text(text)
        print("✅ آمار ارسال شد با موفقیت.")
    except Exception as e:
        print(f"⚠️ خطا در /stats: {e}")
        await message.reply_text(f"⚠️ خطا در آمار:\n`{e}`")

# ===============================
#     اجرای ربات
# ===============================
print("✅ Userbot started successfully with auto-reply, auto-join, send_groups, send_users & stats!")
app.run()
