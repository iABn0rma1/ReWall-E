import re
import discord
from discord.ext import commands
import random
import asyncio
import config
import datetime
import re

time_regex = re.compile("(?:(\d{1,5})(h|s|m|d))+?")
time_dict = {'h': 3600, 's': 1, 'm': 60, 'd': 86400}


def convert(argument):
    args = argument.lower().split(" ")
    matches = re.findall(time_regex, "".join(args))
    time = 0
    for key, value in matches:
        try:
            time += time_dict[value] * float(key)
        except KeyError:
            raise commands.BadArgument(f"{value} is an invalid time key! `h|m|s|d` are valid time keys")
        except ValueError:
            raise commands.BadArgument(f"{key} isn't even a number dummy")
    return time


class Giveaway(commands.Cog, name="Giveaway Category"):
    """> Commands for Hosting Giveaways"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["rollagain", "rr"], hidden=True)
    @commands.has_any_role('Moderator', 'Mod', 'Admin', 'Owner')
    async def reroll(self, ctx, message: discord.Message):
        """> re-rolls the specified giveaway in the current channel"""
        giveawaymsg = await ctx.fetch_message(message.id)
        users = await giveawaymsg.reactions[0].users().flatten()
        users.pop(users.index(ctx.guild.me))
        users.pop(users.index(ctx.author))

        winner = random.choice(users)
        new_users = []
        for x in users:
            if x != self.bot.user and x != ctx.author:
                new_users.append(x)
                users = new_users
        await ctx.send(f'__**{winner.mention} has won the Giveaway!**__')
        embed = discord.Embed(title="🎉 __**GIVEAWAY ENDED**__ 🎉",
                              description=f"__*Winner(s):*__\n• {winner}", colour=discord.Colour.from_rgb(250, 0, 0))

        embed.set_author(name=f"Hosted by: {giveawaymsg.author.name}", icon_url=ctx.author.avatar_url)

        embed.timestamp = datetime.datetime.utcnow() + datetime.timedelta(seconds=0)

        await message.edit(embed=embed)

    @commands.command(
        brief="> Interactively Sets Up the Giveaway", hidden=True,
        aliases=["ga", "giveaway", 'giveawaystart', 'startgv', 'gvstart'])
    @commands.guild_only()
    @commands.is_owner()
    @commands.has_permissions(manage_messages=True)
    async def startgiveaway(self, ctx):
        """`Creates a giveaway (interactive setup)`"""

        # Check if the user replying to the bot
        # Is the author
        def is_me(m):
            return m.author == ctx.author

        await ctx.send(
            "Aight lets start setting up the giveaway\nWhat channel will it be in?")  # Starts setting up the giveaway
        while True:
            try:
                msg = await self.bot.wait_for('message', timeout=60.0, check=is_me)
                channel_converter = discord.ext.commands.TextChannelConverter()  # Converts the channel mentioned
                channel = await channel_converter.convert(ctx, msg.content)
            except commands.BadArgument:
                await ctx.send("Bruh that channel doesn't even exist. Try again")
                # Raises exception made in the TimeConverter
            else:
                await ctx.send(
                    f"Great, the giveaway will start in {channel.mention}\nBut how many winners will there be? (Choose between `1-25`)")
                msg = await self.bot.wait_for('message', timeout=60.0, check=is_me)
                break
        while True:
            try:
                s = random.sample(range(1000000), k=25)
                bro = int(msg.content)  # Converts the number of winners into a number/int for later on
            except ValueError:
                await ctx.send(
                    "You really thought that was a number? Try again")  # Errors if the amount of winners isn't a number
                msg = await self.bot.wait_for('message', timeout=60.0, check=is_me)
            else:
                await ctx.send(
                    f"Ok there will be {bro} winners\nHow much time should this giveaway last for?\nPlease say one of these options: `#d|#h|#m|#s`")
                msg2 = await self.bot.wait_for('message', timeout=60.0, check=is_me)
                break
        while True:
            try:
                time = int(convert(msg2.content))
                # convert is the word from the TimeConverter Function at the top of the file, to convert the x amount of d|h|m|s
            except ValueError:
                await ctx.send("That isn't an option. Please choose x amount of `d|h|m|s`")
                msg = await self.bot.wait_for('message', timeout=60.0, check=is_me)
            else:
                break
        await ctx.send(f"Aight, the giveaway will last {time}s\nNow what are you giving away?")
        msg = await self.bot.wait_for('message', timeout=60.0, check=is_me)
        prize = msg.content  # The item we're giving away
        await ctx.send(f"Aight cool, the giveaway is now starting in :\n{channel.mention}")

        await asyncio.sleep(1.75)

        giveawayembed = discord.Embed(
            description=f"__*REACT With 🎉 to participate!*__",
            colour=discord.Colour.from_rgb(250,0,0))

        giveawayembed.add_field(
            name="_*Prize:*_",
            value=f"🏆 {prize}")
        giveawayembed.add_field(
            name=f"_*Lasts:*_",
            value=f"__**{time}s**__")

        giveawayembed.set_author(
            name=f"Hosted by: {ctx.author.name}",
            icon_url=ctx.author.avatar_url)

        giveawayembed.set_footer(
            text=f"{bro} Winners | Ends ")

        giveawayembed.timestamp = datetime.datetime.utcnow() + datetime.timedelta(seconds=time)

        sendgiveaway = await channel.send(
            content="🎉 **New Giveaway!** 🎉",
            embed=giveawayembed)
        await sendgiveaway.add_reaction('🎉')

        for number in range(int(time), 0, -5):
            # Edits the original giveaway embed to create a countdown for the timer
            timecounter = discord.Embed(
                description=f"__*REACT With 🎉 to participate!*__\n\n",
                colour=discord.Colour.from_rgb(250,0,0))

            timecounter.set_footer(text=f"{bro} Winner(s) | Ends ")

            timecounter.set_author(name=f"Hosted by: {ctx.author.name}", icon_url=ctx.author.avatar_url)

            timecounter.add_field(name="_*Prize:*_", value=f"🏆 {prize}")
            timecounter.add_field(name="_*Time Left:*_", value=f"_*{number}s*_")

            timecounter.timestamp = datetime.datetime.utcnow() + datetime.timedelta(seconds=number)

            await sendgiveaway.edit(embed=timecounter)
            await asyncio.sleep(5)

        sendgiveaway = await channel.fetch_message(sendgiveaway.id)
        for reaction in sendgiveaway.reactions:
            if reaction.emoji == '🎉':
                # Checks for the users that reacted to 🎉
                message = await channel.fetch_message(sendgiveaway.id)
                users = await message.reactions[0].users().flatten()
                users.pop(users.index(ctx.guild.me))
                try:
                    users.pop(users.index(ctx.author))
                except:
                    pass
                if len(users) == 0:
                    await channel.send("No winner was decided")
                    return
                list_of_string = []
                winners = random.sample(users, k=bro)
                for each in winners:
                    astring = str(each)
                    list_of_string.append(astring)
                    bruh = "\n• ".join(map(str, winners))
                    embed = discord.Embed(title="🎉 __**GIVEAWAY ENDED**__ 🎉",
                                          description=f"__*Winner(s):*__\n• {bruh}", colour=discord.Colour.from_rgb(250,0,0))

                    embed.add_field(name="Prize:", value=f"🏆 {prize}")

                    embed.set_author(name=f"Hosted by: {ctx.author.name}", icon_url=ctx.author.avatar_url)

                    embed.set_footer(text=f"{bro} Winners | Ended ")

                    embed.timestamp = datetime.datetime.utcnow() + datetime.timedelta(seconds=number)

                    await sendgiveaway.edit(embed=embed)
        await channel.send(f"🎉 Congratulations {','.join([x.mention for x in winners])} you won: **{prize}** 🎉\
        \nPlease contact {ctx.author.mention} about your prize.")

async def GetGiveawayMessage(bot, ctx, contentOne="Test Message", timeout=90.0):
    await ctx.send(f"{contentOne}")
    try:
        msg = await bot.wait_for('message', timeout=timeout, check=None)
        if msg:
            return msg.content
    except asyncio.TimeoutError:
        return False

def setup(bot):
    bot.add_cog(Giveaway(bot))