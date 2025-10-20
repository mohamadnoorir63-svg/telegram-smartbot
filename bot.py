import os
import re
import aiohttp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# ========= توکن‌ها =========
BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

TRANSLATE_MODEL = "Helsinki-NLP/opus-mt-fa-en"

# ========= تابع ترجمه =========
async def translate_text(text: str):
    if not HF_TOKEN:
        return "❌ توکن HuggingFace تنظیم نشده است."

    url = f"https://api-inference.huggingface.co/models/{TRANSLATE_MODEL}"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": text}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status != 200:
                return f"⚠️ خطا در ترجمه (کد {response.status})"
            data = await response.json()
            if isinstance(data, list) and "translation_text" in data[0]:
                return data[0]["translation_text"]
            else:
                return "⚠️ خطا در پاسخ مدل."

# ========= هندلر پیام =========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    match = re.match(r"^(?:ترجمه|translate)\s+(.+)$", text, re.IGNORECASE)
    if not match:
        return
    input_text = match.group(1)
    await update.message.reply_text("⏳ در حال ترجمه...")
    translated = await translate_text(input_text)
    await update.message.reply_text(f"🔤 نتیجه ترجمه:\n{translated}")

# ========= شروع ربات =========
def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN در محیط تنظیم نشده است!")
        return
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
