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
            ext = f"cogs.{filename[:-3]}"
            if ext not in client.extensions:
                await client.load_extension(ext)
                
# ---------------------------------------------

@client.event
async def on_ready():
    synced = await client.tree.sync()
    print(f"Synced commands - {len(synced)}")


# ---------------------------------------------


app = Flask(__name__)

@app.route("/")
def home():
    return "OK", 200

# ---------------------------------------------
# START BOTH TOGETHER (SAFE)
# ---------------------------------------------

async def start():
    # start flask inside asyncio loop
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        None,
        lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)), debug=False)
    )

# ---------------------------------------------
# MAIN
# ---------------------------------------------

async def main():
    # start flask
    asyncio.create_task(start())

    # start discord (ONE login only)
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main()
