import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# 🔑 ENV Vars on Heroku
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

# 🔁 مدل‌های پایدار برای فارسی↔انگلیسی
MODEL_FA_EN = "Helsinki-NLP/opus-mt-fa-en"
MODEL_EN_FA = "Helsinki-NLP/opus-mt-en-fa"
HF_BASE = "https://api-inference.huggingface.co/models"
HEADERS = {"Authorization": f"Bearer {HUGGINGFACE_TOKEN}"} if HUGGINGFACE_TOKEN else {}

def detect_lang(text: str) -> str:
    # تشخیص بسیار ساده: وجود حروف فارسی
    if any("آ" <= ch <= "ی" for ch in text):
        return "fa"
    return "en"

def call_hf(model: str, text: str):
    url = f"{HF_BASE}/{model}"
    payload = {
        "inputs": text,
        "options": {"wait_for_model": True}  # اگر مدل درحال Warmup بود صبر کند
    }
    try:
        r = requests.post(url, headers=HEADERS, json=payload, timeout=60)
    except Exception as e:
        return None, f"⛔ اتصال به Hugging Face نشد: {e}"
    if r.status_code != 200:
        # پیام خطای شفاف‌تر
        try:
            j = r.json()
            msg = j.get("error") or j.get("message") or str(j)
        except Exception:
            msg = r.text
        return None, f"⚠️ خطا از API (کد {r.status_code}): {msg}"
    # پاسخ استاندارد ترجمه: [{"translation_text": "..."}]
    try:
        data = r.json()
        if isinstance(data, list) and data and "translation_text" in data[0]:
            return data[0]["translation_text"], None
        # برخی سرورها خروجی متفاوت می‌دهند
        if isinstance(data, dict) and "generated_text" in data:
            return data["generated_text"], None
        return None, "⚠️ فرمت پاسخ مدل قابل پردازش نبود."
    except Exception:
        return None, "⚠️ خطا در خواندن پاسخ مدل."

async def translate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not HUGGINGFACE_TOKEN:
        return await update.message.reply_text("❌ HUGGINGFACE_TOKEN تنظیم نشده.")
    if not context.args:
        return await update.message.reply_text("📘 بنویس:\n/translate متن")

    text = " ".join(context.args).strip()
    await update.message.reply_text("⏳ در حال ترجمه...")

    src = detect_lang(text)
    model = MODEL_FA_EN if src == "fa" else MODEL_EN_FA
    result, err = call_hf(model, text)

    if err:
        return await update.message.reply_text(err)
    await update.message.reply_text(f"🔤 نتیجه ترجمه:\n{result}")

async def pinghf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تست سریع سلامت توکن/مدل‌ها"""
    if not HUGGINGFACE_TOKEN:
        return await update.message.reply_text("❌ HUGGINGFACE_TOKEN ست نشده.")
    try:
        r = requests.get(f"{HF_BASE}/{MODEL_EN_FA}", headers=HEADERS, timeout=30)
        await update.message.reply_text(
            "✅ ارتباط با Hugging Face برقرار است." if r.status_code in (200, 404)
            else f"⚠️ پاسخ غیرمنتظره: {r.status_code}"
        )
    except Exception as e:
        await update.message.reply_text(f"⛔ تست ناموفق: {e}")

def main():
    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_TOKEN ست نشده.")
        return
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("translate", translate_cmd))
    app.add_handler(CommandHandler("pinghf", pinghf))
    print("🤖 Bot is running…")
    app.run_polling()

if __name__ == "__main__":
    main()
