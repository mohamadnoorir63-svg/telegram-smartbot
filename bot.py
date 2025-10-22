import os
import asyncio
from pyrogram import Client, filters

# ---------- تنظیمات ----------
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")  # حتما در Config Vars بذار
SUDO_USERS = [7089376754]  # آی‌دی عددی خودت
LINKS_FILE = "links.txt"
CHECK_INTERVAL = 5  # هر چند دقیقه فایل links.txt چک بشه

# ---------- ساخت یوزربات ----------
app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

joined_links = set()        # لینک‌هایی که قبلاً جوین شده‌اند
waiting_for_links = {}      # حالت "منتظر لینک" برای هر چت

# فیلتر برای فقط قبول پیام از سودو
sudo_filter = filters.user(SUDO_USERS)

# ---------- دستور: بیا (شروع) ----------
@app.on_message(sudo_filter & filters.text & filters.regex(r"^بیا$"))
async def ask_for_links(client, message):
    waiting_for_links[message.chat.id] = True
    await message.reply_text(
        "📎 لینک‌ها رو بفرست (هر کدوم در یک خط) یا فایل txt بفرست.\n"
        "وقتی تموم شد بنویس: **پایان**"
    )

# ---------- گرفتن لینک‌ها به صورت متنی ----------
@app.on_message(sudo_filter & filters.text)
async def handle_links(client, message):
    chat_id = message.chat.id
    if not waiting_for_links.get(chat_id):
        return

    text = message.text.strip()
    if text == "پایان":
        waiting_for_links[chat_id] = False
        await message.reply_text("✅ دریافت لینک‌ها تموم شد — دارم پردازش می‌کنم...")
        return

    links = [line.strip() for line in text.splitlines() if line.strip()]
    await join_multiple(client, message, links)

# ---------- گرفتن لینک‌ها از فایل txt ----------
@app.on_message(sudo_filter & filters.document)
async def handle_file(client, message):
    # قبول فقط فایل text/plain یا پسوند txt
    mime = (message.document.mime_type or "").lower()
    name = (message.document.file_name or "").lower()
    if "text" in mime or name.endswith(".txt"):
        file_path = await message.download()
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                links = [line.strip() for line in f if line.strip()]
            await join_multiple(client, message, links)
        finally:
            try:
                os.remove(file_path)
            except:
                pass
    else:
        await message.reply_text("❗ فایل txt بفرست لطفاً.")

# ---------- تابع تلاش برای جوین یک لینک ----------
async def try_join(bot, link):
    # لینک‌های joinchat / + یا یوزرنیم/گروه عمومی
    if link.startswith(("https://t.me/joinchat/", "https://t.me/+")):
        await bot.join_chat(link)
    elif link.startswith(("https://t.me/", "@")):
        username = link.replace("https://t.me/", "").replace("@", "")
        if not username:
            raise ValueError("یوزرنیم ناقص است")
        await bot.join_chat(username)
    else:
        raise ValueError("لینک معتبر نیست")

# ---------- تابع ورود به چند لینک با هندل دقیق خطا ----------
async def join_multiple(client, message, links):
    results = []
    for link in links:
        if link in joined_links:
            results.append(f"⏭ قبلاً عضو شده بودم: {link}")
            continue

        try:
            await try_join(app, link)  # چون تک سشن، از app استفاده می‌کنیم
            joined_links.add(link)
            results.append(f"✅ Joined: {link}")
        except Exception as e:
            # تفکیک خطاها برای پیام کاربر
            err = str(e)
            if "USER_ALREADY_PARTICIPANT" in err or "already participant" in err.lower():
                joined_links.add(link)
                results.append(f"⏭ قبلاً عضو بودم: {link}")
            elif "INVITE_HASH_EXPIRED" in err or "invite" in err.lower():
                results.append(f"🚫 لینک منقضی یا غیرقابل‌استفاده: {link}")
            else:
                results.append(f"❌ خطا برای {link}: {err}")

    # ارسال نتیجه (آخرین 30 خط)
    if message:
        text = "\n".join(results[-30:]) or "🔎 هیچ لینکی پردازش نشد."
        await message.reply_text(f"📋 نتیجه:\n{text}")

# ---------- بررسی خودکار فایل links.txt ----------
async def auto_check_links():
    while True:
        await asyncio.sleep(CHECK_INTERVAL * 60)
        if os.path.exists(LINKS_FILE):
            try:
                with open(LINKS_FILE, "r", encoding="utf-8") as f:
                    links = [line.strip() for line in f if line.strip()]
                if links:
                    print(f"🔁 auto checking {len(links)} links...")
                    # از یک پیام ساختگی استفاده می‌کنیم (خروجی روی لاگ)
                    class Dummy:
                        async def reply_text(self, text): print(text)
                    await join_multiple(app, Dummy(), links)
            except Exception as e:
                print("Auto-check error:", e)

# ---------- خروج از گروه ----------
@app.on_message(sudo_filter & filters.regex(r"^برو بیرون$"))
async def leave_group(client, message):
    try:
        await client.leave_chat(message.chat.id)
        await message.reply_text("🚪 از گروه خارج شدم.")
    except Exception as e:
        await message.reply_text(f"⚠️ خطا هنگام خروج: {e}")

# ---------- وضعیت ----------
@app.on_message(sudo_filter & filters.regex(r"^وضعیت$"))
async def status(client, message):
    await message.reply_text(f"🟢 فعال!\nتعداد گروه‌های جوین‌شده: {len(joined_links)}")

# ---------- شروع امن و پایدار ----------
async def main():
    # قبل از استارت حتما SESSION_STRING در Config Vars باید وجود داشته باشه
    if not SESSION_STRING:
        print("ERROR: SESSION_STRING is missing in config vars.")
        return

    await app.start()
    print("✅ Single-session Userbot started and running.")
    # اجرا همزمان تسک خودکار
    asyncio.create_task(auto_check_links())
    await asyncio.Event().wait()  # نگه داشتن برنامه برای همیشه

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print("Fatal error:", e)
