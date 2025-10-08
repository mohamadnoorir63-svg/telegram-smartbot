import os
import telebot
import logging
from openai import OpenAI

# فعال‌سازی لاگ‌ها برای دیدن خطاها در Heroku
logging.basicConfig(level=logging.INFO)

# گرفتن متغیرها از محیط
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
SUDO_ID = os.environ.get("SUDO_ID")

bot = telebot.TeleBot(BOT_TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)

# پاسخ‌های آماده ساده
simple_responses = {
    "سلام": ["سلام! 🌹", "درود بر تو 👋", "سلام رفیق! 😄"],
    "خوبی": ["مرسی، تو خوبی؟ 😁", "عالی‌ام، امیدوارم تو هم همینطور باشی 🌸"],
    "خداحافظ": ["خداحافظ 👋", "فعلاً 🌹", "بدرود دوست من! 🌼"]
}

# تابع برای پرسش از ChatGPT
def ask_gpt(message_text):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "تو یک دستیار فارسی هوشمند هستی."},
            {"role": "user", "content": message_text}
        ],
        temperature=0.7,
        max_tokens=200
    )
    return response.choices[0].message.content.strip()


# هندلر پیام‌ها
@bot.message_handler(func=lambda m: True)
def handle_message(m):
    text = m.text.strip()

    # مرحله ۱: اگر پیام در پاسخ‌های ساده بود
    for key, replies in simple_responses.items():
        if key in text:
            bot.reply_to(m, random.choice(replies))
            return

    # مرحله ۲: سعی کن از ChatGPT جواب بگیری
    try:
        reply = ask_gpt(text)
        bot.reply_to(m, reply)
    except Exception as e:
        logging.exception(f"OpenAI error: {e}")
        bot.reply_to(m, "یه مشکلی پیش اومد 😅 لطفاً دوباره امتحان کن.")


# دستور تست اتصال ChatGPT
@bot.message_handler(commands=['ai_test'])
def ai_test(m):
    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":"فقط بنویس OK"}],
            temperature=0.2,
            max_tokens=5
        )
        txt = r.choices[0].message.content.strip()
        bot.reply_to(m, f"✅ نتیجه تست: {txt}")
    except Exception as e:
        logging.exception(f"/ai_test error: {e}")
        bot.reply_to(m, "❌ تست ناموفق شد، لاگ‌ها رو در هروکو چک کن.")

import random
bot.polling(none_stop=True)
