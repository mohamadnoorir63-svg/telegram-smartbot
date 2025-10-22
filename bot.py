# bot.py
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import os, asyncio, yt_dlp, shutil, uuid

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH"))

app = Client("musicbot", api_id=API_ID, api_hash=API_HASH)

# وضعیت‌ها در حافظه (برای هر chat_id یک صف و state)
chats = {}  # chat_id -> {"queue": [ {"query":..., "title":...} ], "playing": False, "paused": False, "volume": 100, "speed":1.0}

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def make_panel(chat_id):
    st = chats.get(chat_id, {"queue":[], "playing":False, "paused":False, "volume":100})
    queue_len = len(st["queue"])
    playing = st["playing"]
    paused = st["paused"]
    vol = st.get("volume", 100)

    txt = f"🎧 پنل موزیک — صف: {queue_len}\nوضعیت: {'⏸️ متوقف' if paused else ('▶️ درحال پخش' if playing else '⛔ غیرفعال')}\nحجم:{vol}%"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("⏯️ پخش/ادامه", callback_data=f"play|{chat_id}"),
         InlineKeyboardButton("⏸️ توقف", callback_data=f"pause|{chat_id}"),
         InlineKeyboardButton("⏹️ متوقف و پاک", callback_data=f"stop|{chat_id}")],
        [InlineKeyboardButton("⏭️ رد کن", callback_data=f"skip|{chat_id}"),
         InlineKeyboardButton("🔽 ولوم-", callback_data=f"vol-|{chat_id}"),
         InlineKeyboardButton("🔼 ولوم+", callback_data=f"vol+|{chat_id}")],
        [InlineKeyboardButton("⏪ -30s", callback_data=f"seek-|{chat_id}"),
         InlineKeyboardButton("دریافت فایل", callback_data=f"download|{chat_id}"),
         InlineKeyboardButton("⏩ +30s", callback_data=f"seek+|{chat_id}")],
    ])
    return txt, kb

async def download_track(query):
    # دانلود آهنگ با yt_dlp (همان تنظیمات شما)
    rand_name = str(uuid.uuid4())
    outtmpl = os.path.join(DOWNLOAD_DIR, f"{rand_name}.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "noplaylist": True,
        "quiet": True,
    }
    def _dl():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if query.startswith("http"):
                info = ydl.extract_info(query, download=True)
            else:
                info = ydl.extract_info(f"ytsearch1:{query}", download=True)
                # ytsearch1 returns dict with entries
                if isinstance(info, dict) and "entries" in info:
                    info = info["entries"][0]
        return info
    info = await asyncio.to_thread(_dl)
    # آماده‌سازی نام فایل
    # ydl.prepare_filename unavailable here; reconstruct filename
    ext = info.get("ext") or "mp3"
    filename = None
    # yt_dlp usually writes file as outtmpl with ext
    for f in os.listdir(DOWNLOAD_DIR):
        if f.startswith(rand_name):
            filename = os.path.join(DOWNLOAD_DIR, f)
            break
    if not filename:
        raise Exception("فایل دانلود نشد")
    return filename, info

@app.on_message(filters.text & ~filters.private)
async def text_handler(client, message):
    # اضافه کردن آهنگ به صف با دستورات قبلیِ تو (music / آهنگ / music without slash / musik)
    text = (message.text or "").strip()
    chat_id = message.chat.id

    query = None
    # حالت با اسلش: /music ...
    if text.startswith("/music") or text.startswith("!music"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            await message.reply_text("❌ لطفاً نام آهنگ یا لینک رو بنویس: `/music Arash`")
            return
        query = parts[1].strip()
    elif text.lower().startswith("آهنگ "):
        query = text[len("آهنگ "):].strip()
    elif text.lower().startswith("music "):
        query = text[len("music "):].strip()
    elif text.lower().startswith("musik "):
        query = text[len("musik "):].strip()
    else:
        return  # نگه ندار بقیه پیام‌ها را

    if not query:
        await message.reply_text("نام آهنگ خالیه.")
        return

    # ایجاد وضعیت چت اگر نبود
    if chat_id not in chats:
        chats[chat_id] = {"queue":[], "playing":False, "paused":False, "volume":100}
    chats[chat_id]["queue"].append({"query": query})

    txt, kb = make_panel(chat_id)
    await message.reply_text(f"✅ به صف اضافه شد:\n`{query}`", reply_markup=kb)

@app.on_callback_query()
async def cb_handler(client, cq):
    data = cq.data or ""
    parts = data.split("|")
    action = parts[0]
    try:
        chat_id = int(parts[1])
    except:
        await cq.answer("خطا")
        return

    if chat_id not in chats:
        chats[chat_id] = {"queue":[], "playing":False, "paused":False, "volume":100}

    state = chats[chat_id]

    # PLAY
    if action == "play":
        if state["playing"]:
            state["paused"] = False
            await cq.answer("ادامه پخش")
        else:
            # اگر صف خالیست پیام بده
            if not state["queue"]:
                await cq.answer("صف خالیست")
            else:
                state["playing"] = True
                state["paused"] = False
                await cq.answer("در حال پخش...")
                # پخش اولین آهنگ در صف (به‌صورت ارسال فایل audio)
                item = state["queue"].pop(0)
                query = item["query"]
                msg = await cq.message.edit_text(f"🎧 دانلود و پخش: `{query}`")
                try:
                    filepath, info = await download_track(query)
                    title = info.get("title", "Unknown")
                    performer = info.get("uploader", "Unknown")
                    await client.send_audio(chat_id, audio=filepath, title=title, performer=performer, caption=f"🎶 {title}\n👤 {performer}")
                    os.remove(filepath)
                except Exception as e:
                    await cq.message.edit_text(f"❌ خطا در دانلود/پخش:\n`{e}`")
                finally:
                    state["playing"] = False
                    # بعد از پخش پنل رو آپدیت کن
                    txt, kb = make_panel(chat_id)
                    await cq.message.edit_text(txt, reply_markup=kb)

    # PAUSE: فقط حالت paused رو ست میکنیم
    elif action == "pause":
        state["paused"] = True
        state["playing"] = False
        await cq.answer("توقف شد")
        txt, kb = make_panel(chat_id)
        await cq.message.edit_text(txt, reply_markup=kb)

    # STOP: پاک کردن صف و حالت
    elif action == "stop":
        state["queue"].clear()
        state["playing"] = False
        state["paused"] = False
        await cq.answer("صف پاک شد و پخش متوقف شد")
        txt, kb = make_panel(chat_id)
        await cq.message.edit_text(txt, reply_markup=kb)

    # SKIP: همانند play ولی نوتیف بده
    elif action == "skip":
        if not state["queue"]:
            await cq.answer("صف خالیست")
        else:
            # فوراً play بعدی
            await cq.answer("رد به آهنگ بعدی...")
            # set playing false تا play handler قبلی اجرا کند (اینجا ساده: اجرا می‌کنیم)
            state["playing"] = True
            item = state["queue"].pop(0)
            query = item["query"]
            try:
                filepath, info = await download_track(query)
                title = info.get("title", "Unknown")
                performer = info.get("uploader", "Unknown")
                await client.send_audio(chat_id, audio=filepath, title=title, performer=performer, caption=f"🎶 {title}\n👤 {performer}")
                os.remove(filepath)
            except Exception as e:
                await cq.message.edit_text(f"❌ خطا در دانلود/پخش:\n`{e}`")
            finally:
                state["playing"] = False
                txt, kb = make_panel(chat_id)
                await cq.message.edit_text(txt, reply_markup=kb)

    # VOLUME +/-
    elif action in ("vol+", "vol-"):
        v = state.get("volume", 100)
        if action == "vol+":
            v = min(200, v + 10)
        else:
            v = max(10, v - 10)
        state["volume"] = v
        await cq.answer(f"ولوم: {v}% (نمایشی)")
        txt, kb = make_panel(chat_id)
        await cq.message.edit_text(txt, reply_markup=kb)

    # SEEK و DOWNLOAD (seek فقط نمایشی، download فایل آخر صف یا در حال پخش را می‌فرستد)
    elif action == "download":
        # اگر چیزی اخیراً پخش شده نداریم، پیام بده
        await cq.answer("دریافت فایل (اگر در دسترس باشد)...")
        await cq.message.reply_text("این دکمه فایل فعلی را دانلود می‌کند اگر موجود باشد (در این نمونه هر فایل بلافاصله پس از ارسال حذف می‌شود).")
        # فقط اطلاع می‌دهیم در این پیاده‌سازی فایل پس از ارسال حذف می‌شود.
    else:
        await cq.answer("دکمه نامشخص")

print("🎧 Music control panel bot starting...")
app.run()
