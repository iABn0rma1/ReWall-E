import discord
import re
import shlex
import argparse
import asyncio
import btime
import datetime
import random
import default
from typing import Optional
from discord.utils import escape_markdown
from checks import MemberID, BannedMember
from default import responsible, timetext, date
from discord.ext import commands, tasks
from discord.ext.commands import BucketType

class Arguments(argparse.ArgumentParser):
    def error(self, message):
        raise RuntimeError(message)

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    async def do_removal(self, ctx, limit, predicate, *, before=None, after=None):
        if limit > 2000:
            return await ctx.send("You can purge maximum amount of 2000 messages!")

        if before is None:
            before = ctx.message
        else:
            before = discord.Object(id=before)

        if after is not None:
            after = discord.Object(id=after)
        # if predicate is True:
        #     msgs = []
        #     for message in await ctx.channel.history(limit=limit).flatten():
        #         msgs.append(f"[{message.created_at}] {message.author} - {message.content}\n")
        #     msgs.reverse()
        #     msghis = "".join(msgs)

        try:
            deleted = await ctx.channel.purge(limit=limit, before=before, after=after, check=predicate)
            # if predicate is True:
            #     await self.log_delete(ctx, data=discord.File(BytesIO(("".join(msgs)).encode("utf-8")), filename=f"{ctx.message.id}.txt"), messages=len(deleted))
        except discord.Forbidden as e:
            return await ctx.send("No permissions")
        except discord.HTTPException as e:
            return await ctx.send(f"Looks like you got an error: {e}")

        deleted = len(deleted)
        if deleted == 1:
            messages = f"<:RS_bin:781641561867812905> Deleted **1** message"
        elif deleted > 1:
            messages = f"<:RS_bin:781641561867812905> Deleted **{deleted}** messages"
        elif deleted == 0:
            messages = f"Was unable to delete any messages"

        to_send = '\n'.join(messages)

        if len(to_send) > 2000:

            text = f"<:RS_bin:781641561867812905> Removed `{deleted}` messages"
            await ctx.channel.send(text, delete_after=5)
        else:
            e = discord.Embed(colour=discord.Colour.from_rgb(250,0,0))
            e.description = f"{messages}"
            await ctx.channel.send(embed=e, delete_after=5)

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True, manage_messages=True)
    async def kick(self, ctx, members: commands.Greedy[discord.Member], *, reason: str = None):
        """> Kicks member from server.
        You can also provide multiple members to kick.
        """
        if not members:
            return await ctx.send(f"<:xmark:784187150542569503> | You're missing an argument - **members**")

        error = '\n'
        try:
            total = len(members)
            if total > 10:
                return await ctx.send("You can kick only 10 members at once!")

            failed = 0
            failed_list = []
            success_list = []
            for member in members:
                if member == ctx.author:
                    failed += 1
                    failed_list.append(f"{member.mention} ({member.id}) - you are the member?")
                    continue
                if member.top_role.position >= ctx.author.top_role.position:
                    failed += 1
                    failed_list.append(
                        f"{member.mention} ({member.id}) - member is above you in role hierarchy or has the same role.")
                    continue
                if member.top_role.position >= ctx.guild.me.top_role.position:
                    failed += 1
                    failed_list.append(
                        f"{member.mention} ({member.id}) - member is above me in role hierarchy or has the same role.")
                    continue
                try:
                    await ctx.guild.kick(member, reason=responsible(ctx.author, f"{reason or 'No reason'}"))
                    success_list.append(f"{member.mention} ({member.id})")
                except discord.HTTPException as e:
                    print(e)
                    failed += 1
                    failed_list.append(f"{member.mention} - {e}")
                except discord.Forbidden as e:
                    print(e)
                    failed += 1
                    failed_list.append(f"{member.mention} - {e}")
            muted = ""
            notmuted = ""
            if success_list and not failed_list:
                muted += "**I've successfully kicked {0} member(s):**\n".format(total)
                for num, res in enumerate(success_list, start=0):
                    muted += f"`[{num + 1}]` {res}\n"
                await ctx.send(muted)
            if success_list and failed_list:
                muted += "**I've successfully kicked {0} member(s):**\n".format(total - failed)
                notmuted += f"**However I failed to kick the following {failed} member(s):**\n"
                for num, res in enumerate(success_list, start=0):
                    muted += f"`[{num + 1}]` {res}\n"
                for num, res in enumerate(failed_list, start=0):
                    notmuted += f"`[{num + 1}]` {res}\n"
                await ctx.send(muted + notmuted)
            if not success_list and failed_list:
                notmuted += f"**I failed to kick all the members:**\n"
                for num, res in enumerate(failed_list, start=0):
                    notmuted += f"`[{num + 1}]` {res}\n"
                await ctx.send(notmuted)

        except Exception as e:
            print(e)
            return await ctx.send(
                f":warning: Something failed! Error: (Please report it to my developers):\n- {e}")

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True, manage_messages=True)
    async def ban(self, ctx, members: commands.Greedy[discord.Member], *, reason: str = None):
        """> Ban member from the server.
        You can also provide multiple members to ban.
        """

        if not members:
            x_moji = discord.utils.get(ctx.guild.emojis, name="x")
            return await ctx.send(f"{x_moji} | You're missing an argument - **members**")

        error = '\n'
        try:
            total = len(members)
            if total > 10:
                return await ctx.send("You can ban only 10 members at once!")

            failed = 0
            failed_list = []
            success_list = []
            for member in members:
                if member == ctx.author:
                    failed += 1
                    failed_list.append(f"{member.mention} ({member.id}) - you are the member?")
                    continue
                if member.top_role.position >= ctx.author.top_role.position:
                    failed += 1
                    failed_list.append(
                        f"{member.mention} ({member.id}) - member is above you in role hierarchy or has the same role.")
                    continue
                if member.top_role.position >= ctx.guild.me.top_role.position:
                    failed += 1
                    failed_list.append(
                        f"{member.mention} ({member.id}) - member is above me in role hierarchy or has the same role.")
                    continue
                try:
                    await ctx.guild.ban(member, reason=responsible(ctx.author, f"{reason or 'No reason'}"))
                    success_list.append(f"{member.mention} ({member.id})")
                except discord.HTTPException as e:
                    print(e)
                    failed += 1
                    failed_list.append(f"{member.mention} - {e}")
                except discord.Forbidden as e:
                    print(e)
                    failed += 1
                    failed_list.append(f"{member.mention} - {e}")
            muted = ""
            notmuted = ""
            if success_list and not failed_list:
                muted += "**I've successfully banned {0} member(s):**\n".format(total)
                for num, res in enumerate(success_list, start=0):
                    muted += f"`[{num + 1}]` {res}\n"
                await ctx.send(muted)
            if success_list and failed_list:
                muted += "**I've successfully banned {0} member(s):**\n".format(total - failed)
                notmuted += f"**However I failed to ban the following {failed} member(s):**\n"
                for num, res in enumerate(success_list, start=0):
                    muted += f"`[{num + 1}]` {res}\n"
                for num, res in enumerate(failed_list, start=0):
                    notmuted += f"`[{num + 1}]` {res}\n"
                await ctx.send(muted + notmuted)
            if not success_list and failed_list:
                notmuted += f"**I failed to ban all the members:**\n"
                for num, res in enumerate(failed_list, start=0):
                    notmuted += f"`[{num + 1}]` {res}\n"
                await ctx.send(notmuted)

        except Exception as e:
            print(e)
            return await ctx.send(
                f":warning: Something failed! Error: (Please report it to my developers):\n- {e}")

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def hackban(self, ctx, user: MemberID, *, reason: str = None):
        """> Ban a user that isn't in this server """

        try:
            try:
                m = await commands.MemberConverter().convert(ctx, str(user))
                if m is not None:
                    return await ctx.send(f":warning: Hack-ban is to ban users that are not in this server.")
            except:
                pass
            await ctx.guild.ban(user, reason=responsible(ctx.author, reason))
            await ctx.send(f"<:check:784187150660665384> Banned **{await self.bot.fetch_user(user)}** for `{reason}`")
        except Exception as e:
            print(e)
            return await ctx.send(f"<:xmark:784187150542569503> Something failed!")

    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Please give a user to be banned')

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True, manage_messages=True)
    async def unban(self, ctx, user: BannedMember, *, reason: str = None):
        """> Unbans user from server
        """
        try:
            await ctx.message.delete()
            await ctx.guild.unban(user.user, reason=responsible(ctx.author, reason))
            await ctx.send(
                f"<:check:784187150660665384> **{user.user}** was unbanned successfully, with a reason: ``{reason}``",
                delete_after=15)
        except Exception as e:
            print(e)
            await ctx.send(f"<:xmark:784187150542569503> Something failed while trying to unban.")

    @unban.error
    async def unban_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Please give a user to be unbanned')

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True, manage_messages=True)
    async def unbanall(self, ctx, *, reason: str = None):
        """> Unban all users from the server """
        bans = len(await ctx.guild.bans())

        try:
            unbanned = 0

            if bans == 0:
                return await ctx.send("This guild has no bans.")

            def check(r, u):
                return u.id == ctx.author.id and r.message.id == checkmsg.id

            checkmsg = await ctx.send(f"Are you sure you want to unban **{bans}** members from this guild?")
            await checkmsg.add_reaction(f'<:check:784187150660665384>')
            await checkmsg.add_reaction(f'<:xmark:784187150542569503>')
            await checkmsg.add_reaction('🔍')
            react, user = await self.bot.wait_for('reaction_add', check=check, timeout=30.0)

            # ? They want to unban everyone

            if str(react) == f"<:check:784187150660665384>":
                unb = await ctx.channel.send(f"Unbanning **{bans}** members from this guild.")
                await checkmsg.delete()
                for user in await ctx.guild.bans():
                    await ctx.guild.unban(user.user, reason=responsible(ctx.author, reason))
                    await unb.edit(content=f"<a:loading1:784376190349344768> Processing unbans...")
                await unb.edit(content=f"Unbanned **{bans}** members from this guild.", delete_after=15)

            # ? They don't want to unban anyone

            if str(react) == f"<:xmark:784187150542569503>":
                await checkmsg.delete()
                await ctx.channel.send("Alright. Not unbanning anyone..")

            # ? They want to see ban list

            if str(react) == "🔍":
                await checkmsg.clear_reactions()
                ban = []
                for banz in await ctx.guild.bans():
                    ben = f"• {banz.user}\n"
                    ban.append(ben)
                    e = discord.Embed(colour=discord.Colour.from_rgb(250,0,0), title=f"Bans for {ctx.guild}",
                                      description="".join(ban))
                    e.set_footer(text="Are you sure you want to unban them all?")
                    await checkmsg.edit(content='', embed=e)
                await checkmsg.add_reaction(f'<:check:784187150660665384>')
                await checkmsg.add_reaction(f'<:xmark:784187150542569503>')
                react, user = await self.bot.wait_for('reaction_add', check=check, timeout=30.0)

                # ? They want to unban everyone

                if str(react) == f"<:check:784187150660665384>":
                    unb = await ctx.channel.send(f"Unbanning **{bans}** members from this guild.")
                    await checkmsg.delete()
                    for user in await ctx.guild.bans():
                        await ctx.guild.unban(user.user, reason=responsible(ctx.author, reason))
                        await unb.edit(content=f"<a:loading1:784376190349344768> Processing unbans...")
                    await unb.edit(content=f"Unbanned **{bans}** members from this guild.", delete_after=15)

                # ? They don't want to unban anyone

                if str(react) == f"<:xmark:784187150542569503>":
                    await checkmsg.delete()
                    await ctx.channel.send("Alright. Not unbanning anyone..")

        except Exception as e:
            print(e)
            return

    @commands.command()
    @commands.has_permissions(administrator = True)
    @commands.guild_only()
    async def banlist(self, ctx):
        """> Displays the server's banlist"""
        try:
            banlist = await ctx.guild.bans()
        except discord.errors.Forbidden:
            await ctx.send("moderation.no_ban_perms")
            return
        bancount = len(banlist)
        display_bans = []
        bans = None
        if bancount == 0:
            bans = ("moderation.no_bans", ctx)
        else:
            for ban in banlist:
                if len(", ".join(display_bans)) < 1800:
                    display_bans.append(str(ban.user))
                else:
                    bans = "".join(display_bans) + ("moderation.banlist_and_more", ctx).format()

                    len(banlist) - len(display_bans)
                    break
        if not bans:
            bans = "\n".join(display_bans)
            embed = discord.Embed(title = f'{bancount} Users banned', description = f'{bans}',
                                  colour = discord.Colour.from_rgb(250,0,0))
        await ctx.send(embed = embed)

    @commands.group(aliases=['clear', 'prune'],
                    invoke_without_command=True)
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge(self, ctx, count=100):
        """> Purge messages in the chat. Default amount is set to **100**"""
        await ctx.message.delete()
        await self.do_removal(ctx, count, lambda e: True)

    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @commands.guild_only()
    async def all(self, ctx, count=100):
        """> Removes all messages
        Might take longer if you're purging messages that are older than 2 weeks """
        await ctx.message.delete()
        await self.do_removal(ctx, count, lambda e: True)

    @purge.command(brief="User messages", description="Clear messages sent from an user")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @commands.guild_only()
    async def user(self, ctx, member: discord.Member, count=100):
        """> Removes user messages """
        await ctx.message.delete()
        await self.do_removal(ctx, count, lambda e: e.author == member)

    @purge.command(name='bot')
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @commands.guild_only()
    async def _bot(self, ctx, prefix=None, count=100):
        """> Removes a bot user's messages and messages with their optional prefix."""

        def predicate(m):
            return (m.webhook_id is None and m.author.bot) or (prefix and m.content.startswith(prefix))

        await self.do_removal(ctx, count, predicate)

    @purge.command()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @commands.guild_only()
    async def embeds(self, ctx, count=100):
        """> Removes messages that have embeds in them."""
        await self.do_removal(ctx, count, lambda e: len(e.embeds))

    @purge.command()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @commands.guild_only()
    async def images(self, ctx, count=100):
        """> Removes messages that have embeds or attachments."""
        await self.do_removal(ctx, count, lambda e: len(e.embeds) or len(e.attachments))

    @purge.command()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @commands.guild_only()
    async def contains(self, ctx, *, substr: str):
        """> Removes all messages containing a substring.
        The substring must be at least 3 characters long.
        """
        if len(substr) < 3:
            await ctx.send(f":warning: substring must be at least 3 characters long.")
        else:
            await self.do_removal(ctx, 100, lambda e: substr in e.content)

    @purge.command(name='emoji')
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @commands.guild_only()
    async def _emoji(self, ctx, search=100):
        """> Removes all messages containing custom emoji."""
        custom_emoji = re.compile(r'<:(\w+):(\d+)>')

        def predicate(m):
            return custom_emoji.search(m.content)

        await self.do_removal(ctx, search, predicate)

    @purge.command()
    @commands.has_guild_permissions(manage_messages=True)
    @commands.guild_only()
    async def removereactions(self, ctx, id: int):
        """> Clear reactions from a message"""
        try:
            message = await ctx.channel.fetch_message(id)
        except discord.errors.NotFound:
            await ctx.send(f":xmark:784187150542569503> | I can't find message with `{id}` id in this channel")
            return
        try:
            await message.clear_reactions()
            await ctx.send(f"<:check:784187150660665384> Successfully removed all the reactions from message with `{id}` id")
        except discord.errors.Forbidden:
            await ctx.send(f"⚠ I guess I'm lacking the permission to manage roles.")


    @purge.command()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @commands.guild_only()
    async def custom(self, ctx, *, args: str):
        """> A more advanced purge command.
        This command uses a powerful "command line" syntax.
        Most options support multiple values to indicate 'any' match.
        If the value has spaces it must be quoted.
        The messages are only deleted if all options are met unless
        the `--or` flag is passed, in which case only if any is met.
        The following options are valid.
        `--user`: A mention or name of the user to remove.
        `--contains`: A substring to search for in the message.
        `--starts`: A substring to search if the message starts with.
        `--ends`: A substring to search if the message ends with.
        `--search`: How many messages to search. Default 100. Max 2000.
        `--after`: Messages must come after this message ID.
        `--before`: Messages must come before this message ID.
        Flag options (no arguments):
        `--bot`: Check if it's a bot user.
        `--embeds`: Check if the message has embeds.
        `--files`: Check if the message has attachments.
        `--emoji`: Check if the message has custom emoji.
        `--reactions`: Check if the message has reactions
        `--or`: Use logical OR for all options.
        `--not`: Use logical NOT for all options.
        """
        parser = Arguments(add_help=False, allow_abbrev=False)
        parser.add_argument('--user', nargs='+')
        parser.add_argument('--contains', nargs='+')
        parser.add_argument('--starts', nargs='+')
        parser.add_argument('--ends', nargs='+')
        parser.add_argument('--or', action='store_true', dest='_or')
        parser.add_argument('--not', action='store_true', dest='_not')
        parser.add_argument('--emoji', action='store_true')
        parser.add_argument('--bot', action='store_const', const=lambda m: m.author.bot)
        parser.add_argument('--embeds', action='store_const', const=lambda m: len(m.embeds))
        parser.add_argument('--files', action='store_const', const=lambda m: len(m.attachments))
        parser.add_argument('--reactions', action='store_const', const=lambda m: len(m.reactions))
        parser.add_argument('--search', type=int, default=100)
        parser.add_argument('--after', type=int)
        parser.add_argument('--before', type=int)

        try:
            args = parser.parse_args(shlex.split(args))
        except Exception as e:
            await ctx.send(str(e))
            return

        predicates = []
        if args.bot:
            predicates.append(args.bot)

        if args.embeds:
            predicates.append(args.embeds)

        if args.files:
            predicates.append(args.files)

        if args.reactions:
            predicates.append(args.reactions)

        if args.emoji:
            custom_emoji = re.compile(r'<:(\w+):(\d+)>')
            predicates.append(lambda m: custom_emoji.search(m.content))

        if args.user:
            users = []
            converter = commands.MemberConverter()
            for u in args.user:
                try:
                    user = await converter.convert(ctx, u)
                    users.append(user)
                except Exception as e:
                    await ctx.send(str(e))
                    return

            predicates.append(lambda m: m.author in users)

        if args.contains:
            predicates.append(lambda m: any(sub in m.content for sub in args.contains))

        if args.starts:
            predicates.append(lambda m: any(m.content.startswith(s) for s in args.starts))

        if args.ends:
            predicates.append(lambda m: any(m.content.endswith(s) for s in args.ends))

        op = all if not args._or else any

        def predicate(m):
            r = op(p(m) for p in predicates)
            if args._not:
                return not r
            return r

        args.search = max(0, min(2000, args.search))  # clamp from 0-2000
        await self.do_removal(ctx, args.search, predicate, before=args.before, after=args.after)

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def clone(self, ctx, channel: discord.TextChannel, *, reason: str = None):
        """> Clone text channel in the server"""
        server = ctx.message.guild
        if reason is None:
            reason = 'No reason'
        try:
            await ctx.message.delete()
        except:
            pass
        for c in ctx.guild.channels:
            if c.name == f'{channel.name}-clone':
                return await ctx.send(f"<:xmark:784187150542569503> {channel.name} clone already exists!")
        await channel.clone(name=f'{channel.name}-clone', reason=responsible(ctx.author, reason))
        await ctx.send(f"<:check:784187150660665384> Successfully cloned {channel.name}")

    @commands.command(aliases=["vmute"])
    @commands.guild_only()
    @commands.has_guild_permissions(mute_members=True)
    @commands.bot_has_guild_permissions(mute_members=True)
    @commands.has_guild_permissions(manage_guild=True)
    async def voicemute(self, ctx, members: commands.Greedy[discord.Member], reason: str = None):
        """> Voice mute member in the server """

        if not members:
            return await ctx.send(f"<:xmark:784187150542569503> | You're missing an argument - **members**")

        error = '\n'
        try:
            total = len(members)
            if total > 10:
                return await ctx.send("You can voice mute only 10 members at once!")

            failed = 0
            failed_list = []
            success_list = []
            for member in members:
                if member == ctx.author:
                    failed += 1
                    failed_list.append(f"{member.mention} ({member.id}) - you are the member?")
                    continue
                if member.top_role.position >= ctx.author.top_role.position:
                    failed += 1
                    failed_list.append(
                        f"{member.mention} ({member.id}) - member is above you in role hierarchy or has the same role.")
                    continue
                if member.top_role.position >= ctx.guild.me.top_role.position:
                    failed += 1
                    failed_list.append(
                        f"{member.mention} ({member.id}) - member is above me in role hierarchy or has the same role.")
                    continue
                try:
                    await member.edit(mute=True, reason=responsible(ctx.author, reason))
                    success_list.append(f"{member.mention} ({member.id})")
                except discord.HTTPException as e:
                    print(e)
                    failed += 1
                    failed_list.append(f"{member.mention} - {e}")
                except discord.Forbidden as e:
                    print(e)
                    failed += 1
                    failed_list.append(f"{member.mention} - {e}")
            muted = ""
            notmuted = ""
            if success_list and not failed_list:
                muted += "**I've successfully voice muted {0} member(s):**\n".format(total)
                for num, res in enumerate(success_list, start=0):
                    muted += f"`[{num + 1}]` {res}\n"
                await ctx.send(muted)
            if success_list and failed_list:
                muted += "**I've successfully voice muted {0} member(s):**\n".format(total - failed)
                notmuted += f"**However I failed to voice mute the following {failed} member(s):**\n"
                for num, res in enumerate(success_list, start=0):
                    muted += f"`[{num + 1}]` {res}\n"
                for num, res in enumerate(failed_list, start=0):
                    notmuted += f"`[{num + 1}]` {res}\n"
                await ctx.send(muted + notmuted)
            if not success_list and failed_list:
                notmuted += f"**I failed to voice mute all the members:**\n"
                for num, res in enumerate(failed_list, start=0):
                    notmuted += f"`[{num + 1}]` {res}\n"
                await ctx.send(notmuted)

        except Exception as e:
            print(e)
            return await ctx.send(
                f":warning: Something failed! Error: (Please report it to my developers):\n- {e}")

    @commands.command(aliases=["vunmute"])
    @commands.guild_only()
    @commands.has_guild_permissions(mute_members=True)
    @commands.bot_has_guild_permissions(mute_members=True)
    async def voiceunmute(self, ctx, members: commands.Greedy[discord.Member], reason: str = None):
        """> Voice unmute member in the server """

        if not members:
            return await ctx.send(f"<:xmark:784187150542569503> | You're missing an argument - **members**")

        error = '\n'
        try:
            total = len(members)
            if total > 10:
                return await ctx.send("You can voice unmute only 10 members at once!")

            failed = 0
            failed_list = []
            success_list = []
            for member in members:
                if member == ctx.author:
                    failed += 1
                    failed_list.append(f"{member.mention} ({member.id}) - you are the member?")
                    continue
                if member.top_role.position >= ctx.author.top_role.position:
                    failed += 1
                    failed_list.append(
                        f"{member.mention} ({member.id}) - member is above you in role hierarchy or has the same role.")
                    continue
                if member.top_role.position >= ctx.guild.me.top_role.position:
                    failed += 1
                    failed_list.append(
                        f"{member.mention} ({member.id}) - member is above me in role hierarchy or has the same role.")
                    continue
                try:
                    await member.edit(mute=False, reason=responsible(ctx.author, reason))
                    success_list.append(f"{member.mention} ({member.id})")
                except discord.HTTPException as e:
                    print(e)
                    failed += 1
                    failed_list.append(f"{member.mention} - {e}")
                except discord.Forbidden as e:
                    print(e)
                    failed += 1
                    failed_list.append(f"{member.mention} - {e}")
            muted = ""
            notmuted = ""
            if success_list and not failed_list:
                muted += "**I've successfully voice unmuted {0} member(s):**\n".format(total)
                for num, res in enumerate(success_list, start=0):
                    muted += f"`[{num + 1}]` {res}\n"
                await ctx.send(muted)
            if success_list and failed_list:
                muted += "**I've successfully voice unmuted {0} member(s):**\n".format(total - failed)
                notmuted += f"**However I failed to voice unmute the following {failed} member(s):**\n"
                for num, res in enumerate(success_list, start=0):
                    muted += f"`[{num + 1}]` {res}\n"
                for num, res in enumerate(failed_list, start=0):
                    notmuted += f"`[{num + 1}]` {res}\n"
                await ctx.send(muted + notmuted)
            if not success_list and failed_list:
                notmuted += f"**I failed to voice unmute all the members:**\n"
                for num, res in enumerate(failed_list, start=0):
                    notmuted += f"`[{num + 1}]` {res}\n"
                await ctx.send(notmuted)

        except Exception as e:
            print(e)
            return await ctx.send(
                f":warning: Something failed! Error: (Please report it to my developers):\n- {e}")

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    async def newusers(self, ctx, *, count: int):
        """> See the newest members in the server
        Limit is set to `10`
        """
        if len(ctx.guild.members) < count:
            return await ctx.send(f"This server has only {len(ctx.guild.members)} members")
        counts = max(min(count, 10), 1)

        if not ctx.guild.chunked:
            await self.bot.request_offline_members(ctx.guild)
        members = sorted(ctx.guild.members, key=lambda m: m.joined_at, reverse=True)[:counts]
        
        e = discord.Embed(title='Newest member(s) in this server', colour=discord.Colour.from_rgb(250,0,0))
        for member in members:
            data = f'**Joined Server at** {btime.human_timedelta(member.joined_at)}\
                \n**Account created at** {btime.human_timedelta(member.created_at)}'
            e.add_field(name=f'**{member}** ({member.id})', value=data, inline=False)
            if count > 10:
                e.set_footer(text="Limit is set to 10")

        await ctx.send(embed=e)

    @commands.command(aliases=['ar'])
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def announcerole(self, ctx, *, role: discord.Role):
        """> Make a role mentionable you want to mention in announcements.

        The role will become unmentionable after you mention it or you don't mention it for 30seconds. """
        if role == ctx.guild.default_role:
            return await ctx.send("To prevent abuse, I won't allow mentionable role for everyone/here role.")

        if ctx.author.top_role.position <= role.position:
            return await ctx.send(
                "It seems like the role you attempt to mention is over your permissions, therefor I won't allow you.")

        if ctx.me.top_role.position <= role.position:
            return await ctx.send("This role is above my permissions, I can't make it mentionable ;-;")

        if role.mentionable == True:
            return await ctx.send(f"<:xmark:784187150542569503> That role is already mentionable!")

        await role.edit(mentionable=True, reason=f"announcerole command")
        msg = await ctx.send(
            f"**{role.mention}** is now mentionable, if you don't mention it within 30 seconds, I will revert the changes.")

        while True:
            def role_checker(m):
                if (role.mention in m.content):
                    return True
                return False

            try:
                checker = await self.bot.wait_for('message', timeout=30.0, check=role_checker)
                if checker.author.id == ctx.author.id:
                    await role.edit(mentionable=False, reason=f"announcerole command")
                    return await msg.edit(
                        content=f"**{role.mention}** mentioned by **{ctx.author}** in {checker.channel.mention}",
                        allowed_mentions=discord.AllowedMentions(roles=False))
                    break
                else:
                    await checker.delete()
            except asyncio.TimeoutError:
                await role.edit(mentionable=False, reason=f"announcerole command")
                return await msg.edit(content=f"**{role.mention}** was never mentioned by **{ctx.author}**...",
                                      allowed_mentions=discord.AllowedMentions(roles=False))
                break

    @commands.command()
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    async def nuke(self, ctx):
        """> Nuke current channel"""
        temp_channel: discord.TextChannel = await ctx.channel.clone()
        await temp_channel.edit(position=ctx.channel.position)
        await ctx.channel.delete(reason="Nuke")
        embed = discord.Embed(colour=discord.Colour.from_rgb(250, 0, 0),
                              description=f"{ctx.author.mention} Nuked This Channel!")
        embed.set_image(url="https://media.tenor.com/images/04dc5750f44e6d94c0a9f8eb8abf5421/tenor.gif")
        await temp_channel.send(embed=embed)

    @commands.command(aliases=["lockdown"])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def quarantine(self, ctx, channel: discord.TextChannel = None):
        """> Quarantine a channel"""
        if channel is None:
            channel = ctx.channel

        for role in ctx.guild.roles:
            if role.permissions.administrator:
                await channel.set_permissions(role, send_messages=True, read_messages=True)
            elif role.name == "@everyone":
                await channel.set_permissions(role, read_messages=False)
                await ctx.send(f":lock:The channel {channel.mention} has been quarantined")

    @commands.command(aliases=["unlockdown"])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def unquarantine(self, ctx, channel: discord.TextChannel = None):
        """> Unquarantine a quarantined channel"""
        if channel is None:
            channel = ctx.channel

        await channel.set_permissions(ctx.guild.roles[0], read_messages=True)
        await ctx.send(f":lock:The channel {channel.mention} has been recovered")

    @commands.command(name="lockchannel", aliases=['lock'])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def lockchannel(self, ctx, channel: discord.TextChannel = None, *, reason: str = None):
        """> Lock a channel"""
        if reason is None:
            reason = "No reason"
        if channel is None:
            channel = ctx.channel

        if channel.overwrites_for(ctx.guild.default_role).send_messages == False:
            return await ctx.send(f"<:xmark:784187150542569503> {channel.mention} is already locked!", delete_after=20)
        else:
            try:
                await channel.set_permissions(ctx.guild.default_role, send_messages=False,
                                              reason=responsible(ctx.author, reason))
                await channel.send(f"🔒 This channel was locked for: `{reason}`")
                await ctx.send(f"<:check:784187150660665384> {channel.mention} was locked!", delete_after=20)
            except Exception as e:
                print(default.traceback_maker(e))
                await ctx.send(f"Error! ```py\n{e}```")

    @commands.command(name="unlockchannel", aliases=['unlock'])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def unlockchannel(self, ctx, channel: discord.TextChannel = None, *, reason: str = None):
        """> unlock a locked channel"""
        if reason is None:
            reason = "No reason"
        if channel is None:
            channel = ctx.channel

        if channel.overwrites_for(ctx.guild.default_role).send_messages is None:
            return await ctx.send(f"<:xmark:784187150542569503> {channel.mention} is not locked!", delete_after=20)
        elif channel.overwrites_for(ctx.guild.default_role).send_messages == False:
            try:
                await channel.set_permissions(ctx.guild.default_role, overwrite=None,
                                              reason=responsible(ctx.author, reason))
                await channel.send(f":unlock: This channel was unlocked for: `{reason}`")
                await ctx.send(f"<:check:784187150660665384> {channel.mention} was unlocked!", delete_after=20)
            except Exception as e:
                print(default.traceback_maker(e))
                await ctx.send(f"Error! ```py\n{e}```")

    @commands.command(name="slowmode", aliases=['setdelay', 'sm'])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def setdelay(self, ctx, seconds: int):
        """> Set slow mode"""
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.send(f"Set the slowmode in this channel to **{seconds}** seconds!")

    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    @commands.command()
    async def roleid(self, ctx, *, role: discord.Role):
        """> Gets the id for the specified role"""
        await ctx.send(f"Roll name: {role.mention} | Role id: `{role.id}`")

    @commands.has_guild_permissions(manage_roles=True)
    @commands.guild_only()
    @commands.command()
    async def createrole(self, ctx, *, name: str):
        """> Creates a role with the specified name"""
        try:
            await ctx.guild.create_role(name=name, reason="{ctx.author}")
            await ctx.send(f"<:check:784187150660665384> Successfully created role {name}, {ctx.author}")
        except discord.errors.Forbidden:
            await ctx.send("⚠ I guess I'm lacking the permission to manage roles.", ctx)

    @commands.has_guild_permissions(manage_roles=True)
    @commands.guild_only()
    @commands.command()
    async def deleterole(self, ctx, *, name: str):
        """> Deletes the role with the specified name"""
        role = discord.utils.get(ctx.guild.roles, name=name)
        reason = "{ctx.author}"
        if role is None:
            await ctx.send(f"<:xmark:784187150542569503> | I can't find `{name}` role")
            return
        try:
            await role.delete(reason=reason)
            await ctx.send(f"<:check:784187150660665384> Successfully deleted role `{name}`, {ctx.author.name}")
        except discord.errors.Forbidden:
            if role.position == ctx.me.top_role.position:
                await ctx.send(f"⚠ `{name}` role is higher than me and I cannot access it.")
            elif role.position > ctx.me.top_role.position:
                await ctx.send(f"⚠ `{name}` role is higher than me and I cannot access it.")
            else:
                await ctx.send("⚠ I guess I'm lacking the permission to manage roles.")

    @commands.has_guild_permissions(manage_roles=True)
    @commands.guild_only()
    @commands.command()
    async def renamerole(self, ctx, name: str, newname: str):
        """> Renames a role with the specified name, be sure to put double quotes (\") around the name and the new name"""
        role = discord.utils.get(ctx.guild.roles, name=name)
        if role is None:
            await ctx.send(f":xmark:784187150542569503> | I can't find role `{name}`")
            return
        try:
            await role.edit(reason=(f"Moderation rename role `{name}` requested by {ctx.author.name}"), name=newname)
            await ctx.send(f"Role `{name}` is successfully renamed to `{newname}`")
        except discord.errors.Forbidden:
            if role.position == ctx.me.top_role.position:
                await ctx.send(f"⚠ `{name}` role is higher than me and I cannot access it.")
            elif role.position > ctx.me.top_role.position:
                await ctx.send(f"⚠ `{name}` role is higher than me and I cannot access it.")
            else:
                await ctx.send("⚠ I guess I'm lacking the permission to manage roles.")

    @commands.command(name="addrole", aliases=['ad'])
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def addrole(self, ctx, role: discord.Role, user: discord.Member):
        """> Add role to a user"""
        await user.add_roles(role)
        await ctx.message.delete()
        await ctx.send(f"Successfully Added {role.mention} to {user.mention}")

    @commands.command(name="removerole", aliases=['rd'])
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def removerole(self, ctx, role: discord.Role, user: discord.Member):
        """> Remove a role from user"""
        await user.remove_roles(role)
        await ctx.message.delete()
        await ctx.send(f"Successfully Removed {role.mention} from {user.mention}")

    @commands.command(aliases=["nick"])
    @commands.guild_only()
    @commands.has_permissions(manage_nicknames=True)
    async def setnick(self, ctx, members: commands.Greedy[discord.Member], *, name: str = None):
        """> Change or remove anyones nickname """

        if not members:
            return await ctx.send(f"❌ | You're missing an argument - **members**")
        if name and len(name) > 32:
            return await ctx.send(f"❌ Nickname is too long! You can't have nicknames longer than 32 characters")
        error = '\n'
        try:
            total = len(members)
            if total > 10:
                return await ctx.send("You can re-name only 10 members at once!")

            failed = 0
            failed_list = []
            success_list = []
            for member in members:
                if member == ctx.author:
                    failed += 1
                    failed_list.append(f"{member.mention} ({member.id}) - you are the member?")
                    continue
                if member.top_role.position >= ctx.author.top_role.position:
                    failed += 1
                    failed_list.append(
                        f"{member.mention} ({member.id}) - member is above you in role hierarchy or has the same role.")
                    continue
                if member.top_role.position >= ctx.guild.me.top_role.position:
                    failed += 1
                    failed_list.append(
                        f"{member.mention} ({member.id}) - member is above me in role hierarchy or has the same role.")
                    continue
                try:
                    await member.edit(nick=name)
                    success_list.append(f"{member.mention} ({member.id})")
                except discord.HTTPException as e:
                    print(e)
                    failed += 1
                    failed_list.append(f"{member.mention} - {e}")
                except discord.Forbidden as e:
                    print(e)
                    failed += 1
                    failed_list.append(f"{member.mention} - {e}")
            muted = ""
            notmuted = ""
            if success_list and not failed_list:
                muted += "**I've successfully re-named {0} member(s):**\n".format(total)
                for num, res in enumerate(success_list, start=0):
                    muted += f"`[{num + 1}]` {res}\n"
                await ctx.send(muted)
            if success_list and failed_list:
                muted += "**I've successfully re-named {0} member(s):**\n".format(total - failed)
                notmuted += f"**However I failed to re-name the following {failed} member(s):**\n"
                for num, res in enumerate(success_list, start=0):
                    muted += f"`[{num + 1}]` {res}\n"
                for num, res in enumerate(failed_list, start=0):
                    notmuted += f"`[{num + 1}]` {res}\n"
                await ctx.send(muted + notmuted)
            if not success_list and failed_list:
                notmuted += f"**I failed to re-name all the members:**\n"
                for num, res in enumerate(failed_list, start=0):
                    notmuted += f"`[{num + 1}]` {res}\n"
                await ctx.send(notmuted)

        except Exception as e:
            print(e)
            return await ctx.send(f"⚠ Something failed! Error: (Please report it to my developers):\n- {e}")

    @commands.command()
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def voicemuteall(self, ctx, *, vc: discord.VoiceChannel):
        """> Mutes everyone in a voice channel"""
        for vcmember in vc.members:
            if not vcmember.bot:
                await vcmember.edit(mute=True)
        await ctx.send(
            embed=discord.Embed(description=f'{ctx.author.name} muted everyone in {vc.name}', colour=0xbc0a1d))

    @commands.command()
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def voiceunmuteall(self, ctx, *, vc: discord.VoiceChannel):
        """> Unmutes everyone in a voice channel"""
        for vcmember in vc.members:
            if not vcmember.bot:
                await vcmember.edit(mute=False)
        await ctx.send(
            embed=discord.Embed(description=f'{ctx.author.name} unmuted everyone in {vc.name}', colour=0xbc0a1d))

    @commands.command(aliases=['deafenall', 'disablevc'])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def vcoff(self, ctx, *, vc: discord.VoiceChannel):
        """> Mutes and deafens everyone in a voice channel."""
        for vcmember in vc.members:
            if not vcmember.bot:
                await vcmember.edit(deafen=True)
                await vcmember.edit(mute=True)
        await ctx.send(embed=discord.Embed(description=f'{ctx.author.name} disabled {vc.name}', colour=0xbc0a1d))

    @commands.command(aliases=['undeafenall', 'enablevc'])
    @commands.guild_only()
    @commands.has_guild_permissions(manage_guild=True)
    async def vcon(self, ctx, *, vc: discord.VoiceChannel):
        """> Unmutes and undeafens everyone in a voice channel."""
        for x in vc.members:
            if not x.bot:
                await x.edit(deafen=False)
                await x.edit(mute=False)
        await ctx.send(embed=discord.Embed(description=f'{ctx.author.name} enabled {vc.name}', colour=0xbc0a1d))

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str = None):
        """> Warn a member for something
        Time will be logged in UTC """

        if reason is None:
            reason = "No reason."
        else:
            reason = reason

        if member == ctx.author:
            return await ctx.send("Ok you're warned, dummy...")
        if member.top_role.position >= ctx.author.top_role.position and ctx.author != ctx.guild.owner:
            return await ctx.send("You can't warn someone who's higher or equal to you!")

        random_id = random.randint(1111, 99999)

        e = discord.Embed(colour=discord.Colour.from_rgb(250,0,0),
                          description=f"Successfully warned **{member}** for: **{reason}** with ID: **{random_id}**",
                          delete_after=15)
        e.timestamp(datetime.datetime.utcnow)
        await ctx.send(embed=e)

    @commands.command(
        name="channelstats",
        aliases=["cs"],
        )
    @commands.has_guild_permissions(manage_channels=True)
    async def channelstats(self, ctx):
        """> Get stats of current channel"""
        channel = ctx.channel

        embed = discord.Embed(
            title=f"Stats for **{channel.name}**",
            description=f"{'Category: {}'.format(channel.category.name) if channel.category else 'This channel is not in a category'}",
            colour=discord.Colour.from_rgb(250, 0, 0)
        )
        embed.add_field(name="Channel Guild", value=ctx.guild.name, inline=False)
        embed.add_field(name="Channel Id", value=channel.id, inline=False)
        embed.add_field(
            name="Channel Topic",
            value=f"{channel.topic if channel.topic else 'No topic.'}",
            inline=False,
        )
        embed.add_field(name="Channel Position", value=channel.position, inline=False)
        embed.add_field(
            name="Channel Slowmode Delay", value=channel.slowmode_delay, inline=False
        )
        embed.add_field(name="Channel is nsfw?", value=channel.is_nsfw(), inline=False)
        embed.add_field(name="Channel is news?", value=channel.is_news(), inline=False)
        embed.add_field(
            name="Channel Creation Time", value=channel.created_at, inline=False
        )
        embed.add_field(
            name="Channel Permissions Synced",
            value=channel.permissions_synced,
            inline=False,
        )
        embed.add_field(name="Channel Hash", value=hash(channel), inline=False)

        await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True)
    @commands.has_guild_permissions(manage_channels=True)
    async def new(self, ctx):
        """> Create a new Category or Channel"""
        await ctx.send("Invalid sub-command passed.")

    @new.command(
        name="category",
usage="<role> <Category name>",
    )
    @commands.has_guild_permissions(manage_channels=True)
    async def category(self, ctx, role: discord.Role, *, name):
        """> Create a new category"""
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True),
            role: discord.PermissionOverwrite(read_messages=True),
        }
        category = await ctx.guild.create_category(name=name, overwrites=overwrites)
        await ctx.send(f"Hey dude, I made {category.name} for ya!")

    @new.command(
        name="channel",
        usage="<role> <channel name>",
    )
    @commands.has_guild_permissions(manage_channels=True)
    async def channel(self, ctx, role: discord.Role, *, name):
        """> Create a new channel"""
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True),
            role: discord.PermissionOverwrite(read_messages=True),
        }
        channel = await ctx.guild.create_text_channel(
            name=name,
            overwrites=overwrites,
            category=self.bot.get_channel(720169568965754932),
        )
        await ctx.send(f"Hey dude, I made {channel.name} for ya!")

    @commands.group(invoke_without_command=True)
    @commands.has_guild_permissions(manage_channels=True)
    async def delete(self, ctx):
        """> Category or Channel"""
        await ctx.send("Invalid sub-command passed")

    @delete.command(
        name="category", description="Delete a category", usage="<category> [reason]"
    )
    @commands.has_guild_permissions(manage_channels=True)
    async def _category(self, ctx, category: discord.CategoryChannel, *, reason=None):
        """> Delte a category"""
        await category.delete(reason=reason)
        await ctx.send(f"hey! I deleted {category.name} for you")

    @delete.command(
        name="channel", description="Delete a channel", usage="<channel> [reason]"
    )
    @commands.has_guild_permissions(manage_channels=True)
    async def _channel(self, ctx, channel: discord.TextChannel = None, *, reason=None):
        """> Delete a channel"""
        channel = channel or ctx.channel
        await channel.delete(reason=reason)
        await ctx.send(f"hey! I deleted {channel.name} for you")

    @commands.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def mute(self, ctx, member: discord.Member = None, *, reason='Not Given'):
        """> Mute a member"""
        if member == None:
            await ctx.send('Please provide a member.')
            return
        role = discord.utils.get(ctx.guild.roles, name="Muted")
        if role not in ctx.guild.roles:
            perms = discord.Permissions(add_reactions=False, send_messages=False, connect=False)
            await ctx.guild.create_role(name='Muted', permissions=perms)
            await member.add_roles(role)
            for x in member.roles:
                if x == ctx.guild.default_role:
                    pass
                else:
                    y = discord.utils.get(ctx.guild.roles, name=x.name)
                    await member.remove_roles(y)
            await ctx.send(f"{member} has been muted by {ctx.author.name}")
        else:
            for x in member.roles:
                if x == ctx.guild.default_role:
                    pass
                else:
                    y = discord.utils.get(ctx.guild.roles, name=x.name)
                    await member.remove_roles(y)
            await member.add_roles(role)
            await ctx.send(f"{member} has been muted by {ctx.author.name} using the role: {role}")

    @commands.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def unmute(self, ctx, member: discord.Member = None):
        """> Unmute a muted user"""
        if member == None:
            await ctx.send('Please give a member.')
            return
        role = discord.utils.get(ctx.guild.roles, name="Muted")
        try:
            await member.remove_roles(role)
            await ctx.send('Sucessfully unmuted {}.'.format(member))
        except Exception:
            await ctx.send('That user isnt muted!')

    @commands.group()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def find(self, ctx):
        """> Finds a user within your search term """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @find.command(name="playing")
    async def find_playing(self, ctx, *, search: str):
        """> Finds a user with playing status"""
        loop = []
        for i in ctx.guild.members:
            if i.activities and (not i.bot):
                for g in i.activities:
                    if g.name and (search.lower() in g.name.lower()):
                        loop.append(f"{i} | {type(g).__name__}: {g.name} ({i.id})")

        await default.prettyResults(
            ctx, "playing", f"Found **{len(loop)}** on your search for **{search}**", loop
        )

    @find.command(name="username", aliases=["name"])
    async def find_name(self, ctx, *, search: str):
        """> Finds a user with the given name"""
        loop = [f"{i} ({i.id})" for i in ctx.guild.members if search.lower() in i.name.lower() and not i.bot]
        await default.prettyResults(
            ctx, "name", f"Found **{len(loop)}** on your search for **{search}**", loop
        )

    @find.command(name="nickname", aliases=["nick"])
    async def find_nickname(self, ctx, *, search: str):
        """> Finds a user with the given nickname"""
        loop = [f"{i.nick} | {i} ({i.id})" for i in ctx.guild.members if i.nick if
                (search.lower() in i.nick.lower()) and not i.bot]
        await default.prettyResults(
            ctx, "name", f"Found **{len(loop)}** on your search for **{search}**", loop
        )

    @find.command(name="id")
    async def find_id(self, ctx, *, search: int):
        """> Finds a user with the given id"""
        loop = [f"{i} | {i} ({i.id})" for i in ctx.guild.members if (str(search) in str(i.id)) and not i.bot]
        await default.prettyResults(
            ctx, "name", f"Found **{len(loop)}** on your search for **{search}**", loop
        )

    @find.command(name="discriminator", aliases=["discrim"])
    async def find_discriminator(self, ctx, *, search: str):
        """> Finds a user with the given discriminator"""
        if not len(search) == 4 or not re.compile("^[0-9]*$").search(search):
            return await ctx.send("You must provide exactly 4 digits")

        loop = [f"{i} ({i.id})" for i in ctx.guild.members if search == i.discriminator]
        await default.prettyResults(
            ctx, "discriminator", f"Found **{len(loop)}** on your search for **{search}**", loop
        )

async def setup(bot):
    await bot.add_cog(Moderation(bot))