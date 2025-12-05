# bot.py
import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pytgcalls import PyTgCalls, idle
from player import MusicPlayer
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH")
SESSION = os.environ.get("SESSION")  # optional: if you prefer userbot sessionstring

# We'll run two clients:
# - bot_client: bot (handles commands)
# - user_client: user account (joins voice chats and streams)
# You can also use the bot client for some operations, but voice requires a user account.

# If you have SESSION (string session) use it for user_client; otherwise create a new session file "user_session"
user_session_name = "user_session" if not SESSION else SESSION

# create bot client
bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

# create user client (Pyrogram)
if SESSION:
    user = Client(
        name="user",
        session_string=SESSION,
        api_id=API_ID,
        api_hash=API_HASH,
    )
else:
    user = Client(
        "user",
        api_id=API_ID,
        api_hash=API_HASH,
    )

# PyTgCalls attached to user client
pytgcalls = PyTgCalls(user)

# music player (manages queue per chat)
player = MusicPlayer(pytgcalls, user)

@bot.on_message(filters.command("start"))
async def start(_, m: Message):
    await m.reply_text("سلام! من ربات موزیک‌پلیر هستم. دستورات: /join, /play <url|query>, /pause, /resume, /skip, /stop, /queue")

@bot.on_message(filters.command("join") & filters.group)
async def join(_, m: Message):
    chat_id = m.chat.id
    await m.reply_text("درحال تلاش برای اتصال به ویس...")
    await player.join(chat_id)
    await m.reply_text("وصل شدم ✅")

@bot.on_message(filters.command("leave") & filters.group)
async def leave(_, m: Message):
    chat_id = m.chat.id
    await player.leave(chat_id)
    await m.reply_text("از ویس خارج شدم ✅")

@bot.on_message(filters.command("play") & filters.group)
async def play(_, m: Message):
    chat_id = m.chat.id
    if len(m.command) < 2:
        return await m.reply_text("فرمت: /play <لینک یا عبارت جستجو>")
    query = m.text.split(None, 1)[1]
    msg = await m.reply_text(f"درحال افزودن به صف: `{query}`")
    await player.add_to_queue(chat_id, query, requester=m.from_user.mention)
    await msg.edit_text("افزوده شد ✅")

@bot.on_message(filters.command("pause") & filters.group)
async def pause(_, m: Message):
    chat_id = m.chat.id
    await player.pause(chat_id)
    await m.reply_text("توقف شد ⏸️")

@bot.on_message(filters.command("resume") & filters.group)
async def resume(_, m: Message):
    chat_id = m.chat.id
    await player.resume(chat_id)
    await m.reply_text("ادامه یافت ▶️")

@bot.on_message(filters.command("skip") & filters.group)
async def skip(_, m: Message):
    chat_id = m.chat.id
    await player.skip(chat_id)
    await m.reply_text("ترک شد — درحال پخش آهنگ بعدی ⏭️")

@bot.on_message(filters.command("stop") & filters.group)
async def stop(_, m: Message):
    chat_id = m.chat.id
    await player.stop(chat_id)
    await m.reply_text("توقف کامل و خالی شدن صف ⏹️")

@bot.on_message(filters.command("queue") & filters.group)
async def queue_cmd(_, m: Message):
    chat_id = m.chat.id
    qtext = await player.show_queue(chat_id)
    await m.reply_text(qtext or "صف خالی است.")

async def main():
    await user.start()
    await pytgcalls.start()
    await bot.start()
    print("Bot & user client started.")
    # keep running
    await idle()
    await bot.stop()
    await pytgcalls.stop()
    await user.stop()

if __name__ == "__main__":
    asyncio.run(main())
