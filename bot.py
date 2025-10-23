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
/leave - خروج از گروه فعلی  
/stats - نمایش آمار کامل گروه‌ها و کاربران  
"""
    await message.reply_text(text)


@app.on_message(filters.command("pm") & filters.user(SUDO_ID))
async def pm(_, message: Message):
    try:
        parts = message.text.split(" ", 2)
        if len(parts) < 3:
            return await message.reply_text("❌ فرمت نادرست است.\nمثال:\n`/pm 123456789 سلام!`")
        user_id = int(parts[1])
        msg = parts[2]
        await app.send_message(user_id, msg)
        await message.reply_text(f"✅ پیام به `{user_id}` ارسال شد.")
    except Exception as e:
        await message.reply_text(f"⚠️ خطا:\n`{e}`")


@app.on_message(filters.command("broadcast") & filters.user(SUDO_ID))
async def broadcast(_, message: Message):
    if len(message.text.split()) < 2:
        return await message.reply_text("❌ متن پیام را وارد کنید.")
    text = message.text.split(" ", 1)[1]
    count = 0
    async for dialog in app.get_dialogs():
        try:
            await app.send_message(dialog.chat.id, text)
            count += 1
            await asyncio.sleep(0.5)
        except:
            continue
    await message.reply_text(f"📢 پیام برای {count} چت ارسال شد.")


@app.on_message(filters.command("leave") & filters.user(SUDO_ID))
async def leave_chat(_, message: Message):
    try:
        chat_id = message.chat.id
        await app.leave_chat(chat_id)
        await message.reply_text("🚪 ربات از گروه خارج شد.")
    except Exception as e:
        await message.reply_text(f"⚠️ خطا در خروج:\n`{e}`")

# ===============================
#  پاسخ خودکار + ذخیره کاربران خصوصی (فقط یک‌بار)
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
        text = ""
        if message.text:
            text = message.text
        elif message.caption:
            text = message.caption

        # بررسی لینک‌ها (حتی در فوروارد)
        links = re.findall(r"(https?://t\.me/(?:joinchat/|\+)?[A-Za-z0-9_\-]+)", text)

        if not links:
            return

        joined = 0
        failed = 0
        last_link = None

        for link in links:
            last_link = link
            if link in links_data:  # اگر قبلاً جوین شده، رد کن
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
                await app.send_message(
                    SUDO_ID,
                    f"⚠️ خطا در جوین به:\n{link}\n`{e}`"
                )

        # ارسال گزارش به مدیر
        if joined > 0:
            await app.send_message(
                SUDO_ID,
                f"✅ با موفقیت به {joined} لینک جدید جوین شدم!\n📎 آخرین لینک: {last_link}"
            )
        elif failed > 0:
            await app.send_message(
                SUDO_ID,
                f"❌ نتوانستم به {failed} لینک جوین شوم (جزئیات بالا ارسال شد)"
            )

    except Exception as e:
        print(f"❌ خطای کلی در بررسی لینک‌ها: {e}")
        await app.send_message(SUDO_ID, f"⚠️ خطا کلی در بررسی لینک‌ها:\n`{e}`")

# ===============================
#     آمار کامل (Stats)
# ===============================

@app.on_message(filters.command("stats"))
async def stats(_, message: Message):
    try:
        # شناسایی فرستنده برای نمایش ID
        sender_id = message.from_user.id if message.from_user else None
        groups = 0
        privates = 0
        channels = 0

        async for dialog in app.get_dialogs():
            if dialog.chat.type == "private":
                privates += 1
            elif dialog.chat.type == "group":
                groups += 1
            elif dialog.chat.type == "supergroup" or dialog.chat.type == "channel":
                channels += 1

        total_users = len(users_data)
        total_links = len(links_data)

        text = f"""
📊 **آمار ربات:**

👤 کاربران خصوصی: `{privates}`
👥 گروه‌ها: `{groups}`
📢 سوپرگروه‌ها / کانال‌ها: `{channels}`
💾 کاربران ذخیره‌شده: `{total_users}`
🔗 لینک‌های جوین‌شده: `{total_links}`

🆔 آیدی فرستنده: `{sender_id}`
⚙️ مدیریت تنظیم‌شده: `{SUDO_ID}`
"""
        await message.reply_text(text)
    except Exception as e:
        await message.reply_text(f"⚠️ خطا در آمار:\n`{e}`")

# ===============================
#     اجرای ربات
# ===============================
print("✅ Userbot started successfully with auto-reply, auto-join & stats!")
app.run()
