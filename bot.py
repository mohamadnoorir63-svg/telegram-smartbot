import os
import telebot
from openai import OpenAI

# گرفتن توکن‌ها از متغیرهای محیطی Heroku
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = telebot.TeleBot(BOT_TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)

# دستور استارت
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام 🌹\nمن ربات هوشمند نوری هستم 🤖\nهرچی بپرسی سعی می‌کنم بهترین جواب رو بدم ✨")

# پاسخ خودکار با ChatGPT
@bot.message_handler(func=lambda message: True)
def chat_with_ai(message):
    try:
        user_message = message.text

        # درخواست از ChatGPT
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "تو یک ربات تلگرام فارسی باهوش و مودب هستی."},
                {"role": "user", "content": user_message}
            ]
        )

        ai_reply = response.choices[0].message.content
        bot.reply_to(message, ai_reply)

    except Exception as e:
        bot.reply_to(message, "یه مشکلی پیش اومد 😅 لطفاً دوباره امتحان کن.")

# اجرای مداوم ربات
bot.infinity_polling()
