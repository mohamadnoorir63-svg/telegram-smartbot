import os
import asyncio
from pyrogram import Client, filters

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

SUDO_USERS = [7089376754]
CHECK_INTERVAL = 5  # دقیقه
LINKS_FILE = "links.txt"

app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
joined_links = set()
waiting_for_links = {}

def is_sudo(_, __, message):
    return message.from_user and message.from_user.id in SUDO_USERS

sudo_filter = filters.create(is_sudo)

@app.on_message(sudo_filter & filters.text & filters.regex(r"^بیا$"))
async def ask_for_links(client, message):
    waiting_for_links[message.chat.id] = True
    await message.reply_text("📎 لینک‌ها رو بفرست یا فایل `links.txt` رو بفرست.\nوقتی تموم شد بنویس: **پایان**")

@app.on_message(sudo_filter & filters.text)
async def handle_links(client, message):
    chat_id = message.chat.id
    if not waiting_for_links.get(chat_id):
        return
    text = message.text.strip()
    if text == "پایان":
        waiting_for_links[chat_id] = False
        await message.reply_text("✅ تموم شد. حالا خودکار هم بررسی می‌کنم هر چند دقیقه.")
        return
    links = [line.strip() for line in text.splitlines() if line.strip()]
    await join_multiple(client, message, links)

@app.on_message(sudo_filter & filters.document)
async def handle_file(client, message):
    if message.document.mime_type == "text/plain":
        file_path = await message.download()
        with open(file_path, "r", encoding="utf-8") as f:
            links = [line.strip() for line in f if line.strip()]
        await join_multiple(client, message, links)
        os.remove(file_path)

async def join_multiple(client, message, links):
    results = []
    for link in links:
        if link in joined_links:
            results.append(f"⏭ قبلاً عضو شده بودم: {link}")
            continue
        try:
            if link.startswith(("https://t.me/joinchat/", "https://t.me/+")):
                await client.join_chat(link)
                joined_links.add(link)
                results.append(f"✅ JoinChat: {link}")
            elif link.startswith(("https://t.me/", "@")):
                username = link.replace("https://t.me/", "").replace("@", "")
                await client.join_chat(username)
                joined_links.add(link)
                results.append(f"✅ Public: {username}")
            else:
                results.append(f"⚠️ لینک معتبر نیست: {link}")
        except Exception as e:
            results.append(f"❌ خطا برای {link}: {e}")
    if message:
        await message.reply_text("\n".join(results[-20:]))

async def auto_check_links():
    while True:
        await asyncio.sleep(CHECK_INTERVAL * 60)
        if os.path.exists(LINKS_FILE):
            with open(LINKS_FILE, "r", encoding="utf-8") as f:
                links = [line.strip() for line in f if line.strip()]
            if links:
                print(f"🔁 Checking {len(links)} links...")
                class DummyMsg:
                    async def reply_text(self, text): print(text)
                dummy_msg = DummyMsg()
                await join_multiple(app, dummy_msg, links)

@app.on_message(sudo_filter & filters.regex(r"^برو بیرون$"))
async def leave_group(client, message):
    try:
        await client.leave_chat(message.chat.id)
        await message.reply_text("🚪 از گروه خارج شدم.")
    except Exception as e:
        await message.reply_text(f"خطا هنگام خروج: {e}")

@app.on_message(sudo_filter & filters.regex(r"^وضعیت$"))
async def status(client, message):
    await message.reply_text(f"🟢 فعال!\nتعداد گروه‌های جوین‌شده: {len(joined_links)}")

print("✅ Userbot Auto-Join started...")

async def main():
    async with app:
        asyncio.create_task(auto_check_links())
        await asyncio.Future()  # keeps running

asyncio.run(main())
