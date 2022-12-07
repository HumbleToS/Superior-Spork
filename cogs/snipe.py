import discord
from discord.ext import commands

from utils import libs


def snipe_embed(message):
    embed = discord.Embed(description=message[0], color=libs.pastel_color())
    embed.set_author(name=message[1], icon_url=message[2])
    return embed


def edit_snipe_embed(message):
    embed = discord.Embed(title="Edit Sniped", color=libs.pastel_color())
    embed.add_field(name="Before", value=message[0], inline=False)
    embed.add_field(name="After", value=message[1], inline=False)
    embed.set_footer(text=f"Message edited by {message[2]}")
    return embed


class Snipe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        try:
            del self.bot.snipes[guild.id]
            del self.bot.edit_snipes[guild.id]
        except KeyError:
            pass

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        try:
            del self.bot.snipes[channel.guild.id][channel.id]
            del self.bot.edit_snipes[channel.guild.id][channel.id]
        except KeyError:
            pass

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        if message.guild and message.author != self.bot.user:
            message_author = str(message.author)
            message_author_avatar = message.author.display_avatar.url
            try:
                self.bot.snipes[message.guild.id][message.channel.id] = [
                    message.content,
                    message_author,
                    message_author_avatar,
                ]
            except KeyError:
                self.bot.snipes[message.guild.id] = {
                    message.channel.id: [message.content, message_author, message_author_avatar]
                }
        return

    @commands.Cog.listener()
    async def on_message_edit(self, before_edit, after_edit):
        if before_edit.author.bot:
            return
        if before_edit.guild and before_edit.author != self.bot.user:
            edit_author = str(before_edit.author)
            try:
                self.bot.edit_snipes[before_edit.guild.id][before_edit.channel.id] = [
                    before_edit.content,
                    after_edit.content,
                    edit_author,
                ]
            except KeyError:
                self.bot.edit_snipes[before_edit.guild.id] = {
                    before_edit.channel.id: [before_edit.content, after_edit.content, edit_author]
                }
        return

    @commands.hybrid_command(name='snipe', aliases=['s'], description="Snipe the last deleted message")
    async def snipe(self, ctx):
        if not ctx.guild:
            return await ctx.send("This command can only be used in a server")
        try:
            sniped_message = self.bot.snipes[ctx.guild.id][ctx.channel.id]
        except KeyError:
            return await ctx.send(
                embed=discord.Embed(description="There are no deleted messages to snipe!", color=libs.pastel_color())
            )
        await ctx.send(f"{discord.utils.format_dt(discord.utils.utcnow())}", embed=snipe_embed(sniped_message))

    @commands.hybrid_command(name='editsnipe', aliases=['es'], description='Snipe the last edited message')
    async def edit_snipe(self, ctx):
        if not ctx.guild:
            return await ctx.send('This command can only be used in a server.')
        try:
            sniped_edit = self.bot.edit_snipes[ctx.guild.id][ctx.channel.id]
        except KeyError:
            return await ctx.send(embed=discord.Embed(description="There are no edits to snipe!", color=libs.pastel_color()))
        await ctx.send(f"{discord.utils.format_dt(discord.utils.utcnow())}", embed=edit_snipe_embed(sniped_edit))


async def setup(bot):
    await bot.add_cog(Snipe(bot))
