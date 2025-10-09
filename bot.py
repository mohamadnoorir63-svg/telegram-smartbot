# -*- coding: utf-8 -*-
import os, json, time, datetime
from telebot import TeleBot, types
from openai import OpenAI

# --------- ENV ---------
BOT_TOKEN        = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
ADMIN_ID         = int(os.getenv("ADMIN_ID") or "0")  # عددی
ADMIN_USERNAME   = os.getenv("ADMIN_USERNAME") or "@NOORI_NOOR"
BOT_NAME_FARSI   = "ربات هوشمند نوری 🤖"

if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN تعریف نشده است.")
if not ADMIN_ID:
    raise SystemExit("ADMIN_ID (عددی) تعریف نشده است.")
if not OPENAI_API_KEY:
    raise SystemExit("OPENAI_API_KEY تعریف نشده است.")

# --------- INIT ---------
bot    = TeleBot(BOT_TOKEN, parse_mode="HTML")
client = OpenAI(api_key=OPENAI_API_KEY)

DATA_FILE = "data.json"
DEFAULT_FREE_COINS = 5

def now_ts(): return int(time.time())

def load_data():
    base = {
        "users": {}, "banned": [], "muted": {},
        "groups": {}, "support_open": {},
        "admin_reply_to": None, "pending_broadcast": False
    }
    if not os.path.exists(DATA_FILE):
        save_data(base)
        return base
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        d = json.load(f)
    for k,v in base.items():
        if k not in d: d[k]=v
    save_data(d); return d

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

data = load_data()
def is_admin(uid): return str(uid)==str(ADMIN_ID)

def ensure_user(uid, name=""):
    su=str(uid)
    if su not in data["users"]:
        data["users"][su]={"coins":DEFAULT_FREE_COINS,"active":True,"name":name}
        save_data(data)

def get_bot_username():
    try: return bot.get_me().username
    except: return "NoorirSmartBot"

def get_bot_id():
    try: return bot.get_me().id
    except: return None

# --------- KEYBOARDS ---------
def kb_user(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(types.KeyboardButton("راهنما 💡"), types.KeyboardButton("شارژ مجدد 🟩"))
    kb.row(types.KeyboardButton("پشتیبانی ☎️"), types.KeyboardButton("سازنده 👤"))
    kb.row(types.KeyboardButton("افزودن به گروه ➕"))
    kb.row(types.KeyboardButton("روشن / خاموش 🧠"))
    return kb

def kb_admin():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(types.KeyboardButton("آمار کاربران 📊"), types.KeyboardButton("ارسال همگانی 📣"))
    kb.row(types.KeyboardButton("سکوت کاربر 🤐"), types.KeyboardButton("بن کاربر 🚫"))
    kb.row(types.KeyboardButton("لیست بن‌ها 🚫"), types.KeyboardButton("لیست سکوت‌ها 🤫"))
    kb.row(types.KeyboardButton("راهنمای سودو 📘"), types.KeyboardButton("لفت بده ↩️"))
    return kb

def ikb_user():
    ik = types.InlineKeyboardMarkup()
    ik.add(types.InlineKeyboardButton("➕ افزودن به گروه", url=f"https://t.me/{get_bot_username()}?startgroup=add"))
    ik.add(types.InlineKeyboardButton("ارتباط با سازنده", url=f"https://t.me/{ADMIN_USERNAME.replace('@','')}"))
    return ik

def ikb_support(uid):
    ik = types.InlineKeyboardMarkup()
    ik.add(
        types.InlineKeyboardButton("پاسخ به کاربر ✉️", callback_data=f"reply:{uid}"),
        types.InlineKeyboardButton("بستن گفتگو ❌", callback_data=f"close:{uid}")
    )
    return ik

# --------- START ---------
@bot.message_handler(commands=["start"])
def start_cmd(m):
    uid=m.from_user.id
    ensure_user(uid, m.from_user.first_name or "")
    if is_admin(uid):
        bot.reply_to(m, "👑 سلام مدیر! وارد پنل مدیریتی شدی.", reply_markup=kb_admin())
    else:
        bot.reply_to(m,
            f"سلام! 👋 به <b>{BOT_NAME_FARSI}</b> خوش اومدی.\n"
            "با ارسال متن یا عکس پاسخ هوش مصنوعی بگیر.\n"
            f"هر کاربر {DEFAULT_FREE_COINS} پیام رایگان دارد.",
            reply_markup=kb_user(uid))
        bot.send_message(uid,"می‌تونی از این دکمه‌ها استفاده کنی:",reply_markup=ikb_user())

# --------- پشتیبانی دوطرفه ---------
@bot.callback_query_handler(func=lambda c: c.data and (c.data.startswith("reply:") or c.data.startswith("close:")))
def cb_support(c):
    if not is_admin(c.from_user.id): return bot.answer_callback_query(c.id,"فقط مدیر.")
    try:
        act,raw=c.data.split(":"); uid=int(raw)
        if act=="reply":
            data["admin_reply_to"]=uid; save_data(data)
            bot.answer_callback_query(c.id,"حالت پاسخ فعال شد.")
            bot.send_message(c.message.chat.id,f"✍️ پیام‌های بعدی برای کاربر {uid} ارسال می‌شود.")
        elif act=="close":
            data["support_open"][str(uid)]=False
            if data.get("admin_reply_to")==uid: data["admin_reply_to"]=None
            save_data(data)
            bot.answer_callback_query(c.id,"بسته شد.")
            bot.send_message(uid,"🔒 گفتگوی پشتیبانی بسته شد.")
    except Exception as e:
        bot.answer_callback_query(c.id,f"خطا: {e}")

@bot.message_handler(func=lambda m:m.chat.type=="private" and is_admin(m.from_user.id) and data.get("admin_reply_to"))
def admin_reply(m):
    target=data.get("admin_reply_to")
    try:
        bot.copy_message(target,m.chat.id,m.message_id)
        bot.reply_to(m,f"✅ ارسال شد برای {target}")
    except Exception as e:
        bot.reply_to(m,f"❌ خطا: {e}")

@bot.message_handler(func=lambda m:m.chat.type=="private" and is_admin(m.from_user.id))
def admin_close(m):
    t=(m.text or "").split()
    if len(t)==2 and t[0]=="پایان":
        uid=t[1]
        data["support_open"][uid]=False
        if data.get("admin_reply_to")==int(uid): data["admin_reply_to"]=None
        save_data(data)
        bot.reply_to(m,f"🔒 گفتگوی {uid} بسته شد.")# --------- ADMIN PANEL ---------
@bot.message_handler(func=lambda m:m.chat.type=="private" and is_admin(m.from_user.id))
def admin_panel(m):
    t=(m.text or "").strip()
    # ارسال همگانی
    if t=="ارسال همگانی 📣":
        data["pending_broadcast"]=True; save_data(data)
        bot.reply_to(m,"پیامت را بفرست تا برای همه ارسال شود. لغو: لغو")
        return
    if data.get("pending_broadcast"):
        if t=="لغو":
            data["pending_broadcast"]=False; save_data(data)
            bot.reply_to(m,"لغو شد."); return
        ok,fail=0,0
        for su in list(data["users"].keys()):
            try: bot.copy_message(int(su),m.chat.id,m.message_id); ok+=1
            except: fail+=1
        for sg in list(data["groups"].keys()):
            try: bot.copy_message(int(sg),m.chat.id,m.message_id); ok+=1
            except: fail+=1
        data["pending_broadcast"]=False; save_data(data)
        bot.reply_to(m,f"📣 ارسال شد: موفق {ok} | ناموفق {fail}")
        return

    # آمار
    if t=="آمار کاربران 📊":
        bot.reply_to(m,
            f"کاربران: {len(data['users'])}\n"
            f"گروه‌ها: {len(data['groups'])}\n"
            f"بن‌شده: {len(data['banned'])}\n"
            f"در سکوت: {len([1 for _,v in data['muted'].items() if v>now_ts()])}")
        return

    if t=="راهنمای سودو 📘":
        bot.reply_to(m,
        "دستورات فارسی سودو:\n"
        "• شارژ [uid] [تعداد]\n"
        "• بن [uid] | حذف بن [uid]\n"
        "• سکوت [uid] [ساعت] | حذف سکوت [uid]\n"
        "• لفت گروه [آیدی] | لفت همه گروه‌ها\n"
        "در گروه: شارژ گروه [روز] | لفت بده")
        return

    # دستورات فارسی
    p=t.split()
    try:
        if p[0]=="شارژ" and len(p)==3:
            uid=int(p[1]); num=int(p[2])
            ensure_user(uid); data["users"][str(uid)]["coins"]+=num; save_data(data)
            bot.reply_to(m,f"✅ به کاربر {uid} {num} سکه اضافه شد.")
            try: bot.send_message(uid,f"💰 سکه شما {num} عدد شارژ شد.")
            except: pass
            return
        if p[0]=="بن" and len(p)==2:
            uid=p[1]
            if uid not in data["banned"]: data["banned"].append(uid); save_data(data)
            bot.reply_to(m,f"🚫 کاربر {uid} بن شد."); return
        if p[0]=="حذف" and len(p)==3 and p[1]=="بن":
            uid=p[2]
            if uid in data["banned"]: data["banned"].remove(uid); save_data(data)
            bot.reply_to(m,f"✅ بن کاربر {uid} برداشته شد."); return
        if p[0]=="سکوت" and len(p)==3:
            uid=p[1]; hrs=float(p[2])
            data["muted"][uid]=now_ts()+int(hrs*3600); save_data(data)
            bot.reply_to(m,f"🤐 کاربر {uid} تا {hrs} ساعت در سکوت است."); return
        if p[0]=="حذف" and len(p)==3 and p[1]=="سکوت":
            uid=p[2]; data["muted"].pop(uid,None); save_data(data)
            bot.reply_to(m,f"✅ سکوت کاربر {uid} برداشته شد."); return
        if p[0]=="لفت" and len(p)==3 and p[1]=="گروه":
            gid=int(p[2])
            try: bot.send_message(gid,"👋 ربات به درخواست ادمین خارج می‌شود."); bot.leave_chat(gid)
            except: pass
            bot.reply_to(m,f"از گروه {gid} خارج شدم."); return
        if t=="لفت همه گروه‌ها":
            c=0
            for g in list(data["groups"].keys()):
                try: bot.leave_chat(int(g)); c+=1
                except: pass
            bot.reply_to(m,f"↩️ از {c} گروه خارج شدم."); return
    except Exception as e:
        bot.reply_to(m,f"❌ خطا: {e}")

# --------- خوش‌آمد به گروه + اطلاع ادمین ---------
@bot.message_handler(content_types=["new_chat_members"])
def added_to_group(m):
    try:
        me=get_bot_id()
        for u in m.new_chat_members:
            if u.id==me:
                gid=str(m.chat.id)
                data["groups"].setdefault(gid,{"expires":0,"active":True}); save_data(data)
                bot.send_message(m.chat.id,
                    "سلام 🌸 من ربات هوشمند نوری‌ام.\n"
                    "برای فعال‌سازی پاسخ در گروه بنویس:\n«شارژ گروه 1»")
                bot.send_message(ADMIN_ID,
                    f"➕ افزوده شدم به گروه:\n{m.chat.title}\nID: <code>{m.chat.id}</code>")
    except: pass

# --------- دستورهای گروهی مدیر ---------
@bot.message_handler(func=lambda m:m.chat.type in ["group","supergroup"] and is_admin(m.from_user.id))
def group_admin_cmds(m):
    txt=(m.text or "").strip()
    p=txt.split()
    if txt=="لفت بده":
        try: bot.leave_chat(m.chat.id)
        except: pass
        return
    if len(p)==3 and p[0]=="شارژ" and p[1]=="گروه":
        days=int(p[2])
        gid=str(m.chat.id)
        data["groups"].setdefault(gid,{"expires":0,"active":True})
        data["groups"][gid]["expires"]=now_ts()+days*86400
        data["groups"][gid]["active"]=True; save_data(data)
        bot.reply_to(m,f"✅ گروه {days} روز شارژ شد.")

# --------- پاسخ هوش مصنوعی متنی ---------
@bot.message_handler(func=lambda m:m.chat.type=="private" and not is_admin(m.from_user.id))
def ai_private(m):
    uid=m.from_user.id; ensure_user(uid,m.from_user.first_name or "")
    if str(uid) in data["banned"]: return
    if str(uid) in data["muted"] and data["muted"][str(uid)]>now_ts(): return
    u=data["users"][str(uid)]
    if m.text=="پشتیبانی ☎️":
        data["support_open"][str(uid)]=True; save_data(data)
        bot.reply_to(m,"به پشتیبانی وصل شدی. بنویس پیام خود را؛ برای خروج: پایان پشتیبانی")
        bot.send_message(ADMIN_ID,f"📩 پیام جدید از {uid}")
        return
    if m.text=="پایان پشتیبانی":
        data["support_open"][str(uid)]=False; save_data(data)
        bot.reply_to(m,"✅ گفتگوی پشتیبانی بسته شد."); return
    if data["support_open"].get(str(uid)):
        bot.copy_message(ADMIN_ID,m.chat.id,m.message_id,reply_markup=ikb_support(uid))
        return
    if not u["active"]:
        bot.reply_to(m,"⏸ گفتگو با هوش غیرفعال است."); return
    if u["coins"]<=0:
        bot.reply_to(m,"💸 سکه تمام شده. با پشتیبانی تماس بگیر."); return
    if m.text:
        q=m.text.strip()
        try:
            r=client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role":"system","content":"You are a helpful AI that answers in Persian."},
                    {"role":"user","content":q}
                ]
            )
            ans=r.choices[0].message.content
            bot.reply_to(m,f"🤖 {ans}")
            u["coins"]-=1; save_data(data)
        except Exception as e:
            bot.reply_to(m,f"❌ خطا در پاسخ: {e}")

# --------- پاسخ تصویری ---------
@bot.message_handler(content_types=["photo"])
def ai_photo(m):
    uid=m.from_user.id; ensure_user(uid)
    if str(uid) in data["banned"]: return
    if str(uid) in data["muted"] and data["muted"][str(uid)]>now_ts(): return
    if m.chat.type=="private":
        u=data["users"][str(uid)]
        if not u["active"]: return bot.reply_to(m,"⏸ غیرفعال است.")
        if u["coins"]<=0: return bot.reply_to(m,"💸 سکه تمام شده.")
        f=bot.get_file(m.photo[-1].file_id)
        url=f"https://api.telegram.org/file/bot{BOT_TOKEN}/{f.file_path}"
        try:
            r=client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role":"user",
                    "content":[
                        {"type":"text","text":"این تصویر را توصیف کن."},
                        {"type":"image_url","image_url":{"url":url}}
                    ]
                }]
            )
            ans=r.choices[0].message.content
            bot.reply_to(m,f"🖼️ تحلیل تصویر:\n{ans}")
            u["coins"]-=1; save_data(data)
        except Exception as e:
            bot.reply_to(m,f"❌ خطا در تصویر: {e}")

# --------- پاسخ هوش مصنوعی در گروه ---------
@bot.message_handler(func=lambda m:m.chat.type in ["group","supergroup"])
def ai_group(m):
    txt=(m.text or "").strip()
    if not txt: return
    want=False
    if txt.startswith("ربات "): want=True
    un=get_bot_username().lower()
    if f"@{un}" in txt.lower(): want=True
    if m.reply_to_message and m.reply_to_message.from_user and m.reply_to_message.from_user.id==get_bot_id():
        want=True
    if not want: return
    gid=str(m.chat.id)
    g=data["groups"].get(gid,{"expires":0,"active":False})
    if g["expires"]<now_ts(): return
    q=txt.replace("ربات ","",1)
    try:
        r=client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role":"system","content":"You are a helpful AI that answers in Persian."},
                {"role":"user","content":q}
            ]
        )
        ans=r.choices[0].message.content
        bot.reply_to(m,f"🤖 {ans}")
    except Exception as e:
        if is_admin(m.from_user.id): bot.reply_to(m,f"❌ خطا: {e}")

# --------- START POLLING ---------
if __name__=="__main__":
    print("Bot is running ...")
    bot.infinity_polling(skip_pending=True, timeout=20)
