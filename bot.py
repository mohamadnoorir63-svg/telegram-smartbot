import os, re, time, asyncio
from pyrogram import Client, filters

# ====== ⚙️ Grundeinstellungen ======
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

try:
    SUDO_ID = int(os.getenv("SUDO_ID"))
except:
    SUDO_ID = 7089376754  # Standard-ID

# ====== 📁 Datei-Pfade ======
USERS_FILE = "users.txt"
GREETED_FILE = "greeted.txt"
GROUPS_FILE = "groups.txt"

known_users, greeted_users, joined_groups = set(), set(), set()
message_count = 0
left_groups_counter = 0
start_time = time.time()
waiting_for_links = {}

# ====== Hilfsfunktionen ======
def load_lines(path):
    if not os.path.exists(path): return []
    with open(path, "r", encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()]

for l in load_lines(USERS_FILE):
    try: known_users.add(l.split("|")[0].strip())
    except: pass
for l in load_lines(GREETED_FILE): greeted_users.add(l)
for l in load_lines(GROUPS_FILE): joined_groups.add(l)

# ====== Client ======
app = Client("SaraUserbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# ====== Zeitformat ======
def uptime_text(seconds):
    s = int(seconds)
    m = s // 60
    h = m // 60
    m = m % 60
    if h: return f"{h} Stunden, {m} Minuten"
    if m: return f"{m} Minuten"
    return f"{s} Sekunden"

# ====== Sudo-Erkennung ======
def is_sudo(msg):
    return (
        getattr(msg, "outgoing", False)
        or (msg.from_user and msg.from_user.id == SUDO_ID)
    )

# ====== Gruppenzählung ======
async def count_groups(client):
    count = 0
    async for d in client.get_dialogs():
        if d.chat and d.chat.type in ("group", "supergroup"):
            count += 1
    return count

# ====== Private Nachrichten (Speichern & Begrüßung) ======
@app.on_message(filters.private & filters.text)
async def private_message(client, message):
    global message_count
    message_count += 1
    user = message.from_user
    if not user: return

    uid = str(user.id)
    name = user.first_name or "Unbekannt"
    username = f"@{user.username}" if user.username else "—"

    # Speichern des Benutzers
    if uid not in known_users:
        known_users.add(uid)
        with open(USERS_FILE, "a", encoding="utf-8") as f:
            f.write(f"{uid} | {name} | {username}\n")
        print(f"🆕 Neuer Benutzer: {name} ({uid})")

    # Persischer Gruß nur einmal
    text = message.text.strip().lower()
    if text in ["سلام", "salam", "hi", "hello", "hallo"] and uid not in greeted_users:
        greeted_users.add(uid)
        with open(GREETED_FILE, "a", encoding="utf-8") as f:
            f.write(uid + "\n")
        await message.reply_text("سلام 🌹 خوش اومدی 💬")

# ====== Gruppen bereinigen ======
async def clean_bad_groups(client, message=None):
    global left_groups_counter
    left = 0
    checked = 0
    async for dialog in client.get_dialogs():
        chat = dialog.chat
        if chat and chat.type in ("group", "supergroup"):
            checked += 1
            try:
                await client.get_chat_members_count(chat.id)
            except Exception:
                try:
                    await client.leave_chat(chat.id)
                    left += 1
                    left_groups_counter += 1
                except:
                    pass

    msg = f"🧹 Überprüft: {checked}\n🚪 Verlassen: {left}"
    if message:
        await message.reply_text(msg)
    else:
        await client.send_message(SUDO_ID, msg)

# ====== Beitritt zu Gruppen ======
async def join_links(client, message, links):
    joined = 0
    failed = 0
    results = []

    for link in links:
        try:
            link = link.strip()
            if link.startswith("@"):
                link = link[1:]
            await client.join_chat(link)
            joined += 1
            joined_groups.add(link)
            with open(GROUPS_FILE, "a", encoding="utf-8") as f:
                f.write(link + "\n")
            results.append(f"✅ Beigetreten: {link}")
        except Exception as e:
            failed += 1
            results.append(f"❌ {link} → {e}")

    report = "\n".join(results[-30:]) or "—"
    await message.reply_text(f"📋 Ergebnis:\n{report}\n\n✅ Erfolgreich: {joined} | ❌ Fehler: {failed}")

# ====== Befehle (Deutsch) ======
@app.on_message(filters.text)
async def sara_commands(client, message):
    if not is_sudo(message):
        return

    text = message.text.strip().lower()
    cid = message.chat.id

    # /ping
    if text in ["/ping"]:
        await message.reply_text("🟢 Ich bin online!")
        return

    # /beitreten
    if text == "/beitreten":
        waiting_for_links[cid] = []
        await message.reply_text("📎 Sende die Links (jeder in einer neuen Zeile)\nSchreibe **/ende**, wenn du fertig bist.")
        return

    # /ende
    if text == "/ende" and cid in waiting_for_links:
        links = waiting_for_links.pop(cid)
        if not links:
            await message.reply_text("⚠️ Keine Links empfangen.")
            return
        await message.reply_text(f"🔍 Beitrete {len(links)} Gruppen...")
        await join_links(client, message, links)
        return

    # /statistiken
    if text == "/statistiken":
        gcount = await count_groups(client)
        await message.reply_text(
            f"📊 Statistik:\n"
            f"👥 Benutzer gespeichert: {len(known_users)}\n"
            f"👩‍👩‍👧 Gruppen beigetreten: {gcount}\n"
            f"⏱ Laufzeit: {uptime_text(time.time() - start_time)}"
        )
        return

    # /bereinigen
    if text == "/bereinigen":
        await clean_bad_groups(client, message)
        return

    # Links empfangen
    if cid in waiting_for_links:
        new_links = [l.strip() for l in text.splitlines() if l.strip()]
        waiting_for_links[cid].extend(new_links)
        await message.reply_text(f"✅ {len(new_links)} neue Links hinzugefügt.")

# ====== Automatischer Bericht ======
async def hourly_report():
    while True:
        try:
            gcount = await count_groups(app)
            uptime = uptime_text(time.time() - start_time)
            text = (
                "📊 Automatischer Bericht von Sara\n\n"
                f"👥 Benutzer: {len(known_users)}\n"
                f"💬 Nachrichten (privat): {message_count}\n"
                f"👩‍👩‍👧 Gruppen: {gcount}\n"
                f"🚪 Verlassen: {left_groups_counter}\n"
                f"⏱ Laufzeit: {uptime}"
            )
            await app.send_message(SUDO_ID, text)
        except Exception as e:
            print("hourly report error:", e)
        await asyncio.sleep(3600)  # jede Stunde

# ====== Start ======
async def main_loop():
    await app.start()
    print("✅ Sara ist gestartet.")
    try:
        await app.send_message(SUDO_ID, "💖 Sara ist jetzt aktiv und bereit!")
    except:
        pass
    asyncio.create_task(hourly_report())
    await asyncio.Event().wait()

async def run_forever():
    while True:
        try:
            await main_loop()
        except Exception as e:
            print("⚠️ Fehler:", e)
            try:
                await app.send_message(SUDO_ID, "❌ Sara ist abgestürzt! Starte neu ...")
            except:
                pass
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(run_forever())
