import os
import re
from pyrogram import Client

# ---------- ⚙️ تنظیمات ----------
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

# ---------- 📱 ساخت یوزربات ----------
app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# ---------- 🔗 تابع هوشمند برای جوین ----------
async def smart_join(client, message, raw_link):
    link = re.sub(r"[\u200b\u200c\uFEFF\s]+", "", raw_link)  # پاکسازی فاصله‌های مخفی
    if not link:
        return

    try:
        # 1️⃣ لینک‌های خصوصی یا joinchat (مثل +abc123 یا /joinchat/)
        if "joinchat" in link or re.search(r"/\+", link):
            await client.join_chat(link)
            await message.reply_text(f"✅ وارد شدم (دعوت خصوصی): {link}")
            return

        # 2️⃣ لینک‌های عمومی (با username)
        if link.startswith("https://t.me/") or link.startswith("http://t.me/") or link.startswith("https://telegram.me/"):
            slug = link.split("/")[-1].split("?")[0]
            if slug.startswith("+"):
                await client.join_chat(link)
                await message.reply_text(f"✅ وارد شدم (لینک +): {link}")
                return
            else:
                try:
                    await client.join_chat(slug)
                    await message.reply_text(f"✅ وارد شدم (یوزرنیم): {slug}")
                    return
                except Exception as e:
                    # اگر لینک عمومی جواب نداد، دوباره با joinchat تست کن
                    if "USERNAME_INVALID" in str(e):
                        fixed = link.replace("https://t.me/", "https://t.me/+")
                        try:
                            await client.join_chat(fixed)
                            await message.reply_text(f"✅ لینک اصلاح شد و وارد شدم → {fixed}")
                            return
                        except Exception as e2:
                            raise e2
                    else:
                        raise e

        # 3️⃣ اگر فقط با @ شروع شده
        if link.startswith("@"):
            await client.join_chat(link[1:])
            await message.reply_text(f"✅ وارد شدم (از @): {link}")
            return

        # 4️⃣ هر چیز دیگر
        await message.reply_text(f"⚠️ ساختار لینک ناشناخته بود: {link}")

    except Exception as e:
        err = str(e)
        # 🔍 شناسایی نوع خطا و نمایش فارسی
        if "USERNAME_INVALID" in err:
            msg = "❌ لینک عمومی معتبر نیست یا کانال خصوصی شده."
        elif "INVITE_HASH_EXPIRED" in err:
            msg = "⏳ لینک منقضی شده یا حذف شده."
        elif "CHANNEL_PRIVATE" in err:
            msg = "🔒 کانال خصوصی و غیرقابل دسترسی است."
        elif "USER_BANNED_IN_CHANNEL" in err:
            msg = "🚫 این اکانت در آن کانال بن شده است."
        elif "PEER_ID_INVALID" in err:
            msg = "⚠️ نیاز به گفتگو یا مجوز بیشتر برای جوین."
        else:
            msg = f"❌ خطا ناشناخته:\n{err}"

        await message.reply_text(f"{msg}\n\n🔗 `{link}`")
        print(f"⚠️ Error joining {link}: {err}")

# ---------- 📩 گوش دادن به پیام‌ها ----------
@app.on_message()
async def auto_join_handler(client, message):
    if not message.text:
        return

    text = message.text
    # پیدا کردن همه لینک‌ها در متن
    links = re.findall(r"(https?://t\.me/[^\s]+|https?://telegram\.me/[^\s]+|@[\w\d_]+)", text)

    if not links:
        return

    for l in links:
        await smart_join(client, message, l)

# ---------- 🚀 شروع ----------
print("🚀 ربات آماده است — هر لینکی بفرست، خودش تشخیص می‌دهد و جوین می‌شود...")
app.run()
