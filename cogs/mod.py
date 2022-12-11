import asyncio
import datetime

import discord
from discord.ext import commands

from utils import libs
from utils.checks import *


class Moderation(commands.Cog, name="moderation"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="mod", with_app_command=True, description="Shows all moderation commands")
    async def mod_help(self, ctx):
        mod_cmds = [
            f"`{cmd.name}` - {cmd.description} {'' if len(cmd.aliases) == 0 else f'`{cmd.aliases}`'} {'' if cmd.usage is None else f'`[{cmd.usage}]`'}"
            for cmd in self.bot.get_cog("moderation").walk_commands()
        ]

        em = discord.Embed(
            title="Moderation",
            description="\n".join(mod_cmds),
            color=libs.pastel_color(),
        )
        em.set_footer(text="Moderation is constantly being worked on !")
        await ctx.send(embed=em)

    @commands.hybrid_command(name="clear", with_app_command=True, description="Delete an recreate a channel")
    @commands.has_permissions(manage_channels=True)
    @is_guild_owner()
    async def clear(self, ctx):
        def clear_check(m: discord.Message):
            return m.author == ctx.guild.owner and m.channel.id == ctx.channel.i

        await ctx.send(
            f"Are you sure you want to clear {ctx.channel.mention} `(this will delete the channel and create a new one in its place)`?\nPlease with respond with yes or no."
        )
        try:
            msg = await self.bot.wait_for("message", timeout=15, check=clear_check)
        except asyncio.TimeoutError:
            return await ctx.send("This command has expired!")
        else:
            if msg.content.lower() == "yes":
                new_channel = await ctx.channel.clone()
                await new_channel.edit(position=ctx.channel.position)
                await ctx.channel.delete()
                await new_channel.send(f"Cleared {new_channel.mention}!", delete_after=30)
            else:
                return await ctx.send("Channel clear avoided.")

    @commands.hybrid_command(
        name="addrole",
        aliases=["ar"],
        with_app_command=True,
        description="Gives a role to a member",
    )
    @commands.has_permissions(manage_roles=True)
    async def add_role(self, ctx, member: discord.Member, *, role_name: str):
        for i in ctx.guild.roles:
            if role_name in i.name:
                role_name = i.name
            elif role_name in i.name.lower():
                role_name = i.name
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            em = discord.Embed(
                title="Error",
                description=f"Role `{role_name}` was not found",
                color=libs.pastel_color(),
            )

            return await ctx.send(embed=em)
        if ctx.author.top_role <= role:
            em = discord.Embed(
                title="Error",
                description="That role can not be given by you",
                color=libs.pastel_color(),
            )

            return await ctx.send(embed=em)
        try:
            await member.add_roles(role)
            em = discord.Embed(
                title="Role Given",
                description=f"`+ Added {role.name} to {member}`",
                color=libs.pastel_color(),
            )

            await ctx.send(embed=em)
        except discord.Forbidden:
            em = discord.Embed(
                title="Error",
                description="I can not do this, I do not have permissions above the given role",
                color=libs.pastel_color(),
            )

            await ctx.send(embed=em)

    @commands.hybrid_command(
        name="createrole",
        aliases=["cr"],
        with_app_command=True,
        description="Creates a role",
    )
    @commands.has_permissions(manage_roles=True)
    async def create_role(self, ctx, *, role_name: str):
        created_role = await ctx.guild.create_role(name=role_name)
        em = discord.Embed(
            title="Role Created",
            description=f"`- Created Role: {created_role.name}`\n`- Role ID: {created_role.id}`",
            color=libs.pastel_color(),
        )
        await ctx.send(embed=em)

    @commands.hybrid_command(
        name="removerole",
        aliases=["rr"],
        with_app_command=True,
        description="Removes a role from a member",
    )
    @commands.has_permissions(manage_roles=True)
    async def remove_role(self, ctx, member: discord.Member, *, role_name: str):
        for i in ctx.guild.roles:
            if role_name in i.name:
                role_name = i.name
            elif role_name in i.name.lower():
                role_name = i.name
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if ctx.author.top_role <= role:
            em = discord.Embed(
                title="Error",
                description="`That role can not be taken by you`",
                color=libs.pastel_color(),
            )

            return await ctx.send(embed=em)
        try:
            await member.remove_roles(role)
            em = discord.Embed(
                title="Role Taken",
                description=f"`- Removed {role.name} from {member}`",
                color=libs.pastel_color(),
            )

            return await ctx.send(embed=em)
        except discord.errors.Forbidden:
            em = discord.Embed(
                title="Error",
                description="I can not do this, I do not have Permissions above the taken role",
                color=libs.pastel_color(),
            )

            return await ctx.send(embed=em)

    @commands.hybrid_command(name="ban", with_app_command=True, description="Ban a member from the server")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.User, *, reason: str = None):
        if reason is None:
            reason = "No reason provided"
        reason = f"{reason} / Done by {ctx.author}"
        check = ctx.guild.get_member(member.id)
        if check is None:
            await ctx.guild.ban(member, reason=reason)
            return await ctx.send(
                f"Banned {member} ({member.id})\nReason: {reason}",
                allowed_mentions=discord.AllowedMentions(users=False, roles=False),
            )

        if ctx.author.top_role <= check.top_role:
            return await ctx.send("That users perms are equal to or higher then yours!")
        try:
            await ctx.guild.ban(member, reason=reason)
            await ctx.send(
                f"Banned {member} ({member.id})\nReason: {reason}",
                allowed_mentions=discord.AllowedMentions(users=False, roles=False),
            )

        except discord.Forbidden:
            em = discord.Embed(
                title="Error",
                description="I do not have the permissions to ban that user",
                color=libs.pastel_color(),
            )

            return await ctx.send(embed=em)

    @commands.hybrid_command(name="unban", with_app_command=True, description="Unban a user from the server")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, member: discord.User):
        try:
            await ctx.guild.unban(discord.Object(id=member.id))
        except discord.NotFound:
            return await ctx.send("That user is not banned.")
        await ctx.send(
            f"Unbanned {member} ({member.id})",
            allowed_mentions=discord.AllowedMentions(users=False, roles=False),
        )

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.is_owner()
    async def massunban(self, ctx, *users: discord.User):
        unbanned_list = []
        for i in users:
            try:
                await ctx.guild.unban(i, reason=f"Mass unban / Done by {ctx.author}")
                unbanned_list.append(f"`{str(i)}`")
            except discord.NotFound:
                pass
        await ctx.send(
            f"Unbanned `{len(unbanned_list)}` users:\n{', '.join(unbanned_list) if unbanned_list else 'No users were unbanned'}"
        )

    @commands.hybrid_command(
        name="mute",
        aliases=["timeout"],
        with_app_command=True,
        description="Timeout a member",
    )
    @commands.has_permissions(moderate_members=True)
    async def mute(self, ctx, member: discord.Member, time: int, reason: str = None):
        if ctx.author.top_role <= member.top_role:
            return await ctx.send("That users perms are equal to or higher then yours!")
        if time > 30240:
            return await ctx.send("You can only timeout a user for 21 days (30,240 minutes!)")

        if member.is_timed_out():
            date_format = "%A, %d %B %Y %I:%M %p"
            return await ctx.send(f"That member is timed out until `{member.timed_out_until.strftime(date_format)}`")

        if reason is None:
            reason = "No reason provided"
        reason = f"{reason} / Done by {ctx.author}"
        try:
            await member.timeout(discord.utils.utcnow() + datetime.timedelta(minutes=time), reason=reason)

            await ctx.send(
                f"Timed out {member} for `{time:,}` minute(s).\nReason: {reason}",
                allowed_mentions=discord.AllowedMentions(users=False, roles=False),
            )

        except discord.Forbidden:
            em = discord.Embed(
                title="Error",
                description="I do not have the permissions to moderate that user",
                color=libs.pastel_color(),
            )

            return await ctx.send(embed=em)

    @commands.hybrid_command(name="unmute", with_app_command=True, description="Timeout a member")
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx, member: discord.Member, reason: str = None):
        if ctx.author.top_role <= member.top_role:
            return await ctx.send("That users perms are equal to or higher then yours!")
        if not member.is_timed_out():
            return await ctx.send("That member isn't timed out")
        if reason is None:
            reason = "No reason provided"
        reason = f"{reason} / Done by {ctx.author}"
        try:
            await member.edit(timed_out_until=None)
            await ctx.send(
                f"Removed timeout for {member}.",
                allowed_mentions=discord.AllowedMentions(users=False, roles=False),
            )

        except discord.Forbidden:
            em = discord.Embed(
                title="Error",
                description="I do not have the permissions to moderate that user",
                color=libs.pastel_color(),
            )

            return await ctx.send(embed=em)

    @commands.hybrid_command(name="kick", with_app_command=True, description="Kick a member from the server")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = None):
        if reason is None:
            reason = "No reason provided"
        reason = f"{reason} / Done by {ctx.author}"
        if ctx.author.top_role <= member.top_role:
            return await ctx.send("That users perms are equal to or higher then yours!")
        try:
            await member.kick(reason=reason)
            await ctx.send(
                f"Kicked {member} ({member.id})\nReason: {reason}",
                allowed_mentions=discord.AllowedMentions(users=False, roles=False),
            )

        except discord.Forbidden:
            em = discord.Embed(
                title="Error",
                description="I do not have the permissions to kick that user",
                color=libs.pastel_color(),
            )

            return await ctx.send(embed=em)

    # await ctx.channel.purge(limit={limit}, check=lambda m:"{msg}" in m.content)
    # await ctx.channel.purge(limit=500, check=lambda m:m.author.id==ctx.author.id)
    @commands.hybrid_group(name="purge", with_app_command=True, description="Purge messages in chat")
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int):
        async with ctx.typing():
            if amount > 201:
                if ctx.author.id in self.bot.owner_ids:
                    await ctx.message.delete()
                    deleted = await ctx.channel.purge(limit=amount)
                    return await ctx.send("Purged `{:,}` message(s) in {}}.".format(len(deleted), ctx.channel.mention))

                return await ctx.send("Purge Limit is 200")
            if not ctx.interaction:
                await ctx.message.delete()
            try:
                deleted = await ctx.channel.purge(limit=amount)
                await ctx.send(
                    "Purged `{:,}` message(s) in {}.".format(len(deleted), ctx.channel.mention),
                    delete_after=10,
                )

            except discord.errors.Forbidden:
                await ctx.send("I don't have permission to purge messages in this channel.")

    @purge.command(name="bots", description="Purge bot commands in chat")
    @commands.has_permissions(manage_messages=True)
    async def purge_bots(self, ctx, amount: int):
        async with ctx.typing():
            if not ctx.interaction:
                await ctx.message.delete()
            try:
                deleted_bot = await ctx.channel.purge(limit=amount, check=lambda m: m.author.bot == True)
                await ctx.send(f"Purged {len(deleted_bot):,} message(s) from bots!", delete_after=10)
            except discord.errors.Forbidden:
                await ctx.send("I don't have permission to purge messages in this channel.")

    @purge.command(name="user", description="Purge messages of a specific user")
    @commands.has_permissions(manage_messages=True)
    async def purge_user(self, ctx, member: discord.Member, amount: int):
        async with ctx.typing():
            if not ctx.interaction:
                await ctx.message.delete()
            try:
                deleted_user = await ctx.channel.purge(limit=amount, check=lambda m: m.author.id == member.id)
                await ctx.send(
                    f"Purged {len(deleted_user):,} message(s) from `{member}`!",
                    delete_after=10,
                )
            except discord.errors.Forbidden:
                await ctx.send("I don't have permission to purge messages in this channel.")

    @commands.hybrid_command(
        name="nick",
        aliases=["rename"],
        with_app_command=True,
        description="Change a members nickname",
    )
    @commands.has_permissions(manage_nicknames=True)
    async def nickname(self, ctx, member: discord.Member, *, nickname: str):
        await member.edit(nick=nickname)
        await ctx.send(
            f'{member.mention} was nicknamed to "`{nickname}`"',
            allowed_mentions=discord.AllowedMentions(users=False, roles=False),
        )


async def setup(bot):
    await bot.add_cog(Moderation(bot))
