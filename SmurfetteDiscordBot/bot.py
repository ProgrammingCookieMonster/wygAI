import os
import logging
import discord

from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("smurfette")

TOKEN = os.environ["DISCORD_TOKEN"]
WELCOME_CHANNEL_ID = int(os.environ["WELCOME_CHANNEL_ID"])
UNREGISTERED_ROLE_ID = int(os.environ["UNREGISTERED_ROLE_ID"])
VERIFIED_ROLE_ID = int(os.environ["VERIFIED_ROLE_ID"])

# keep logging in case channel stays up
LOG_CHANNEL_ID = os.environ.get("LOG_CHANNEL_ID")
LOG_CHANNEL_ID = int(LOG_CHANNEL_ID) if LOG_CHANNEL_ID else None

BANNER_IMAGE_PATH = "assets/welcome.gif" # local path, decided to keep a gif local to ensure it passes on

# button click belongs to the specific button, defined after restarts
SET_NAME_CUSTOM_ID = "smurfette:set_button_name"

# intents define the event category the bot can handle on Discord
# Smurfette needs access to the privileged intent of "members" so it can change their nicknames
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Modal UI pop-up for the name change.
# the required field is on false as new members are unlikely to have ovvenames, allows them to change to simple First/Last
class SetNameModal(discord.ui.Modal, title="Set your server name!"):
    first_name = discord.ui.TextInput(label="First Name", placeholder="Papa", max_length=30)
    union_title = discord.ui.TextInput(label="Union Title/ åvve-name", placeholder="Gargamel", max_length=30, required=False)
    last_name = discord.ui.TextInput(label="Last Name", placeholder="Smurf", max_length=30)

    # async function waits and takes in the input from the default Discord submit button that is forced with the Modal
    async def on_submit(self, interaction: discord.Interaction):
        # and here the input is being cleanly stripped and built into a spaced full discord server name
        # append each input field to the parts and build the name
        parts = [str(self.first_name).strip()]

        if str(self.union_title).strip():
            parts.append(str(self.union_title).strip())

        parts.append(str(self.last_name).strip())


        new_nick = " ".join(parts)[:32]

        # the user interacts with the button
        # but the bot edits the nickname using it's own permissions instead of calling on the user's hierarchical role permissions
        member = interaction.user
        guild = interaction.guild
        try:
            await member.edit(nick=new_nick, reason="Self-service onboarding rename by SmurfetteBot.")
        except:
            await interaction.response.send_message("I couldn't change your nickname. This can happen due to a few reasons: you are the owner of the server; your highest role is currently higher than mine; or something is wrong with the server/code I am hosted at. All members of WYSIWYG are allowed to change their own nicknames in the settings at all times. If you cannot or you don't know how, flag a member of @Presidie or @Styrelsen to change your server name.", ephemeral=True)
            return # does not attempt role changing if the name failed so far

        # removes the forced onboarding role of "unregistered-user" and assigns "Trusted", as the whole interaction passes as a bot check as well
        unregistered_role = guild.get_role(UNREGISTERED_ROLE_ID)
        verified_role = guild.get_role(VERIFIED_ROLE_ID)
        try:
            # acts only if the target doesn't already match the goal
            if unregistered_role and unregistered_role in member.roles:
                await member.remove_roles(unregistered_role, reason="User completed server onboarding rename process, removing unregistered role.")
            if verified_role and verified_role not in member.roles:
                await member.add_roles(verified_role, reason="User completed server onboarding rename process and earned the Trusted badge.")
        except:
            log.warning(f"Missing permissions to swap roles for user/id: {member.display_name}/{member.id}")

        # modal response
        await interaction.response.send_message(f"All set -- server nickname changed to **{new_nick}**. Welcome in!", ephemeral=True)

        # logging in the welcome-zone -- for SUDO and presidium only
        if LOG_CHANNEL_ID:
            log_channel =guild.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                log_embed = discord.Embed(
                    description=(f"{member.mention} verified as a trusted user by bypassing the onboarding name change program & set their server nickname to **{new_nick}**"),
                    colour=discord.Color.green(),
                )
                log_embed.set_footer(text=f"User Name/ID: {member.display_name}/{member.id}")
                try:
                    await log_channel.send(embed=log_embed)
                except:
                    log.warning("Missing permissions to post in this channel? %s", LOG_CHANNEL_ID)

# container for interactive components set to not expire unless completed or dismissed
class WelcomeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

   # maps to render to the specific button defined before, should stay the same on reset
    @discord.ui.button(label="Set My Name!", style=discord.ButtonStyle.primary, custom_id=SET_NAME_CUSTOM_ID)
    async def set_name(self, interaction: discord.Interaction, button: discord.ui.Button):
        # interaction --> send modal to trigger pop-up
        await interaction.response.send_modal(SetNameModal())

# fires once on the onboarding process
@bot.event
async def on_ready():
    bot.add_view(WelcomeView())
    log.info("Logged in as %s (id: %s)", bot.user, bot.user.id)

# command for posting the card on the channel. only admin can do that, needs the first time post and re-posting in case it goes down
@bot.command(name="postwelcome")
@commands.has_permissions(administrator=True)
async def post_welcome(ctx: commands.Context):
    """Admin-only one-off command: post/re-post the onboarding card."""
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel is None:
        await ctx.send("Could not find welcome channel, check ID on SBC service.", delete_after=8)
        return

    embed = discord.Embed(
        title="Welcome to the Official server of WYSIWYG!",
        description=("In order to avoid bot onboardings and to keep things organized, we would like you to assist our hand-coded bot in changing your very own Server Nickname. It helps out a lot when the board is looking for a specific person they know by their first name but would have a totally different discord nickname.\n\n"
        "Name format: **First name + 'Union Name/Ovvename' + Last name**. You can leave the Union Name empty if you haven't gotten one from your committee yet. \n\n"
        "Click the button below and fill in the fields -- takes about 10 seconds. Unless you are a bot? 👀👀"
    ), color=discord.Color.green(),
    )

    # set banner on message
    file = None
    if BANNER_IMAGE_PATH:
        file = discord.File(BANNER_IMAGE_PATH, filename="welcome.gif")
        embed.set_image(url="attachment://welcome.gif")
    if file:
        await channel.send(embed=embed, file=file, view=WelcomeView())
    # render button
    await channel.send(embed=embed, view=WelcomeView())
    await ctx.send("Posted the onboarding card.", delete_after=5)

# run the bot
bot.run(TOKEN)