import discord
import time
from discord import app_commands
from discord.ext import commands
from discord.utils import get

wip_cooldowns = {}
cooldown_messages = {}

class slashWIP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="wip",
        description="Pings the WIP role."
    )
    @app_commands.describe(
        image="Attach image",
        message="Optional message"
    )
    async def slashwip(
        self,
        interaction: discord.Interaction,
        image: discord.Attachment,
        message: str = None,  
    ):
        wip_channel = get(interaction.guild.channels, name="👀・wip")
        if interaction.channel != wip_channel:
            await interaction.response.send_message(content=f"You can only use this command in {wip_channel}!", ephemeral=True)

        wip_role = get(interaction.guild.roles, name="WIP")

        now = time.time()
        user_id = interaction.user.id
        last_used = wip_cooldowns.get(user_id, 0)
        cooldown_seconds = 7200

        if now - last_used < cooldown_seconds:
            remaining = cooldown_seconds - (now - last_used)
            h = int(remaining // 3600)
            m = int(remaining % 3600 // 60)
            s = int(remaining % 60)
            
            bot_msg = await interaction.response.send_message(f"You can ping WIP again in {h}h {m}m {s}s!")
            cooldown_messages[user_id] = bot_msg.id
            return

        if not image.content_type.startswith("image/"):
            return await interaction.response.send_message(
                "You have to attach an image to ping WIP!",
                ephemeral=True
            )

        content = ""
        if message:
            content += f"{message} "
        content += f"{wip_role.mention}"

        await interaction.response.send_message(
            content=content,
            allowed_mentions=discord.AllowedMentions(roles=True),
            file=await image.to_file()
        )

        wip_cooldowns[user_id] = now

async def setup(bot):
    await bot.add_cog(slashWIP(bot))
