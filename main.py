import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os
import asyncio
from threading import Thread
from flask import Flask

# ---------------------------------------------

OWNER_IDS = {859500303186657300} 

def owner_or_permissions(**perms):
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.id in OWNER_IDS:
            return True
        
        if interaction.guild is None:
            return False
        guild_perms = interaction.user.guild_permissions
        return all(getattr(guild_perms, name, False) == value for name, value in perms.items())
    return app_commands.check(predicate)

# ---------------------------------------------

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ---------------------------------------------

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await client.load_extension(f"cogs.{filename[:-3]}")

# ---------------------------------------------

@client.event
async def on_ready():
    synced = await client.tree.sync()
    print(f"Synced commands - {len(synced)}")


# ---------------------------------------------

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
                      
async def start_bot():
    await load_cogs()
    try:
        await client.start(TOKEN)
    except discord.HTTPException as e:
        print(f"Rate limited or HTTP error: {e}. Retrying in 60 seconds...")
        await asyncio.sleep(60)
        await start_bot()

if __name__ == "__main__":
    flask_thread = Thread(target=run_web, daemon=True)
    flask_thread.start()
    asyncio.run(start_bot())
