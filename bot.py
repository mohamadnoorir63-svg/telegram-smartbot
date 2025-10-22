import os
from pyrogram import Client, filters

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

# ✅ فقط خودت کنترلش می‌کنی
SUDO_USERS = [7089376754]

app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
waiting_for_links = {}

def is_sudo(_, __, message):
    return message.from_user and message.from_user.id in SUDO_USERS

sudo_filter = filters.create(is_sudo)

@app.on_message(sudo_filter & filters.text & filters.regex(r"^بیا$"))
async def ask_for_links(client, message):
    waiting_for_links[message.chat.id] = True
    await message.reply_text("📎 همه لینک‌های گروه‌هاتو (هر کدوم در یک خط) بفرست!\nیا فایل لینک‌هارو بفرست (txt)\nوقتی تموم شد بنویس: **پایان**")

@app.on_message(sudo_filter & filters.text)
async def handle_links(client, message):
    chat_id = message.chat.id
    if not waiting_for_links.get(chat_id):
        return

    text = message.text.strip()

    # اگه گفت پایان
    if text == "پایان":
        waiting_for_links[chat_id] = False
        await message.reply_text("✅ عملیات تموم شد! هرجا تونستم عضو شدم.")
        return

    # چند لینک در یک پیام
    links = [line.strip() for line in text.splitlines() if line.strip()]
    await join_multiple(client, message, links)

@app.on_message(sudo_filter & filters.document)
async def handle_file(client, message):
    """اگر فایل txt حاوی لینک فرستاده بشه"""
    if message.document.mime_type == "text/plain":
        file_path = await message.download()
        with open(file_path, "r", encoding="utf-8") as f:
            links = [line.strip() for line in f if line.strip()]
        await join_multiple(client, message, links)
        os.remove(file_path)

async def join_multiple(client, message, links):
    """تلاش برای ورود به چندین لینک"""
    results = []
    for link in links:
        try:
            if link.startswith(("https://t.me/joinchat/", "https://t.me/+")):
                await client.join_chat(link)
                results.append(f"✅ JoinChat: {link}")
            elif link.startswith(("https://t.me/", "@")):
                username = link.replace("https://t.me/", "").replace("@", "")
                await client.join_chat(username)
                results.append(f"✅ Public: {username}")
            else:
                results.append(f"⚠️ لینک معتبر نیست: {link}")
        except Exception as e:
            results.append(f"❌ خطا برای {link}: {e}")

    reply = "\n".join(results)
    await message.reply_text(f"📋 نتیجه:\n{reply[:4000]}")  # جلوگیری از خطای طول پیام

@app.on_message(sudo_filter & filters.regex(r"^برو بیرون$"))
async def leave_group(client, message):
    try:
        await client.leave_chat(message.chat.id)
    except Exception as e:
        await message.reply_text(f"خطا هنگام خروج: {e}")

print("✅ Userbot (multi-link + file + sudo) started...")
app.run()
