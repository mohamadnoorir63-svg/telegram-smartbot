from pyrogram import Client, filters
from pyrogram.types import Message
import os
import asyncio
import re

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
/broadcast <message> - ارسال پیام همگانی به همه چت‌ها  
/leave - خروج از گروه فعلی  
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
#     قابلیت جدید ۱:
#  پاسخ خودکار + ذخیره کاربران خصوصی
# ===============================

@app.on_message(filters.private & ~filters.me)
async def auto_reply_and_save(_, message: Message):
    try:
        text = message.text.lower() if message.text else ""
        user = message.from_user

        # ذخیره اطلاعات کاربر
        with open("contacts.txt", "a", encoding="utf-8") as f:
            f.write(f"{user.id} - {user.first_name or ''} {user.last_name or ''}\n")

        # پاسخ خودکار
        if "سلام" in text:
            await message.reply_text("سلام بفرما؟ 😊")

    except Exception as e:
        print(f"خطا در ذخیره یا پاسخ خودکار: {e}")

# ===============================
#     قابلیت جدید ۲:
#  جوین خودکار در لینک‌ها
# ===============================

@app.on_message(filters.text & ~filters.me)
async def auto_join_links(_, message: Message):
    try:
        text = message.text

        # پشتیبانی از تمام حالت‌های لینک تلگرام (joinchat و + و عمومی)
        links = re.findall(r"(https?://t\.me/(?:joinchat/|\+)?[A-Za-z0-9_\-]+)", text)

        if not links:
            return

        joined = 0
        failed = 0
        last_link = None

        for link in links:
            last_link = link
            try:
                if "joinchat" in link or "/+" in link:
                    # لینک خصوصی یا دعوتی
                    invite_code = link.split("/")[-1]
                    await app.import_chat_invite_link(invite_code)
                else:
                    # لینک عمومی
                    await app.join_chat(link)

                joined += 1
                await asyncio.sleep(2)

            except Exception as e:
                failed += 1
                print(f"⚠️ خطا در جوین به {link}: {e}")
                await app.send_message(
                    SUDO_ID,
                    f"⚠️ خطا در جوین به:\n{link}\n`{e}`"
                )
                continue

        # ارسال گزارش کلی به مدیر
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
#     اجرای ربات
# ===============================
print("✅ Userbot started successfully with auto-reply & auto-join!")
app.run()
