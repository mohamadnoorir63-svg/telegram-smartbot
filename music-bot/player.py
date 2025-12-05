# player.py
import os
import asyncio
import shlex
import uuid
from yt_dlp import YoutubeDL
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import AudioPiped
from pyrogram import Client
from collections import defaultdict
from asyncio import Lock
import subprocess

ydl_opts = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'outtmpl': 'downloads/%(id)s.%(ext)s',
    'restrictfilenames': True,
}

os.makedirs("downloads", exist_ok=True)

class Track:
    def __init__(self, title, path, duration=None, requester=None):
        self.title = title
        self.path = path
        self.duration = duration
        self.requester = requester

class MusicPlayer:
    def __init__(self, pytgcalls: PyTgCalls, user_client: Client):
        self.pytgcalls = pytgcalls
        self.user = user_client
        self.queues = defaultdict(list)    # chat_id -> [Track, ...]
        self.locks = defaultdict(Lock)    # chat_id -> Lock
        # event handlers
        self.pytgcalls.on_stream_end()(self._on_stream_end)

    async def join(self, chat_id):
        # join vc muted (no mic)
        # For group calls, we can just create a stream when playing
        # But to ensure user is present, we can attempt to join with silent audio
        return True

    async def leave(self, chat_id):
        try:
            await self.pytgcalls.leave_group_call(chat_id)
        except Exception:
            pass
        self.queues.pop(chat_id, None)

    async def add_to_queue(self, chat_id, query, requester=None):
        async with self.locks[chat_id]:
            track = await self._download_track(query)
            if not track:
                return False
            self.queues[chat_id].append(track)
            # if nothing is playing -> start
            if len(self.queues[chat_id]) == 1:
                await self._start_play(chat_id)
            return True

    async def _download_track(self, query):
        # if query looks like url - yt-dlp will handle; otherwise it's a search
        opts = ydl_opts.copy()
        # allow yt-dlp to search with "ytsearch1:" prefix if not url
        if not query.startswith("http"):
            query = f"ytsearch1:{query}"
        try:
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(query, download=True)
                # when using ytsearch1, info['entries'][0]
                if 'entries' in info:
                    info = info['entries'][0]
                filename = ydl.prepare_filename(info)
                title = info.get("title", "Unknown")
                return Track(title=title, path=filename, duration=info.get("duration"), requester=None)
        except Exception as e:
            print("ydl error:", e)
            return None

    async def _start_play(self, chat_id):
        if not self.queues[chat_id]:
            return
        track = self.queues[chat_id][0]
        # use ffmpeg via AudioPiped (pytgcalls will spawn ffmpeg)
        source = track.path
        try:
            await self.pytgcalls.join_group_call(
                chat_id,
                AudioPiped(source),
            )
        except Exception as e:
            print("join/play error:", e)

    async def pause(self, chat_id):
        try:
            await self.pytgcalls.pause_stream(chat_id)
        except Exception:
            pass

    async def resume(self, chat_id):
        try:
            await self.pytgcalls.resume_stream(chat_id)
        except Exception:
            pass

    async def skip(self, chat_id):
        async with self.locks[chat_id]:
            if self.queues[chat_id]:
                # remove current
                current = self.queues[chat_id].pop(0)
                # try to stop and start next
                try:
                    await self.pytgcalls.leave_group_call(chat_id)
                except Exception:
                    pass
                if self.queues[chat_id]:
                    await self._start_play(chat_id)

    async def stop(self, chat_id):
        async with self.locks[chat_id]:
            self.queues[chat_id].clear()
            try:
                await self.pytgcalls.leave_group_call(chat_id)
            except Exception:
                pass

    async def show_queue(self, chat_id):
        q = self.queues.get(chat_id, [])
        if not q:
            return None
        lines = []
        for i, t in enumerate(q, start=1):
            lines.append(f"{i}. {t.title}")
        return "\n".join(lines)

    async def _on_stream_end(self, chat_id):
        # called when stream ends — start next if any
        async with self.locks[chat_id]:
            if self.queues[chat_id]:
                # remove finished track
                try:
                    self.queues[chat_id].pop(0)
                except Exception:
                    pass
            if self.queues[chat_id]:
                await self._start_play(chat_id)
            else:
                # leave vc when queue empty
                try:
                    await self.pytgcalls.leave_group_call(chat_id)
                except Exception:
                    pass
