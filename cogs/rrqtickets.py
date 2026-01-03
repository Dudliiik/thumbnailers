import discord
from discord.ext import commands
import asyncio
import re
from datetime import timedelta

# ---------------------------------------------

class rqreminder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pattern = re.compile(r"^role-request-")
        self.required = 5
        self.delay = 5
        self.extensions = (".png", ".jpg", ".jpeg", ".webp")
        self.poll_answers = ["Rookie Artist", "Artist-", "Artist", "Artist+", "Professional Artist"]
        self.active = set()
        self.done = set()

# ---------------------------------------------

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        if isinstance(channel, discord.TextChannel) and self.pattern.match(channel.name):
            opener = self.opener(channel)
            if opener:
                self.active.add(channel.id)
                self.bot.loop.create_task(self.timeout(channel, opener))

    def opener(self, channel):
        for target, overwrite in channel.overwrites.items():
            if isinstance(target, discord.Member) and overwrite.send_messages:
                return target

    async def timeout(self, channel, opener):
        await asyncio.sleep(self.delay)
        channel = channel.guild.get_channel(channel.id)
        if not channel or channel.id in self.done:
            self.active.discard(channel.id)
            return
        if await self.count(channel, opener) < self.required:
            await channel.send(f"{opener.mention} Reminder to upload atleast {self.required} thumbnails")
        self.active.discard(channel.id)

    async def count(self, channel, opener):
        total = 0
        async for msg in channel.history(limit=300):
            if msg.author.id == opener.id:
                total += sum(a.filename.lower().endswith(self.extensions) for a in msg.attachments)
        return total

# ---------------------------------------------

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not isinstance(message.channel, discord.TextChannel):
            return
        channel = message.channel
        if not self.pattern.match(channel.name) or not message.attachments or channel.id in self.done:
            return
        opener = self.opener(channel)
        if not opener or message.author.id != opener.id:
            return
        if await self.count(channel, opener) >= self.required:
            poll = discord.Poll(question="Vote for an artist role", duration=timedelta(hours=24))
            for answer in self.poll_answers:
                poll.add_answer(text=answer)
            await channel.send(content=f"Applicant: {opener.mention}", poll=poll)
            self.done.add(channel.id)
            self.active.discard(channel.id)

# ---------------------------------------------

async def setup(bot):
    await bot.add_cog(rqreminder(bot))
