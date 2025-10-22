import os
import asyncio
import random
from pyrogram import Client, filters

# ---------- ⚙️ تنظیمات اصلی ----------
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

SUDO_USERS = [7089376754]  # آیدی عددی خودت
DATA_FILE = "users.txt"
GROUPS_FILE = "groups.txt"

# ---------- 💬 تنظیمات پیام‌ها ----------
AUTO_GROUP_MESSAGES = [
    "سلام بچه‌ها 😄",
    "کسی هست حرف بزنه؟ 😅",
    "حوصلم سر رفته 😐",
    "یه آهنگ خوب پیشنهاد بدین 🎶",
    "چیکار می‌کنین رفقا؟ 😎",
]

# ---------- 🧠 ساخت یوزربات ----------
app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
known_users = set()
joined_groups = set()
waiting_for_links = {}

# ---------- 🧍 ذخیره کاربران جدید ----------
@app.on_message(filters.private)
async def save_user(client, message):
    user_id = message.from_user.id
    name = message.from_user.first_name or "ناشناس"
    if user_id not in known_users:
        known_users.add(user_id)
        with open(DATA_FILE, "a", encoding="utf-8") as f:
            f.write(f"{user_id} | {name}\n")
        print(f"🆕 کاربر جدید ثبت شد: {name} ({user_id})")
        await message.reply_text("سلام 😄 خوش اومدی 💖")

# ---------- 💌 پاسخ خودکار به پیام‌های خصوصی ----------
@app.on_message(filters.private & filters.text)
async def auto_reply_pm(client, message):
    if message.from_user.id not in SUDO_USERS:
        await message.reply_text("سلام 😊 من فعلاً مشغولم، بعداً میام صحبت کنیم 💬")

# ---------- 👑 فقط برای سودو (تو) ----------
def is_sudo(_, __, message):
    return message.from_user and message.from_user.id in SUDO_USERS

sudo_filter = filters.create(is_sudo)

# ---------- 🪄 دستور «بیا» ----------
@app.on_message(filters.text & sudo_filter)
async def sara_commands(client, message):
    text = message.text.strip().lower()

    # 🟢 بیا
    if text == "بیا":
        waiting_for_links[message.chat.id] = True
        await message.reply_text("📎 لینک‌هاتو بفرست (هر کدوم در یک خط)، وقتی تموم شد بنویس: پایان")
        return

    # 📊 آمار
    if text == "آمار":
        await message.reply_text(
            f"📊 آمار فعلی:\n"
            f"👥 کاربران ذخیره‌شده: {len(known_users)}\n"
            f"👥 گروه‌های جوین‌شده: {len(joined_groups)}\n"
            f"💖 سارا فعاله و گوش به فرمانته!"
        )
        return

    # 🧹 پاکسازی گروه‌های بن‌شده
    if text == "پاکسازی":
        await clean_banned_groups(client, message)
        return

    # 🚪 خروج از گروه فعلی
    if text == "برو بیرون":
        try:
            await client.leave_chat(message.chat.id)
            await message.reply_text("🚪 از گروه خارج شدم.")
        except Exception as e:
            await message.reply_text(f"⚠️ خطا هنگام خروج: {e}")
        return

    # 🟢 پایان دریافت لینک‌ها
    if text == "پایان" and waiting_for_links.get(message.chat.id):
        waiting_for_links[message.chat.id] = False
        await message.reply_text("✅ دریافت لینک‌ها تموم شد، دارم می‌رم سراغشون 😎")
        return

# ---------- 📎 گرفتن لینک‌ها ----------
@app.on_message(sudo_filter & filters.text)
async def handle_links(client, message):
    chat_id = message.chat.id
    if not waiting_for_links.get(chat_id):
        return

    links = [line.strip() for line in message.text.splitlines() if line.strip()]
    for link in links:
        await try_join_group(client, message, link)

# ---------- 📄 تابع جوین ----------
async def try_join_group(client, message, link):
    try:
        if link.startswith(("https://t.me/joinchat/", "https://t.me/+")):
            await client.join_chat(link)
        elif link.startswith(("https://t.me/", "@")):
            username = link.replace("https://t.me/", "").replace("@", "")
            await client.join_chat(username)
        else:
            await message.reply_text(f"⚠️ لینک نامعتبر: {link}")
            return
        joined_groups.add(link)
        with open(GROUPS_FILE, "a", encoding="utf-8") as f:
            f.write(f"{link}\n")
        await message.reply_text(f"✅ با موفقیت عضو شدم: {link}")
    except Exception as e:
        err = str(e)
        if "USER_ALREADY_PARTICIPANT" in err:
            await message.reply_text(f"⏭ قبلاً عضو بودم: {link}")
        elif "INVITE_HASH_EXPIRED" in err:
            await message.reply_text(f"🚫 لینک منقضی یا نامعتبر: {link}")
        else:
            await message.reply_text(f"❌ خطا در جوین {link}:\n`{err}`")

# ---------- 🧹 پاکسازی گروه‌های بن‌شده ----------
async def clean_banned_groups(client, message):
    left = 0
    for g in list(joined_groups):
        try:
            chat = await client.get_chat(g)
            if chat and chat.type in ["group", "supergroup", "channel"]:
                continue
        except Exception:
            try:
                await client.leave_chat(g)
                left += 1
            except:
                pass
            joined_groups.remove(g)
    await message.reply_text(f"🧹 پاکسازی انجام شد — از {left} گروه خارج شدم.")

# ---------- 🤖 پیام دوره‌ای در گروه‌ها ----------
async def periodic_group_messages():
    while True:
        if joined_groups:
            msg = random.choice(AUTO_GROUP_MESSAGES)
            for g in list(joined_groups):
                try:
                    await app.send_message(g, msg)
                except:
                    pass
        await asyncio.sleep(20 * 60)  # هر ۲۰ دقیقه

# ---------- 🚀 شروع ----------
async def main():
    await app.start()
    print("💖 سارا بات فعال شد و در حال اجراست...")
    asyncio.create_task(periodic_group_messages())
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
