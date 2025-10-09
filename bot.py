# -*- coding: utf-8 -*-
# Persian Lux AI Panel v26 – ReplyKeyboard Edition
# Designed for Mohammad Noor 👑 (@NOORI_NOOR)

import os, json, random, time, logging, datetime
import telebot
from telebot import types
import openai

# ===== ⚙️ تنظیمات پایه =====
TOKEN = os.environ.get("BOT_TOKEN")
SUDO_ID = int(os.environ.get("SUDO_ID", "0"))
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
openai.api_key = OPENAI_KEY

DATA_FILE = "data.json"
LOG_FILE = "error.log"
logging.basicConfig(filename=LOG_FILE, level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

# ===== 💾 داده =====
def base_data():
    return {
        "users": {},
        "groups": {},
        "banned": [],
        "muted": {},
        "support": {},
        "ai_global": True
    }

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(base_data())
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===== 🧩 ابزار =====
def is_sudo(uid):
    return str(uid) == str(SUDO_ID)

def ai_reply(prompt):
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"user","content":prompt}],
            temperature=0.7)
        return resp.choices[0].message["content"].strip()
    except Exception as e:
        return f"❌ خطا در پاسخ از هوش: {e}"

# ===== 📱 پنل‌ها =====
def user_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🧠 روشن / خاموش", "💎 سکه من")
    kb.row("💬 راهنما", "🛠 پشتیبانی")
    kb.row("➕ افزودن به گروه", "👑 سازنده")
    return kb

def admin_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📊 آمار", "💎 شارژ")
    kb.row("💌 ارسال همگانی", "🤖 کنترل هوش")
    kb.row("🚫 بن‌ها", "🔕 سکوت‌ها")
    kb.row("🔚 لفت بده", "🔙 بازگشت")
    return kb

# ===== 🚀 استارت =====
@bot.message_handler(commands=["start"])
def start_cmd(m):
    d = load_data()
    uid = str(m.from_user.id)
    if uid not in d["users"]:
        d["users"][uid] = {"coins":5,"ai_on":True,"charged_until":None}
        save_data(d)
    bot.send_message(
        m.chat.id,
        "👋 سلام به <b>Persian Lux AI Panel v26</b> خوش اومدی 💎\n\n"
        "من یه دستیار هوشمند و مدیریتی هستم.\n"
        "از دکمه‌های پایین برای شروع استفاده کن 👇",
        reply_markup=user_keyboard()
    )

# ===== 👑 پنل مدیریت سودو =====
@bot.message_handler(commands=["admin"])
def admin_panel(m):
    if is_sudo(m.from_user.id):
        bot.send_message(m.chat.id, "👑 پنل مدیریت باز شد:", reply_markup=admin_keyboard())

# ===== 💬 رفتار دکمه‌ها و دستورات پایه =====
@bot.message_handler(func=lambda m: True)
def all_msgs(m):
    d = load_data()
    uid = str(m.from_user.id)
    txt = (m.text or "").strip()
    d["users"].setdefault(uid, {"coins":5,"ai_on":True})
    user = d["users"][uid]

    # --- دکمه‌های کاربر ---
    if txt == "🧠 روشن / خاموش":
        user["ai_on"] = not user["ai_on"]
        save_data(d)
        bot.reply_to(m, "✅ هوش شخصی " + ("روشن شد" if user["ai_on"] else "خاموش شد"))
        return
    if txt == "💎 سکه من":
        bot.reply_to(m, f"💰 تعداد سکه‌های شما: {user['coins']}")
        return
    if txt == "💬 راهنما":
        bot.reply_to(m,
            "📘 برای استفاده بنویس:\n"
            "«ربات بگو + جمله‌ی خودت»\n"
            "هر پیام ۱ سکه مصرف می‌کند 💎")
        return
    if txt == "🛠 پشتیبانی":
        bot.reply_to(m, "📝 پیام خود را ارسال کن تا به پشتیبانی برسه ✨")
        d["support"][uid] = True
        save_data(d)
        return
    if txt == "➕ افزودن به گروه":
        bot.reply_to(m, f"📎 برای افزودن من به گروه: https://t.me/{bot.get_me().username}?startgroup=true")
        return
    if txt == "👑 سازنده":
        bot.reply_to(m, "👤 سازنده: @NOORI_NOOR 💎")
        return

    # --- دکمه‌های مدیر ---
    if is_sudo(m.from_user.id):
        if txt == "📊 آمار":
            bot.reply_to(m, f"👥 کاربران: {len(d['users'])}\n💬 گروه‌ها: {len(d['groups'])}")
            return
        if txt == "💎 شارژ":
            bot.reply_to(m, "🔋 برای شارژ گروه بنویس:\n<code>شارژ گروه 2</code>\nیا کاربر:\n<code>شارژ کاربر 12345 3</code>")
            return
        if txt == "💌 ارسال همگانی":
            bot.reply_to(m, "📢 پیام خود را ریپلای کن و بنویس «ارسال»")
            return
        if txt == "🤖 کنترل هوش":
            d["ai_global"] = not d["ai_global"]
            save_data(d)
            bot.reply_to(m, f"🤖 هوش کلی {'فعال' if d['ai_global'] else 'غیرفعال'} شد.")
            return
        if txt == "🔚 لفت بده":
            bot.send_message(m.chat.id, "👋 ربات از این گفتگو خارج شد.")
            bot.leave_chat(m.chat.id)
            returnif txt == "🚫 بن‌ها":
            bot.reply_to(m, "❗ برای بن کاربر، روی پیامش ریپلای کن و بنویس «بن»")
            return
        if txt == "🔕 سکوت‌ها":
            bot.reply_to(m, "🔇 برای سکوت کاربر، روی پیامش ریپلای کن و بنویس «سکوت»")
            return
        if txt == "🔙 بازگشت":
            bot.send_message(m.chat.id, "↩ بازگشت به منوی کاربر", reply_markup=user_keyboard())
            return

    # ========== دستورات مدیریتی در گروه ==========
    if m.chat.type in ["group", "supergroup"]:
        gid = str(m.chat.id)
        d["groups"].setdefault(gid, {"charged_until": None, "banned": [], "muted": []})
        ginfo = d["groups"][gid]

        # ✅ فقط سودو می‌تواند بن، سکوت و شارژ کند
        if is_sudo(m.from_user.id):
            if txt.startswith("بن "):
                target = txt.split(" ")[1]
                ginfo["banned"].append(target)
                save_data(d)
                bot.reply_to(m, f"🚫 کاربر {target} بن شد.")
                return
            if txt.startswith("حذف بن "):
                target = txt.split(" ")[2]
                if target in ginfo["banned"]:
                    ginfo["banned"].remove(target)
                    save_data(d)
                    bot.reply_to(m, f"✅ بن {target} حذف شد.")
                return
            if txt.startswith("سکوت "):
                target = txt.split(" ")[1]
                ginfo["muted"].append(target)
                save_data(d)
                bot.reply_to(m, f"🔇 کاربر {target} تا ۵ ساعت ساکت شد.")
                time.sleep(5 * 60 * 60)
                if target in ginfo["muted"]:
                    ginfo["muted"].remove(target)
                    save_data(d)
                return
            if txt.startswith("حذف سکوت "):
                target = txt.split(" ")[2]
                if target in ginfo["muted"]:
                    ginfo["muted"].remove(target)
                    save_data(d)
                    bot.reply_to(m, f"🔊 سکوت {target} برداشته شد.")
                return
            if txt.startswith("شارژ گروه "):
                days = int(txt.split(" ")[2])
                until = (datetime.datetime.now() + datetime.timedelta(days=days)).timestamp()
                ginfo["charged_until"] = until
                save_data(d)
                bot.reply_to(m, f"🔋 گروه برای {days} روز شارژ شد.")
                return
            if txt == "نمایش شارژ گروه":
                if ginfo.get("charged_until") and ginfo["charged_until"] > time.time():
                    remain = int(ginfo["charged_until"] - time.time()) // 86400
                    bot.reply_to(m, f"📅 شارژ گروه تا {remain} روز دیگر فعال است.")
                else:
                    bot.reply_to(m, "⚠️ این گروه شارژ ندارد.")
                return

        # 🚷 اگر کاربر بن شده یا در سکوت است
        if str(m.from_user.id) in ginfo["banned"]:
            bot.delete_message(m.chat.id, m.message_id)
            return
        if str(m.from_user.id) in ginfo["muted"]:
            bot.delete_message(m.chat.id, m.message_id)
            return

        # 💬 پاسخ هوش مصنوعی فقط در صورت شارژ
        if txt.startswith("ربات بگو"):
            if d["ai_global"] and ginfo.get("charged_until") and ginfo["charged_until"] > time.time():
                q = txt.replace("ربات بگو", "").strip()
                bot.send_chat_action(m.chat.id, "typing")
                ans = ai_reply(q)
                bot.reply_to(m, ans)
            else:
                bot.reply_to(m, "⚠️ گروه شارژ ندارد.\nفقط سودو می‌تواند شارژ کند.")
        return

    # ========== پیام خصوصی ==========
    if m.chat.type == "private":
        user = d["users"][uid]
        if uid in d.get("banned", []):
            return
        if uid in d.get("support", {}):
            # ارسال پیام کاربر به سودو
            bot.forward_message(SUDO_ID, m.chat.id, m.message_id)
            bot.send_message(m.chat.id, "✅ پیام شما به پشتیبانی ارسال شد.")
            d["support"].pop(uid, None)
            save_data(d)
            return

        # پاسخ پشتیبانی سودو
        if is_sudo(m.from_user.id) and m.reply_to_message and m.reply_to_message.forward_from:
            try:
                user_id = m.reply_to_message.forward_from.id
                bot.send_message(user_id, f"📬 پاسخ پشتیبانی:\n{m.text}")
                bot.send_message(m.chat.id, "✅ پاسخ ارسال شد.")
            except Exception as e:
                bot.reply_to(m, f"❌ خطا در ارسال: {e}")
            return

        # پاسخ هوش مصنوعی در پیوی
        if txt.startswith("ربات بگو"):
            if not d["ai_global"]:
                bot.reply_to(m, "🤖 هوش کلی غیرفعال است.")
                return
            if not user["ai_on"]:
                bot.reply_to(m, "🧠 هوش شخصی شما خاموش است. روی «روشن / خاموش» بزن.")
                return
            if user["coins"] <= 0:
                bot.reply_to(m, "⚠️ موجودی شما تمام شده است! برای شارژ به پشتیبانی پیام دهید 💎")
                return

            q = txt.replace("ربات بگو", "").strip()
            bot.send_chat_action(m.chat.id, "typing")
            ans = ai_reply(q)
            user["coins"] -= 1
            save_data(d)
            bot.reply_to(m, ans)
            return
        else:
            bot.reply_to(m, "برای استفاده بنویس:\n<code>ربات بگو + جمله مورد نظر</code>")

print("🤖 Persian Lux AI Panel v26 (ReplyKeyboard Edition) اجرا شد 💎")
while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        logging.error(f"Crash: {e}")
        time.sleep(5)
