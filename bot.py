import os
import re
import asyncio
from pyrogram import Client, filters
from pyrogram.errors import FloodWait

# ---------- ENV ----------
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

# فقط ادمین/مالک: آیدی عددی خودت را اینجا بگذار
SUDO_USERS = [7089376754]

# فایل‌ها
USERS_FILE = "users_min.txt"
GROUPS_FILE = "groups_min.txt"

# حالت‌ها
auto_join_enabled = set()     # chat_id هایی که Auto-Join در آنها روشن است
known_users = set()
known_groups = set()

# ---------- Pyrogram Client ----------
app = Client("userbot_min", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# ---------- Helpers ----------
def is_sudo(_, __, m):
    return m.from_user and m.from_user.id in SUDO_USERS

sudo = filters.create(is_sudo)

LINK_REGEX = re.compile(r"(https?://t\.me/[^\s]+|@[\w\d_]+)")

def extract_links(text: str):
    if not text:
        return []
    return LINK_REGEX.findall(text)

async def safe_send(chat_id, text):
    try:
        await app.send_message(chat_id, text)
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await app.send_message(chat_id, text)
    except Exception:
        pass

def save_user(uid: int, name: str):
    if uid in known_users:
        return
    known_users.add(uid)
    with open(USERS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{uid} | {name}\n")

def save_group(chat_title_or_username: str):
    if chat_title_or_username in known_groups:
        return
    known_groups.add(chat_title_or_username)
    with open(GROUPS_FILE, "a", encoding="utf-8") as f:
        f.write(chat_title_or_username + "\n")

# ---------- Commands (English, no slash) ----------
@app.on_message(sudo & filters.text)
async def english_commands(client, m):
    text = (m.text or "").strip().lower()

    # john on / john off : toggle auto-join for this chat
    if text == "john on":
        auto_join_enabled.add(m.chat.id)
        await m.reply_text("✅ Auto-Join enabled for this chat.")
        return
    if text == "john off":
        auto_join_enabled.discard(m.chat.id)
        await m.reply_text("🛑 Auto-Join disabled for this chat.")
        return

    # stats
    if text == "stats":
        await m.reply_text(
            "📊 Stats\n"
            f"👥 Saved users: {len(known_users)}\n"
            f"👥 Known groups: {len(known_groups)}\n"
            f"⚙️ Auto-Join ON here: {'Yes' if m.chat.id in auto_join_enabled else 'No'}"
        )
        return

# ---------- Auto-Join when enabled in link-dump chats ----------
@app.on_message(filters.text & ~filters.private)
async def auto_join_links(client, m):
    # فقط اگر برای این چت روشن شده باشه
    if m.chat.id not in auto_join_enabled:
        return

    links = extract_links(m.text)
    if not links:
        return

    results = []
    for link in links:
        try:
            if link.startswith(("https://t.me/", "http://t.me/")):
                chat = await client.join_chat(link)
            elif link.startswith("@"):
                chat = await client.join_chat(link[1:])  # remove '@'
            else:
                results.append(f"⚠️ invalid: {link}")
                continue

            title_or_user = chat.title or chat.username or str(chat.id)
            save_group(title_or_user)
            results.append(f"✅ joined: {title_or_user}")
            await asyncio.sleep(1)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            results.append(f"⏳ retry after {e.value}s: {link}")
        except Exception as e:
            results.append(f"❌ {link}: {e}")

    if results:
        # فقط خلاصه کوتاه
        await m.reply_text("📥 Auto-Join:\n" + "\n".join(results[-10:]))

# ---------- Private hello + save user ----------
@app.on_message(filters.private & filters.text)
async def private_hello(client, m):
    text = (m.text or "").strip().lower()
    u = m.from_user
    if not u:
        return

    # ذخیره کاربر برای اد در آینده
    save_user(u.id, u.first_name or "Unknown")

    # اگر سلام داد (فارسی/انگلیسی) جواب «سلام» بده
    if text in {"سلام", "salam", "hi", "hello"}:
        await m.reply_text("سلام 🌹")

# ---------- Startup ----------
async def main():
    await app.start()
    # پیام خصوصی به سودو که بالا اومده (اختیاری)
    for uid in SUDO_USERS:
        await safe_send(uid, "✅ Minimal userbot is up. Commands: 'john on', 'john off', 'stats'.")
    print("✅ Minimal userbot started.")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
