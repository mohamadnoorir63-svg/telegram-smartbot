import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# 🔑 گرفتن توکن‌ها از محیط هاست (Heroku)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

# 🌍 مدل ترجمه چندزبانه — پشتیبانی از فارسی و انگلیسی
API_URL = "https://api-inference.huggingface.co/models/facebook/m2m100_418M"
HEADERS = {"Authorization": f"Bearer {HUGGINGFACE_TOKEN}"}


# 🔍 تابع تشخیص زبان ساده (فارسی یا انگلیسی)
def detect_language(text: str) -> str:
    if any("آ" <= ch <= "ی" for ch in text):  # وجود حروف فارسی
        return "fa"
    return "en"


# 🧠 تابع ترجمه با مدل HuggingFace
async def translate_text(text: str):
    src_lang = detect_language(text)
    tgt_lang = "en" if src_lang == "fa" else "fa"

    payload = {
        "inputs": text,
        "parameters": {"src_lang": src_lang, "tgt_lang": tgt_lang}
    }

    response = requests.post(API_URL, headers=HEADERS, json=payload)

    if response.status_code == 200:
        data = response.json()
        try:
            return data[0]["translation_text"]
        except Exception:
            return "⚠️ خطا در پردازش پاسخ مدل."
    else:
        return f"⚠️ خطا در ترجمه (کد {response.status_code})"


# 💬 فرمان /translate
async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("📘 لطفاً بنویس:\n/translate [متن شما]")
        return

    text = " ".join(context.args)
    await update.message.reply_text("⏳ در حال ترجمه...")

    translated = await translate_text(text)
    await update.message.reply_text(f"🔤 نتیجه ترجمه:\n{translated}")


# 🚀 شروع ربات
def main():
    if not TELEGRAM_TOKEN:
        print("❌ BOT TOKEN تنظیم نشده است.")
        return

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("translate", translate))
    print("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
