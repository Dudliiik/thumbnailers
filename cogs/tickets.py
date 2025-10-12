import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import os
import re
import time
from discord.ui import Button
from github import Github

# Close Button ---------------------------------

class CloseButton(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Close", emoji="🔒", style=discord.ButtonStyle.gray, custom_id="close_button")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Sure?",
            description="Are you sure about closing this ticket?",
            color=discord.Colour.dark_blue()
        )
        await interaction.response.send_message(embed=embed, view=Buttons(self.bot), ephemeral=True)

# Buttons --------------------------------------

GITHUB_REPO = "Dudliiik/thumbnailers"  
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

TRANSCRIPT_FOLDER = os.path.join(os.getcwd(), "transcripts") 
os.makedirs(TRANSCRIPT_FOLDER, exist_ok=True) 

async def get_member_safe(guild, user_id):
    member = guild.get_member(user_id)
    if not member:
        try:
            member = await guild.fetch_member(user_id)
        except discord.NotFound:
            member = None
    return member

async def replace_links(text):
    url_regex = r'(https?://[^\s]+)'
    return re.sub(url_regex, r'<a href="\1" target="_blank">\1</a>', text)

async def replace_mentions(text, msg):
    guild = msg.guild

    # Channel mentions <#id>
    text = re.sub(
        r"<#(\d+)>",
        lambda m: f'<span class="channel-mention">#{guild.get_channel(int(m[1])).name if guild.get_channel(int(m[1])) else "deleted-channel"}</span>',
        text
    )

    # User mentions <@id> or <@!id>
    async def user_replace(match):
        user_id = int(match.group(1))
        member = guild.get_member(user_id)
        if not member:
            try:
                member = await guild.fetch_member(user_id)
            except:
                member = None
        display_name = member.display_name if member else f"Unknown User ({user_id})"
        return f'<span class="mention">@{display_name}</span>'

    user_mentions = re.findall(r"<@!?(\d+)>", text)
    for uid in user_mentions:
        member = guild.get_member(int(uid))
        if not member:
            try:
                member = await guild.fetch_member(int(uid))
            except:
                member = None
        display_name = member.display_name if member else f"Unknown User ({uid})"
        text = re.sub(f"<@!?{uid}>", f'<span class="mention">@{display_name}</span>', text)

    # Role mentions <@&id>
    def role_replace(m):
        role = guild.get_role(int(m[1]))
        if role:
            r, g, b = role.color.r, role.color.g, role.color.b
            bg = f"rgb({int(r*0.25)},{int(g*0.25)},{int(b*0.25)})" if role.color.value else "rgba(255,255,255,0.1)"
            color = f"#{role.color.value:06x}" if role.color.value else "#ffffff"
            return f'<span class="role-mention" style="background-color:{bg}; color:{color};">@{role.name}</span>'
        else:
            return "@deleted-role"

    text = re.sub(r"<@&(\d+)>", role_replace, text)

    return text

def push_to_github(file_path, file_name):
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        try:
            contents = repo.get_contents(file_name)
            repo.update_file(contents.path, f"Update {file_name}", content, contents.sha)
        except Exception:
            repo.create_file(file_name, f"Add {file_name}", content)

        return f"https://dudliiik.github.io/thumbnailers/{file_name}"

    except Exception as e:
        print(f"[GitHub Push Error] {e}")
        return None
    

class Buttons(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.red, custom_id="confirm_close")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        cog = self.bot.get_cog("Tickets")
        if cog:
            await cog.generate_transcript(interaction.channel, interaction.user)
            if interaction.channel.id in cog.ticket_owners:
                del cog.ticket_owners[interaction.channel.id]
            await asyncio.sleep(0.5)
            try:
                await interaction.channel.delete()
            except Exception as e:
                print(f"Failed to delete channel: {e}")

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.gray, custom_id="cancel_close")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await interaction.delete_original_response()
        self.stop()

# Ticket Categories ----------------------------

class TicketCategory(discord.ui.Select):
    def __init__(self, bot):
        self.bot = bot
        options = [
            discord.SelectOption(label="Partnership", description="Open this only if your server follows our guidelines.", emoji="🎫"),
            discord.SelectOption(label="Role Request", description="Open this ticket to apply for an artist rankup.", emoji="⭐"),
            discord.SelectOption(label="Support", description="Open this ticket if you have any general queries.", emoji="📩")
        ]
        super().__init__(placeholder="Select a topic", min_values=1, max_values=1, options=options, custom_id="ticket_category_dropdown")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.message.edit(view=TicketDropdownView(self.bot))

        category = self.values[0]
        user = interaction.user

        categories = {
            "Partnership": {
                "title": "Partnership Ticket",
                "description": "Thanks {user.name} for contacting the partnership team of **Thumbnailers**!\n"
                               "Send your server's ad, and the ping you're expecting with any other additional details.\n"
                               "Our team will respond to you shortly.",
                "ping": [1136118197725171813, 1102975816062730291],
                "ping_user": True,
                "discord_category": "Partnership Tickets",
                "ticket_opened_category": "Partnership ticket"
            },
            "Role Request": {
                "title": "Role Request Ticket",
                "description": "Thank you for contacting support.\n"
                               "Please refer to <#1102968475925876876> and make sure you send the amount of thumbnails required for the rank you're applying for, as and when you open the ticket. "
                               "Make sure you link 5 minecraft based thumbnails at MINIMUM if you apply for one of the artist roles.",
                "ping": [1156543738861064192],
                "ping_user": False,
                "discord_category": "Role Request Tickets",
                "ticket_opened_category": "Role Request ticket"
            },
            "Support": {
                "title": "Support Ticket",
                "description": "Thanks {user.name} for contacting the support team of **Thumbnailers**!\n"
                               "Please explain your case so we can help you as quickly as possible!",
                "ping": [1102976554759368818, 1102975816062730291],
                "ping_user": True,
                "discord_category": "Support Tickets",
                "ticket_opened_category": "Support ticket"
            }
        }

        channel_name = f"{category.lower().replace(' ', '-')}-{user.name}"

        if category != "Support" and discord.utils.get(interaction.guild.channels, name=channel_name):
            await interaction.followup.send(f"You already have a ticket in {category} category.", ephemeral=True)
            return

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        }

        discord_category_name = categories[category]["discord_category"]
        category_obj = discord.utils.get(interaction.guild.categories, name=discord_category_name)

        if category_obj is None:
            channel = await interaction.guild.create_text_channel(
                name=channel_name,
                overwrites=overwrites,
                reason=f"Ticket opened by {user} for {category}"
            )
        else:
            channel = await interaction.guild.create_text_channel(
                name=channel_name,
                overwrites=overwrites,
                category=category_obj,
                reason=f"Ticket opened by {user} for {category}"
            )

        config = categories[category]
        embed = discord.Embed(
            title=config["title"],
            description=config["description"].format(user=user),
            color=discord.Color.blue()
        )

        view = CloseButton(self.bot)
        ping_roles = " ".join(f"<@&{rid}>" for rid in config["ping"])

        content = f"{user.mention} {ping_roles}" if config.get("ping_user", True) else ping_roles

        await channel.send(content=content, embed=embed, view=view)
        await interaction.followup.send(f"Your {categories[category]['ticket_opened_category']} has been opened {channel.mention} ✅", ephemeral=True)

# ----------------- Opened Ticket embed ------------------

        guild = channel.guild
        transcript_channel = discord.utils.get(guild.text_channels, name="📝・ticket-transcript")
        if transcript_channel:
            transcript_embed = discord.Embed(
                title="Ticket Created",
                description=f"{interaction.user.mention} created a new ticket\n\nTicket: `{channel.name}`\nCreator: {interaction.user.mention}",
                color=discord.Color.blue()
            )
            transcript_embed.set_footer(text="Thumbnailers", icon_url=self.bot.user.display_avatar.url)
            view = discord.ui.View()
            view.add_item(Button(label="🔗 Channel", url=channel.jump_url))
            await transcript_channel.send(embed=transcript_embed, view=view)

# ---------------- Persistent TicketView ----------------

class CloseTicketView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="✅ Accept & Close", style=discord.ButtonStyle.green, custom_id="accept_close")
    async def accept_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=False)

        if not is_ticket_channel(interaction.channel):
            await interaction.followup.send("This button can only be used in ticket channels.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"{interaction.user.name} has accepted ticket closure.",
            description="This ticket has been closed and will be deleted shortly.",
            color=discord.Colour.dark_blue()
        )
        await interaction.followup.send(embed=embed)

        cog = self.bot.get_cog("Tickets")
        if cog:
            await cog.generate_transcript(interaction.channel, interaction.user)

        await asyncio.sleep(2)
        try:
            await interaction.channel.delete()
        except Exception as e:
            print(f"Failed to delete channel: {e}")

    @discord.ui.button(label="❌ Deny & Keep Open", style=discord.ButtonStyle.gray, custom_id="deny_keep")
    async def deny_keep(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_ticket_channel(interaction.channel):
            await interaction.response.send_message(
                "This button can only be used in ticket channels.", ephemeral=True)
            return
        await interaction.response.send_message(
            content=f"{interaction.user.mention} has denied the ticket closure.", ephemeral=False)
        await interaction.message.delete()

# ---------------- Helper Function ----------------

def is_ticket_channel(channel: discord.abc.GuildChannel):
    ticket_prefixes = ["partnership-", "support-", "role-request-"]
    return any(channel.name.startswith(prefix) for prefix in ticket_prefixes)


class TicketDropdownView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.add_item(TicketCategory(bot))


# ------------ Ticket setup command ------------

GUILD_ID = 1415013619246039082

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ticket_owners = {}  
        bot.add_view(CloseButton(bot))
        bot.add_view(CloseTicketView(bot))
        bot.add_view(Buttons(bot))
        bot.add_view(TicketDropdownView(bot))

    # --------- Ticket Open Command ----------
    @commands.has_permissions(manage_messages=True)
    @commands.command(aliases=["ticket"])
    async def ticket_command(self, ctx):
        embed = discord.Embed(
            title="Open a ticket!",
            description=(
                "Welcome! You can create a ticket for any of the categories listed below. "
                "Please ensure you select the appropriate category for your issue. "
                "If your concern doesn't align with any of the options provided, feel free to create a general support ticket. Thank you!\n\n"
                "**Warn system for wrong tickets.**\n"
                "A straight warning will be issued for opening incorrect tickets for incorrect reasons. "
                "It is quite clear what ticket you need to open for what problem."
            ),
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed, view=TicketDropdownView(self.bot))

    # ----------------- /closerequest -----------------
    @app_commands.command(
        name="closerequest",
        description="Sends a message asking the user to confirm the ticket is able to be closed."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def closerequest(self, interaction: discord.Interaction):
        if not is_ticket_channel(interaction.channel):
            await interaction.response.send_message("You can only use this command in ticket channels.", ephemeral=True)
            return

        embed = discord.Embed(
            title="Close Request",
            description=f"{interaction.user.mention} has marked your ticket as resolved. Would you like to close the ticket or cancel the closure request?",
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=embed, view=CloseTicketView(self.bot))

    # ----------- Generate Transcript -----------
    async def generate_transcript(self, channel: discord.TextChannel, executor: discord.Member):
        guild = channel.guild
        transcript_channel = discord.utils.get(guild.text_channels, name="📝・ticket-transcript")
        if transcript_channel is None:
            print(f"Transcript channel not found.")
            return

        os.makedirs("transcripts", exist_ok=True)
        timestamp = int(time.time())
        base_name = f"{channel.name}_{timestamp}.html"
        file_path = os.path.join("transcripts", base_name)


        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Transcript - {channel}</title>
<style>
html, body {{ font-family: "gg sans", Arial, sans-serif; background: #36393E; color: #dcddde; margin: 4px; padding: 0; overflow-x: hidden; }}
.header {{ background-color: #36393E; color: #fff; font-size: 20px; font-weight: bold; padding: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.3); }}
.messages {{ margin: 0; padding: 10px; max-width: 1000px; }}
.message {{ display: flex; width: 100%; max-width: none; margin-bottom: 13px; padding: 4px 4px; box-sizing: border-box;}}
.message:hover{{background-color: #32353A; width: 400%;}}
.avatar {{ width: 42px; height: 42px; border-radius: 50%; margin-right: 15px; flex-shrink: 0; }}
.message-content {{ display: flex; flex-direction: column; max-width: 600px; }}
.time {{ font-size: 0.75em; color: #72767d; margin-left: 12px; }}
.content {{ margin-top: 2px; white-space: pre-wrap; }}
.embed {{ border-left: 4px solid #4f545c; background:#2F3136; padding:10px; border-radius:4px; max-width:500px; }}
.attachment {{ margin-top: 5px; margin-left: 50px; }}
.attachment img, .embed img {{ max-width: 300px; max-height: 300px; display: block; margin-top:5px; border-radius:4px; }}
.mention, .role-mention, .channel-mention {{ border-radius: 4px; padding: 2px 2px; font-size: 0.95em; font-weight: 500; white-space: nowrap; }}
.mention {{ background-color: rgba(88, 101, 242, 0.3); color: #A5B5F9; }}
.role-mention {{ background-color: rgba(255, 255, 255, 0.1); color: inherit; }}
.channel-mention {{ background-color: rgba(88, 101, 242, 0.3); color: #A5B5F9; }}
button {{ margin-top: 4px; padding: 8px 12px; border-radius: 4px; border:none; cursor:pointer; background-color:#5865F2; color:white; }}
button:hover{{ filter: brightness(1.2); }}
a {{ color: #00b0f4; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
</style>
</head>
<body>
<div class="header"># {channel}</div>
<div class="messages">
"""

        async for msg in channel.history(limit=None, oldest_first=True):
            is_bot = "bot" if getattr(msg.author, "bot", False) else ""
            html += f'<div class="message">'
            html += f'<img src="{msg.author.display_avatar.url}" class="avatar">'
            html += f'<div class="message-content">'
            member = await get_member_safe(channel.guild, msg.author.id)
            role_color = "#dcddde"
            if member:
                colored_roles = [r for r in member.roles if r.name != "@everyone" and r.color.value != 0]
                if colored_roles:
                    top_role = max(colored_roles, key=lambda r: r.position)
                    role_color = f"#{top_role.color.value:06x}"

            display_name = member.display_name if member else msg.author.name
            user_display = f'<span class="author {is_bot}" style="color:{role_color}">{display_name}</span>'
            time_str = msg.created_at.strftime("%d. %m. %Y %I:%M %p")
            time_html = f'<span class="time">{time_str}</span>'
            html += f'<div style="display:flex;align-items:center;">{user_display}{time_html}</div>'

            if msg.content:
                content_html = await replace_mentions(msg.content, msg)
                content_html = await replace_links(content_html)
                content_html = content_html.replace("**", "<b>").replace("*", "<i>").replace("__", "<u>")
                html += f'<div class="content">{content_html}</div>'

            for embed in msg.embeds:
                embed_color = f"#{embed.color.value:06x}" if embed.color else "#4f545c"
                html += f'<div class="embed" style="border-left:4px solid {embed_color}; background:#2F3136; padding:10px; margin-top:8px; border-radius:4px; max-width:520px;">'
                if embed.title:
                    html += f'<div style="font-weight:600; font-size:16px; margin-bottom:4px;">{embed.title}</div>'
                if embed.description:
                    desc_html = await replace_mentions(embed.description, msg)
                    html += f'<div style="font-size:14px; white-space:pre-wrap; margin-bottom:6px;">{desc_html}</div>'
                for field in embed.fields:
                    field_html = await replace_mentions(field.value, msg)
                    html += f'<div style="margin-top:4px;">'
                    html += f'<div style="font-weight:600; font-size:14px; margin-bottom:2px;">{field.name}</div>'
                    html += f'<div style="font-size:14px; white-space:pre-wrap;">{field_html}</div></div>'
                if embed.image and embed.image.url:
                    html += f'<img src="{embed.image.url}" style="max-width:100%; margin-top:6px;">'
                if embed.thumbnail and embed.thumbnail.url:
                    html += f'<img src="{embed.thumbnail.url}" style="max-width:80px; max-height:80px; margin-top:6px;">'
                html += '</div>'

            for attachment in msg.attachments:
                if attachment.content_type and attachment.content_type.startswith("image/"):
                    html += f'<div class="attachment"><a href="{attachment.url}">{attachment.filename}</a><br><img src="{attachment.url}" style="max-width:400px; max-height:400px; margin-top:6px;"></div>'
                else:
                    html += f'<div class="attachment"><a href="{attachment.url}">{attachment.filename}</a></div>'

            # Buttons (komponenty)
            if msg.components:
                html += '<div style="display:flex; gap:4px; flex-wrap:wrap; margin-top:4px;">'
                for action_row in msg.components:
                    for component in action_row.children:
                        emoji = str(component.emoji) if component.emoji else ""
                        label = component.label or "Button"

                        if component.style == discord.ButtonStyle.green:
                            bg = "#3BA55D"
                        elif component.style == discord.ButtonStyle.red:
                            bg = "#ED4245"
                        elif component.style == discord.ButtonStyle.gray:
                            bg = "#4F545C"
                        elif component.style == discord.ButtonStyle.blurple:
                            bg = "#5865F2"
                        else:
                            bg = "#5865F2"

                        html += f'''
                        <button style="
                            background-color:{bg};
                            color:white;
                            border:none;
                            border-radius:4px;
                            padding:4px 10px;
                            font-size:14px;
                            font-weight:500;
                            cursor:pointer;
                            display:inline-flex;
                            align-items:center;
                            gap:4px;
                            white-space:nowrap;
                        ">{emoji} {label}</button>'''
                html += '</div>'

            html += '</div></div>'

        html += "</div></body></html>"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html)

        public_url = push_to_github(file_path, f"transcripts/{base_name}")

        embed = discord.Embed(
            title="Ticket Closed",
            description=f"{executor.mention} closed a ticket \n\nTicket: `{channel.name}` \nCommand Executor: {executor.mention}",
            color=discord.Colour.red()
        )
        embed.set_footer(text="Thumbnailers", icon_url=self.bot.user.display_avatar.url)
        view = discord.ui.View()
        view.add_item(Button(label="📄 Transcript", style = discord.ButtonStyle.link, url = public_url))
        await transcript_channel.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Tickets(bot))
    
