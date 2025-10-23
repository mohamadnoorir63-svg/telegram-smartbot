import os
import re
import asyncio
from pyrogram import Client, filters

# ================= ⚙️ تنظیمات اصلی =================
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

SUDO_ID = 7089376754  # آیدی عددی خودت
SUDO_USERS = [SUDO_ID]

# ================= 📱 ساخت یوزربات =================
app = Client("sara_userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# ================= 📁 متغیرها و فایل‌ها =================
USERS_FILE = "users.txt"
waiting_for_links = {}
known_users = set()
joined_groups = set()
CLEAN_INTERVAL = 6 * 60 * 60  # هر ۶ ساعت

# فایل کاربران را بارگذاری می‌کنیم (اگر وجود داشته باشد)
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                uid = line.split("|")[0].strip()
                known_users.add(uid)

# ================= 🔰 فیلتر مخصوص سودو =================
def is_sudo(_, __, message):
    return message.from_user and message.from_user.id in SUDO_USERS
sudo = filters.create(is_sudo)

# ================= 💬 پاسخ خودکار در پی‌وی =================
@app.on_message(filters.private & filters.text)
async def auto_reply_private(client, message):
    text = message.text.strip().lower()
    user = message.from_user

    if str(user.id) not in known_users:
        known_users.add(str(user.id))
        username = f"@{user.username}" if user.username else "نداره"
        with open(USERS_FILE, "a", encoding="utf-8") as f:
            f.write(f"{user.id} | {user.first_name} | {username}\n")
        print(f"🆕 کاربر جدید ثبت شد: {user.first_name} ({user.id})")

    if text in ["سلام", "hi", "hello", "salam"]:
        await message.reply_text("سلام 🌹 خوش اومدی 💬")

# ================= 🔗 دستورهای مدیریتی =================
@app.on_message(sudo & filters.text)
async def sara_commands(client, message):
    text = message.text.strip().lower()
    chat_id = message.chat.id

    # 🟢 بیا
    if text == "بیا":
        waiting_for_links[chat_id] = []
        await message.reply_text("📎 لینک‌هاتو بفرست (هر کدوم در یک خط)\nوقتی تموم شد بنویس: پایان")
        return

    # 🟢 پایان
    if text == "پایان" and chat_id in waiting_for_links:
        links = waiting_for_links.pop(chat_id)
        if not links:
            await message.reply_text("⚠️ هیچ لینکی دریافت نشد.")
            return
        await message.reply_text(f"🔍 دارم {len(links)} تا لینک رو بررسی می‌کنم...")
        await join_links(client, message, links)
        return

    # 🟢 آمار
    if text in ["آمار", "stats"]:
        joined_count = 0
        try:
            async for d in client.get_dialogs():
                if d.chat and d.chat.type in ["group", "supergroup"]:
                    joined_count += 1
        except Exception:
            pass
        await message.reply_text(
            f"📊 آمار فعلی:\n"
            f"👥 گروه‌های عضو شده: {joined_count}\n"
            f"👤 کاربران ذخیره‌شده: {len(known_users)}\n"
            f"⚙️ سارا فعاله و گوش به فرمانه 💖"
        )
        return

    # 🧹 پاکسازی دستی
    if text in ["پاکسازی دستی", "clean"]:
        await message.reply_text("🔍 در حال پاکسازی دستی گروه‌های خراب...")
        await clean_broken_groups(manual=True)
        await message.reply_text("✅ پاکسازی دستی تموم شد.")
        return

    # 🚪 برو بیرون
    if text == "برو بیرون":
        try:
            await client.leave_chat(message.chat.id)
            await message.reply_text("🚪 از گروه خارج شدم.")
        except Exception as e:
            await message.reply_text(f"⚠️ خطا هنگام خروج: {e}")
        return

    # 📎 دریافت لینک‌ها
    if chat_id in waiting_for_links:
        new_links = [line.strip() for line in text.splitlines() if line.strip()]
        waiting_for_links[chat_id].extend(new_links)
        await message.reply_text(f"✅ {len(new_links)} لینک جدید اضافه شد.")
        return

# ================= 🤖 جوین به لینک‌ها =================
async def join_links(client, message, links):
    joined = 0
    failed = 0
    results = []

    for link in links:
        try:
            if link.startswith("https://t.me/") or link.startswith("http://t.me/"):
                await client.join_chat(link)
            elif link.startswith("@"):
                await client.join_chat(link.replace("@", ""))
            else:
                results.append(f"⚠️ لینک نامعتبر: {link}")
                continue
            joined += 1
            results.append(f"✅ وارد شدم → {link}")
        except Exception as e:
            failed += 1
            results.append(f"❌ خطا برای {link}: {e}")

    joined_groups.update(links)
    await message.reply_text(
        f"📋 نتیجه:\n" + "\n".join(results[-20:]) +
        f"\n\n✅ موفق: {joined} | ❌ خطا: {failed}"
    )

# ================= 🔗 جوین خودکار از کانال لینک‌دونی =================
@app.on_message(filters.channel & filters.text)
async def auto_join_from_channels(client, message):
    text = message.text
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
        await client.send_message(SUDO_ID, f"🚀 {joined} گروه جدید از کانال لینک‌دونی جوین شد.")

# ================= 🧹 پاکسازی گروه‌های خراب =================
async def clean_broken_groups(manual=False):
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

        groups_list = "\n".join([f"🚪 {g}" for g in left_groups]) if left_groups else "✅ هیچ گروهی نیاز به پاکسازی نداشت."
        report = (
            f"🧹 {'پاکسازی دستی' if manual else 'پاکسازی خودکار'} انجام شد.\n"
            f"📊 بررسی‌شده: {checked}\n"
            f"🚪 ترک‌شده: {left_count}\n\n"
            f"{groups_list}"
        )
        await app.send_message(SUDO_ID, report)
        print(report)
    except Exception as e:
        await app.send_message(SUDO_ID, f"⚠️ خطا در پاکسازی: {e}")
        print(f"⚠️ {e}")

# ================= 🕒 پاکسازی خودکار =================
async def auto_clean_task():
    while True:
        await clean_broken_groups(manual=False)
        await asyncio.sleep(CLEAN_INTERVAL)

# ================= ♻️ ری‌استارت خودکار در صورت خطا =================
async def auto_restart_on_crash():
    while True:
        try:
            await main_loop()
        except Exception as e:
            print(f"⚠️ خطای اصلی: {e}\nدر حال ری‌استارت...")
            try:
                await app.send_message(SUDO_ID, f"❌ سارا خاموش شد!\nدر حال تلاش برای روشن شدن مجدد...")
            except:
                pass
            await asyncio.sleep(10)  # بعد از ۱۰ ثانیه خودش دوباره بالا میاد

# ================= 🚀 حلقه اصلی =================
async def main_loop():
    await app.start()
    print("✅ سارا بات با موفقیت فعال شد و در حال اجراست...")

    # 💬 پیام شروع برای سودو
    try:
        await app.send_message(SUDO_ID, "💖 سارا روشن شد و فعاله!\nهمه‌چی آماده‌ست 🌹")
    except Exception as e:
        print(f"⚠️ نتونستم پیام شروع بفرستم: {e}")

    asyncio.create_task(auto_clean_task())
    await asyncio.Event().wait()

# ================= 🏁 اجرای نهایی =================
if __name__ == "__main__":
    asyncio.run(auto_restart_on_crash())
