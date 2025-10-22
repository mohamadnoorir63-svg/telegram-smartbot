import os
from pyrogram import Client, filters

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# ذخیره وضعیت منتظر لینک بودن
waiting_for_link = {}

@app.on_message(filters.me & filters.text & filters.regex(r"^بیا$"))
async def ask_for_link(client, message):
    """وقتی گفتی بیا، ازت لینک می‌خواد"""
    waiting_for_link[message.chat.id] = True
    await message.reply_text("📎 لینک گروه رو بفرست تا واردش بشم!")

@app.on_message(filters.me & filters.text)
async def join_when_link_sent(client, message):
    """وقتی لینک فرستادی، بره تو گروه"""
    if waiting_for_link.get(message.chat.id):
        text = message.text.strip()
        if text.startswith("https://t.me/") or text.startswith("@"):
            try:
                link = text.replace("https://t.me/", "").replace("@", "")
                await client.join_chat(link)
                await message.reply_text(f"✅ با موفقیت وارد گروه [{link}](https://t.me/{link}) شدم!")
            except Exception as e:
                await message.reply_text(f"❌ نتونستم وارد شم:\n`{e}`")
            waiting_for_link[message.chat.id] = False
        else:
            await message.reply_text("❗ لطفاً لینک معتبر بفرست (مثلاً https://t.me/examplegroup)")

@app.on_message(filters.me & filters.regex(r"^برو بیرون$"))
async def leave_group(client, message):
    try:
        await client.leave_chat(message.chat.id)
    except Exception as e:
        await message.reply_text(f"خطا هنگام خروج: {e}")

print("✅ Userbot started and waiting for your commands...")
app.run()
