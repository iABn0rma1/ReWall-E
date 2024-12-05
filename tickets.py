import asyncio
import discord
from io import BytesIO
from datetime import datetime
import config
from discord.ext import commands

class tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def open_ticket(self, guild, user):
        category = self.bot.get_channel(config.TICKET_ID)
        support = guild.get_role(config.SUPPORT_ID)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            support: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, 
                                                  manage_permissions=True, manage_channels=True)
        }

        channel = await category.create_text_channel(name=f"ticket-{user.name}", overwrites=overwrites,
                                                     reason=f"Support ticket channel - {user.id}",
                                                     topic=f"User ID: {user.id}")
        await self.bot.db.execute("INSERT INTO tickets(user_id, status, ticket_channel) VALUES($1, $2, $3)", user.id, 0, channel.id)
        fetch_tickets = "SELECT count(*) FROM tickets"
        ticket_id = await self.bot.db.fetchval(fetch_tickets)
        print(ticket_id)

        def checks(r, u):
            return u.id == user.id and r.message.id == subject_message.id

        reactions_dict = {
            '❓': "General Question",
            "<:privacy:733465503594708992>": "Privacy policy concerns or data deletion request",
            "<:partner:748833273383485440>": "Partnership pplication",
            "🐛": "Bug report"
        }

        channel_dict = {
            '❓': "question-",
            "<:privacy:733465503594708992>": "privacy-",
            "<:partner:748833273383485440>": "partner-",
            "🐛": "bug-"
        }

        subject_message = await channel.send(f"{user.mention} Please choose the subject of your ticket.\n\n"
                                             "❓ General Question\n<:privacy:733465503594708992> Privacy policy concerns - data deletion request\n"
                                             f"<:partner:748833273383485440> Partnership application\n🐛 Bug report", allowed_mentions=discord.AllowedMentions(users=True))
        for reaction in reactions_dict:
            await subject_message.add_reaction(reaction)
        try:
            loop = True
            while loop:
                react, user = await self.bot.wait_for('reaction_add', check=checks, timeout=60.0)

                if str(react) not in reactions_dict:
                    await subject_message.remove_reaction(react)
                elif str(react) in reactions_dict:
                    loop = False
                    subject = reactions_dict[str(react)]
                    await channel.edit(name=f"{channel_dict[str(react)]}{user.name}")
                    await subject_message.delete()
        except Exception:
            loop = False
            subject = reactions_dict['❓']
            await channel.edit(name=f"{channel_dict['❓']}{user.name}")
            await subject_message.delete()
            await channel.send("You took too long, setting subject automatically.", delete_after=20)

        ticket_embed = discord.Embed(color=14715915, title='New Ticket Opened', timestamp=datetime.utcnow())
        ticket_embed.set_author(name=user, icon_url=user.avatar_url)
        ticket_embed.description = "Thanks for creating this support ticket! " \
                                   "Please leave your message below " \
                                   "and wait for an answer from one of the support team members.\n" \
                                   f"**Ticket Subject:** {subject}"
        ticket_embed.set_footer(text=f"Ticket #{ticket_id}")
        ticket_pin = await channel.send(embed=ticket_embed)
        await ticket_pin.pin()
        ticket_type = 1 if subject == reactions_dict['❓'] else 2 if subject == reactions_dict['<:privacy:733465503594708992>'] else 3 if subject == reactions_dict['<:partner:748833273383485440>'] else 4

        try:
            await user.send(f"I've successfully created your ticket `#{ticket_id}` and set the subject to: {subject}")
        except Exception:
            pass

        log_embed = discord.Embed(color=2007732, timestamp=datetime.utcnow())
        log_embed.set_author(name=f"Ticket opened by {user} ({user.id})", icon_url=user.avatar_url)
        log_embed.description = f"**Ticket Subject:** {subject}"
        log_embed.add_field(name="Channel:", value=channel.mention)
        log_embed.add_field(name="User:", value=f"[{user}](https://discord.com/users/{user.id})")
        log_embed.set_footer(text=f"Ticket #{ticket_id}")
        log_channel = self.bot.get_channel(config.LOG_ID)
        log_msg = await log_channel.send(embed=log_embed)
        query = 'UPDATE tickets SET ticket_type = $1, log_message = $2, ticket_pin = $3, ticket_id = $4 WHERE user_id = $5 AND status = $6'
        await self.bot.db.execute(query, ticket_type, log_msg.id, ticket_pin.id, ticket_id, user.id, 0)

    async def close_ticket(self, ticket_channel, ticket_id, user, mod, reason):
        try:
            def check(c):
                return c.channel.id == ticket_channel.id

            confirm_message = await ticket_channel.send("Deleting ticket in 15 seconds. To abort please send a message.")

            try:
                confirm_close = await self.bot.wait_for('message', check=check, timeout=15.0)

                if confirm_close:
                    return await confirm_message.edit(content='Not closing the ticket.')
            except Exception:
                await confirm_message.edit(content="Closing ticket...")

            ticket_info = await self.bot.db.fetchval("SELECT log_message FROM tickets WHERE ticket_channel = $1", ticket_channel.id)
            log_message = await self.bot.get_channel(config.LOG_ID).fetch_message(ticket_info)
            messages = []
            for message in await ticket_channel.history().flatten():
                messages.append(f"[{message.created_at}] {message.author} - {message.content}\n")

            messages.reverse()
            file = discord.File(BytesIO(("".join(messages)).encode("utf-8")), filename=f"ticket-{ticket_id}.txt")

            log_channel = self.bot.get_channel(config.LOG_ID)
            log_file = await log_channel.send(content=f"{log_message.jump_url}", file=file)
            url = f"https://txt.discord.website/?txt={log_channel.id}/{log_file.attachments[0].id}/ticket-{ticket_id}"

            embed = log_message.embeds[0]
            embed.color = 13388105
            embed.remove_field(0)
            embed.insert_field_at(0, name="Channel:", value=f"[#{ticket_channel.name}]({url})")
            embed.description += f"\n**Ticket closed by:** {mod} ({mod.id})\n**Reason:** {reason}"
            await log_message.edit(embed=embed)
            await ticket_channel.delete(reason=f'Ticket closed by {mod} ({mod.id}) - {reason}')
            query = 'UPDATE tickets SET status = $1, reason = $2 WHERE ticket_channel = $3'
            await self.bot.db.execute(query, 1, reason, ticket_channel.id)

            send_embed = discord.Embed(color=13388105, title='Ticket Closed!', timestamp=datetime.utcnow())
            send_embed.set_author(name=mod, icon_url=mod.avatar_url)
            send_embed.description = f"Hey!\n{mod} closed your ticket for: {reason}.\n" \
                                     f" You can look at the full ticket transaction by [`clicking here`]({url})"
            send_embed.set_footer(text=f'Your ticket id was #{ticket_id}')

            try:
                user = self.bot.get_user(user)
                await user.send(embed=send_embed)
            except Exception as e:
                print(e)
                return

        except Exception as e:
            print('error: ' + e)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.guild_id != config.GUILD_ID:
            return

        guild = self.bot.get_guild(payload.guild_id)
        user = guild.get_member(payload.user_id)
        channel = payload.member.guild.get_channel(config.TICKET_ID)
        message = await channel.fetch_message(config.TICKET_MSG_ID)
        check = await self.bot.db.fetchval("SELECT ticket_channel FROM tickets WHERE user_id = $1 AND status = $2", user.id, 0)

        if payload.message_id == config.TICKET_MSG_ID:
            await message.remove_reaction(payload.emoji, payload.member)
            if str(payload.emoji) == '🎫':
                if check:
                    try:
                        return await user.send(f"Hey! You already have a support ticket opened at {self.bot.get_channel(check).mention}.")
                    except Exception:
                        return
                await self.open_ticket(guild, user)

    @commands.command(name='close-ticket',
                      aliases=['closeticket', 'close'])
    @commands.guild_only()
    @commands.has_role(config.SUPPORT_ID)
    async def closeticket(self, ctx, *, reason: str):
        """ Close a support ticket """
        check = await self.bot.db.fetch("SELECT user_id, ticket_id FROM tickets WHERE ticket_channel = $1", ctx.channel.id)

        if not check:
            return await ctx.send(f"This channel isn't a ticket.", delete_after=15)
        elif check:
            await self.close_ticket(ctx.channel, check[0]['ticket_id'], check[0]['user_id'], ctx.author, reason)


def setup(bot):
    bot.add_cog(tickets(bot))