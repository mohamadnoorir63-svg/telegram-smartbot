from pyrogram import Client
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import InputStream, AudioPiped

app = Client("music_bot")
vc = PyTgCalls(app)

def join_and_play(chat_id, file_path):
    vc.join_group_call(chat_id, AudioPiped(file_path))
