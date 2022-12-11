import logging
import os
import pathlib
import random
from datetime import time, timezone
from typing import Optional

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands, tasks

from utils import libs

_logger = logging.getLogger(__name__)


class BotLogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.GUILD_LOG_CHANNEL_ID = bot.config.get("guild_join_leave_log_channel")
        self.presence_loop.start()

    def cog_unload(self):
        self.presence_loop.cancel()

    @tasks.loop(
        time=[
            time(hour=6, tzinfo=timezone.utc),
            time(hour=12, tzinfo=timezone.utc),
            time(hour=18, tzinfo=timezone.utc),
            time(hour=0, tzinfo=timezone.utc),
        ]
    )
    async def presence_loop(self):
        random_status = random.choice([discord.Status.online, discord.Status.dnd, discord.Status.idle])
        activity = discord.Activity(type=discord.ActivityType.watching, name=f"over {len(self.bot.guilds):,} servers")
        await self.bot.change_presence(status=random_status, activity=activity)

    @presence_loop.before_loop
    async def before_presence(self):
        _logger.info("Websocket is starting...")
        await self.bot.wait_until_ready()
        _logger.info("Websocket has started!")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        log_channel = self.bot.get_channel(self.GUILD_LOG_CHANNEL_ID)
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
        await log_channel.send(embed=em)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        log_channel = self.bot.get_channel(self.GUILD_LOG_CHANNEL_ID)
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
        await log_channel.send(embed=em)

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
    @commands.is_owner()
    async def cog(self, interaction: discord.Interaction, options: Choice[str], extension: Optional[str]):
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
    @commands.is_owner()
    async def module(self, ctx, option, *, extension: str = "all"):
        if option == 'l':
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
