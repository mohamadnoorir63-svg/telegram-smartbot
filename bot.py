import os
import re
import asyncio
from pyrogram import Client, filters

# ---------- ⚙️ تنظیمات ----------
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

# آیدی عددی خودت
SUDO_USERS = [7089376754]
SUDO_ID = 7089376754

# ---------- 📱 ساخت یوزربات ----------
app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# ---------- 🧠 متغیرهای کمکی ----------
waiting_for_links = {}
USERS_FILE = "users.txt"
known_users = set()

# ---------- بارگذاری کاربران ذخیره‌شده ----------
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("|")
            if len(parts) >= 1:
                try:
                    known_users.add(int(parts[0]))
                except:
                    pass

# ---------- 🎯 فیلتر فقط برای خودت ----------
def is_sudo(_, __, message):
    return message.from_user and message.from_user.id in SUDO_USERS

sudo = filters.create(is_sudo)

# ---------- 🟢 وقتی روشن شد ----------
@app.on_message(filters.outgoing & filters.text & filters.regex("^/start$"))
async def start_message(client, message):
    await message.reply_text("✅ یوزربات روشن و آماده است!")

# ---------- 🟢 دستورهای فارسی ----------
@app.on_message(sudo & filters.text)
async def sara_commands(client, message):
    text = message.text.strip().lower()
    chat_id = message.chat.id

    # ✅ بیا
    if text == "بیا":
        waiting_for_links[chat_id] = []
        await message.reply_text("📎 لینک‌هاتو بفرست (هر کدوم در یک خط)\nوقتی تموم شد بنویس: پایان")
        return

    # ✅ پایان
    if text == "پایان" and chat_id in waiting_for_links:
        links = waiting_for_links.pop(chat_id)
        if not links:
            await message.reply_text("⚠️ هیچ لینکی دریافت نشد.")
            return
        await message.reply_text(f"🔍 دارم {len(links)} تا لینک رو بررسی می‌کنم...")
        await join_links(client, message, links)
        return

    # ✅ آمار
    if text in ["آمار", "stats"]:
        joined_count = 0
        try:
            dialogs = await client.get_dialogs()
            for d in dialogs:
                if d.chat and d.chat.type in ["group", "supergroup"]:
                    joined_count += 1
        except Exception:
            pass
        await message.reply_text(
            f"📊 آمار فعلی:\n"
            f"👥 گروه‌های عضو شده: {joined_count}\n"
            f"⚙️ سارا فعاله و آماده‌ی فرمانه 💖"
        )
        return

    # ✅ پاکسازی
    if text in ["پاکسازی", "clean"]:
        await clean_broken_groups(client, message)
        return

    # ✅ برو بیرون
    if text == "برو بیرون":
        try:
            await client.leave_chat(message.chat.id)
            await message.reply_text("🚪 از گروه خارج شدم.")
        except Exception as e:
            await message.reply_text(f"⚠️ خطا هنگام خروج: {e}")
        return

    # ✅ لینک‌ها در حال دریافت
    if chat_id in waiting_for_links:
        new_links = [line.strip() for line in text.splitlines() if line.strip()]
        waiting_for_links[chat_id].extend(new_links)
        await message.reply_text(f"✅ {len(new_links)} لینک جدید اضافه شد.")
        return


# ---------- 🤖 جوین خودکار از کانال‌های مجاز ----------
ALLOWED_CHANNELS = ["MyLinksChannel", "SaraGroups"]

@app.on_message(filters.channel & filters.text)
async def auto_join_from_allowed_channels(client, message):
    chat = message.chat
    if chat.username not in ALLOWED_CHANNELS:
        return

    text = message.text
    links = re.findall(r"(https://t\.me/[^\s]+|@[\w\d_]+)", text)
    if not links:
        return

    joined = 0
    failed = 0
    success_links = []
    failed_links = []

    for link in links:
        try:
            if link.startswith("@"):
                link = link.replace("@", "")
            await client.join_chat(link)
            joined += 1
            success_links.append(link)
            print(f"✅ Joined from channel {chat.username}: {link}")
        except Exception as e:
            failed += 1
            failed_links.append(f"{link} → {e}")
            print(f"⚠️ Error joining {link}: {e}")

    try:
        report_text = (
            f"📢 گزارش از کانال @{chat.username}\n"
            f"✅ گروه‌های جدید: {joined}\n"
            f"❌ خطاها: {failed}\n\n"
        )
        if success_links:
            report_text += "📋 گروه‌های موفق:\n" + "\n".join(f"• {l}" for l in success_links[:10])
        if failed_links:
            report_text += "\n\n⚠️ خطاها:\n" + "\n".join(f"• {l}" for l in failed_links[:5])
        await client.send_message(SUDO_ID, report_text)
    except Exception as e:
        print(f"⚠️ ارسال گزارش به سودو ناموفق بود: {e}")


# ---------- 🧹 پاکسازی ----------
CLEAN_INTERVAL = 6 * 60 * 60  # هر 6 ساعت

async def clean_broken_groups(client, message=None, manual=False):
    print("🧹 شروع بررسی گروه‌ها ...")
    left_count = 0
    checked = 0
    left_groups = []

    try:
        async for dialog in app.get_dialogs():
            chat = dialog.chat
            if chat and chat.type in ["group", "supergroup"]:
                checked += 1
                try:
                    members = await app.get_chat_members_count(chat.id)
                    if members == 0:
                        await app.leave_chat(chat.id)
                        left_count += 1
                        left_groups.append(chat.title or str(chat.id))
                except Exception:
                    try:
                        title = chat.title or str(chat.id)
                        await app.leave_chat(chat.id)
                        left_count += 1
                        left_groups.append(title)
                    except:
                        pass

        if left_groups:
            groups_list = "\n".join([f"🚪 {name}" for name in left_groups[:20]])
        else:
            groups_list = "✅ هیچ گروهی نیاز به ترک نداشت."

        report = (
            f"🧹 {'پاکسازی دستی' if manual else 'پاکسازی خودکار'} انجام شد.\n"
            f"📊 گروه‌های بررسی‌شده: {checked}\n"
            f"🚪 گروه‌های ترک‌شده: {left_count}\n\n"
            f"{groups_list}"
        )

        await app.send_message(SUDO_ID, report)
        print(report)
        if message:
            await message.reply_text(report)

    except Exception as e:
        err = f"⚠️ خطا در پاکسازی: {e}"
        await app.send_message(SUDO_ID, err)
        print(err)
        if message:
            await message.reply_text(err)


async def auto_clean_task():
    while True:
        await clean_broken_groups(app, manual=False)
        await asyncio.sleep(CLEAN_INTERVAL)


@app.on_message(sudo & filters.text & filters.regex(r"^(پاکسازی دستی)$"))
async def manual_clean_command(client, message):
    await message.reply_text("🔍 در حال پاکسازی دستی گروه‌های خراب...")
    await clean_broken_groups(client, message, manual=True)
    await message.reply_text("✅ پاکسازی دستی تموم شد!")


# ---------- 🔗 جوین خودکار ----------
@app.on_message(filters.text & ~filters.private)
async def auto_join_links(client, message):
    text = message.text.strip()
    if "t.me/" not in text:
        return
    parts = text.split()
    links = [p for p in parts if "t.me/" in p or p.startswith("@")]
    if not links:
        return
    await join_links(client, message, links)


# ---------- 🤖 جوین شدن به لینک‌ها ----------
async def join_links(client, message, links):
    joined = 0
    failed = 0
    results = []

    for link in links:
        link = re.sub(r"[\s\u200c\u200b]+", "", link)
        if not link:
            continue

        try:
            # نوع لینک را تشخیص بده
            if "joinchat" in link or link.startswith("https://t.me/+"):
                # لینک دعوت خصوصی (گروه یا کانال)
                await client.join_chat(link)

            elif link.startswith("https://t.me/") or link.startswith("http://t.me/"):
                # لینک عمومی
                username = link.split("t.me/")[1]
                if "/" in username:
                    username = username.split("/")[0]
                await client.join_chat(username)

            elif link.startswith("@"):
                username = link.replace("@", "")
                await client.join_chat(username)

            else:
                results.append(f"⚠️ لینک نامعتبر: {link}")
                continue

            joined += 1
            results.append(f"✅ وارد شدم → {link}")

        except Exception as e:
            failed += 1
            err = str(e)
            # پیام‌های خطا رو مشخص‌تر نمایش بده
            if "USER_BANNED_IN_CHANNEL" in err:
                results.append(f"🚫 مسدود از کانال/گروه → {link}")
            elif "INVITE_HASH_EXPIRED" in err:
                results.append(f"⏳ لینک منقضی شده → {link}")
            elif "CHANNEL_PRIVATE" in err:
                results.append(f"🔒 گروه/کانال خصوصی و قابل دسترسی نیست → {link}")
            elif "USERNAME_INVALID" in err:
                results.append(f"❌ یوزرنیم نامعتبر یا وجود ندارد → {link}")
            elif "PEER_ID_INVALID" in err:
                results.append(f"⚠️ نیاز به گفتگو یا دسترسی بیشتر → {link}")
            else:
                results.append(f"❌ خطای ناشناخته برای {link}:\n{err}")

    text = "\n".join(results[-10:]) or "هیچ نتیجه‌ای ثبت نشد."
    await message.reply_text(
        f"📋 نتیجه نهایی:\n{text}\n\n✅ موفق: {joined} | ❌ خطا: {failed}"
    )

# ---------- 💬 چت خصوصی: ذخیره و پاسخ ----------
@app.on_message(filters.private & filters.text)
async def handle_private_message(client, message):
    user = message.from_user
    if not user:
        return

    user_id = str(user.id)
    name = user.first_name or "ناشناس"
    username = f"@{user.username}" if user.username else "نداره"
    text = message.text.strip().lower()

    # بررسی اینکه آیا کاربر جدید است
    is_new_user = False
    if user_id not in known_users:
        known_users.add(user_id)
        is_new_user = True
        with open(USERS_FILE, "a", encoding="utf-8") as f:
            f.write(f"{user_id} | {name} | {username}\n")
        print(f"🆕 کاربر جدید ثبت شد: {name} ({user_id})")

    # پاسخ‌ها
    if is_new_user:
        await message.reply_text(f"{name} سلام 🌹")
    elif text in ["سلام", "salam", "hi", "hello"]:
        await message.reply_text(f"سلام {name} 👋")


# ---------- 🚀 شروع ----------
print("✅ یوزربات فارسی با موفقیت فعال شد و در حال اجراست...")
app.run()
