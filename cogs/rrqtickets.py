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

        if not isinstance(channel, discord.TextChannel):
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

        await channel.send(content=f"Applicant: {opener.mention}", poll=poll)

        self.done.add(channel.id)
        self.active.discard(channel.id)

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
