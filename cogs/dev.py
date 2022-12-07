import asyncio
import datetime
import io
import textwrap
import traceback
from contextlib import redirect_stdout

import discord
from discord.ext import commands
from utils import libs
from utils.checks import *


class ButtonOnCooldown(commands.CommandError):
    def __init__(self, retry_after: float):
        self.retry_after = retry_after


def key(interaction: discord.Interaction):
    return interaction.user


class SuggestionButtonView(discord.ui.View):
    def __init__(self, user: commands.Context.author, bot: commands.Bot):
        super().__init__(timeout=120)
        self.user = user
        self.bot = bot
        self.cd = commands.CooldownMapping.from_cooldown(1, 60, key)

    async def interaction_check(self, interaction: discord.Interaction):
        retry_after = self.cd.update_rate_limit(interaction)

        if interaction.user != self.user:
            await interaction.response.send_message("You can't use this button!", ephemeral=True)
            return False

        if retry_after:
            raise ButtonOnCooldown(retry_after)

        return True

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item):
        if isinstance(error, ButtonOnCooldown):
            cooldown_timer = int(error.retry_after)
            cooldown_display = discord.utils.format_dt(
                discord.utils.utcnow() + datetime.timedelta(seconds=cooldown_timer),
                style="R",
            )
            await interaction.response.send_message(
                f"This button is on cooldown, you can suggest again in {cooldown_display}.",
                ephemeral=True,
            )
            await discord.utils.sleep_until(discord.utils.utcnow() + datetime.timedelta(seconds=cooldown_timer))
            await interaction.edit_original_response(content="The button is no longer on cooldown, you can suggest again!")
        else:
            await super().on_error(interaction, error, item)

    @discord.ui.button(label="Make a Suggestion", style=discord.ButtonStyle.primary)
    async def suggestion_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SuggestionModal(user=self.user, bot=self.bot))


class SuggestionModal(discord.ui.Modal):
    def __init__(self, user: discord.User, bot: commands.Bot):
        super().__init__(title="Suggestion")
        self.user = user
        self.bot = bot

    suggestion = discord.ui.TextInput(
        label="What is your suggestion?",
        placeholder="Type your suggestion here...",
        min_length=20,
        max_length=2000,
        style=discord.TextStyle.paragraph,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("Thank you for your suggestion!", ephemeral=True)

        suggest_dest = self.bot.get_channel(1000151288975204372)
        embed = discord.Embed(description=self.suggestion.value, color=0xFFFFFF)
        embed.set_author(name=self.user, icon_url=self.user.avatar.url)
        embed.set_footer(text=f"User ID: {self.user.id}")
        await suggest_dest.send(
            f"{discord.utils.format_dt(discord.utils.utcnow())} ({discord.utils.format_dt(discord.utils.utcnow(), style='R')})",
            embed=embed,
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message("You sir, fucked something up!", ephemeral=True)
        traceback.print_tb(error.__traceback__)


class DeveloperCommands(commands.Cog, name="developer"):
    def __init__(self, bot):
        self.bot = bot
        self._last_result = None

    def cleanup_code(self, content):
        if content.startswith("```") and content.endswith("```"):
            return "\n".join(content.split("\n")[1:-1])
        return content.strip("` \n")

    @commands.hybrid_command(name="suggest", description="Suggest a feature for the bot")
    @commands.cooldown(1, 60, type=commands.BucketType.user)
    async def suggest(self, ctx: commands.Context):

        if ctx.interaction:
            return await ctx.interaction.response.send_modal(SuggestionModal(user=ctx.interaction.user, bot=self.bot))

        embed = discord.Embed(
            description="Click the button below to make a suggestion!",
            color=libs.pastel_color(),
        )
        await ctx.send(embed=embed, view=SuggestionButtonView(user=ctx.author, bot=self.bot))

    # sets a reminder for a user
    @commands.command(aliases=["reminder"])
    @is_admin()
    async def remind(self, ctx, time: int, *, message: str):
        await ctx.send(
            f'I set your reminder for "`{message}`"',
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=False, replied_user=False),
        )
        seconds = time * 60
        await asyncio.sleep(int(seconds))
        em = discord.Embed(description=message, color=libs.pastel_color())
        await ctx.send(
            f"{ctx.author.mention}",
            embed=em,
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, replied_user=False),
        )

    # shows admin help command
    @commands.command()
    @is_admin()
    async def admin(self, ctx):
        adm_cmds = [
            f"`{command.name}` {f' - {command.description}' if command.description else ''} {'' if len(command.aliases) == 0 else f'`{command.aliases}`'} {'' if command.usage is None else f'`[{command.usage}]`'}"
            for command in self.bot.get_cog("developer").walk_commands()
        ]

        em = discord.Embed(
            title="Bot Admin Commands",
            description="\n".join(adm_cmds),
            color=libs.pastel_color(),
        )

        await ctx.send(embed=em)

    @commands.group(
        name="ls",
        invoke_without_command=True,
        description="List all servers the bot is in",
    )
    @is_real_owner()
    async def list_servers(self, ctx):
        server_list = [
            "Guild Name: {} | Guild ID: {} | Member Count: {:,}".format(guild.name, guild.id, len(guild.members))
            for guild in self.bot.guilds
        ]

        await ctx.send(
            "```md\n* Servers -\n# I am in {:,} servers ({})```".format(
                len(self.bot.guilds), discord.utils.utcnow().strftime("%m-%d-%y")
            )
        )

        for m in libs.split_message("\n".join(server_list), "```", "```"):
            await ctx.send(m)

    @list_servers.command(name="leave", description="Leave a server")
    @is_real_owner()
    async def leave_server(self, ctx, guild: discord.Guild):
        guild_name = guild.name
        await guild.leave()
        await ctx.send(f"I have left `{guild_name}`")

    @commands.command(name="eval")
    @eval_perms()
    async def _eval(self, ctx, *, body: str):
        """
        Executes code within a discord bot
        """
        env = {
            "bot": self.bot,
            "ctx": ctx,
            "channel": ctx.channel,
            "author": ctx.author,
            "guild": ctx.guild,
            "message": ctx.message,
            "_": self._last_result,
        } | globals()

        body = self.cleanup_code(body)
        stdout = io.StringIO()
        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'
        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(f"```\n{e.__class__.__name__}: {e}\n```")
        func = env["func"]
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            await ctx.send(f"```\n{value}{traceback.format_exc()}\n```")
        else:
            value = stdout.getvalue()
            if ret is None:
                if value:
                    await ctx.send(f"```\n{value}\n```")
            else:
                self._last_result = ret
                await ctx.send(f"```\n{value}{ret}\n```")


async def setup(bot):
    await bot.add_cog(DeveloperCommands(bot))
