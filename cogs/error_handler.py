import math
import sys
import traceback

import discord
from discord.ext import commands
from utils import libs, checks


class ErrorHandler(commands.Cog, name="error handler"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):

        if hasattr(ctx.command, "on_error"):
            return

        ignored = (commands.CommandNotFound, commands.NotOwner)
        error = getattr(error, "original", error)
        command_used = ctx.invoked_with

        if isinstance(error, ignored):
            return

        if isinstance(error, commands.CommandOnCooldown):
            return await ctx.send(
                f"You can do `{command_used}` again in {math.floor(error.retry_after * 100) / 100} seconds"
            )

        elif isinstance(error, commands.TooManyArguments):
            return await ctx.send(f"The command `{command_used}` was used with too many arguments")

        elif isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="Error",
                description=f"You do not have the permissions `({', '.join(error.missing_permissions)})` to use `{command_used}`!",
                color=libs.pastel_color(),
            )
            return await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="Error",
                description=f"You're missing the required argument `{error.param.name}`\nUsage: `{libs.get_command_signature(ctx, ctx.command)}`",
                color=libs.pastel_color(),
            )
            return await ctx.send(embed=embed)
        elif isinstance(error, commands.UserInputError):
            return await ctx.send(
                f"The command `{command_used}` was used incorrectly\nUsage: `{libs.get_command_signature(ctx, ctx.command)}`"
            )
        elif isinstance(error, checks.NotGuildOwner):
            return await ctx.send(f'The command `{command_used}` can only be used by the server owner.')
        elif isinstance(error, checks.NotBotAdmin):
            return await ctx.send(f'The command `{command_used}` can only be used by bot admins.')
        else:
            print(f"Ignoring exception in command {ctx.command}", file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))
