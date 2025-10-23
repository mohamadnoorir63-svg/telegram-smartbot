import os
from pyrogram import Client, filters

# ---------- ⚙️ تنظیمات ----------
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

# عدد آی‌دی خودت (از @userinfobot بگیر)
SUDO_USERS = [7089376754]

# ---------- 📱 ساخت یوزربات ----------
app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# ---------- 🧠 متغیرهای کمکی ----------
waiting_for_links = {}

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

# ---------- 🔗 جوین خودکار از کانال‌ها یا گروه‌های لینک‌دونی ----------
@app.on_message(filters.text & ~filters.private)
async def auto_join_links(client, message):
    text = message.text.strip()

    # فقط اگر لینک t.me توی پیام هست
    if "t.me/" not in text:
        return

    # استخراج لینک‌ها از پیام
    parts = text.split()
    links = [p for p in parts if "t.me/" in p or p.startswith("@")]

    if not links:
        return

    results = []
    for link in links:
        try:
            if link.startswith("https://t.me/") or link.startswith("http://t.me/"):
                await client.join_chat(link)
            elif link.startswith("@"):
                username = link.replace("@", "")
                await client.join_chat(username)
            else:
                continue
            results.append(f"✅ جوین شد: {link}")
        except Exception as e:
            results.append(f"❌ خطا برای {link}: {e}")

    # ارسال گزارش به سودو (تو)
    try:
        for sudo_id in SUDO_USERS:
            await client.send_message(
                sudo_id,
                f"📥 جوین خودکار انجام شد:\n" + "\n".join(results[-10:])
            )
    except:
        pass
        # ---------- 🧍 ذخیره کاربران جدید در فایل ----------
USERS_FILE = "users.txt"
known_users = set()

# در شروع، فایل قبلی رو بارگذاری می‌کنیم (اگه وجود داشت)
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("|")
            if len(parts) >= 1:
                try:
                    known_users.add(int(parts[0]))
                except:
                    pass
                    # ---------- 📋 نمایش لیست کاربران ذخیره‌شده ----------
@app.on_message(sudo & filters.text & filters.regex(r"^(کاربرا|users)$"))
async def show_users_list(client, message):
    if not os.path.exists(USERS_FILE):
        await message.reply_text("⚠️ هنوز هیچ کاربری ذخیره نشده.")
        return

    with open(USERS_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if not lines:
        await message.reply_text("⚠️ هنوز هیچ کاربری در فایل نیست.")
        return
        # ---------- ➕ اد کردن کاربر از لیست ----------
@app.on_message(sudo & filters.text & filters.regex(r"^اد (\d+)$"))
async def add_user_from_list(client, message):
    match = message.matches[0]
    index = int(match.group(1)) - 1  # چون کاربرا از 1 شماره‌گذاری می‌شن

    if not os.path.exists(USERS_FILE):
        await message.reply_text("⚠️ فایل کاربران وجود ندارد.")
        return

    with open(USERS_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    if not lines:
        await message.reply_text("⚠️ هیچ کاربری در فایل نیست.")
        return

    if index < 0 or index >= len(lines):
        await message.reply_text(f"⚠️ عدد اشتباهه! فقط {len(lines)} کاربر ذخیره شدن.")
        return

    # گرفتن آیدی از فایل
    user_line = lines[index]
    user_id = int(user_line.split("|")[0].strip())

    try:
        await client.add_chat_members(message.chat.id, user_id)
        await message.reply_text(f"✅ کاربر شماره {index + 1} با موفقیت اد شد.\n👤 `{user_line}`")
    except Exception as e:
        await message.reply_text(f"❌ خطا در اد کردن:\n`{e}`")

    # فقط 30 تای آخر برای جلوگیری از زیاد شدن متن
    text = "\n".join([line.strip() for line in lines[-30:]])
    count = len(lines)

    await message.reply_text(f"👥 تعداد کل کاربران: {count}\n\n{text}")

@app.on_message(filters.private)
async def save_user_info(client, message):
    user = message.from_user
    if not user:
        return
        
# ---------- 🧍 ذخیره خودکار کاربران جدید ----------
USERS_FILE = "users.txt"
known_users = set()

# بارگذاری قبلی‌ها (اگر فایل موجوده)
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                user_id = line.split("|")[0].strip()
                known_users.add(user_id)

@app.on_message(filters.private & filters.text)
async def auto_save_user(client, message):
    user_id = str(message.from_user.id)
    name = message.from_user.first_name or "ناشناس"
    username = f"@{message.from_user.username}" if message.from_user.username else "نداره"

    if user_id not in known_users:
        known_users.add(user_id)
        with open(USERS_FILE, "a", encoding="utf-8") as f:
            f.write(f"{user_id} | {name} | {username}\n")
        print(f"🆕 کاربر جدید ثبت شد: {name} ({user_id})")

        await message.reply_text(
            f"سلام {name} 🌹\n"
            "خوش اومدی به ربات من 💬\n"
            "فعلاً من رباتم ولی شاید یه روز آدم شدم 😄"
        )
    # اگر کاربر قبلاً ذخیره نشده
    if user.id not in known_users:
        known_users.add(user.id)
        name = user.first_name or "ناشناس"
        username = f"@{user.username}" if user.username else "—"
        with open(USERS_FILE, "a", encoding="utf-8") as f:
            f.write(f"{user.id} | {name} | {username}\n")
        print(f"🆕 کاربر جدید ذخیره شد: {name} ({user.id})")
        await message.reply_text("سلام 😄 خوش اومدی 💖")

import re

# ---------- 🤖 جوین خودکار از کانال‌های لینک‌دونی ----------
@app.on_message(filters.channel & filters.text)
async def auto_join_from_channels(client, message):
    text = message.text
    # پیدا کردن لینک‌ها با regex
    links = re.findall(r"(https://t\.me/[^\s]+|@[\w\d_]+)", text)

    if not links:
        return

    joined = 0
    for link in links:
        try:
            if link.startswith("@"):
                link = link.replace("@", "")
            await client.join_chat(link)
            joined += 1
            print(f"✅ Joined from channel: {link}")
        except Exception as e:
            print(f"⚠️ Join error for {link}: {e}")

    if joined > 0:
        print(f"🚀 {joined} گروه جدید از کانال لینک‌دونی شناسایی و جوین شد!")
# ---------- 🤖 جوین شدن به لینک‌ها ----------
async def join_links(client, message, links):
    joined = 0
    failed = 0
    results = []

    for link in links:
        try:
            if link.startswith("https://t.me/") or link.startswith("http://t.me/"):
                await client.join_chat(link)
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
            results.append(f"❌ خطا برای {link}: {e}")

    result_text = "\n".join(results[-20:]) or "هیچ نتیجه‌ای ثبت نشد."
    await message.reply_text(f"📋 نتیجه نهایی:\n{result_text}\n\n✅ موفق: {joined} | ❌ خطا: {failed}")


# ---------- 💬 پاسخ خودکار به سلام در پی‌وی ----------
@app.on_message(filters.private & filters.text)
async def auto_reply_private(client, message):
    text = message.text.strip().lower()
    if text in ["سلام", "salam", "hi", "hello"]:
        await message.reply_text("سلام 🌹 خوش اومدی 💬")


# ---------- 🧹 پاکسازی گروه‌های خراب ----------
async def clean_broken_groups(client, message):
    left_count = 0
    try:
        dialogs = await client.get_dialogs()
        for d in dialogs:
            if d.chat and d.chat.type in ["group", "supergroup"]:
                try:
                    members = await client.get_chat_members_count(d.chat.id)
                    if members == 0:
                        await client.leave_chat(d.chat.id)
                        left_count += 1
                except Exception:
                    try:
                        await client.leave_chat(d.chat.id)
                        left_count += 1
                    except:
                        pass
    except Exception as e:
        await message.reply_text(f"⚠️ خطا هنگام پاکسازی: {e}")
        return

    await message.reply_text(f"🧹 پاکسازی انجام شد.\n🚪 از {left_count} گروه خارج شدم.")


# ---------- 🚀 شروع ----------
print("✅ یوزربات فارسی با موفقیت فعال شد و در حال اجراست...")
app.run()
