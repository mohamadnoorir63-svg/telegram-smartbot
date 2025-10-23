import os
import re
import asyncio
from pyrogram import Client, filters

# ---------- ⚙️ تنظیمات ----------

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

# ---------- 📱 ساخت یوزربات ----------

app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# آیدی سودو برای گزارش
ADMIN_ID = 7089376754

# فایل ذخیره کاربران
USERS_FILE = "users.txt"
known_users = set()

# بارگذاری کاربران ذخیره‌شده
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("|")
            if len(parts) >= 1:
                try:
                    known_users.add(int(parts[0]))
                except:
                    pass

# ---------- 🔁 تابع جوین با چند بار تلاش ----------

async def try_join(client, link, retries=3, delay=3):
    for attempt in range(1, retries + 1):
        try:
            chat = await client.join_chat(link)
            print(f"✅ Joined successfully → {link} (Try {attempt})")

            # ارسال گزارش به سودو بعد از جوین موفق
            try:
                await client.send_message(
                    ADMIN_ID,
                    f"✅ با موفقیت وارد شدم:\n📎 {link}\n🆔 {chat.id}\n📛 {chat.title or 'بدون نام'}",
                )
            except Exception as e:
                print(f"⚠️ ارسال گزارش به سودو ناموفق بود: {e}")

            return True

        except Exception as e:
            err = str(e)
            print(f"⚠️ Error on try {attempt} for {link}: {err}")
            if attempt < retries:
                await asyncio.sleep(delay)
            else:
                raise e
    return False

# ---------- 🧠 تابع هوشمند برای جوین ----------

async def smart_join(client, message, raw_link):
    link = re.sub(r"[\u200b\u200c\uFEFF\s]+", "", raw_link).strip()
    if not link:
        return

    try:
        # 🔹 لینک‌های خصوصی joinchat یا +hash
        if "joinchat" in link or re.search(r"/\+", link):
            await try_join(client, link)
            await message.reply_text(f"✅ وارد شدم (دعوت خصوصی): {link}")
            return

        # 🔹 لینک‌های عمومی t.me یا telegram.me
        if link.startswith("https://t.me/") or link.startswith("http://t.me/") or link.startswith("https://telegram.me/"):
            slug = link.split("/")[-1].split("?")[0]
            if slug.startswith("+"):
                await try_join(client, link)
                await message.reply_text(f"✅ وارد شدم (لینک +): {link}")
                return
            else:
                try:
                    await try_join(client, slug)
                    await message.reply_text(f"✅ وارد شدم (یوزرنیم): {slug}")
                    return
                except Exception as e:
                    if "USERNAME_INVALID" in str(e):
                        fixed = link.replace("https://t.me/", "https://t.me/+")
                        await try_join(client, fixed)
                        await message.reply_text(f"✅ لینک اصلاح شد و وارد شدم → {fixed}")
                        return
                    else:
                        raise e

        # 🔹 لینک‌هایی که با @ شروع می‌شوند
        if link.startswith("@"):
            await try_join(client, link[1:])
            await message.reply_text(f"✅ وارد شدم (از @): {link}")
            return

        # 🔹 سایر موارد
        await message.reply_text(f"⚠️ ساختار لینک نامشخص بود: {link}")

    except Exception as e:
        err = str(e)
        if "USERNAME_INVALID" in err:
            msg = "❌ لینک عمومی معتبر نیست یا کانال خصوصی شده."
        elif "INVITE_HASH_EXPIRED" in err:
            msg = "⏳ لینک منقضی یا حذف شده."
        elif "CHANNEL_PRIVATE" in err:
            msg = "🔒 کانال خصوصی و غیرقابل دسترسی است."
        elif "USER_BANNED_IN_CHANNEL" in err:
            msg = "🚫 این اکانت در آن کانال بن شده است."
        elif "PEER_ID_INVALID" in err:
            msg = "⚠️ نیاز به مجوز یا گفتگو برای جوین."
        else:
            msg = f"❌ خطای ناشناخته:\n{err}"

        await message.reply_text(f"{msg}\n\n🔗 `{link}`")
        print(f"⚠️ Error joining {link}: {err}")

# ---------- 📩 فقط پیوی و کانال ----------

@app.on_message((filters.private | filters.channel) & filters.text)
async def handle_links(client, message):
    text = message.text.strip()

    # بررسی لینک‌ها
    links = re.findall(r"(https?://t\.me/[^\s]+|https?://telegram\.me/[^\s]+|@[\w\d_]+)", text)
    if links:
        for link in links:
            await smart_join(client, message, link)
        return

    # 👋 اگر لینک نبود ولی در پی‌وی پیام داده شد
    if message.chat.type == "private":
        user = message.from_user
        if user and user.id not in known_users:
            known_users.add(user.id)
            name = user.first_name or "کاربر"
            username = f"@{user.username}" if user.username else "نداره"
            with open(USERS_FILE, "a", encoding="utf-8") as f:
                f.write(f"{user.id} | {name} | {username}\n")
            print(f"🆕 کاربر جدید ثبت شد: {name} ({user.id})")

            # ۵ ثانیه بعد پیام ساده بده
            await asyncio.sleep(5)
            await client.send_message(user.id, "سلام بفرمایید؟")

# ---------- 🚫 نادیده گرفتن گروه‌ها ----------

@app.on_message(filters.group)
async def ignore_groups(client, message):
    return

# ---------- 🚀 شروع ----------

print("🚀 یوزربات فعال شد — پاسخ سلام فعال شد و فقط در پیوی و کانال‌ها کار می‌کند.")
app.run()
