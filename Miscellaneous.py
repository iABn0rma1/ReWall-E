import discord
import datetime
import asyncio
import aiohttp
import random
import config
import pendulum
from discord import Spotify
from discord.ext import commands
from discord.ext.commands import BucketType
from discord.ext.commands.errors import MissingRequiredArgument, CommandOnCooldown

class Miscellaneous(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["toss", "flip"])
    @commands.guild_only()
    async def coinflip(self, ctx):
        """> Coin flip!"""
        await ctx.send(f"**{ctx.author.name}** flipped a coin and got **{random.choice(['Heads','Tails'])}**!")

    @commands.command()
    async def spotify(self, ctx, user: discord.Member = None):
        """> Get info of spotify song [user] is listening to"""
        user = user or ctx.author
        for activity in user.activities:
            if isinstance(activity, Spotify):
                embed = discord.Embed(color=activity.color)
                embed.title = f'{user.name} is listening to {activity.title}'
                embed.set_thumbnail(url=activity.album_cover_url)
                embed.description = f"Song Name: {activity.title}\nSong Artist: {activity.artist}\nSong Album: {activity.album}\
                    \nSong Lenght: {pendulum.duration(seconds=activity.duration.total_seconds()).in_words(locale='en')}"
            await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 690, BucketType.user)
    async def report(self, ctx, *args):
        """> Reports to the developer"""
        if args == []:
            await ctx.send('Please give me a report to send. This has been flagged.')
            return
        counter = random.randint(1, 1000)
        channel = self.bot.get_channel(config.LOG_ID)
        x = ' '.join(map(str, args))
        if x == None:
            await ctx.send('You going to report nothing?')
        else:
            embed = discord.Embed(
                title=f'Report #{counter}',
                color=discord.Color.from_rgb(250, 0, 0),
                description=f'The user `{ctx.author}` from the guild `{ctx.guild}` has sent a report!'
            )
            embed.add_field(name='Query?', value=f'{x}')
            embed.set_footer(text=f'User ID: {ctx.author.id}\nGuild ID: {ctx.guild.id}')
            await channel.send(embed=embed)
            await ctx.send(f'Your report has successfully been sent!')

    @commands.command(aliases=["latency"])
    async def ping(self, ctx):
        """> See bot's latency to discord"""
        ping = round(self.bot.latency * 1000)
        await ctx.send(f":ping_pong: Pong   |   {ping}ms")

async def setup(bot):
    await bot.add_cog(Miscellaneous(bot))
