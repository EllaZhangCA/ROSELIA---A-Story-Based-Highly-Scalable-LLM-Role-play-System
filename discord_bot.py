import os, asyncio
import discord
from datetime import datetime
from zoneinfo import ZoneInfo
import tzlocal
from dotenv import load_dotenv

import roleplay_engine

load_dotenv()
TOKEN      = os.getenv("DISCORD_TOKEN")
CHARACTER  = os.getenv("CHARACTER_NAME", "Moka")

raw_ids = os.getenv("ALLOWED_CHANNEL_IDS_DC", "")
ALLOWED_CHANNEL_IDS = [int(cid.strip()) for cid in raw_ids.split(",") if cid.strip()]

intents = discord.Intents.default()
intents.message_content = True
client  = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"{CHARACTER} BOT is now live:{client.user}")
    print("Allowed speaking channels: ", ALLOWED_CHANNEL_IDS)

@client.event
async def on_message(msg: discord.Message):
    # Ignore the message from bot itself
    if msg.author == client.user:
        return

    # Ignore channels that now allowed
    if msg.channel.id not in ALLOWED_CHANNEL_IDS:
        return

    # Clean too short txt
    user_txt = msg.content.strip()
    if len(user_txt) < 2:
        return

    # Use local ISO time
    try:
        local_tz = ZoneInfo(tzlocal.get_localzone_name())
    except Exception:
        local_tz = ZoneInfo("UTC")
    iso_time = datetime.now(local_tz).isoformat()

    # Use roleplay_engine
    reply = await asyncio.to_thread(
        roleplay_engine.generate_reply,
        msg.author.name,
        user_txt,
        iso_time
    )
    if reply:
        try:
            await msg.channel.send(reply)
        except Exception as e:
            print("Failed to send message: ", e)

if __name__ == "__main__":
    if TOKEN:
        client.run(TOKEN)
    else:
        print("ERROR: DISCORD_TOKEN didn't setted in the environment variables")
