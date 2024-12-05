from keep_alive import keep_alive

import discord
import DiscordUtils
import asyncio
import time
import datetime
from io import BytesIO
from PIL import Image, ImageDraw
import config
from discord.ext import commands, tasks

TOKEN = config.BOT_TOKEN

client = commands.Bot(command_prefix=commands.when_mentioned_or('%'), intents=discord.Intents.all(),
                      description="BOT", pm_help=True, case_insensitive=True,
                      owner_id=config.OWNER_ID
                      )
tracker = DiscordUtils.InviteTracker(client)

client._uptime = None

client.remove_command("help")

@client.event
async def on_connect():
    if client._uptime is None:
        print(f"Connected to Discord. Getting ready...")
        print(f'-----------------------------')

@client.event
async def on_ready():
    change_status.start()
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('--------------------------------------')
    client.starttime = time.time()
    print(client.starttime)
    print(f'--------------------------------------')
    print(f'Bot ready!')
    print(f"Successfully logged in as: {client.user.name}")
    print(f"ID: {client.user.id}")
    print(f"Total servers: {len(client.guilds)}")
    print(f"Total Members: {len(client.users)}")
    print(f"Discord.py version: {discord.__version__}")
    print(f'--------------------------------------')
    await tracker.cache_invites()
    for extension in config.EXTENSIONS:
        try:
            await client.load_extension(extension)
        except Exception as e:
            print(e)

@tasks.loop(seconds=10)
async def change_status():
    await client.change_presence(activity=discord.Game(name="%help"), 
                                 status=discord.Status.idle)
    await asyncio.sleep(10)
    await client.change_presence(activity=discord.Activity
                                 (type=discord.ActivityType.listening, name="DM for help"),
                                 status=discord.Status.idle)
    await asyncio.sleep(10)

import aiohttp
from io import BytesIO
from PIL import Image, ImageDraw
import discord

@client.event
async def on_member_join(member):
    welcome = Image.open("welcome.png")
    AVATAR_SIZE = 256

    # Fetch the avatar image
    async with aiohttp.ClientSession() as session:
        async with session.get(member.avatar.url) as response:
            if response.status != 200:
                print("Failed to fetch avatar image.")
                return
            avatar_data = BytesIO(await response.read())

    # Process the avatar image
    avatar_image = Image.open(avatar_data).convert("RGBA")
    avatar_image = avatar_image.resize((AVATAR_SIZE, AVATAR_SIZE))

    # Create a circular mask for the avatar
    circle_image = Image.new("L", (AVATAR_SIZE, AVATAR_SIZE), 0)
    circle_draw = ImageDraw.Draw(circle_image)
    circle_draw.ellipse((0, 0, AVATAR_SIZE, AVATAR_SIZE), fill=255)

    # Apply the circular mask
    circular_avatar = Image.new("RGBA", (AVATAR_SIZE, AVATAR_SIZE))
    circular_avatar.paste(avatar_image, (0, 0), mask=circle_image)

    # Paste the circular avatar onto the welcome image
    welcome.paste(circular_avatar, (460, 45), circular_avatar)

    # Save the final image to a BytesIO object
    output = BytesIO()
    welcome.save(output, format="PNG")
    output.seek(0)  # Reset stream position

    # Fetch the inviter (this assumes you have a `tracker` object set up to fetch the inviter)
    inviter = await tracker.fetch_inviter(member)

    # Create the embed message
    embed = discord.Embed(
        color=discord.Color.from_rgb(250, 0, 0),
        description=f"<a:DN_Wlcm:720229315723132950> Welcome to {member.guild.name},\
                      where nemesis thrives and the weak die.\
                      \n<a:DN_ThisR:719866047930302464> Be sure to read <#{config.RULES_ID}>\
                      \n<a:DN_ThisR:719866047930302464> and claim your roles from <#{config.ROLES_ID}>"
    )
    embed.set_author(
        name=f"Namaste {member.name}",
        icon_url=member.avatar.url
    )

    # Set the footer with inviter info and total member count
    embed.set_footer(text=f"Invited by: {inviter} | Total Members: {len(list(member.guild.members))}")

    # Get the channel where the welcome message should be sent
    channel = client.get_channel(config.JOIN_ID)

    # Send the embed with the in-memory image
    file = discord.File(output, filename="welcome.png")
    embed.set_image(url="attachment://welcome.png")
    await channel.send(file=file, embed=embed)

@client.event
async def on_message(message):
    if message.content.startswith(f"<@!{client.user.id}>") or message.content == f"<@!{client.user.id}>":
        await message.channel.send(f"My prefix is `%`")

    if message.channel.id == config.MEME_ID:    #memes
        await message.add_reaction(f"<:PizzaSlut:1217203161429708873>")
        # await message.add_reaction(f"<:DN_NotOk:766392304138715138>")
        # await message.add_reaction(f"<:DN_GetRekt:766549673556836384>")
        # await message.add_reaction(f"<:DN_RIP:766549674076143636>")
        # await message.add_reaction(f"<:DN_GG:786903401128001596>")
        # await message.add_reaction(f"<:DN_WTF:766549673665495071>")
        # await message.add_reaction(f"<:DN_LOL:766549673955033088>")
        # await message.add_reaction(f"<:DN_Clap:766392302884749363>")
        # await message.add_reaction(f"<:DN_LaughingWithGun:721551289670172672>")
        # await message.add_reaction(f"<:DN_PepeRevenge:719868161083834451>")

    client.channel = client.get_channel(config.LOG_ID)
    if not client.channel:
        print(f'Channel with ID {config.LOG_ID} not found.')
        await client.close()
    author = message.author
    if author == client.user:
        return
    if type(message.channel) is discord.DMChannel:
        # for the purpose of nicknames, if anys
        for server in client.guilds:
            member = server.get_member(author.id)
            if member:
                author = member
            break
        embed = discord.Embed(title="Mod Mail 📬", description=message.content,
                              colour=discord.Colour.from_rgb(250,0,0))
        if isinstance(author, discord.Member) and author.nick:
            author_name = f'{author.nick} ({author})'
        else:
            author_name = str(author)
        embed.timestamp=datetime.datetime.utcnow()
        embed.set_author(name=author_name)#,
                        #  icon_url=author.avatar_url if author.avatar else author.default_avatar_url)
        to_send = f'{author.mention}'
        if message.attachments:
            attachment_urls = []
            for attachment in message.attachments:
                attachment_urls.append(f'[{attachment.filename}]({attachment.url}) '
                                       f'({attachment.size} bytes)')
            attachment_msg = '\N{BULLET} ' + '\n\N{BULLET} '.join(attachment_urls)
            embed.add_field(name='Attachments', value=attachment_msg, inline=False)
        await client.channel.send(to_send, embed=embed)
        client.last_id = author.id
    await client.process_commands(message)

keep_alive()
client.run(f"{TOKEN}")