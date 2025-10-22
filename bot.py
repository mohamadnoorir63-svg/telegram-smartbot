import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message

# ---------- تنظیمات ----------
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
# اجازه می‌ده از ENV هم بخونی هم هاردکد داشته باشی
SUDO_ENV = os.getenv("SUDO_USERS", "").strip()
SUDO_USERS = {7089376754}  # آی‌دی خودت (می‌تونی حذف کنی)
if SUDO_ENV:
    for x in SUDO_ENV.replace(",", " ").split():
        if x.isdigit():
            SUDO_USERS.add(int(x))

LINKS_FILE = "links.txt"
CHECK_INTERVAL = 5  # دقیقه

app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

joined_links = set()
waiting_for_links = {}  # chat_id -> bool

def norm(s: str) -> str:
    # حذف نیم‌فاصله و کاراکترهای نامرئی و یکسان‌سازی ی/ک
    if not s:
        return ""
    s = s.replace("\u200c", "").replace("\u200f", "").replace("\u2067", "").strip()
    s = s.replace("ي", "ی").replace("ك", "ک")
    return s

def is_sudo(msg: Message) -> bool:
    return msg.from_user and msg.from_user.id in SUDO_USERS

# ---------- وقتی بالا آمد، به سودو خبر بده ----------
@app.on_message(filters.me & filters.private)
async def _noop_me(_, __):  # برای جلوگیری از هشدار Pyrogram
    pass

async def notify_online():
    # به هر سودویی که توانستیم، پیام بدهیم
    for uid in list(SUDO_USERS):
        try:
            await app.send_message(uid, "✅ یوزربات روشن و آنلاین است!")
        except Exception as e:
            print(f"[notify] couldn't pm {uid}: {e}")

# ---------- دستور: بیا ----------
@app.on_message(filters.text)
async def dispatcher(client, message: Message):
    if not is_sudo(message):
        # برای عیب‌یابی: چاپ کن که پیام آمد ولی از سودو نبود
        print(f"[ignored] from {message.from_user.id if message.from_user else 'unknown'}: {message.text!r}")
        return

    text_raw = message.text or ""
    text = norm(text_raw)
    chat_id = message.chat.id

    # تشخیص دستور "بیا"
    if text in {"بیا", "بيا", "BIA", "Bia", "bia"}:
        waiting_for_links[chat_id] = True
        print(f"[state] waiting_for_links[{chat_id}] = True")
        await message.reply_text(
            "📎 لینک‌ها رو بفرست (هر خط یک لینک) یا فایل txt بده.\n"
            "وقتی تموم شد بنویس: **پایان**"
        )
        return

    # خروج از گروه
    if text in {"برو بیرون", "خروج"}:
        try:
            await client.leave_chat(chat_id)
            await message.reply_text("🚪 از گروه خارج شدم.")
        except Exception as e:
            await message.reply_text(f"⚠️ خطا هنگام خروج: {e}")
        return

    # وضعیت
    if text in {"وضعیت", "status", "ping"}:
        await message.reply_text(f"🟢 فعال!\nتعداد لینک‌های جوین‌شده: {len(joined_links)}")
        return

    # اگر در حالت دریافت لینک هستیم
    if waiting_for_links.get(chat_id):
        if text == "پایان":
            waiting_for_links[chat_id] = False
            print(f"[state] waiting_for_links[{chat_id}] = False")
            await message.reply_text("✅ دریافت لینک‌ها تموم شد — دارم پردازش می‌کنم...")
            return

        links = [norm(line) for line in text_raw.splitlines() if norm(line)]
        if links:
            print(f"[links] got {len(links)} links from chat {chat_id}")
            await join_multiple(client, message, links)
        return

# ---------- فایل txt ----------
@app.on_message(filters.document)
async def handle_file(client, message: Message):
    if not is_sudo(message):
        return
    mime = (message.document.mime_type or "").lower()
    name = (message.document.file_name or "").lower()
    if "text" in mime or name.endswith(".txt"):
        file_path = await message.download()
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                links = [norm(line) for line in f if norm(line)]
            await join_multiple(client, message, links)
        finally:
            try:
                os.remove(file_path)
            except:
                pass
    else:
        await message.reply_text("❗ فقط فایل txt بفرست.")

# ---------- جوین ----------
async def try_join(bot: Client, link: str):
    if link.startswith(("https://t.me/joinchat/", "https://t.me/+")):
        await bot.join_chat(link)
    elif link.startswith(("https://t.me/", "@")):
        username = link.replace("https://t.me/", "").replace("@", "")
        if not username:
            raise ValueError("یوزرنیم ناقص است")
        await bot.join_chat(username)
    else:
        raise ValueError("لینک معتبر نیست")

async def join_multiple(client: Client, message: Message, links: list[str]):
    results = []
    for link in links:
        if link in joined_links:
            results.append(f"⏭ قبلاً عضو شده بودم: {link}")
            continue
        try:
            await try_join(app, link)
            joined_links.add(link)
            results.append(f"✅ Joined: {link}")
        except Exception as e:
            err = str(e)
            if "USER_ALREADY_PARTICIPANT" in err or "already participant" in err.lower():
                joined_links.add(link)
                results.append(f"⏭ قبلاً عضو بودم: {link}")
            elif "INVITE_HASH_EXPIRED" in err or "invite" in err.lower():
                results.append(f"🚫 لینک منقضی/غیرقابل‌استفاده: {link}")
            else:
                results.append(f"❌ خطا برای {link}: {err}")

    text = "\n".join(results[-30:]) or "🔎 هیچ لینکی پردازش نشد."
    try:
        await message.reply_text(f"📋 نتیجه:\n{text}")
    except Exception as e:
        print("[send result error]", e, text)

# ---------- چک خودکار فایل links.txt ----------
async def auto_check_links():
    while True:
        await asyncio.sleep(CHECK_INTERVAL * 60)
        if os.path.exists(LINKS_FILE):
            try:
                with open(LINKS_FILE, "r", encoding="utf-8") as f:
                    links = [norm(line) for line in f if norm(line)]
                if links:
                    print(f"🔁 auto checking {len(links)} links...")
                    class Dummy:
                        async def reply_text(self, text): print(text)
                    await join_multiple(app, Dummy(), links)
            except Exception as e:
                print("Auto-check error:", e)

# ---------- main ----------
async def main():
    if not SESSION_STRING:
        print("ERROR: SESSION_STRING is missing in config vars.")
        return
    await app.start()
    print("✅ Userbot is up.")
    await notify_online()
    asyncio.create_task(auto_check_links())
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print("Fatal error:", e)
