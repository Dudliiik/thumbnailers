
import discord
from discord import app_commands

# ---------------------------------------------

class Members(app_commands.Group):
    def __init__(self):
        super().__init__(name="member", description="Member info commands")

    @app_commands.command(
        name="info",
        description="Sends info about a member."
    )
    async def info(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer()

        roles = [role.mention for role in member.roles if role.name != "@everyone"]
        roles_display = ", ".join(roles) if roles else "No roles"

        info_embed = discord.Embed(
            title="",
            color=discord.Color.purple()
        )

        info_embed.set_author(name=member.display_name, icon_url = member.display_avatar.url)
        info_embed.set_thumbnail(url=member.display_avatar.url)

        info_embed.add_field(name="User", value=f"{member.mention}\nID: {member.id}", inline=True)
        info_embed.add_field(name="Joined", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
        info_embed.add_field(name="Roles", value=roles_display, inline=False)

        info_embed.set_footer(
            text="Thumbnailers",
            icon_url=interaction.client.user.display_avatar.url
        )

        await interaction.followup.send(embed=info_embed)

# ---------------------------------------------

@app_commands.command(
    name="thelp",
    description="Sends a list of all the bot's commands.",
)
async def helpcmnd(interaction:discord.Interaction):
    help_embed = discord.Embed(
        title="", 
        description=(f"**Member commands**\n\n`- /artist about\n- /artist list\n- /artist req\n- /member info`\n\n**Channel commands**\n\n`- !feedback\n- !help\n- !wip`\n\n**Admin Commands**\n\n`- /role remove\n- /role add\n- /purge\n- /psd\n- /closerequest\n- /shutdown`"),
        color = discord.Colour.pink()
    )
    help_embed.add_field(name="",value="",inline=True)
    help_embed.set_footer(text="Thumbnailers", icon_url=interaction.client.user.display_avatar.url)
    await interaction.response.send_message(embed=help_embed)

# ---------------------------------------------

async def setup(bot):
    bot.tree.add_command(Members())
    bot.tree.add_command(helpcmnd)