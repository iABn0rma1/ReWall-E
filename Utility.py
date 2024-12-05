import sys
import psutil
import asyncio
import discord
import default
import datetime
import config
from publicflags import UserFlags
# from paginator import Pages
from collections import Counter
from discord.ext import commands, tasks
from discord.utils import escape_markdown

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _get_ram_usage(self):
        memory = psutil.virtual_memory()
        total_memory = round(memory.total / 1000000000, 2)
        available_memory = round(memory.available / 1000000000, 2)
        memory_used = round(total_memory - available_memory, 2)
        memory_percent = round(total_memory / available_memory, 2)

        return "{0}% - {1}GB / {2}GB used ({3}GB available)".format(memory_percent, memory_used, 
                                                                    total_memory, available_memory)

    @commands.command(aliases=["botinfo"])
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def about(self, ctx):
        """> Displays basic information about the bot """

        version = '01.10'

        channel_types = Counter(type(c) for c in self.bot.get_all_channels())

        te = len([c for c in set(self.bot.walk_commands()) if c.cog_name == "Owner"])
        se = len([c for c in set(self.bot.walk_commands()) if c.cog_name == "Staff"])
        xd = len([c for c in set(self.bot.walk_commands())])
        ts = se + te
        totcmd = xd - ts

        platform = sys.platform
        ver = sys.version
        api = sys.api_version
        disc = discord.__version__

        ownerID = self.bot.get_user(config.OWNER_ID)

        CPU_Usage = str(psutil.cpu_percent(None, False)) + "%"
        RAM_Usage = self._get_ram_usage()

        embed = discord.Embed(colour = discord.Colour.from_rgb(250, 0, 0))
        embed.set_author(name=self.bot.user.name,
                         icon_url=f"https://images-ext-1.discordapp.net/external/QSCWqyN--Xd8qkW0GwIrRk2UopjvQ87CNOw_foaJ6Tk/%3Fsize%3D1024/https/cdn.discordapp.com/avatars/785775388286517249/96abf0b9ae176acb29a301180095fd30.png")
        embed.description = f"""
            __**About:**__\
            \n**Developer:** {escape_markdown(str(ownerID), as_needed=True)}\
            \n**Bot version:** {version}\n**Platform:** {platform}\n**Commands:** {totcmd}\
            \n**Prefix:** My prefix is `%`\n**Created on:** {default.date(self.bot.user.created_at)}\
            ({self.bot.user.created_at})
        """

        embed.add_field(name="Python Version", value=ver)
        embed.add_field(name="‎", value="‎", inline=True)
        embed.add_field(name="C API Version", value=api, inline=True)

        embed.add_field(name="Total CPU Usage", value=CPU_Usage)
        embed.add_field(name="‎", value="‎", inline=True)
        embed.add_field(name="Total RAM Usage", value=RAM_Usage, inline=True)

        embed.set_thumbnail(url=f"{ownerID.avatar.url}")
        embed.set_footer(text= f'Made with Discord.py {disc}',
                         icon_url='https://images-ext-1.discordapp.net/external/h2NyqrWmotzW-h7JoyZqQ7dEGoXIQeZ4eqlHimj1pLk/https/i.imgur.com/6pg6Xv4.png')

        try:
            embed.set_image(url=ctx.guild.banner_url_as(format='png'))
        except:
            pass

        await ctx.send(embed=embed)

    @commands.command(aliases=['pfp', 'av'])
    @commands.cooldown(1, 5, commands.BucketType.member)
    @commands.guild_only()
    async def avatar(self, ctx, user: discord.User = None):
        """> Displays what avatar user is using"""
        user = user or ctx.author
        if user is self.bot.user:
            embed = discord.Embed(colour=discord.Colour.from_rgb(250, 0, 0),
                                  title=f'{self.bot.user.name}\'s Profile Picture!')
            embed.set_image(url=self.bot.user.avatar.url if user.avatar else user.default_avatar.url)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(colour=discord.Colour.from_rgb(250, 0, 0),
                                  title=f'{user}\'s Profile Picture!')
            embed.set_image(url = user.avatar.url if user.avatar else user.default_avatar.url)
            await ctx.send(embed=embed)

    @commands.command(aliases=["si", 'server'])
    @commands.guild_only()
    async def serverinfo(self, ctx):
        """> Overview about the information of a server"""
        guild = ctx.guild
        error_404 = "https://cdnl.iconscout.com/lottie/premium/thumb/404-error-page-animation-download-in-lottie-json-gif-static-svg-file-formats--loading-not-found-the-ultimate-pack-design-development-animations-3299952.gif"

        # Guild description and icon/banner
        description = guild.description or "No description available."
        icon_url = guild.icon.url if guild.icon else error_404
        banner_url = guild.banner.url if guild.banner else error_404

        # MFA level
        mfa_status = "Enabled" if guild.mfa_level > 0 else "Disabled"

        # Member counts
        unique_online = sum(1 for m in guild.members if m.status is discord.Status.online and not isinstance(m.activity, discord.Streaming))
        unique_idle = sum(1 for m in guild.members if m.status is discord.Status.idle and not isinstance(m.activity, discord.Streaming))
        unique_dnd = sum(1 for m in guild.members if m.status is discord.Status.dnd and not isinstance(m.activity, discord.Streaming))
        unique_streaming = sum(1 for m in guild.members if isinstance(m.activity, discord.Streaming))
        unique_offline = len(guild.members) - (unique_online + unique_idle + unique_dnd + unique_streaming)

        total_members = len(guild.members)
        human_count = sum(1 for m in guild.members if not m.bot)
        bot_count = total_members - human_count

        # Nitro boost info
        nitro_msg = f"This server has **{guild.premium_subscription_count}** boosts."

        # Embed construction
        embed = discord.Embed(
            title="Server Information",
            description=description,
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=icon_url)
        embed.set_image(url=banner_url)

        # General information field
        embed.add_field(
            name="__**General Information**__",
            value=(
                f"**Guild Name:** {guild.name}\n"
                f"**Guild ID:** {guild.id}\n"
                f"**Guild Owner:** {guild.owner}\n"
                f"**Created At:** {guild.created_at.strftime('%A %d %B %Y, %H:%M')}\n"
                f"**MFA Status:** {mfa_status}\n"
                f"**Verification Level:** {guild.verification_level.name.capitalize()}"
            ),
            inline=True
        )

        # Members and channels field
        embed.add_field(
            name="__**Members and Channels**__",
            value=(
                f"<:online:783012763638824992> **Online:** {unique_online}\n"
                f"<:idle:783012763861516339> **Idle:** {unique_idle}\n"
                f"<:dnd:783012763932819496> **Do Not Disturb:** {unique_dnd}\n"
                f"<:stream:783012763617591400> **Streaming:** {unique_streaming}\n"
                f"<:offline:783012764180152391> **Offline:** {unique_offline}\n"
                f"**Total Members:** {total_members} ({human_count} Humans / {bot_count} Bots)\n"
                f"**Text Channels:** {len(guild.text_channels)}\n"
                f"**Voice Channels:** {len(guild.voice_channels)}\n"
                f"**Roles:** {len(guild.roles)}"
            ),
            inline=True
        )

        # Server boost info
        embed.add_field(
            name="__**Server Boost Status**__",
            value=nitro_msg,
            inline=False
        )
        await ctx.send(embed=embed)

    @commands.command(name="userinfo", aliases=['ui', 'whois'])
    async def userinfo(self, ctx, user: discord.Member = None):
        """> Overview about the information of an user"""
        user = user or ctx.author

        badges = {
            'hs_brilliance': f'<:brilliance:782237533937336340>',
            'discord_employee': f'<:staff:784160633674793021>',
            'discord_partner': f'<:partner:784160633548963861>',
            'hs_events': f'<:events:784162225446191105>',
            'bug_hunter_lvl1': f'<:bughunter:784160633728925760>',
            'hs_bravery': f'<:bravery:782238095093399563>',
            'hs_balance': f'<:balance:782238156141494282>',
            'early_supporter': f'<:supporter:784160633826181140>',
            'bug_hunter_lvl2': f'<:bughunter:784160633728925760>',
            'verified_dev': f'<:verified:784160633527730186>'
        }

        badge_list = []
        flag_vals = UserFlags((await self.bot.http.get_user(user.id))['public_flags'])
        for i in badges.keys():
            if i in [*flag_vals]:
                badge_list.append(badges[i])

        if user.bot:
            bot = "Yes"
        elif not user.bot:
            bot = "No"

        if badge_list:
            discord_badges = ' '.join(badge_list)
        elif not badge_list:
            discord_badges = ''

        usercheck = ctx.guild.get_member(user.id)
        if usercheck:

            if usercheck.nick is None:
                nick = "N/A"
            else:
                nick = usercheck.nick

            status = {
                "online": f"{f'<:online_mob:784158326333112382>' if usercheck.is_on_mobile() else f'<:online:783012763638824992>'}",
                "idle": f"{f'<:idle_mob:784158326824501338>' if usercheck.is_on_mobile() else f'<:idle:783012763861516339>'}",
                "dnd": f"{f'<:dnd_mob:784158326727639070>' if usercheck.is_on_mobile() else f'<:dnd:783012763932819496>'}",
                "offline": f"<:offline:783012764180152391>"
            }

            if usercheck.activities:
                ustatus = ""
                for activity in usercheck.activities:
                    if activity.type == discord.ActivityType.streaming:
                        ustatus += f"<:stream:783012763617591400>"
            else:
                ustatus = f'{status[str(usercheck.status)]}'

            if not ustatus:
                ustatus = f'{status[str(usercheck.status)]}'

            uroles = []
            for role in usercheck.roles:
                if role.is_default():
                    continue
                uroles.append(role.mention)

            uroles.reverse()

            emb = discord.Embed(color=ctx.author.colour)
            emb.set_author(icon_url=user.avatar.url, name=f"{user.name}'s information")
            emb.add_field(name="__**Personal Info:**__",
                          value=f"**Full name:** {user} {discord_badges}\n**User ID:** {user.id}\
                          \n**Account created:** {user.created_at.__format__('%A %d %B %Y, %H:%M')}\
                          \n**Bot:** {bot}\n**Avatar URL:** [Click here]({user.avatar.url})",
                          inline=False)
            emb.add_field(name="__**Activity Status:**__",
                          value=f"**Status:** {ustatus}\n**Activity status:** {default.member_activity(usercheck)}",
                          inline=False)
            emb.add_field(name="__**Server Info:**__",
                          value=f"**Nickname:** {user.nick}\n**Joined at:** {default.date(usercheck.joined_at)}\
                          \n**Roles: ({len(usercheck.roles) - 1}) **" + ", ".join(
                              uroles), inline=True)
            emb.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)

            await ctx.send(embed=emb)

    @commands.command(aliases=['guildstaff'])
    @commands.cooldown(1, 5, commands.BucketType.member)
    @commands.guild_only()
    async def serverstaff(self, ctx):
        """> Check which server staff are online in the server"""
        message = ""
        online, idle, dnd, offline = [], [], [], []

        for user in ctx.guild.members:
            if ctx.channel.permissions_for(user).kick_members or \
                    ctx.channel.permissions_for(user).ban_members:
                if not user.bot and user.status is discord.Status.online:
                    online.append(f"**{user}**")
                if not user.bot and user.status is discord.Status.idle:
                    idle.append(f"**{user}**")
                if not user.bot and user.status is discord.Status.dnd:
                    dnd.append(f"**{user}**")
                if not user.bot and user.status is discord.Status.offline:
                    offline.append(f"**{user}**")

        if online:
            message += f"<:online:783012763638824992> {', '.join(online)}\n"
        if idle:
            message += f"<:idle:783012763861516339> {', '.join(idle)}\n"
        if dnd:
            message += f"<:dnd:783012763932819496> {', '.join(dnd)}\n"
        if offline:
            message += f"<:offline:783012764180152391> {', '.join(offline)}\n"

        e = discord.Embed(color=discord.Colour.from_rgb(250,0,0), title=f"{ctx.guild.name} mods",
                          description="This lists everyone who can ban and/or kick.")
        e.add_field(name="Server Staff List:", value=message)

        await ctx.send(embed=e)

    @commands.command(brief='Privacy policy', aliases=['pp', 'policy', 'privacypolicy'])
    async def privacy(self, ctx):
        e = discord.Embed(color=discord.Color.blurple(), title=f"{self.bot.user} Privacy Policy's")
        e.add_field(name='What data is being stored?', value="No data of you is being stored as of now", inline=False)
        e.add_field(name='What should I do if I have any concerns?', value=f"You can shoot a direct message to **{ctx.guild.owner}** or email us at `amanbarthwal0110@gmail.com`")
        await ctx.send(embed=e)

    @commands.command(name='time', brief='Displays Bot Owner\'s time')
    async def time(self, ctx):
        time = datetime.datetime.now()
        await ctx.send(f"Current <@{config.OWNER_ID}>'s time is: {time.strftime('%H:%M')}\
            \nCET (Central European Time)", allowed_mentions=discord.AllowedMentions(users=False))

    @commands.command()
    async def lem(self, ctx):
        """Lists all available emotes in the server"""
        
        # Get the server (guild) from the context
        guild = ctx.guild
        
        # Check if the guild has any custom emotes
        if guild.emojis:
            emote_list = "\n".join([f"{emote.name}: {emote.url}" for emote in guild.emojis])
            await ctx.send(f"Here are the available emotes:\n{emote_list}")
        else:
            await ctx.send("This server has no custom emotes.")

    @commands.command(aliases=['se', 'emotes'])
    @commands.cooldown(1, 5, commands.BucketType.member)
    @commands.guild_only()
    async def serveremotes(self, ctx):
        """> Get a list of all the emotes in the server"""

        _all = []
        for num, e in enumerate(ctx.guild.emojis, start=0):
            _all.append(f"`[{num + 1}]` {e} **{e.name}** | {e.id}\n")

        if len(_all) == 0:
            return await ctx.send(f"<:xmark:784187150542569503> Server has no emotes!")

        paginator = Pages(ctx,
                          title=f"{ctx.guild.name} emotes list",
                          entries=_all,
                          thumbnail=None,
                          per_page=15,
                          embed_color=discord.Colour.from_rgb(250,0,0),
                          show_entry_count=True,
                          author=ctx.author)
        await paginator.paginate()

async def setup(bot):
    await bot.add_cog(Utility(bot))