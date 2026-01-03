import discord
from discord import app_commands
from main import owner_or_permissions
from datetime import timedelta

# ---------------------------------------------

class Roles(app_commands.Group):
    def __init__(self):
        super().__init__(name="role", description="Role commands")

    @app_commands.command(
        name="add",
        description="Adds a role to a member.",
    )
    @owner_or_permissions(manage_roles=True)
    async def addRole(self, interaction: discord.Interaction, user: discord.Member, role: discord.Role):
        await interaction.response.defer()
        try:
            if role >= interaction.guild.me.top_role:
                await interaction.followup.send("I cannot assign this role because it is higher than my highest role!")
                return

            if role in user.roles:
                await interaction.followup.send(f"{user.name} already has the role {role.name}")
            else:
                await user.add_roles(role)
                await interaction.followup.send(f"Added {role.name} to {user.name}!")
        except discord.Forbidden:
            await interaction.followup.send(f"I cannot manage the role {role.name}")

# ---------------------------------------------

    @app_commands.command(
        name="remove",
        description="Removes a role from a member.",
    )
    @owner_or_permissions(manage_roles=True)
    async def removeRole(self, interaction: discord.Interaction, user: discord.Member, role: discord.Role):
        await interaction.response.defer()
        try:
            if role >= interaction.guild.me.top_role:
                await interaction.followup.send("I cannot remove this role because it is higher than my highest role!")
                return
                
            if role not in user.roles:
                 await interaction.followup.send(f"{user.name} doesn't have this role")
            else:
                 await user.remove_roles(role)
                 await interaction.followup.send(f"Removed {role.name} from {user.name}!")
        except discord.Forbidden:
            await interaction.followup.send(f"I cannot manage the role {role.name}")

# ---------------------------------------------

@app_commands.command(
        name="shutdown", 
        description="Shuts down the bot.",
        )
@owner_or_permissions(administrator=True)
async def shutdown(interaction: discord.Interaction):
    await interaction.response.send_message("🛑 Shut down the bot...", ephemeral=False)
    await interaction.client.close()

# ---------------------------------------------

@app_commands.command(
    name="purge",
    description="Clears messages",
)
@owner_or_permissions(manage_messages=True)
async def purge(interaction: discord.Interaction, amount: int):
    await interaction.response.defer()
    deleted = await interaction.channel.purge(limit=amount+1)
    real_deleted = max(len(deleted) - 1, 0)
    await interaction.channel.send(f"Purged {real_deleted} messages", delete_after=4)

# ---------------------------------------------

@app_commands.command(
    name="artistpoll",
    description="Posts an artist vote poll (optional)",
)
@owner_or_permissions(administrator=True)
async def artistpoll(interaction: discord.Interaction):
    poll = discord.Poll(
        question="Vote for an artist role",
        duration=timedelta(hours=24)
    )

    poll.add_answer(text="Rookie Artist")
    poll.add_answer(text="Artist-")
    poll.add_answer(text="Artist")
    poll.add_answer(text="Artist+")
    poll.add_answer(text="Professional Artist")

    await interaction.response.send_message(poll=poll)

# ---------------------------------------------

async def setup(bot):
    bot.tree.add_command(Roles())
    bot.tree.add_command(purge)
    bot.tree.add_command(shutdown)
    bot.tree.add_command(artistpoll)
