import glob
import random

import discord
from discord.ext import commands

max_len = 2000


def linecount():
    linecount = 0
    for file in glob.glob("./**/*.py", recursive=True):
        try:
            with open(file, "rb") as f:
                linecount += len(f.readlines())
        except:
            pass
    return linecount


def neon_color():
    return discord.Color.from_hsv(random.random(), 0.7, 1.0)


def pastel_color():
    return discord.Color.from_hsv(random.random(), 0.28, 0.97)


def check_list(list):
    return len(list) == 0


def convert_timedelta(duration):
    days, seconds = duration.days, duration.seconds
    hours = seconds // 3600
    return days, hours


def split_message(message, prefix="", suffix=""):
    lines = [prefix]
    for line in message.split("\n"):
        if len(lines[-1] + line + "\n" + suffix) > max_len:
            lines[-1] += suffix
            lines.append(prefix)
        lines[-1] += line + "\n"
    lines[-1] += suffix
    return lines


def get_command_signature(ctx: commands.Context, command: commands.Command):
    parent = command.full_parent_name
    if len(command.aliases) > 0:
        aliases = "|".join(command.aliases)
        fmt = f"[{command.name}|{aliases}]"
        if parent:
            fmt = f"{parent} {fmt}"
        alias = fmt
    else:
        alias = f"{parent} {command.name}" if parent else command.name
    return f'{ctx.clean_prefix}{alias} {command.signature.replace("=None", "")}'


async def get_added_by(client: discord.Client, guild: discord.Guild):
    async for entry in guild.audit_logs(action=discord.AuditLogAction.bot_add, limit=5):
        # limit is 5 for redundancy if multiple bots are added at once for some reason
        if entry.target.id == client.user.id:
            return entry.user.id


async def get_prefix(bot, message):
    if message.guild is None:
        return bot.config.get("default_prefix")
    try:
        return bot.prefixes[message.guild.id]
    except KeyError:
        async with bot.db_pool.acquire() as connection:
            async with connection.transaction():
                prefix = await connection.fetchval("SELECT prefix FROM guilds WHERE id = $1", message.guild.id)
                if prefix:
                    bot.prefixes[message.guild.id] = prefix
                    return prefix
                else:
                    bot.prefixes[message.guild.id] = bot.config.get("default_prefix")
                    return bot.prefixes[message.guild.id]


async def callable_prefix(bot, message):
    if message.guild is None:
        return commands.when_mentioned_or(bot.config.get("default_prefix"))(bot, message)

    try:
        return commands.when_mentioned_or(bot.prefixes[message.guild.id])(bot, message)
    except KeyError:
        async with bot.db_pool.acquire() as connection:
            async with connection.transaction():
                prefix = await connection.fetchval("SELECT prefix FROM guilds WHERE id = $1", message.guild.id)
                bot.prefixes[message.guild.id] = prefix or bot.config.get("default_prefix")
                return commands.when_mentioned_or(bot.prefixes[message.guild.id])(bot, message)
