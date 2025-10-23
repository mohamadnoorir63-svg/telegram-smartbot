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
            await message.reply_text("سلام بفرما؟ ")
            users_data[user_id]["replied"] = True
            save_json(users_file, users_data)

    except Exception as e:
        print(f"⚠️ خطا در پاسخ خودکار یا ذخیره: {e}")

# ===============================
#   جوین خودکار در لینک‌ها (حتی فوروارد شده‌ها)
# ===============================

# نکته: برای پوشش همه حالت‌ها، هر چیزی به شکل t.me/... را می‌گیریم.
LINK_RX = re.compile(r"(?:https?://)?t\.me/[^\s]+")

def _normalize_join_target(raw: str) -> tuple[str, str]:
    """
    ورودی: یک لینک t.me
    خروجی: (link_key_for_cache, join_target)
      - link_key_for_cache : کلید یکتا برای جلوگیری از تکرار (همان لینک normalize شده)
      - join_target : مقداری که مستقیماً به join_chat پاس می‌دهیم
    """
    link = raw.strip()
    # اگر http ندارد، به اولش https اضافه کن
    if not link.startswith("http"):
        link = "https://" + link
    # اگر لینک از نوع joinchat/+ است، کل لینک را به join_chat بده
    if "/joinchat/" in link or "/+" in link:
        return (link, link)
    # اگر عمومی است (t.me/username/....) فقط username را جدا کن
    try:
        tail = link.split("t.me/", 1)[1]
        username = tail.split("/", 1)[0]
        # برای join_chat، یا خود username یا کل لینک جواب می‌دهد؛
        # اما برای پایدارتر بودن، خود username را می‌دهیم.
        return (link, username)
    except Exception:
        # در صورت هر ایراد در پارس، کل لینک را بده
        return (link, link)

@app.on_message((filters.text | filters.caption) & ~filters.me)
async def auto_join_links(_, message: Message):
    try:
        text = message.text or message.caption or ""
        raw_links = LINK_RX.findall(text)

        if not raw_links:
            return

        joined = 0
        failed = 0
        last_link = None

        for raw in raw_links:
            link_key, join_target = _normalize_join_target(raw)
            last_link = link_key

            # اگر قبلاً این لینک/هدف پردازش شده، رد کن
            if link_key in links_data:
                continue

            try:
                # تلاش برای جوین
                chat = await app.join_chat(join_target)
                joined += 1
                # ذخیره اینکه این لینک با موفقیت پردازش شده
                links_data[link_key] = True
                save_json(links_file, links_data)
                await asyncio.sleep(1.5)

            except Exception as e:
                estr = str(e)
                # اگر از قبل عضو بودیم، این هم موفق تلقی کن و در کش ذخیره کن
                # پیام‌های رایج: USER_ALREADY_PARTICIPANT ، You're already a participant
                if "ALREADY" in estr.upper() or "participant" in estr.lower():
                    links_data[link_key] = True
                    save_json(links_file, links_data)
                    print(f"ℹ️ قبلاً عضو بودم: {link_key} -> علامت‌گذاری شد.")
                    continue

                failed += 1
                print(f"⚠️ خطا در جوین به {join_target}: {e}")
                await app.send_message(
                    SUDO_ID,
                    f"⚠️ خطا در جوین به:\n{link_key}\n`{e}`"
                )

        # گزارش
        if joined > 0:
            await app.send_message(
                SUDO_ID,
                f"✅ با موفقیت به {joined} لینک جدید جوین شدم!\n📎 آخرین: {last_link}"
            )
        elif failed > 0:
            await app.send_message(
                SUDO_ID,
                f"❌ نتوانستم به {failed} لینک جوین شوم (جزئیات بالا)."
            )

    except Exception as e:
        print(f"❌ خطای کلی در بررسی لینک‌ها: {e}")
        await app.send_message(SUDO_ID, f"⚠️ خطا کلی در بررسی لینک‌ها:\n`{e}`")

# ===============================
#     آمار کامل (Stats)
# ===============================

@app.on_message(filters.command("stats") & filters.user(SUDO_ID))
async def stats(_, message: Message):
    try:
        sender_id = message.from_user.id if message.from_user else None
        me = await app.get_me()
        sudo_name = f"{me.first_name or ''} {me.last_name or ''}".strip()

        dialogs = [d async for d in app.get_dialogs()]
        groups = sum(1 for d in dialogs if d.chat.type == "group")
        privates = sum(1 for d in dialogs if d.chat.type == "private")
        channels = sum(1 for d in dialogs if d.chat.type in ["supergroup", "channel"])

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
👑 مدیر فعلی سشن: `{sudo_name}` (`{me.id}`)
⚙️ مدیریت تنظیم‌شده در ENV: `{SUDO_ID}`
"""
        await message.reply_text(text)
    except Exception as e:
        await message.reply_text(f"⚠️ خطا در آمار:\n`{e}`")

# ===============================
#     اجرای ربات
# ===============================
print("✅ Userbot started successfully with auto-reply, optimized auto-join & stats!")
app.run()
