import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# گرفتن توکن‌ها از محیط Heroku
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# مدل ترجمه (انگلیسی ⇄ فارسی)
API_URL = "https://api-inference.huggingface.co/models/Helsinki-NLP/opus-mt-en-fa"

headers = {"Authorization": f"Bearer {HUGGINGFACE_TOKEN}"}

async def translate_text(text):
    payload = {"inputs": text}
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        data = response.json()
        return data[0]['translation_text']
    else:
        return f"⚠️ خطا در ترجمه (کد {response.status_code})"

async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ' '.join(context.args)
    await update.message.reply_text("⏳ در حال ترجمه...")
    translation = await translate_text(text)
    await update.message.reply_text(f"🔤 نتیجه ترجمه:\n{translation}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("translate", translate))
    app.run_polling()

if __name__ == "__main__":
    main()
