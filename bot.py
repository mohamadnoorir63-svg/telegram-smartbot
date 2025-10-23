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


# ---------- 🔁 تابع جوین با چند بار تلاش ----------
async def try_join(client, link, retries=3, delay=3):
    for attempt in range(1, retries + 1):
        try:
            await client.join_chat(link)
            print(f"✅ Joined successfully → {link} (Try {attempt})")
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


# ---------- 📩 فقط پیوی و کانال (با پشتیبانی از فوروارد و کپشن) ----------
@app.on_message((filters.private | filters.channel))
async def handle_links(client, message):
    # گرفتن متن، کپشن یا پیام فرواردشده
    text = ""
    if message.text:
        text = message.text
    elif message.caption:
        text = message.caption
    elif message.forward_date:
        # پیام فروارد‌شده — بررسی می‌کنیم آیا از کانال اومده
        if message.forward_from_chat and message.forward_from_chat.type == "channel":
            if message.forward_from_message_id:
                text = getattr(message, "forward_text", "") or getattr(message, "text", "")
        else:
            text = ""

    if not text:
        if message.chat.type == "private":
            await message.reply_text("📎 لینک تلگرام بفرست یا پست کانالی که لینک داره رو فوروارد کن.")
        return

    # پیدا کردن لینک‌ها در پیام یا کپشن
    links = re.findall(r"(https?://t\.me/[^\s]+|https?://telegram\.me/[^\s]+|@[\w\d_]+)", text)
    if not links:
        return

    # پردازش لینک‌ها
    for link in links:
        await smart_join(client, message, link)


# ---------- 🚫 نادیده گرفتن گروه‌ها ----------
@app.on_message(filters.group)
async def ignore_groups(client, message):
    return


# ---------- 🚀 شروع ----------
print("🚀 یوزربات فعال شد — لینک‌ها را از پیوی و فورواردهای کانال می‌خواند...")
app.run()
