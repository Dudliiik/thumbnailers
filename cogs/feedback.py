import time
from discord.ext import commands
from discord.utils import get

feedback_cooldowns = {}
cooldown_messages = {}

class Feedback(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return

        bot_msg_id = cooldown_messages.pop(message.id, None)
        if bot_msg_id:
            bot_msg = message.channel.get_partial_message(bot_msg_id)
            try:
                await bot_msg.delete()
            except:
                pass

    @commands.command()
    async def feedback(self, ctx):
        feedback_channel = get(ctx.guild.channels, name="🙌・feedback")
        if ctx.channel != feedback_channel:
            return
        
        feedback_role = get(ctx.guild.roles, name="Feedback")
        if feedback_role is None:
            await ctx.send("Role 'Feedback' doesn't exist!")
            return

        now = time.time()
        user_id = ctx.author.id
        last_used = feedback_cooldowns.get(user_id, 0)
        cooldown_seconds = 7200

        if now - last_used < cooldown_seconds:
            remaining = cooldown_seconds - (now - last_used)
            h = int(remaining // 3600)
            m = int(remaining % 3600 // 60)
            s = int(remaining % 60)
            
            bot_msg = await ctx.send(f"You can ping Feedback again in {h}h {m}m {s}s!")
            cooldown_messages[ctx.message.id] = bot_msg.id
            return

        if len(ctx.message.attachments) == 0:
            await ctx.send("You have to attach an image to ping Feedback!")
            return

        attachment = ctx.message.attachments[0]
        if not attachment.filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
            await ctx.send("You have to attach an image to ping Feedback!")
            return

        feedback_cooldowns[user_id] = now
        await ctx.reply(content=f"{feedback_role.mention}")

async def setup(bot):
    await bot.add_cog(Feedback(bot))
