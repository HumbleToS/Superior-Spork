import logging
import os
import pathlib

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands, tasks

from utils import checks, libs

_logger = logging.getLogger(__name__)


class BotLogs(commands.Cog, name="bot logs"):
    def __init__(self, bot):
        self.bot = bot
        self.presence_loop.start()

    def cog_unload(self):
        self.presence_loop.cancel()

    @tasks.loop(minutes=15)
    async def presence_loop(self):
        status = discord.Activity(type=discord.ActivityType.watching, name=f"over {len(self.bot.guilds):,} servers")
        await self.bot.change_presence(status=discord.Status.idle, activity=status)

    @presence_loop.before_loop
    async def before_presence(self):
        _logger.info("Websocket is starting...")
        await self.bot.wait_until_ready()
        _logger.info("Websocket has started!")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        joinLogChannel = self.bot.get_channel(1018775340333670430)
        em = discord.Embed(
            title="Joined a Server",
            description=f"Name: {guild.name}\nOwner: {guild.owner}\nMembers: {len(guild.members):,}",
            color=libs.pastel_color(),
        )
        if guild.icon:
            em.set_thumbnail(url=guild.icon.url)
        else:
            em.set_thumbnail(url='https://cdn.discordapp.com/embed/avatars/1.png')
        em.set_footer(text=f"Guild ID: {guild.id}")
        await joinLogChannel.send(embed=em)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        joinLogChannel = self.bot.get_channel(1018775340333670430)
        em = discord.Embed(
            title="Left a Server",
            description=f"Name: {guild.name}\nOwner: {guild.owner}\nMembers: {len(guild.members):,}",
            color=libs.pastel_color(),
        )
        if guild.icon:
            em.set_thumbnail(url=guild.icon.url)
        else:
            em.set_thumbnail(url='https://cdn.discordapp.com/embed/avatars/1.png')
        em.set_footer(text=f"Guild ID: {guild.id}")
        await joinLogChannel.send(embed=em)

    @app_commands.command(name='cog', description='Reload, unload or load cogs!')
    @app_commands.choices(
        options=[
            Choice(name='load', value='load'),
            Choice(name='unload', value='unload'),
            Choice(name='reload', value='reload'),
            Choice(name='load all', value='loadall'),
            Choice(name='reload all', value='reloadall'),
        ]
    )
    @checks.is_real_owner()
    async def cog(self, interaction: discord.Interaction, options: Choice[str], extension: str = None):
        if options.value == 'load':
            try:
                await self.bot.load_extension(extension)
            except commands.errors.ExtensionAlreadyLoaded:
                await interaction.response.send_message(f'The cog `{extension}` is already loaded!')

            await interaction.response.send_message(f'The extension `{extension}` has been loaded!')

        elif options.value == 'unload':
            try:
                await self.bot.unload_extension(extension)
            except commands.errors.ExtensionNotLoaded:
                await interaction.response.send_message(f"The cog `{extension}` wasn't loaded!")

            await interaction.response.send_message(f'The extension `{extension}` has been unloaded!')

        elif options.value == 'reload':
            await self.bot.reload_extension(extension)
            await interaction.response.send_message(f'The extension `{extension}` has been reloaded!')

        elif options.value == 'loadall':
            for file in sorted(pathlib.Path("cogs").glob("**/[!_]*.py")):
                cog = ".".join(file.parts).removesuffix(".py")
                try:
                    await self.bot.load_extension(cog)
                except commands.errors.ExtensionAlreadyLoaded:
                    pass
            await interaction.response.send_message(f'All unloaded extensions have been loaded!')

        elif options.value == 'reloadall':
            for file in sorted(pathlib.Path("cogs").glob("**/[!_]*.py")):
                cog = ".".join(file.parts).removesuffix(".py")
                await self.bot.reload_extension(cog)
            await interaction.response.send_message(f'Reloaded all extensions!')

    @cog.autocomplete('extension')
    async def autocomplete_callback(self, interaction: discord.Interaction, current: str):
        extensions = []
        for file in sorted(pathlib.Path("cogs").glob("**/[!_]*.py")):
            cog = ".".join(file.parts).removesuffix(".py")
            extensions.append(cog)

        return [
            Choice(name=extension.split('.')[1], value=extension.lower())
            for extension in extensions
            if current.lower() in extension.lower()
        ][:25]

    @commands.command(name="module", aliases=['m'])
    @checks.is_real_owner()
    async def module(self, ctx, option=None, *, extension=None):
        if option is None:
            return await ctx.send(f"Usage: `{ctx.clean_prefix}module <load[l]/unload[u]/reload[r]> <module>`")
        elif option == 'l':
            extension = extension.replace(" ", "_")
            await self.bot.load_extension(f'cogs.{extension}')
            await ctx.send(f'Loaded {extension} cog!')
        elif option == 'u':
            extension = extension.replace(" ", "_")
            await self.bot.unload_extension(f'cogs.{extension}')
            await ctx.send(f'Unloaded {extension} cog!')
        elif option == 'r':
            extension = extension.replace(" ", "_")
            if extension == 'all':
                for filename in os.listdir('./cogs'):
                    if filename.endswith('.py'):
                        await self.bot.reload_extension(f'cogs.{filename[:-3]}')
                await ctx.send('Reloaded all cogs!')
            else:
                await self.bot.reload_extension(f'cogs.{extension}')
                await ctx.send(f'Reloaded {extension} cog!')


async def setup(bot):
    await bot.add_cog(BotLogs(bot))
