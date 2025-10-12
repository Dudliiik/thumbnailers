import discord
import time
from discord import app_commands
from discord.ext import commands
from discord.utils import get

help_cooldowns = {}
cooldown_messages = {}

class slashHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="help",
        description="Pings the Help role."
    )
    @app_commands.describe(
        image="Optional: Attach image",
        message="Message"
    )
    async def slashhelp(
        self,
        interaction: discord.Interaction,
        message: str,
        image: discord.Attachment = None
    ):
        help_channel = get(interaction.guild.channels, name="🆘・help")
        if interaction.channel != help_channel:
            await interaction.response.send_message(content=f"You can only use this command in {help_channel}!", ephemeral=True)
            
        help_role = get(interaction.guild.roles, name="Help")

        now = time.time()
        user_id = interaction.user.id
        last_used = help_cooldowns.get(user_id, 0)
        cooldown_seconds = 7200

        if now - last_used < cooldown_seconds:
            remaining = cooldown_seconds - (now - last_used)
            h = int(remaining // 3600)
            m = int(remaining % 3600 // 60)
            s = int(remaining % 60)
            
            bot_msg = await interaction.response.send_message(f"You can ping Help again in {h}h {m}m {s}s!")
            cooldown_messages[user_id] = bot_msg.id
            return

        content = ""
        if message:
            content += f"{message} "
        content += f"{help_role.mention}"

        if image:
            await interaction.response.send_message(
                content=content,
                allowed_mentions=discord.AllowedMentions(roles=True),
                file=await image.to_file()
            )
        else:
            await interaction.response.send_message(
                content=content,
                allowed_mentions=discord.AllowedMentions(roles=True)
            )

        help_cooldowns[user_id] = now

async def setup(bot):
    await bot.add_cog(slashHelp(bot))
