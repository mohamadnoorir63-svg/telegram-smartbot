import os, re, time, json, asyncio
from pyrogram import Client, filters

# ====== ⚙️ تنظیمات اصلی ======
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

# خواندن آیدی سودو از هاست
try:
    SUDO_ID = int(os.getenv("SUDO_ID"))
except:
    SUDO_ID = 7089376754  # مقدار پیش‌فرض درصورت نبود در Config Vars

# ====== 🗂 مسیر فایل‌ها ======
USERS_FILE = "users.txt"
GREETED_FILE = "greeted.txt"
GROUPS_FILE = "groups.txt"

# ====== 💾 داده‌ها ======
known_users, greeted_users, joined_groups = set(), set(), set()
message_count = 0
left_groups_counter = 0
start_time = time.time()
waiting_for_links = {}

# ====== 🧠 توابع کمکی ======
def load_lines(p):
    if not os.path.exists(p):
        return []
    with open(p, "r", encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip()]

for ln in load_lines(USERS_FILE):
    try:
        known_users.add(ln.split("|")[0].strip())
    except:
        pass

for ln in load_lines(GREETED_FILE):
    greeted_users.add(ln)

for ln in load_lines(GROUPS_FILE):
    joined_groups.add(ln)

# ====== 💬 ساخت کلاینت ======
app = Client("sara_userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# ====== ⏱ زمان اجرا به ساعت و دقیقه ======
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

# ====== 👑 تشخیص سودو ======
def is_sudo(msg):
    """چک می‌کنه آیا پیام از صاحب رباته یا نه"""
    return (
        getattr(msg, "outgoing", False)
        or (msg.from_user and msg.from_user.id == SUDO_ID)
    )

# ====== 📡 آمار گروه‌ها ======
async def count_groups(client):
    count = 0
    async for d in client.get_dialogs():
        if d.chat and d.chat.type in ("group", "supergroup"):
            count += 1
    return count

# ====== 💬 هندلر پیام‌های خصوصی ======
@app.on_message(filters.private & filters.text)
async def handle_private(client, message):
    global message_count
    message_count += 1
    user = message.from_user
    if not user:
        return

    uid = str(user.id)
    name = user.first_name or "ناشناس"
    username = f"@{user.username}" if user.username else "نداره"

    # ذخیره کاربر
    if uid not in known_users:
        known_users.add(uid)
        with open(USERS_FILE, "a", encoding="utf-8") as f:
            f.write(f"{uid} | {name} | {username}\n")
        print(f"🆕 کاربر جدید: {uid} | {name}")
        await message.reply_text("✅ ثبت شدی در لیست سارا 💖")

    # سلام فقط یکبار
    txt = message.text.strip().lower()
    if txt in ["سلام", "salam", "hi", "hello"] and uid not in greeted_users:
        greeted_users.add(uid)
        with open(GREETED_FILE, "a", encoding="utf-8") as f:
            f.write(uid + "\n")
        await message.reply_text("سلام 🌹 خوش اومدی 💬")

# ====== 🧹 پاکسازی گروه‌های خراب ======
async def clean_bad_groups(client, message=None):
    global left_groups_counter
    left = 0
    checked = 0

    async for dialog in client.get_dialogs():
        chat = dialog.chat
        if chat and chat.type in ("group", "supergroup"):
            checked += 1
            try:
                await client.get_chat_members_count(chat.id)
            except Exception:
                try:
                    await client.leave_chat(chat.id)
                    left += 1
                    left_groups_counter += 1
                except:
                    pass

    result = f"🧹 بررسی: {checked}\n🚪 ترک: {left}"
    if message:
        await message.reply_text(result)
    else:
        try:
            await client.send_message(SUDO_ID, result)
        except:
            pass

# ====== 🔗 جوین گروه‌ها ======
async def join_links(client, message, links):
    joined = 0
    failed = 0
    results = []

    for link in links:
        try:
            link = link.strip()
            if link.startswith("@"):
                link = link[1:]
            await client.join_chat(link)
            joined += 1
            joined_groups.add(link)
            with open(GROUPS_FILE, "a", encoding="utf-8") as f:
                f.write(link + "\n")
            results.append(f"✅ وارد شدم: {link}")
        except Exception as e:
            failed += 1
            results.append(f"❌ {link} → {e}")

    report = "\n".join(results[-30:]) or "—"
    await message.reply_text(f"📋 نتیجه:\n{report}\n\n✅ موفق: {joined} | ❌ خطا: {failed}")

# ====== ⚙️ هندلر اصلی دستورها ======
@app.on_message(filters.text)
async def sara_commands(client, message):
    if not is_sudo(message):
        return

    text = message.text.strip().lower()
    cid = message.chat.id

    # 🟢 پینگ
    if text in ["پینگ", "ping"]:
        await message.reply_text("🟢 سارا فعاله!")
        return

    # 🟣 جوین
    if text == "جوین":
        waiting_for_links[cid] = []
        await message.reply_text("📎 لینک‌هاتو بفرست (هر کدوم در یک خط)\nوقتی تموم شد بنویس: پایان")
        return

    # 🔚 پایان
    if text == "پایان" and cid in waiting_for_links:
        links = waiting_for_links.pop(cid)
        if not links:
            await message.reply_text("⚠️ هیچ لینکی دریافت نشد.")
            return
        await message.reply_text(f"🔍 دارم {len(links)} تا لینک رو بررسی می‌کنم...")
        await join_links(client, message, links)
        return

    # 📊 آمار کاربران
    if text == "آمار کاربران":
        await message.reply_text(f"👥 کاربران ذخیره‌شده: {len(known_users)}")
        return

    # 👥 آمار گروه‌ها
    if text == "آمار گروه‌ها":
        gcount = await count_groups(client)
        await message.reply_text(f"👩‍👩‍👧 گروه‌های عضو‌شده: {gcount}")
        return

    # 🧹 پاکسازی
    if text == "پاکسازی":
        await clean_bad_groups(client, message)
        return

    # 🟢 لینک‌های درحال دریافت
    if cid in waiting_for_links:
        new_links = [ln.strip() for ln in text.splitlines() if ln.strip()]
        waiting_for_links[cid].extend(new_links)
        await message.reply_text(f"✅ {len(new_links)} لینک اضافه شد.")

# ====== 📈 گزارش خودکار ساعتی ======
async def hourly_report():
    while True:
        try:
            gcount = await count_groups(app)
            uptime = uptime_text(time.time() - start_time)
            txt = (
                f"📊 گزارش خودکار سارا\n\n"
                f"👥 کاربران: {len(known_users)}\n"
                f"💬 پیام‌های پی‌وی: {message_count}\n"
                f"👩‍👩‍👧 گروه‌ها: {gcount}\n"
                f"🚪 ترک‌شده: {left_groups_counter}\n"
                f"⏱ فعالیت: {uptime}"
            )
            await app.send_message(SUDO_ID, txt)
        except Exception as e:
            print("hourly report error:", e)
        await asyncio.sleep(3600)  # هر ساعت

# ====== 🚀 اجرای اصلی ======
async def main_loop():
    await app.start()
    print("✅ سارا بالا آمد.")
    try:
        await app.send_message(SUDO_ID, "💖 سارا فعال شد و آماده‌ست.")
    except:
        pass
    asyncio.create_task(hourly_report())
    await asyncio.Event().wait()

async def run_forever():
    while True:
        try:
            await main_loop()
        except Exception as e:
            print("⚠️ خطا:", e)
            try:
                await app.send_message(SUDO_ID, "❌ سارا خاموش شد! تلاش برای روشن شدن مجدد...")
            except:
                pass
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(run_forever())
