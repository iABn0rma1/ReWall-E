import asyncio
from typing import List
import discord
from discord.ext import commands


def chunks(parts, size):
    """Yield successive size-sized chunks from parts."""
    for i in range(0, len(parts), size):
        yield parts[i:i + size]


def helper(ctx) -> List[discord.Embed]:
    """Displays all commands"""

    cmds_ = []
    cogs = ctx.bot.cogs
    for cog_name, cog in cogs.items():
        commands_ = cog.get_commands()
        commands_ = [cmd for cmd in commands_ if not cmd.hidden]
        for chunk in chunks(commands_, 10):
            embed = discord.Embed(color=discord.Colour.from_rgb(250,0,0))
            embed.set_author(name=f"{cog_name} Commands ({len(commands_)})")
            embed.description = cog.__doc__
            for cmd in chunk:
                embed.add_field(name=f"{cmd.name} {cmd.signature}", value=cmd.help or "No description", inline=False)
            cmds_.append(embed)

    for n, embed in enumerate(cmds_):
        embed.set_footer(
            text=f'Page {n + 1} of {len(cmds_)} | Type "{ctx.prefix}help <command>" for more information'
        )
    return cmds_


def cog_helper(cog: commands.Cog) -> List[discord.Embed]:
    """Displays commands from a cog"""

    name = cog.__class__.__name__
    cmds_ = []
    commands_ = [cmd for cmd in cog.get_commands() if not cmd.hidden]
    if not commands_:
        embed = discord.Embed(
            color=discord.Colour.from_rgb(250,0,0),
            description=f"No visible commands in {name}.",
        ).set_author(name="ERROR 🚫")
        return [embed]

    for chunk in chunks(commands_, 10):
        embed = discord.Embed(color=discord.Colour.from_rgb(250,0,0))
        embed.set_author(name=f"{name} Commands")
        embed.description = cog.__doc__ or "No description available."
        for cmd in chunk:
            embed.add_field(name=f"{cmd.name} {cmd.signature}", value=cmd.help or "No description", inline=False)
        cmds_.append(embed)

    for n, embed in enumerate(cmds_):
        embed.set_footer(text=f"Page {n + 1} of {len(cmds_)}")
    return cmds_


def command_helper(command: commands.Command) -> List[discord.Embed]:
    """Displays a command and its subcommands"""

    subcommands = getattr(command, "commands", [])
    if not subcommands:
        embed = discord.Embed(color=discord.Colour.from_rgb(250,0,0))
        embed.set_author(name=f"{command.name} {command.signature}")
        embed.description = command.help or "No description available."
        return [embed]

    embeds = []
    for chunk in chunks(subcommands, 10):
        embed = discord.Embed(color=discord.Colour.from_rgb(250,0,0))
        embed.set_author(name=f"{command.name} Subcommands")
        embed.description = command.help or "No description available."
        for subcmd in chunk:
            embed.add_field(name=f"{subcmd.name} {subcmd.signature}", value=subcmd.help or "No description", inline=False)
        embeds.append(embed)

    for n, embed in enumerate(embeds):
        embed.set_footer(text=f"Page {n + 1} of {len(embeds)}")
    return embeds


async def paginate(ctx, embeds: List[discord.Embed]) -> None:
    """Paginator for multiple embeds"""
    if not embeds:
        await ctx.send("Nothing to display!")
        return

    current = 0
    message = await ctx.send(embed=embeds[current])

    if len(embeds) == 1:
        return

    reactions = ["⏮️", "◀️", "▶️", "⏭️", "⏹️"]
    for reaction in reactions:
        await message.add_reaction(reaction)

    def check(reaction, user):
        return user == ctx.author and reaction.message.id == message.id and str(reaction.emoji) in reactions

    while True:
        try:
            reaction, _ = await ctx.bot.wait_for("reaction_add", timeout=69, check=check)

            if str(reaction.emoji) == "⏮️":
                current = 0
            elif str(reaction.emoji) == "◀️":
                current = max(current - 1, 0)
            elif str(reaction.emoji) == "▶️":
                current = min(current + 1, len(embeds) - 1)
            elif str(reaction.emoji) == "⏭️":
                current = len(embeds) - 1
            elif str(reaction.emoji) == "⏹️":
                await message.clear_reactions()
                break

            await message.edit(embed=embeds[current])
            await message.remove_reaction(reaction, ctx.author)

        except asyncio.TimeoutError:
            await message.clear_reactions()
            break


class Help(commands.Cog):
    """Help command"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["h"], hidden=True)
    async def help(self, ctx, *, command: str = None):
        if not command:
            await paginate(ctx, helper(ctx))
        else:
            obj = ctx.bot.get_cog(command) or ctx.bot.get_command(command)
            if not obj:
                await ctx.send(f'No command or category found for "{command}".')
                return
            if isinstance(obj, commands.Cog):
                await paginate(ctx, cog_helper(obj))
            elif isinstance(obj, commands.Command):
                await paginate(ctx, command_helper(obj))


async def setup(bot):
    await bot.add_cog(Help(bot))
