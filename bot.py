# -*- coding: utf-8 -*-
import os, json, time, datetime
from telebot import TeleBot, types
from openai import OpenAI

# ----------- تنظیمات محیط ----------
BOT_TOKEN        = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
ADMIN_ID         = int(os.getenv("ADMIN_ID") or "0")
ADMIN_USERNAME   = os.getenv("ADMIN_USERNAME") or "@NOORI_NOOR"
BOT_NAME_FARSI   = "ربات هوشمند نوری 🤖"

if not BOT_TOKEN: raise SystemExit("BOT_TOKEN تعریف نشده است.")
if not ADMIN_ID:  raise SystemExit("ADMIN_ID (عددی) تعریف نشده است.")
if not OPENAI_API_KEY: raise SystemExit("OPENAI_API_KEY تعریف نشده است.")

# ----------- شروع -----------
bot    = TeleBot(BOT_TOKEN, parse_mode="HTML")
client = OpenAI(api_key=OPENAI_API_KEY)

DATA_FILE = "data.json"
DEFAULT_FREE_COINS = 5

def now_ts(): return int(time.time())

def load_data():
    if not os.path.exists(DATA_FILE):
        data = {"users": {}, "banned": [], "muted": {}, "groups": {},
                "support_open": {}, "admin_reply_to": None, "pending_broadcast": False}
        save_data(data)
        return data
    with open(DATA_FILE, "r", encoding="utf-8") as f: d = json.load(f)
    for k in ["users","banned","muted","groups","support_open","admin_reply_to","pending_broadcast"]:
        d.setdefault(k, {} if k in ["users","muted","groups","support_open"] else [])
    return d

def save_data(d): json.dump(d, open(DATA_FILE,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
data = load_data()

def is_admin(uid): return int(uid)==int(ADMIN_ID)
def ensure_user(uid, name=""):
    suid=str(uid)
    if suid not in data["users"]:
        data["users"][suid]={"coins":DEFAULT_FREE_COINS,"active":True,"name":name,"last_prompt":""}
        save_data(data)

# ---------- کیبورد ----------
def kb_user(uid):
    kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("راهنما 💡","شارژ مجدد 🟩")
    kb.row("پشتیبانی ☎️","سازنده 👤")
    kb.row("افزودن به گروه ➕")
    kb.row("روشن / خاموش 🧠")
    return kb

def kb_admin():
    kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("آمار کاربران 📊","شارژ کاربر 💰")
    kb.row("سکوت کاربر 🤐","بن کاربر 🚫")
    kb.row("لیست بن‌ها 🚫","لیست سکوت‌ها 🤫")
    kb.row("ارسال همگانی 📣","لفت بده ↩️")
    kb.row("بازگشت BACK")
    return kb

def ikb_support(uid):
    ik=types.InlineKeyboardMarkup()
    ik.add(types.InlineKeyboardButton("پاسخ ✉️",callback_data=f"reply:{uid}"),
           types.InlineKeyboardButton("بستن ❌",callback_data=f"close:{uid}"))
    return ik

# ---------- شروع ----------
@bot.message_handler(commands=["start"])
def start_cmd(m):
    uid=m.from_user.id
    ensure_user(uid, f"{m.from_user.first_name or ''} {m.from_user.last_name or ''}".strip())
    if is_admin(uid):
        return bot.reply_to(m,"👑 سلام رئیس!",reply_markup=kb_admin())
    text=(f"سلام 👋 به <b>{BOT_NAME_FARSI}</b> خوش اومدی!\n\n"
          "اینجا می‌تونی با هوش مصنوعی واقعی چت کنی یا عکس بفرستی تا تحلیل کنه 🤖\n\n"
          f"📊 {DEFAULT_FREE_COINS} پیام رایگان داری.\n"
          "برای شارژ بیشتر، از پشتیبانی استفاده کن.\n\n"
          "📸 عکس بفرست تا توصیف و تحلیلش رو بنویسم.\n\n"
          "📱 اینستاگرام من:\n"
          "<a href='https://www.instagram.com/pesar_rostayi'>@pesar_rostayi</a>\n"
          "اگر منو دنبال کنی ۵ سکه هدیه می‌گیری 🌟")
    bot.reply_to(m,text,reply_markup=kb_user(uid))

# ---------- مدیریت ----------
@bot.message_handler(func=lambda m:m.chat.type=="private" and is_admin(m.from_user.id))
def admin_private(m):
    txt=(m.text or "").strip()
    if txt=="ارسال همگانی 📣":
        data["pending_broadcast"]=True;save_data(data)
        return bot.reply_to(m,"✍️ پیام خود را بفرست.")
    if data.get("pending_broadcast"):
        if txt=="بازگشت BACK":
            data["pending_broadcast"]=False;save_data(data)
            return bot.reply_to(m,"لغو شد.")
        ok,fail=0,0
        for suid in list(data["users"].keys()):
            try:bot.copy_message(int(suid),m.chat.id,m.message_id);ok+=1
            except:fail+=1
        data["pending_broadcast"]=False;save_data(data)
        return bot.reply_to(m,f"📣 ارسال شد ✅ {ok} | ❌ {fail}")

    if txt=="آمار کاربران 📊":
        bot.reply_to(m,f"👥 {len(data['users'])} کاربر\n🚫 {len(data['banned'])} بن\n🤐 {len(data['muted'])} سکوت")
        return

    parts=txt.split()
    try:
        if parts[0]=="شارژ" and len(parts)==3:
            uid,count=int(parts[1]),int(parts[2]);ensure_user(uid)
            data["users"][str(uid)]["coins"]+=count;save_data(data)
            bot.reply_to(m,f"✅ {count} سکه به {uid} اضافه شد.")
            return
        if parts[0]=="بن" and len(parts)==2:
            data["banned"].append(str(parts[1]));save_data(data)
            return bot.reply_to(m,f"🚫 کاربر {parts[1]} بن شد.")
        if parts[0]=="سکوت" and len(parts)==3:
            uid,h=int(parts[1]),float(parts[2])
            data["muted"][str(uid)]=now_ts()+int(h*3600);save_data(data)
            return bot.reply_to(m,f"🤐 {uid} تا {h} ساعت در سکوت است.")
        if parts[0]=="لیست" and parts[1]=="بن‌ها":
            return bot.reply_to(m,"📜 "+",".join(data["banned"]) if data["banned"] else "لیست خالی است.")
        if parts[0]=="لیست" and "سکوت" in parts[1]:
            alive=[u for u,t in data["muted"].items() if t>now_ts()]
            return bot.reply_to(m,"📜 "+",".join(alive) if alive else "هیچ کاربری در سکوت نیست.")
    except: pass

# ---------- پشتیبانی ----------
@bot.callback_query_handler(func=lambda c:c.data.startswith("reply:") or c.data.startswith("close:"))
def cb_support(c):
    if not is_admin(c.from_user.id): return
    act,uid=c.data.split(":")
    uid=int(uid)
    if act=="reply":
        data["admin_reply_to"]=uid;save_data(data)
        bot.send_message(c.message.chat.id,f"✍️ پاسخ به {uid} فعال شد.")
    else:
        data["support_open"][str(uid)]=False;save_data(data)
        bot.send_message(c.message.chat.id,f"🔒 گفتگو بسته شد.")

@bot.message_handler(func=lambda m:m.chat.type=="private" and is_admin(m.from_user.id) and data.get("admin_reply_to"))
def admin_reply(m):
    target=data["admin_reply_to"]
    try:bot.copy_message(target,m.chat.id,m.message_id)
    except:bot.reply_to(m,"❌ ارسال نشد.")
    
# ---------- پاسخ هوش مصنوعی ----------
def ask_ai(uid,text):
    data["users"][str(uid)]["last_prompt"]=text;save_data(data)
    resp=client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system","content":"You are a Persian assistant."},
            {"role":"user","content":text}
        ])
    return resp.choices[0].message.content

@bot.message_handler(content_types=["photo","text"])
def handle_message(m):
    uid=m.from_user.id;ensure_user(uid)
    if str(uid) in data["banned"]:return
    if str(uid) in data["muted"] and data["muted"][str(uid)]>now_ts():return

    cu=data["users"][str(uid)]
    if cu.get("coins",0)<=0: return bot.reply_to(m,"💸 سکه شما تمام شده است.")
    if not cu.get("active",True): return bot.reply_to(m,"⏸ حالت گفتگو خاموش است.")

    # ادامه تحلیل
    if m.content_type=="text" and m.text.startswith("ادامه تحلیل"):
        new_prompt=cu.get("last_prompt","")+"\n\n"+m.text.replace("ادامه تحلیل","")
        try:
            ans=ask_ai(uid,new_prompt)
            bot.reply_to(m,"🧩 "+ans)
            cu["coins"]-=1;save_data(data)
        except Exception as e: bot.reply_to(m,f"❌ خطا:\n{e}")
        return

    # پیام متنی
    if m.content_type=="text":
        try:
            ans=ask_ai(uid,m.text)
            bot.reply_to(m,"🤖 "+ans)
            cu["coins"]-=1;save_data(data)
        except Exception as e: bot.reply_to(m,f"❌ خطا:\n{e}")
        return

    # تصویر → GPT-4o Vision
    if m.content_type=="photo":
        try:
            f=bot.get_file(m.photo[-1].file_id)
            url=f"https://api.telegram.org/file/bot{BOT_TOKEN}/{f.file_path}"
            resp=client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"user","content":[
                    {"type":"text","text":"این تصویر را توضیح بده."},
                    {"type":"image_url","image_url":{"url":url}}]}])
            bot.reply_to(m,"🖼️ "+resp.choices[0].message.content)
            cu["coins"]-=1;save_data(data)
        except Exception as e: bot.reply_to(m,f"❌ خطا در تحلیل تصویر:\n{e}")

# ---------- گروه ----------
@bot.message_handler(func=lambda m:m.chat.type in ["group","supergroup"])
def group_ai(m):
    text=(m.text or "").strip()
    if not text:return
    gid=str(m.chat.id)
    g=data["groups"].get(gid,{"expires":0,"active":True})
    if g.get("expires",0)<now_ts():return
    if text.startswith("ربات ") or (m.reply_to_message and m.reply_to_message.from_user.id==bot.get_me().id):
        try:
            ans=ask_ai(m.from_user.id,text.replace("ربات ",""))
            bot.reply_to(m,"🤖 "+ans)
        except Exception as e: bot.reply_to(m,f"❌ {e}")

# ---------- اجرا ----------
if __name__=="__main__":
    print("🤖 Bot is running...")
    bot.infinity_polling(skip_pending=True, timeout=20)
