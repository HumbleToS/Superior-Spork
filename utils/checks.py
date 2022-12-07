import json

from discord.ext import commands

config = json.load(open(r"././config.json"))

default_prefix = config.get('default_prefix')
admins = config.get('admins')
owner = config.get('owner')
beta = config.get('beta')

rocky_cmds = [613202332880207872, 896130578221506610, 780417367548756000, 739219467455823921]
eval_users = [739219467455823921, 780417367548756000, 353340381359767552, 524016475661664256]


class NotGuildOwner(commands.CheckFailure):
    pass


class NotBotAdmin(commands.CheckFailure):
    pass


def is_nightmare():
    async def is_nightmare_check(ctx):
        return ctx.guild.id == 812691071867944971

    return commands.check(is_nightmare_check)


def is_dick_users():
    async def is_rocky_user_check(ctx):
        return ctx.author.id in rocky_cmds

    return commands.check(is_rocky_user_check)


def is_admin():
    async def is_admin_check(ctx):
        if ctx.author.id in admins + owner:
            return True
        else:
            raise NotBotAdmin

    return commands.check(is_admin_check)


def is_real_owner():
    async def is_real_owner_check(ctx):
        return ctx.author.id in owner

    return commands.check(is_real_owner_check)


def is_guild_owner():
    async def guild_owner(ctx):
        if ctx.guild is not None and ctx.author == ctx.guild.owner:
            return True
        else:
            raise NotGuildOwner

    return commands.check(guild_owner)


def eval_perms():
    async def eval_perms_check(ctx):
        return ctx.author.id in eval_users

    return commands.check(eval_perms_check)
