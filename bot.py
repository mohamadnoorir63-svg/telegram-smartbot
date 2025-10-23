import os
import re
import difflib
from pyrogram import Client, filters

# Optional libs
try:
    from googleapiclient.discovery import build as youtube_build
except Exception:
    youtube_build = None

try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
except Exception:
    spotipy = None

# ---------- CONFIG ----------
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

YT_API_KEY = os.getenv("YT_API_KEY")  # required for YouTube search
SPOTIFY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")  # optional
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")  # optional

MUSIC_DIR = os.getenv("MUSIC_DIR", "music")  # fallback local dir (you must upload files)

app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# ---------- helpers ----------
def list_local_tracks():
    if not os.path.isdir(MUSIC_DIR):
        return []
    exts = (".mp3", ".m4a", ".ogg", ".wav", ".flac", ".aac")
    files = [f for f in os.listdir(MUSIC_DIR) if f.lower().endswith(exts)]
    files.sort()
    return files

def find_best_local(query, tracks):
    if not tracks:
        return None
    names = [os.path.splitext(t)[0] for t in tracks]
    # direct number
    if query.isdigit():
        idx = int(query) - 1
        if 0 <= idx < len(tracks):
            return tracks[idx]
    # direct match
    lowered = [n.lower() for n in names]
    if query.lower() in lowered:
        return tracks[lowered.index(query.lower())]
    # close match
    matches = difflib.get_close_matches(query.lower(), names, n=1, cutoff=0.4)
    if matches:
        return tracks[names.index(matches[0])]
    for i, n in enumerate(names):
        if query.lower() in n:
            return tracks[i]
    return None

def youtube_search(query, max_results=3):
    """Return list of (title, video_id, url) using YouTube Data API (no downloading)."""
    if youtube_build is None or not YT_API_KEY:
        return []
    try:
        yt = youtube_build("youtube", "v3", developerKey=YT_API_KEY)
        req = yt.search().list(q=query, part="snippet", type="video", maxResults=max_results)
        res = req.execute()
        items = []
        for it in res.get("items", []):
            vid = it["id"]["videoId"]
            title = it["snippet"]["title"]
            url = f"https://www.youtube.com/watch?v={vid}"
            items.append((title, vid, url))
        return items
    except Exception:
        return []

def spotify_search_preview(query):
    """Return (track_name, artist, preview_url, spotify_url) if available."""
    if spotipy is None or not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        return None
    try:
        client_creds = SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)
        sp = spotipy.Spotify(auth_manager=client_creds)
        r = sp.search(q=query, type="track", limit=1)
        items = r.get("tracks", {}).get("items", [])
        if not items:
            return None
        t = items[0]
        name = t["name"]
        artists = ", ".join([a["name"] for a in t["artists"]])
        preview = t.get("preview_url")  # might be None
        spotify_url = t.get("external_urls", {}).get("spotify")
        return (name, artists, preview, spotify_url)
    except Exception:
        return None

# ---------- command: /music <query> ----------
@app.on_message(filters.command("music", prefixes="/") & filters.private)
async def cmd_music(client, message):
    """
    Usage:
      /music <query>
    Behavior:
      1) Try YouTube search and send top result URL (no download).
      2) If Spotify credentials configured, try to find preview_url and send it.
      3) If none, try to find a local file in MUSIC_DIR and send it (you must own the files).
    """
    args = message.text.split(maxsplit=1)
    if len(args) == 1:
        await message.reply_text("Usage: /music <query>\nمثال: /music Mehrdad Jam")
        return

    query = args[1].strip()
    await message.send_chat_action("typing")

    # 1) YouTube (send link)
    yt_results = youtube_search(query, max_results=3)
    if yt_results:
        title, vid, url = yt_results[0]
        text = f"🔎 YouTube: {title}\n{url}"
        await message.reply_text(text)
        return

    # 2) Spotify preview (if available)
    sp = spotify_search_preview(query)
    if sp:
        name, artists, preview_url, spotify_url = sp
        txt = f"🎧 Spotify: {name} — {artists}\n"
        if preview_url:
            txt += f"Preview (30s): {preview_url}\n"
        if spotify_url:
            txt += f"Full: {spotify_url}"
        await message.reply_text(txt)
        return

    # 3) Local fallback
    local_tracks = list_local_tracks()
    track = find_best_local(query, local_tracks)
    if track:
        path = os.path.join(MUSIC_DIR, track)
        try:
            await message.reply_audio(audio=path, caption=os.path.splitext(track)[0])
        except Exception as e:
            await message.reply_text(f"خطا در ارسال فایل محلی: {e}")
        return

    # nothing found
    await message.reply_text("نتیجه‌ای پیدا نشد. یا از /music لیست فایل‌های محلی را بررسی کن و یا فایل‌ها را در پوشهٔ music/ بذار.")

# optional: list local tracks with /musiclist
@app.on_message(filters.command("musiclist", prefixes="/") & filters.private)
async def cmd_musiclist(client, message):
    tracks = list_local_tracks()
    if not tracks:
        await message.reply_text("پوشهٔ music/ خالی است.")
        return
    lines = [f"{i+1}. {os.path.splitext(t)[0]}" for i, t in enumerate(tracks[:50])]
    await message.reply_text("🎶 آهنگ‌های محلی:\n\n" + "\n".join(lines))

# start
print("Music helper bot ready (sends YouTube links, Spotify previews, or local files).")
app.run()
