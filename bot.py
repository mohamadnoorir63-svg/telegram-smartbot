import os, time, asyncio
from pyrogram import Client, filters

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
try:
    SUDO_ID = int(str(os.getenv("SUDO_ID")).strip())
except:
    SUDO_ID = 7089376754

USERS_FILE = "users.txt"
known_users = set()

def load_lines(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()]

for ln in load_lines(USERS_FILE):
    known_users.add(ln.split("|")[0].strip())

app = Client("sara_userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

def uptime_text(seconds):
    sec = int(seconds)
    m = sec // 60
    h = m // 60
    m = m % 60
    if h:
        return f"{h} ساعت و {m} دقیقه"
    if m:
        return f"{m} دقیقه"
    return f"{sec} ثانیه"

start_time = time.time()

@app.on_message(filters.me & filters.text)
async def sara_commands(client, message):
    text = message.text.strip().lower()
    print("📩 Got message:", text)

    if text in ["پینگ", "ping"]:
        await message.reply_text("🟢 سارا فعاله!")
        return

    if text in ["آمار", "users", "آمار کاربران"]:
        await message.reply_text(f"👥 کاربران: {len(known_users)}")
        return

@app.on_message(filters.private & filters.text)
async def private_messages(client, message):
    uid = str(message.from_user.id)
    if uid not in known_users:
        known_users.add(uid)
        with open(USERS_FILE, "a", encoding="utf-8") as f:
            f.write(uid + "\n")
        await message.reply_text("✅ ثبت شدی در لیست سارا 💖")

@app.on_message(filters.command("start", prefixes=["/", ""]))
async def start_msg(client, message):
    await message.reply_text("💖 سارا فعاله و گوش می‌کنه...")

@app.on_message(filters.text & ~filters.me)
async def catch_all(client, message):
    print("⚙️ Received:", message.text)

if __name__ == "__main__":
    print("✅ شروع سارا...")
    app.run()
