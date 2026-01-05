import discord
from discord.ext import commands
from discord.ui import View
import asyncio
import re
from datetime import timedelta

# ---------------------------------------------

class RQReminder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pattern = re.compile(r"^role-request-")
        self.required = 5
        self.delay = 60 * 60

        self.extensions = (".png", ".jpg", ".jpeg", ".webp")
        self.poll_answers = ["Rookie Artist", "Artist-", "Artist", "Artist+", "Professional Artist"]
        self.role_mapping = {"Rookie Artist": "Rookie Artist", "Artist-": "Artist-", "Artist": "Artist", "Artist+": "Artist+", "Professional Artist": "Professional Artist"}

        self.active = set()
        self.done = set()

# ---------------------------------------------

    def get_opener(self, channel):
        for target, overwrite in channel.overwrites.items():
            if isinstance(target, discord.Member):
                if overwrite.send_messages:
                    return target
        return None

# ---------------------------------------------

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):

        if not isinstance(channel, discord.TextChannel):
            return

        if not self.pattern.match(channel.name):
            return

        opener = self.get_opener(channel)
        if opener is None:
            return

        self.active.add(channel.id)
        asyncio.create_task(self.timeout(channel, opener))

# ---------------------------------------------

    async def timeout(self, channel, opener):
        await asyncio.sleep(self.delay)

        channel = channel.guild.get_channel(channel.id)
        if channel is None:
            return

        if channel.id in self.done:
            return

        count = await self.count(channel, opener)

        if count < self.required:
            await channel.send(f"{opener.mention} Reminder to upload atleast **{self.required}** thumbnails.")

        self.active.discard(channel.id)

# ---------------------------------------------

    async def count(self, channel, opener):
        total = 0
        async for message in channel.history(limit=300):
            if message.author.id != opener.id:
                continue

            for attachment in message.attachments:
                if attachment.filename.lower().endswith(self.extensions):
                    total += 1

        return total

# ---------------------------------------------

    @commands.Cog.listener()
    async def on_message(self, message):
        channel = message.channel

        if message.author.bot:
            return

        if not isinstance(message.channel, discord.TextChannel):
            return

        if not self.pattern.match(channel.name):
            return

        if channel.id in self.done:
            return

        opener = self.get_opener(channel)
        if opener is None:
            return

        if message.author.id != opener.id:
            return

        has_link = False

        if re.search(r"https?://\S+", message.content):
            has_link = True

        if message.embeds:
            has_link = True

        if has_link:
            await channel.send(f"{opener.mention} Please **upload your images directly** instead of sending links.")
            return

        if not message.attachments:
            return

        count = await self.count(channel, opener)

        if count < self.required:
            return

        poll = discord.Poll(question="Vote for an artist role", duration=timedelta(hours=24))

        for answer in self.poll_answers:
            poll.add_answer(text=answer)

        poll_message = await channel.send(
            content=f"Applicant: {opener.mention}", poll=poll)

        asyncio.create_task(self.poll_result(poll_message, channel, opener))

        self.done.add(channel.id)
        self.active.discard(channel.id)

# ---------------------------------------------

    async def poll_result(self, poll_message, channel, opener):
        await asyncio.sleep(60 * 60 * 24)

        poll = poll_message.poll
        if poll is None:
            return

        winner = poll.get_winner()
        if winner is None:
            return

        role_name = self.role_mapping.get(winner.text)
        if role_name is None:
            return

        role = discord.utils.get(channel.guild.roles, name=role_name)
        if role is None:
            return

        try:
            await opener.add_roles(role)
            await channel.send(f"{opener.mention} we've given you the **{role.name}** role! Do you have any questions before we close the ticket?", view=CloseTicket(opener))
        except discord.Forbidden:
            await channel.send("I don't have permission to assign roles.", view=CloseTicket(opener))

# ---------------------------------------------

class CloseTicket(View):
    def __init__(self, author, timeout=86400):
        super().__init__(timeout=timeout)
        self.author = author

    @discord.ui.button(label="Close", style=discord.ButtonStyle.red)
    async def close(self, interaction, button):

        if interaction.user != self.author:
            await interaction.response.send_message("Only the ticket opener can close this.", ephemeral=True)
            return

        await interaction.channel.delete()

# ---------------------------------------------

async def setup(bot):
    await bot.add_cog(RQReminder(bot))

