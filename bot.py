import os, re, time, json, asyncio
from pyrogram import Client, filters

# ====== تنظیمات اصلی ======
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
SUDO_ID = 7089376754

USERS_FILE = "users.txt"
GREETED_FILE = "greeted.txt"
GROUPS_FILE = "groups.txt"
SNAP_FILE = "stats_snapshot.json"

known_users, greeted_users, joined_groups = set(), set(), set()
message_count = 0
left_groups_counter = 0
start_time = time.time()
waiting_for_links = {}

# ====== بارگذاری اولیه فایل‌ها ======
def load_lines(p):
    if not os.path.exists(p): return []
    with open(p, "r", encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip()]

for ln in load_lines(USERS_FILE):
    try: known_users.add(ln.split("|")[0].strip())
    except: pass

for ln in load_lines(GREETED_FILE):
    greeted_users.add(ln)

for ln in load_lines(GROUPS_FILE):
    joined_groups.add(ln)

# ====== کلاینت ======
app = Client("sara_userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# ====== فیلتر سودو محکم (سه‌حالته) ======
def is_sudo(_, __, m):
    # حالت 1: پیام از خودت (اکانت خودت) – در هر چتی
    if getattr(m, "outgoing", False):
        return True
    # حالت 2: فرستنده مشخص و آیدی‌اش مساوی سودو
    if m.from_user and m.from_user.id == SUDO_ID:
        return True
    # حالت 3: ادمین ناشناس/کانالیِ خودت داخل گروه (sender_chat == chat) + پیام خروجی نبود
    if m.sender_chat and m.chat and m.sender_chat.id == m.chat.id and m.chat.id == SUDO_ID:
        return True
    return False

sudo = filters.create(is_sudo)

# ====== ابزارها ======
async def dialogs_groups_count(c: Client) -> int:
    cnt = 0
    async for d in c.get_dialogs():
        if d.chat and d.chat.type in ("group", "supergroup"):
            cnt += 1
    return cnt

def uptime_h(ms):
    sec = int(ms)
    m = sec // 60
    h = m // 60
    m = m % 60
    if h: return f"{h} ساعت و {m} دقیقه"
    if m: return f"{m} دقیقه"
    return f"{sec} ثانیه"

# ====== هندلر تست سریع (حتماً جواب بده) ======
@app.on_message(sudo & filters.text & filters.regex(r"^(ping|پینگ)$", flags=re.I))
async def _ping(c, m):
    await m.reply_text("🟢 زنده‌ام!")

# ====== ذخیره‌ی کاربر + جواب سلام فقط یک بار ======
@app.on_message(filters.private & filters.text)
async def pm_save_and_greet(c, m):
    global message_count
    message_count += 1
    u = m.from_user
    if not u: 
        print("PM without from_user")
        return

    uid = str(u.id)
    name = u.first_name or "ناشناس"
    un = f"@{u.username}" if u.username else "نداره"

    # ثبت کاربر
    if uid not in known_users:
        known_users.add(uid)
        with open(USERS_FILE, "a", encoding="utf-8") as f:
            f.write(f"{uid} | {name} | {un}\n")
        print(f"🆕 کاربر جدید: {uid} | {name} | {un}")
        await m.reply_text("✅ ثبت شدی.")

    # سلام فقط یک بار
    txt = (m.text or "").strip().lower()
    if txt in ("سلام", "salam", "hi", "hello"):
        if uid not in greeted_users:
            greeted_users.add(uid)
            with open(GREETED_FILE, "a", encoding="utf-8") as f:
                f.write(uid + "\n")
            await m.reply_text("سلام 🌹 خوش اومدی 💬")

# ====== دستورها (نسخه‌ی ضروری برای راه افتادن) ======
@app.on_message(sudo & filters.text)
async def core_cmds(c, m):
    global left_groups_counter
    t = (m.text or "").strip()
    tl = t.lower()
    cid = m.chat.id

    # جوین
    if tl == "جوین":
        waiting_for_links[cid] = []
        await m.reply_text("📎 لینک‌ها رو بفرست. وقتی تموم شد بنویس: پایان")
        return

    # پایان
    if tl == "پایان" and cid in waiting_for_links:
        links = waiting_for_links.pop(cid)
        if not links:
            await m.reply_text("⚠️ هیچ لینکی دریافت نشد.")
            return
        await m.reply_text(f"🔍 در حال جوین به {len(links)} لینک...")
        await join_links(c, m, links)
        return

    # آمار کاربران
    if tl == "آمار کاربران":
        await m.reply_text(f"👥 کاربران ذخیره‌شده: {len(known_users)}")
        return

    # آمار گروه‌ها
    if tl == "آمار گروه‌ها":
        gc = await dialogs_groups_count(c)
        await m.reply_text(f"👩‍👩‍👧 گروه‌های عضو‌شده: {gc}")
        return

    # پاکسازی
    if tl == "پاکسازی":
        await clean_bad_groups(c, m)
        return

    # دریافت لینک‌ها در حالت انتظار
    if cid in waiting_for_links:
        new_links = [ln.strip() for ln in t.splitlines() if ln.strip()]
        waiting_for_links[cid].extend(new_links)
        await m.reply_text(f"✅ {len(new_links)} لینک اضافه شد.")

# ====== جوین لینک‌ها ======
async def join_links(c, m, links):
    ok = 0; bad = 0
    out = []
    for link in links:
        try:
            L = link.strip()
            if L.startswith("@"): L = L[1:]
            await c.join_chat(L)
            ok += 1
            joined_groups.add(L)
            with open(GROUPS_FILE, "a", encoding="utf-8") as f:
                f.write(L + "\n")
            out.append(f"✅ {L}")
        except Exception as e:
            bad += 1
            out.append(f"❌ {link} → {e}")

    chunk = "\n".join(out[-30:]) if out else "—"
    await m.reply_text(f"📋 نتیجه:\n{chunk}\n\n✅ موفق: {ok} | ❌ خطا: {bad}")

# ====== پاکسازی گروه‌های خراب ======
async def clean_bad_groups(c, m):
    global left_groups_counter
    left = 0
    checked = 0
    async for d in c.get_dialogs():
        ch = d.chat
        if ch and ch.type in ("group", "supergroup"):
            checked += 1
            try:
                await c.get_chat_members_count(ch.id)
            except Exception:
                try:
                    await c.leave_chat(ch.id)
                    left += 1
                    left_groups_counter += 1
                except:
                    pass
    await m.reply_text(f"🧹 بررسی: {checked}\n🚪 ترک: {left}")

# ====== گزارش ساعتی ساده به سودو (برای تست سلامت) ======
async def hourly_report():
    while True:
        try:
            gc = await dialogs_groups_count(app)
            up = time.time() - start_time
            txt = (
                "📊 گزارش خودکار سارا\n\n"
                f"👥 کاربران: {len(known_users)}\n"
                f"💬 پیام‌های پی‌وی: {message_count}\n"
                f"👩‍👩‍👧 گروه‌ها: {gc}\n"
                f"🚪 ترک‌شده: {left_groups_counter}\n"
                f"⏱ فعالیت: {uptime_h(up)}"
            )
            await app.send_message(SUDO_ID, txt)
        except Exception as e:
            print("hourly report error:", e)
        await asyncio.sleep(3600)

# ====== حلقه‌ی پایدار ======
async def main_once():
    await app.start()
    print("✅ سارا بالا آمد.")
    try:
        await app.send_message(SUDO_ID, "💖 سارا فعال شد و آماده‌ست.")
    except Exception as e:
        print("cannot DM sudo:", e)
    asyncio.create_task(hourly_report())
    await asyncio.Event().wait()

async def run_forever():
    while True:
        try:
            await main_once()
        except Exception as e:
            print("CRASH:", e)
            try:
                await app.send_message(SUDO_ID, "❌ سارا خاموش شد! تلاش برای روشن‌شدن دوباره…")
            except: pass
            await asyncio.sleep(8)

if __name__ == "__main__":
    asyncio.run(run_forever())
