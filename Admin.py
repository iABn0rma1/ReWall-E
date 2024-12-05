import discord
from discord.ext import commands, tasks

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def dm(self, ctx, user: discord.User, *, msg=None):
        """> DM a user"""
        if user != None and msg != None:
            try:
                msg = msg or "This Message is sent via DM"
                await user.send(msg)
                embed = discord.Embed(colour=discord.Colour.from_rgb(250,0,0))
                embed.add_field(name="Message:", value=f"`{msg}`", inline=False)
                embed.add_field(name="Sent to:", value=f"`{user.name}`")
                embed.add_field(name="Sent by:", value=f"`{ctx.author.name}`")
                await ctx.send(embed=embed)
            except:
                await ctx.channel.send("Couldn't dm the given user.")
        else:
            await ctx.channel.send("You didn't provide a user's id and/or a message.")

    @commands.command(pass_context=True)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def dm_role(self, ctx, role: discord.Role, *, msg=None):
        """> DM a user"""
        if role != None and msg != None:
            msg = msg or "This Message is sent via DM"
            role = role.members
            for member in role:
                member_id = member.id
                memeber = await self.bot.fetch_user(member_id)
                await member.send(msg)
                embed = discord.Embed(colour=discord.Colour.from_rgb(250, 0, 0))
                embed.add_field(name="Message:", value=f"`{msg}`", inline=False)
                embed.add_field(name="Sent to:", value=f"`{member}`")
                embed.add_field(name="Sent by:", value=f"`{ctx.author.name}`")
                await ctx.send(embed=embed)
        else:
            await ctx.channel.send("You didn't provide a user's id and/or a message.")

    @commands.command(pass_context=True)
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def say(self, ctx, channel: discord.TextChannel, *, msg):
        """> Make the bot say whatever you want"""
        await ctx.send(f'Message sent to {channel.mention}')
        await ctx.message.delete()
        await channel.send("{}".format(msg))

    @commands.command(name='edit')
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def edit(self, ctx, message_id, *, new_msg):
        """> Edit a text msg sent by the bot"""
        msg = await ctx.fetch_message(message_id)
        await msg.edit(content = new_msg)
        await ctx.message.delete()

    @commands.command(hidden=True)
    @commands.has_permissions(administrator = True)
    @commands.guild_only()
    async def announcement(self, ctx, channel: discord.TextChannel ,* ,msg):
        """> Announce anything in the mentioned Text Channel"""
        await ctx.send(f'Message sended to {channel.mention}')
        embed = discord.Embed(
            title = "New Announcement",
            description = msg,
            colour = discord.Colour.from_rgb(250, 0, 0))
        embed.set_author(name="刀ARK么れEMESIS")
        embed.set_thumbnail \
            (url='https://images-ext-1.discordapp.net/external/K5AsUVeDxdVXRiI2CXwLBzR5FnCL2FI3cxqgo6N_vqE/https/cdn.mee6.xyz/moderator-logs/719754177940684881/a_30a6d54032ce1f02d5358247058df837.gif')
        embed.set_footer(text="#NemesisAintBorn", icon_url='https://images-ext-1.discordapp.net/external/pd__2K3vSC-oG_qS3xref25-hpBehKYBsdPJc0i-tHM/https/media.discordapp.net/attachments/778268429715111957/779417104335372299/1605897884519.png')
        await channel.send(content=f"@everyone", embed=embed)

    @commands.command(hidden=True)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def edit_announcement(self, ctx, message_id, *, new_desc):
        """> Edit Announcement"""
        msg = await ctx.fetch_message(message_id)
        embed = discord.Embed(title="New Announcement", description=new_desc,
                              colour=discord.Colour.from_rgb(250, 0, 0),)
        embed.set_author(name="刀ARK么れEMESIS")
        embed.set_thumbnail(url='https://images-ext-1.discordapp.net/external/K5AsUVeDxdVXRiI2CXwLBzR5FnCL2FI3cxqgo6N_vqE/https/cdn.mee6.xyz/moderator-logs/719754177940684881/a_30a6d54032ce1f02d5358247058df837.gif')
        embed.set_footer(text="#NemesisAintBorn", icon_url='https://images-ext-1.discordapp.net/external/pd__2K3vSC-oG_qS3xref25-hpBehKYBsdPJc0i-tHM/https/media.discordapp.net/attachments/778268429715111957/779417104335372299/1605897884519.png')
        await msg.edit(content=f"@everyone", embed=embed)
        await ctx.message.delete()

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def imgembed(self, ctx, channel: discord.TextChannel, *, msg):
        """> Send an image in embed"""
        await ctx.send(f'Message sended to {channel.mention}')
        embed = discord.Embed(
            colour=discord.Colour.from_rgb(250, 0, 0))
        embed.set_image(url=msg)
        await channel.send(embed=embed)

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def edit_imgembed(self, ctx, message_id, *, new_url):
        """> Edit image embed"""
        msg = await ctx.fetch_message(message_id)
        embed = discord.Embed(colour=discord.Colour.from_rgb(250,0,0))
        embed.set_image(url = new_url)
        await msg.edit(embed=embed)
        await ctx.message.delete()

    @commands.command(hidden=True)
    @commands.has_permissions(administrator = True)
    @commands.guild_only()
    async def sayembed(self, ctx, channel: discord.TextChannel, tit ,* ,msg):
        """> Send embed with title"""
        await ctx.send(f'Message sended to {channel.mention}')
        embed = discord.Embed(
            title = tit,
            description = msg,
            colour = discord.Colour.from_rgb(250, 0, 0))
        await channel.send(embed=embed)

    @commands.command(hidden=True)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def edit_sayembed(self, ctx, message_id, new_tit, *, new_msg):
        """> Edit titled Embed"""
        msg = await ctx.fetch_message(message_id)
        embed = discord.Embed(
            title=new_tit,
            description=new_msg,
            colour=discord.Colour.from_rgb(250, 0, 0))
        await msg.edit(embed=embed)
        await ctx.message.delete()

    @commands.command()
    @commands.has_permissions(administrator = True)
    @commands.guild_only()
    async def embed(self, ctx, channel: discord.TextChannel ,* ,msg):
        """> Send an Embed"""
        await ctx.send(f'Message sended to {channel.mention}')
        embed = discord.Embed(
            description = msg,
            colour = discord.Colour.from_rgb(250, 0, 0))
        embed.set_footer(text="#NemesisAintBorn",
                         icon_url='https://images-ext-1.discordapp.net/external/pd__2K3vSC-oG_qS3xref25-hpBehKYBsdPJc0i-tHM/https/media.discordapp.net/attachments/778268429715111957/779417104335372299/1605897884519.png')
        await channel.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def edit_embed(self, ctx, message_id, *, new_msg):
        """> Edit embed"""
        log_channel = self.bot.get_channel(720169568965754932)
        msg = await ctx.fetch_message(message_id)
        embed = discord.Embed(
            description=new_msg,
            colour=discord.Colour.from_rgb(250, 0, 0))
        await msg.edit(embed=embed)
        await log_channel.send(f"Message editted {message_id}")
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(Admin(bot))