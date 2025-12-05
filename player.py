import asyncio
from yt_dlp import YoutubeDL
from pydub import AudioSegment
from pydub.playback import play as play_audio
import aiofiles
import os

class Player:
    def __init__(self, client):
        self.client = client
        self.tasks = {}

    async def play(self, chat_id, query):
        # دانلود موزیک از یوتیوب
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": f"{chat_id}.mp3",
            "quiet": True,
            "no_warnings": True
        }
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.download_audio, query, ydl_opts)

        # پخش موزیک
        await loop.run_in_executor(None, self.play_audio_file, f"{chat_id}.mp3")

    def download_audio(self, query, ydl_opts):
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([query])

    def play_audio_file(self, filename):
        audio = AudioSegment.from_file(filename)
        play_audio(audio)
        os.remove(filename)

    async def stop(self, chat_id):
        # در این نسخه ساده stop فقط حذف فایل و task است
        filename = f"{chat_id}.mp3"
        if os.path.exists(filename):
            os.remove(filename)
