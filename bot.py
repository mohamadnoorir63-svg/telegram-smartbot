import os
import asyncio
import random
import time
from pyrogram import Client, filters

# ---------- ⚙️ تنظیمات ----------
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
SUDO_ID = 7089376754  # آیدی عددی خودت

USERS_FILE = "users.txt"
known_users = set()
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                user_id = line.split("|")[0].strip()
                known_users.add(user_id)

start_time = time.time()
message_count = 0
joined_groups = set()
left_groups = 0

# ---------- 🤖 ساخت یوزربات ----------
app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# ---------- 🎯 فیلتر مخصوص سودو ----------
def is_sudo(_, __, message):
    return message.from_user and message.from_user.id == SUDO_ID

sudo = filters.create(is_sudo)

# ---------- 🟢 اعلام روشن بودن ----------
@app.on_message(filters.outgoing & filters.regex("^/start$"))
async def start_message(client, message):
    await message.reply_text("✅ سارا روشنه و آماده‌ست!")

# ---------- 📥 ذخیره خودکار کاربران جدید ----------
@app.on_message(filters.private & filters.text)
async def auto_save_user(client, message):
    global message_count
    message_count += 1
    user = message.from_user
    if not user:
        return
    user_id = str(user.id)
    name = user.first_name or "ناشناس"
    username = f"@{user.username}" if user.username else "نداره"

    if user_id not in known_users:
        known_users.add(user_id)
        with open(USERS_FILE, "a", encoding="utf-8") as f:
            f.write(f"{user_id} | {name} | {username}\n")
        print(f"🆕 کاربر جدید ثبت شد: {name} ({user_id})")
        await message.reply_text(f"سلام {name} 🌹\nخوش اومدی 💖")

    # پاسخ به سلام فقط یک‌بار
    if message.text.lower() in ["سلام", "salam", "hi", "hello"]:
        await message.reply_text("سلام 😄 خوش اومدی 💬")

# ---------- 🟢 دستورات فارسی برای سودو ----------
waiting_for_links = {}

@app.on_message(sudo & filters.text)
async def sara_commands(client, message):
    global left_groups
    text = message.text.strip().lower()
    chat_id = message.chat.id

    # 📎 بیا
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

    # 🚪 برو بیرون
    if text == "برو بیرون":
        try:
            await client.leave_chat(chat_id)
            await message.reply_text("🚪 از گروه خارج شدم.")
            left_groups += 1
        except Exception as e:
            await message.reply_text(f"⚠️ خطا هنگام خروج: {e}")
        return

    # 📊 آمار
    if text == "آمار":
        uptime = round((time.time() - start_time) / 3600, 2)
        await message.reply_text(
            f"📊 گزارش خودکار سارا\n\n"
            f"👥 کاربران ذخیره‌شده: {len(known_users)}\n"
            f"💬 پیام‌های دریافتی: {message_count}\n"
            f"👩‍👩‍👧 گروه‌های عضو شده: {len(joined_groups)}\n"
            f"🚪 گروه‌های ترک‌شده: {left_groups}\n"
            f"⏱ مدت فعالیت: {uptime} ساعت"
        )
        return

    # 🧹 پاکسازی
    if text == "پاکسازی":
        await clean_broken_groups(client, message)
        return

    # ✳️ اضافه کردن لینک‌ها
    if chat_id in waiting_for_links:
        new_links = [line.strip() for line in text.splitlines() if line.strip()]
        waiting_for_links[chat_id].extend(new_links)
        await message.reply_text(f"✅ {len(new_links)} لینک جدید اضافه شد.")

# ---------- 🤖 جوین لینک‌ها ----------
async def join_links(client, message, links):
    for link in links:
        try:
            if link.startswith("@"):
                link = link.replace("@", "")
            await client.join_chat(link)
            joined_groups.add(link)
            await message.reply_text(f"✅ عضو شدم → {link}")
        except Exception as e:
            await message.reply_text(f"❌ خطا برای {link}: {e}")

# ---------- 🧹 پاکسازی گروه‌های خراب ----------
async def clean_broken_groups(client, message):
    global left_groups
    left = 0
    async for dialog in client.get_dialogs():
        chat = dialog.chat
        if chat and chat.type in ["group", "supergroup"]:
            try:
                await client.get_chat_members_count(chat.id)
            except Exception:
                try:
                    await client.leave_chat(chat.id)
                    left += 1
                    left_groups += 1
                except:
                    pass
    await message.reply_text(f"🧹 پاکسازی انجام شد.\n🚪 از {left} گروه خارج شدم.")

# ---------- 🕒 گزارش خودکار هر ۱ ساعت ----------
async def auto_report():
    while True:
        try:
            uptime = round((time.time() - start_time) / 3600, 2)
            text = (
                f"📊 گزارش خودکار سارا\n\n"
                f"👥 کاربران ذخیره‌شده: {len(known_users)}\n"
                f"💬 پیام‌های دریافتی: {message_count}\n"
                f"👩‍👩‍👧 گروه‌های عضو شده: {len(joined_groups)}\n"
                f"🚪 گروه‌های ترک‌شده: {left_groups}\n"
                f"⏱ مدت فعالیت: {uptime} ساعت"
            )
            await app.send_message(SUDO_ID, text)
            print("✅ گزارش ساعتی ارسال شد.")
        except Exception as e:
            print(f"⚠️ خطا در ارسال گزارش: {e}")
        await asyncio.sleep(3600)  # هر ۱ ساعت

# ---------- ♻️ ری‌استارت داخلی خودکار در صورت خطا ----------
async def run_forever():
    while True:
        try:
            await app.start()
            print("💖 سارا فعال شد و در حال اجراست...")
            asyncio.create_task(auto_report())
            await asyncio.Event().wait()
        except Exception as e:
            print(f"⚠️ خطای داخلی: {e}\n🔄 تلاش برای ری‌استارت دوباره...")
            await asyncio.sleep(10)

# ---------- 🚀 شروع ----------
if __name__ == "__main__":
    asyncio.run(run_forever())
