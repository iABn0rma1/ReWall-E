import timeago as timesince
import discord
import time
import traceback
import json

from Nullify import clean

#from db import emotes

def timeago(target):
    return timesince.format(target)

def timetext(name):
    return f"{name}_{int(time.time())}.txt"

def date(target, clock=True):
    if clock is False:
        return target.strftime("%d %B %Y")
    return target.strftime("%d %B %Y, %H:%M")

def responsible(target, reason):
    responsible = f"[ Mod: {target} ]"
    if reason is None:
        return f"{responsible} no reason."
    return f"{responsible} {reason}"

def traceback_maker(err, advance: bool = True):
    _traceback = ''.join(traceback.format_tb(err.__traceback__))
    error = ('```py\n{1}{0}: {2}\n```').format(type(err).__name__, _traceback, err)
    return error if advance else f"{type(err).__name__}: {err}"

def error_send(err_type, err_msg):
    msg = f"""
Error type: **{err_type}**
Error message: ```py
{err_msg}```"""
    return msg

def next_level(ctx):
    if str(ctx.guild.premium_tier) == "0":
        count = int(2 - ctx.guild.premium_subscription_count)
        txt = f'Next level in **{count}** boosts'
        return txt

    if str(ctx.guild.premium_tier) == "1":
        count = int(15 - ctx.guild.premium_subscription_count)
        txt = f'Next level in **{count}** boosts'
        return txt

    if str(ctx.guild.premium_tier) == "2":
        count = int(30 - ctx.guild.premium_subscription_count)
        txt = f'Next level in **{count}** boosts'
        return txt

    if str(ctx.guild.premium_tier) == "3":
        txt = 'Guild is boosted to its max level'
        return txt


def member_activity(member):

    if not member.activity or not member.activities:
        return "N/A"

    message = "\n"

    for activity in member.activities:

        if activity.type == discord.ActivityType.custom:
            message += f"• "
            if activity.emoji:
                if activity.emoji.is_custom_emoji():
                    message += f'(Emoji) '
                else:
                    message += f"{activity.emoji} "
            if activity.name:
                message += f"{clean(activity.name)}"
            message += "\n"

        elif activity.type == discord.ActivityType.playing:


            message += f"<:rich_presence:784181544859729940> Playing **{clean(activity.name)}** "
            if not isinstance(activity, discord.Game):
                
                if activity.details:
                    message += f"**| {activity.details}** "
                if activity.state:
                    message += f"**| {activity.state}** "
                message += "\n"
            else:
                message += "\n"

        elif activity.type == discord.ActivityType.streaming:
            try:
                if activity.name == activity.platform:
                    act = "Twitch"
                elif activity.name != activity.platform:
                    act = activity.platform
                message += f"<:streamicon:783009153298989086> Streaming **[{activity.name}]({activity.url})** on **{act}**\n"
            except AttributeError:
                message += f"<:streamicon:783009153298989086> Shit broke while trying to figure out streaming details."

        elif activity.type == discord.ActivityType.watching:
            message += f"<:rich_presence:784181544859729940> Watching **{clean(activity.name)}**\n"

        elif activity.type == discord.ActivityType.listening:

            if isinstance(activity, discord.Spotify):
                url = f"https://open.spotify.com/track/{activity.track_id}"
                message += f"<:music_presence:784181544427716659> Listening to **[{activity.title}]({url})** by **{', '.join(activity.artists)}** "
                if activity.album and not activity.album == activity.title:
                    message += f", album — **{activity.album}** "
                message += "\n"
            else:
                message += f"<:music_presence:784181544427716659> Listening to **{clean(activity.name)}**\n"
        
        elif activity.type == 5:
            if activity.url is None:
                message += f"<:rich_presence:784181544859729940> Competing in **{clean(activity.name)}**\n"
                if activity.emoji:
                    message += f" {activity.emoji}\n"
            elif activity.url is not None:
                message += f"<:rich_presence:784181544859729940> Competing in **[{clean(activity.name)}]({activity.url})**\n"
                if activity.emoji:
                    message += f" {activity.emoji}\n"

    return message

async def prettyResults(ctx, filename: str = "Results", resultmsg: str = "Here's the results:", loop=None):
    """ A prettier way to show loop results """
    if not loop:
        return await ctx.send("The result was empty...")

    pretty = "\r\n".join([f"[{str(num).zfill(2)}] {data}" for num, data in enumerate(loop, start=1)])

    if len(loop) < 15:
        return await ctx.send(f"{resultmsg}```ini\n{pretty}```")

    data = BytesIO(pretty.encode('utf-8'))
    await ctx.send(
        content=resultmsg,
        file=discord.File(data, filename=timetext(filename.title()))
    )

def color_picker(color):
    with open('db/settings.json', 'r') as f:
        data = json.load(f)
    
    return data[color]
