import os
import asyncio
from pyrogram import Client, filters

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING1 = os.getenv("SESSION_STRING")   # سشن اصلی
SESSION_STRING2 = os.getenv("SESSION_STRING2")  # سشن پشتیبان (اکانت دوم)

SUDO_USERS = [7089376754]  # آیدی عددی خودت
CHECK_INTERVAL = 5  # دقیقه
LINKS_FILE = "links.txt"

# سشن اصلی و پشتیبان
main_bot = Client("userbot1", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING1)
backup_bot = Client("userbot2", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING2)

joined_links = set()
waiting_for_links = {}

def is_sudo(_, __, message):
    return message.from_user and message.from_user.id in SUDO_USERS

sudo_filter = filters.create(is_sudo)

# ------------------------------------------
# 🟢 دستور: "بیا" برای ارسال لینک‌ها
# ------------------------------------------
@main_bot.on_message(sudo_filter & filters.text & filters.regex(r"^بیا$"))
async def ask_for_links(client, message):
    waiting_for_links[message.chat.id] = True
    await message.reply_text("📎 لینک‌هارو بفرست (هر چندتا خواستی)\nوقتی تموم شد بنویس **پایان** ✅")

# ------------------------------------------
# 📎 وقتی لینک‌ها ارسال می‌شن
# ------------------------------------------
@main_bot.on_message(sudo_filter & filters.text)
async def handle_links(client, message):
    chat_id = message.chat.id
    if not waiting_for_links.get(chat_id):
        return
    text = message.text.strip()
    if text == "پایان":
        waiting_for_links[chat_id] = False
        await message.reply_text("✅ تموم شد! حالا شروع می‌کنم به رفتن توی لینک‌ها.")
        return
    links = [line.strip() for line in text.splitlines() if line.strip()]
    await join_multiple(main_bot, backup_bot, message, links)

# ------------------------------------------
# 📂 اگر فایل txt لینک ارسال شد
# ------------------------------------------
@main_bot.on_message(sudo_filter & filters.document)
async def handle_file(client, message):
    if message.document.mime_type == "text/plain":
        file_path = await message.download()
        with open(file_path, "r", encoding="utf-8") as f:
            links = [line.strip() for line in f if line.strip()]
        await join_multiple(main_bot, backup_bot, message, links)
        os.remove(file_path)

# ------------------------------------------
# 🚀 تابع ورود به چند لینک (با پشتیبان)
# ------------------------------------------
async def join_multiple(client1, client2, message, links):
    results = []
    for link in links:
        if link in joined_links:
            results.append(f"⏭ قبلاً عضو شده بودم: {link}")
            continue
        try:
            await try_join(client1, link)
            joined_links.add(link)
            results.append(f"✅ با اکانت 1 وارد شدم: {link}")
        except Exception as e:
            results.append(f"⚠️ اکانت 1 خطا داد: {link} | {e}")
            try:
                await try_join(client2, link)
                joined_links.add(link)
                results.append(f"🟡 با اکانت 2 وارد شدم: {link}")
            except Exception as e2:
                results.append(f"❌ نتونستم جوین شم: {link} | {e2}")

    if message:
        await message.reply_text("\n".join(results[-20:]))

# ------------------------------------------
# تابع join ساده برای یک لینک
# ------------------------------------------
async def try_join(bot, link):
    if link.startswith(("https://t.me/joinchat/", "https://t.me/+")):
        await bot.join_chat(link)
    elif link.startswith(("https://t.me/", "@")):
        username = link.replace("https://t.me/", "").replace("@", "")
        await bot.join_chat(username)
    else:
        raise ValueError("لینک معتبر نیست")

# ------------------------------------------
# 🔁 بررسی خودکار فایل لینک‌ها
# ------------------------------------------
async def auto_check_links():
    while True:
        await asyncio.sleep(CHECK_INTERVAL * 60)
        if os.path.exists(LINKS_FILE):
            with open(LINKS_FILE, "r", encoding="utf-8") as f:
                links = [line.strip() for line in f if line.strip()]
            if links:
                print(f"🔁 Checking {len(links)} links...")
                class Dummy:
                    async def reply_text(self, text): print(text)
                dummy = Dummy()
                await join_multiple(main_bot, backup_bot, dummy, links)

# ------------------------------------------
# 🚪 خروج از گروه
# ------------------------------------------
@main_bot.on_message(sudo_filter & filters.regex(r"^برو بیرون$"))
async def leave_group(client, message):
    try:
        await client.leave_chat(message.chat.id)
        await message.reply_text("🚪 از گروه خارج شدم.")
    except Exception as e:
        await message.reply_text(f"خطا هنگام خروج: {e}")

# ------------------------------------------
# 📊 وضعیت
# ------------------------------------------
@main_bot.on_message(sudo_filter & filters.regex(r"^وضعیت$"))
async def status(client, message):
    await message.reply_text(f"🟢 فعال!\nتعداد گروه‌های جوین‌شده: {len(joined_links)}")

# ------------------------------------------
# 🔥 شروع یوزربات
# ------------------------------------------
print("✅ Dual-Session Userbot AutoJoin Started...")

async def main():
    async with main_bot, backup_bot:
        asyncio.create_task(auto_check_links())
        await asyncio.Future()  # keeps alive

asyncio.run(main())
