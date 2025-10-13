import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os
import asyncio
import json
from threading import Thread
from cogs.tickets import CloseTicketView
from flask import Flask, send_from_directory


# ---------------- Load .env ----------------

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# ---------------- Discord bot ----------------

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ---------------- Load cogs ----------------

async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await client.load_extension(f"cogs.{filename[:-3]}")


# ---------------- /shutdown command ----------------

@client.tree.command(
        name="shutdown", 
        description="Shuts down the bot.",
        )
async def shutdown(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "Only users with permissions can toggle this command", ephemeral=True)
        return
    await interaction.response.send_message("🛑 Shut down the bot...", ephemeral=False)
    await client.close()

# ---------------- VIP+ Persistent Boost Tracking ----------------

BOOST_FILE = "boost_counts.json"

def load_boosts():
    if os.path.exists(BOOST_FILE):
        with open(BOOST_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_boosts(data):
    with open(BOOST_FILE, "w") as f:
        json.dump(data, f, indent=4)

boost_counts = load_boosts()

@client.event
async def on_member_update(before: discord.Member, after: discord.Member):

    if before.premium_since is None and after.premium_since is not None:
        user_id = str(after.id)
        boost_counts[user_id] = boost_counts.get(user_id, 0) + 1
        save_boosts(boost_counts)  

        if boost_counts[user_id] >= 2:
            role = discord.utils.get(after.guild.roles, name="VIP+")
            if role and role not in after.roles:
                await after.add_roles(role)

    elif before.premium_since is not None and after.premium_since is None:
        role = discord.utils.get(after.guild.roles, name="VIP+")
        if role and role in after.roles:
            await after.remove_roles(role)

# ---------------- Bot event ----------------

GUILD_ID = 1102968474894082081

@client.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)

    artist_group = Artist()
    roles_group = Roles()
    client.tree.add_command(artist_group)
    client.tree.add_command(roles_group)

    synced = await client.tree.sync()
    print(f"Synced commands - {len(synced)}")


# ----------------------- /role give command  ----------------------- 

class Roles(app_commands.Group):
    def __init__(self):
        super().__init__(name="role", description="Role commands")

    @app_commands.command(
        name="add",
        description="Adds a role to a member.",
    )
    @discord.app_commands.checks.has_permissions(manage_roles=True)
    async def addRole(self, interaction: discord.Interaction, user: discord.Member, role: discord.Role):
        await interaction.response.defer()

        if role in user.roles:
            await interaction.followup.send(f"{user.mention} already has the role {role.name}")
        else:
            await user.add_roles(role)
            await interaction.followup.send(f"Added {role.name} to {user.mention}!")


    @app_commands.command(
        name="remove",
        description="Removes a role from a member.",
    )
    @discord.app_commands.checks.has_permissions(manage_roles=True)
    async def removeRole(self, interaction: discord.Interaction, user: discord.Member, role: discord.Role):
        await interaction.response.defer()
        await user.remove_roles(role)
        await interaction.followup.send(f"Removed {role.name} from {user.mention}!")

# ----------------------- /psd add command  ----------------------- 

@client.tree.command(
        name="psd", 
        description="Adds a PSD to the VIP channels."
)
@discord.app_commands.checks.has_permissions(manage_messages=True)
async def psd(interaction:discord.Interaction, link: str, image: discord.Attachment, user: discord.User):
    embed = discord.Embed(title=link)
    embed.set_image(url=image.url)
    embed.set_footer(text=f"Provided by {user}")
    await interaction.response.send_message(embed=embed)

# ------------------ /purge command ----------------------------

@client.tree.command(
    name="purge",
    description="Clears messages",
)
@discord.app_commands.checks.has_permissions(manage_messages=True)
async def purge(interaction: discord.Interaction, amount: int):
    await interaction.response.defer()
    deleted = await interaction.channel.purge(limit=amount+1)
    real_deleted = max(len(deleted) - 1, 0)
    await interaction.channel.send(f"Purged {real_deleted} messages", delete_after=4)

# --------------------- /help command ---------------------
@client.tree.command(
    name="thelp",
    description="Sends a list of all the bot's commands.",
)
async def helpcmnd(interaction:discord.Interaction):
    help_embed = discord.Embed(
        title="",
        description=(f"**Member commands**\n\n`- /artist about\n- /artist list`\n\n**Channel commands**\n\n`- /feedback\n- /help\n- /wip`\n\n**Admin Commands**\n\n`- /role remove\n- /role add\n- /purge\n- /psd\n- /closerequest\n- /shutdown`"),
        color = discord.Colour.pink()
    )
    help_embed.add_field(name="",value="",inline=True)
    help_embed.set_footer(text="Thumbnailers", icon_url=client.user.display_avatar.url)
    await interaction.response.send_message(embed=help_embed)

# ------------------ /artist command ----------------------------
ARTISTS_INFO = {
    831401368324669460: {  # letpicocook
        "name": "Zynfx",
        "description": (
            "Hi, I'm a professional thumbnail artist & graphics designer 🖌️ with +3 years of experience, and had worked with some well-known creators in the industry, throughout my designer career.\n\n"
            "I specialize in creating thumbnails 📈 that are visually stunning and able to get the attention."
        ),
        "image": "https://cdn.discordapp.com/attachments/1361253039314567288/1361253039482208346/a18bc11471372787.6662abe2d3d6f.png?ex=68ee062f&is=68ecb4af&hm=2c1bc6e48f64de31ed4659991108b0218593b840aeecbc16f1dbb40b651e9977&",
        "links": {
            "Twitter": "https://x.com/zynfx_designs",
            "Behance": "https://www.behance.net/zynfx"
        },
        "role": "1102980848606785616"
    },
    338448901432672267: {  # Kbashed
        "name": "Kbashed",
        "description": "I make custom thumbnails that are built to perform. Each one is tailored to your video, your audience, and what actually gets people to click.",
        "image": "",
        "links": {
            "Portfolio": "https://kbashed.com/"
        },
        "role": "1102980848606785616"
    },
    766143826254888998: {  # Realmfx
        "name": "Realmfx",
        "description": "Seasoned thumbnail creator. CTR, horror, documentary- all in one place.",
        "image": "https://media.discordapp.net/attachments/1423979157380923442/1423979157909540954/kai_pfp.jpg?ex=68e398ef&is=68e2476f&hm=3f0439b0b5cbc17f3620da98fdd615c5e12b199f5e42d8a41ac706c62120642e&=&format=webp",
        "links": {
            "Portfolio": "https://www.behance.net/realmfx_",
            "YTJobs": "https://ytjobs.co/talent/profile/380572?r=38&t=tnp&utm_campaign=share-new-profile&utm_ref=talent"
        },
        "role": "1102980848606785616"
    },
    527922466115551251: {  # Andre
        "name": "Andre",
        "description": "Hi, I'm a Minecraft Graphic Designer from Brazil. With +5 years of experience, I've worked with many YouTube creators.\n\n"
                       "I specialize in Thumbnail creation, but I also work with Banners, PFPs, Marketplace Key Arts, and Marketing Arts.",
        "image": "https://media.discordapp.net/attachments/1422591185201004564/1422591185486221372/Sem_Titulo-1.png?ex=68e3d249&is=68e280c9&hm=15a43b2b6676ba05985bc5d548f6dc205c15e2149e9a78aa2235377ffff1c40e&=&format=webp&quality=lossless",
        "links": {
            "Work": "https://andremcdz.myportfolio.com/",
            "Portfolio": "https://www.artstation.com/andre_mcdz",
            "Twitter": "https://x.com/andre_mcdz"
        },
        "role": "1102980848606785616"
    },
    949660082566729748: {  # Fyoncle
        "name": "Fyoncle",
        "description": "Hey there! I'm Fyoncle, I'm doing 3D Art for 6 years now, started in around 2018-2019 with Mine Imator, then Cinema4D and Blender in the last few years. I usually like to do story-based renders, but I also do thumbnail commissions and more, I have a lot of styles I'm switching through.",
        "image": "",
        "links": {
            "Portfolio": "https://www.artstation.com/fyoncle"
        },
        "role": "1102980848606785616"
    },
    598176509345136650: {
        "name": "⚡arik_Gamerz ⚡",
        "description": "Im Finn or arik/arikDZN and I'm a 3D-artist and minecraft artist who uses Blender.",
        "image": "https://media.discordapp.net/attachments/1424432334953910403/1424433448973766686/ARIK_PB.png?ex=68e3ee86&is=68e29d06&hm=1666601b1d280238831b4396e0be2115eadf8d18ab747172bf8ede575b8eaaef&=&format=webp&quality=lossless",
        "links": {
            "Portfolio": "https://ariksportfolio.carrd.co/"
        },
        "role": "1102980848606785616"
    },
    1037169224617050162: { # Emzz
        "name": "Emzzfx",
        "description": "Hey there! I'm an experienced thumbnail designer who has worked with numerous YouTubers. Additionally, I've learned from some of the best designers in the space.",
        "image": "https://media.discordapp.net/attachments/1361457298773512393/1361457298974703666/yutapfp.jpg?ex=68e4e12a&is=68e38faa&hm=d6b21ddfda6b41ea34dc08f2ef8097d063f2c0506a401ecf8378472476420bbb&=&format=webp",
        "links": {
            "Portfolio": "https://www.behance.net/emmz_fx",
            "YTJobs": "https://ytjobs.co/@emmz",
            "Website": "https://solo.to/emmzmc",
            "Twitter": "https://x.com/emmz_fx"
        },
        "role": "1102980848606785616"
    },
    767953235616202833: { # Mango
        "name": "Mangofx",
        "description": "Hey, i’m a highly experienced thumbnail designer who’s worked with several creators including Daquavis, Kiply, Wisp, FlameFrags, Sharpness, and many more.\n\nI’ve accumulated around 30M views with my work.\n\nDm for inquiries—prices start at $100 per thumbnail.",
        "image": "https://cdn.discordapp.com/attachments/1192111563725869112/1427385608145207407/pfpfppfpf_1.png?ex=68eeabf0&is=68ed5a70&hm=06d2af191fc319b8760bb648840b39f2e6657d56f902b728c7f947cfb707996e&",
        "links": {
            "Portfolio": "https://behance.net/mango_fx",
            "Twitter": "https://x.com/realmangofx",
            "Website": "https://mangofx.art/",
            "YTJobs": "https://ytjobs.co/@mangofx"
        },
        "role": "1102980848606785616"
    },
    858108973772439562: {  # wkso
        "name": "wkso",
        "description": "Hey! I'm wkso, I make thumbnails, I've been doing thumbnails for 1.5 years now and worked with many large creators!",
        "image": "",
        "links": {
            "Portfolio": "https://www.behance.net/wkso",
            "Payhip": "https://payhip.com/wkso"
        },
        "role": "1102980848606785616"
    },

    # ARTIST+

    940824020046192650: {  # BLUU
        "name": "BLUU",
        "description": "With over two years of experience, I specialize in creating high-quality thumbnails that elevate content. I've partnered with numerous content creators, bringing a diverse skill set to every project.\n\nDM for inquiries—prices range from $60-80!",
        "image": "https://media.discordapp.net/attachments/1397627818640146432/1397627818824831058/IMG_8011.jpg?ex=68e35016&is=68e1fe96&hm=6962e60f8f952e8e66dadd3cb4704160cb494138351df69893db4a4acad43328&=&format=webp",
        "links": {
            "Portfolio": "https://bluu.ju.mp/",
            "Behance": "https://be.net/bluu_fx",
            "Twitter": "https://x.com/B1UUfx"
        },
        "role": "1102982383571042386"
    },
    887220487468511273: {  # Danmc
        "name": "DanMC",
        "description": "I’m DanMC – a Minecraft Thumbnail Maker with over 3 years of experience in graphic design.\n\nI’m passionate about creating eye-catching thumbnails that help YouTubers impress viewers from the very first glance. Trust in my skills and experience – together, we’ll elevate your content and turn your ideas into reality.",
        "image": "https://media.discordapp.net/attachments/1419630333535457301/1419630334064197663/avartar2.png?ex=68e4ea47&is=68e398c7&hm=d5111d560df7547d6f1f14f4a455bfc0b435b804c9ea7bf947098dddbc0a598b&=&format=webp&quality=lossless",
        "links": {
            "Portfolio": "https://danmc.carrd.co/",
            "Behance": "https://www.behance.net/danthumbnail",
            "YTJobs": "https://ytjobs.co/talent/profile/438393"
        },
        "role": "1102982383571042386"
    },
    821025628127756320: {  # Ninja
        "name": "Ninjanmy",
        "description": "Hi there! I’m a passionate and results-driven thumbnail designer with over 2 years of experience creating scroll-stopping visuals that drive clicks and engagement. My focus is on clean, bold, and highly optimized designs that make your content stand out in any feed.",
        "image": "https://media.discordapp.net/attachments/1380545516873711676/1425120399301152918/IMG_9242.png?ex=68ebb44c&is=68ea62cc&hm=742c429af35c9cb17f66d8eac280a93fc889180a32c02655d20b9433e95c3a76&=&format=webp&quality=lossless&width=1232&height=1232",
        "links": {
            "Portfolio": "https://ninjanmy.carrd.co/",
            "Behance": "https://www.behance.net/ninjanmy-zbxri",
            "Twitter": "https://x.com/ninjanmy"
        },
        "role": "1102982383571042386"
    },
    804312689609408533: {  # Silent
        "name": "Silent",
        "description": "Hi, I'm Silent, a 15 year old graphic designer, thumbnail maker, video editor and YouTuber. I create with a passion that goes beyond just money;)",
        "image": "",
        "links": {
            "Portfolio": "https://silentgfx.carrd.co/",
            "Twitter": "https://x.com/SilentObv",
            "Fiverr": "https://www.fiverr.com/obvsilent_"
        },
        "role": "1102982383571042386"
    },
    836848313356910594: {  # Izze
        "name": "Izze",
        "description": "Hey There! I'm izzlexn, I love making awesome and high converting YT thumbnail designs for you and see your channel grow. Give us a try, and you'll admire our work. </3",
        "image": "",
        "links": {
            "Portfolio": "https://izzegfx.carrd.co/",
            "Commissions": "https://ko-fi.com/izlexn"
        },
        "role": "1102982383571042386"
    },
    877650323655782440: {  # gopg
        "name": "gopg",
        "description": "Hi, I’m gopg, I’m a content creator turned thumbnail artist with 1 year of experience in creating smp thumbnails and 6 years of overall experience in Photoshop\n\nI’m currently working with Flamefrags and have worked with Baablu, TruOriginal, Lomedy, and Dol9hin in the past, accumulating over 20M views across all the videos with my thumbnails.",
        "image": "",
        "links": {
            "Portfolio": "https://www.behance.net/gopg",
            "Twitter": "https://x.com/gopgVEVO"
        },
        "role": "1102982383571042386"
    },
}

ARTIST_ROLES = {
    "Professional Artist": 1102980848606785616,
    "Artist+": 1102982383571042386,
    "Artist": 1102983469933543435
}

class Artist(app_commands.Group):
    def __init__(self):
        super().__init__(name="artist", description="Artist Commands")

    @app_commands.command(
        name="about",
        description="Sends a portfolio of the chosen Artist."
    )
    @app_commands.describe(artist="Choose an artist to view their portfolio")
    async def artistsabout(self, interaction: discord.Interaction, artist: discord.User):
        info = ARTISTS_INFO.get(artist.id)
        if not info:
            await interaction.response.send_message(f"No info found for {artist.name}.", ephemeral=True)
            return
        
        role_id = int(info["role"])
        role = interaction.guild.get_role(role_id)
        if not role:
            await interaction.response.send_message("No Artist roles found.")

        embed = discord.Embed(
            title=info["name"],
            description=f"{info['description']}\n\n**Role:** {role.mention}",
            color=discord.Color.orange()
        )
        embed.set_image(url=info["image"])
        embed.set_footer(text=info["name"], icon_url=artist.display_avatar.url)

        view = discord.ui.View()
        for label, url in info["links"].items():
            view.add_item(discord.ui.Button(label=label, url=url, style=discord.ButtonStyle.link))

        await interaction.response.send_message(embed=embed, view=view)

    # --------------------------------------------------------------------------

    @app_commands.command(
        name="list",
        description="Shows a list of our Artists."
    )
    async def list(self, interaction: discord.Interaction):
        guild = interaction.guild

        await guild.chunk()
        all_members = guild.members

        print(f"Fetched {len(all_members)} members from {guild.name}")

        embed_description = ""
        for role_name, role_id in ARTIST_ROLES.items():
            role = guild.get_role(role_id)
            if not role:
                continue

            members_with_role = [
                f"<@{m.id}>" for m in all_members
                if any(r.id == role.id for r in m.roles)
            ]

            if not members_with_role:
                embed_description += f"{role.mention}\nNo members yet.\n\n"
                continue

            lines = []
            for i in range(0, len(members_with_role), 2):
                pair = members_with_role[i:i+2]
                lines.append(" | ".join(pair))

            member_list_str = "\n- ".join(lines)
            embed_description += f"{role.mention}\n- {member_list_str}\n\n"

        embed = discord.Embed(
            title="🎨 Our Artists",
            description=embed_description or "No artists found.",
            color=discord.Colour.yellow()
        )

        await interaction.response.send_message(
            embed=embed,
            allowed_mentions=discord.AllowedMentions(users = True, roles=True)
        )

app = Flask(__name__)
TRANSCRIPT_FOLDER = os.path.join(os.getcwd(), "transcripts")
os.makedirs(TRANSCRIPT_FOLDER, exist_ok=True)

@app.route("/transcripts/<path:filename>")
def transcripts(filename):
    return send_from_directory(TRANSCRIPT_FOLDER, filename)

@app.route("/")
def home():
    return "Bot is running"

def run_web():
    app.run(host="0.0.0.0", port=10000, debug=False)

                           
# ---------------- Run bot + web ----------------

async def main():
    async with client:
        await load_cogs()
        await client.start(TOKEN)

if __name__ == "__main__":
    flask_thread = Thread(target=run_web, daemon=True)
    flask_thread.start()
    asyncio.run(main())
