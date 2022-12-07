import os
import re
import time

import discord
import psutil
from discord.ext import commands
from discord.ui import Button, View

from utils import libs


class AboutDependencies(discord.ui.View):
    def __init__(self, user: commands.Author, message: discord.Message, initial_embed: discord.Embed):
        super().__init__(timeout=120)
        self.user = user
        self.message = message
        self.initial_embed = initial_embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.user:
            await interaction.response.send_message("You can't use this button!", ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        await self.message.edit(view=None)
        return await super().on_timeout()

    @discord.ui.button(
        label='Dependencies',
        custom_id="dependencies_button",
        style=discord.ButtonStyle.blurple,
    )
    async def _dependencies(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.disabled = True
        for child in self.children:
            if child.custom_id == "go_back:deps":
                child.disabled = False

        deps_embed = discord.Embed(title="Dependencies and Versions", color=libs.pastel_color())

        with open("./requirements.txt", "r") as file:
            contents = file.read()

        dependencies = {}
        for line in contents.splitlines():
            package, version = line.split("==")
            dependencies[package] = version

        deps_embed.description = "\n".join(f"`{dependency}: {version}`" for dependency, version in dependencies.items())
        await interaction.response.edit_message(embed=deps_embed, view=self)

    @discord.ui.button(
        label='Back',
        disabled=True,
        custom_id="go_back:deps",
        style=discord.ButtonStyle.red,
    )
    async def _go_back(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.disabled = True
        for child in self.children:
            if child.custom_id == 'dependencies_button':
                child.disabled = False

        await interaction.response.edit_message(content=None, embed=self.initial_embed, view=self)


class Main(commands.Cog, name="main"):
    def __init__(self, bot):
        self.bot = bot
        self.process = psutil.Process(os.getpid())

    @commands.Cog.listener(name="on_message")
    async def mention_responder(self, message):
        if re.fullmatch(rf"<@!?{self.bot.user.id}>", message.content):
            em = discord.Embed(
                description=f'Hello! My prefix here is `{await libs.get_prefix(self.bot, message)}`',
                color=libs.pastel_color(),
            )
            return await message.reply(embed=em)
        return

    @commands.hybrid_command(name='invite', aliases=['inv'], with_app_command=True, description="Invite the Bot!")
    async def invite(self, ctx):
        invite_btn = Button(
            label="Invite Me!",
            style=discord.ButtonStyle.link,
            url="https://discord.com/api/oauth2/authorize?client_id=770072464767713280&permissions=8&scope=bot%20applications.commands",
        )
        view = View()
        view.add_item(invite_btn)
        await ctx.send(view=view)

    @commands.hybrid_command(name="prefix", with_app_command=True, description="Change the current guild's prefix.")
    @commands.cooldown(1, 60, type=commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True)
    async def prefix(self, ctx, prefix: str) -> None:
        if len(prefix) > 15:
            return await ctx.send("The prefix can't be longer than 15 characters.")
        async with self.bot.db_pool.acquire() as connection:
            async with connection.transaction():
                current_prefix = await connection.fetchval("SELECT prefix FROM guilds WHERE id = $1", ctx.guild.id)
                if current_prefix:
                    await connection.execute("UPDATE guilds SET prefix = $1 WHERE id = $2", prefix, ctx.guild.id)
                    self.bot.prefixes[ctx.guild.id] = prefix
                    await ctx.reply(f"My prefix in `{ctx.guild.name}` has been updated to `{prefix}`")
                else:
                    await connection.execute(
                        "INSERT INTO guilds(id,prefix) VALUES($1,$2) ON CONFLICT (id) DO UPDATE SET prefix = $2",
                        ctx.guild.id,
                        prefix,
                    )
                    self.bot.prefixes[ctx.guild.id] = prefix
                    await ctx.reply(f"My prefix in `{ctx.guild.name}` has been changed to `{prefix}`")

    @commands.hybrid_command(
        name="whois", aliases=['userinfo', 'ui'], with_app_command=True, description="Get a users account details"
    )
    async def user_info(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author
        member_position = sum(
            m.joined_at < member.joined_at for m in ctx.guild.members if m.joined_at is not None and m.bot == False
        )

        spotify = discord.utils.find(lambda a: isinstance(a, discord.Spotify), member.activities)
        if spotify is None:
            em = discord.Embed(description=f"Nickname: `{member.nick}`\nNot on Spotify </3", color=libs.pastel_color())
        else:
            params = {
                'title': spotify.title,
                'cover_url': spotify.album_cover_url,
                'duration_seconds': spotify.duration.seconds,
                'start_timestamp': spotify.start.timestamp(),
                'artists': spotify.artists,
            }

            artists = ', '.join(params['artists'])
            em = discord.Embed(
                description=f"Nickname: `{member.nick}`\nListening to **{params['title']}** by **{artists}**",
                color=libs.pastel_color(),
            )

        em.set_author(name=str(member), icon_url=member.display_avatar.url)
        em.set_thumbnail(url=member.display_avatar.url)
        em.add_field(
            name="Joined",
            value=f"{discord.utils.format_dt(ctx.author.joined_at)} ({discord.utils.format_dt(ctx.author.joined_at, style='R')})",
            inline=False,
        )
        em.add_field(
            name="Registered",
            value=f"{discord.utils.format_dt(ctx.author.created_at)} ({discord.utils.format_dt(ctx.author.created_at, style='R')})",
            inline=False,
        )
        em.add_field(name="Mutual Servers", value=f"You are in `{len(member.mutual_guilds)}` servers with the bot!")
        em.set_footer(
            text=f"User ID: {member.id} | Join Position: {member_position:,}/{ctx.guild.member_count:,} | Date: {ctx.message.created_at.strftime('%m/%d/%Y')}"
        )
        if len(member.roles) > 25:
            em.add_field(name=f"Roles [{len(member.roles)-1}]", value='Too many roles to show!', inline=False)
            return await ctx.send(embed=em)
        elif len(member.roles) > 1:
            em.add_field(
                name=f"Roles [{len(member.roles)-1}]",
                value=', '.join([r.mention for r in member.roles][1:]),
                inline=False,
            )
        await ctx.send(embed=em)

    @commands.hybrid_command(name="serverinfo", with_app_command=True, description="Get server info")
    async def server_info(self, ctx):
        result = self.bot.time_now - ctx.guild.created_at
        days, hours = libs.convert_timedelta(result)
        em = discord.Embed(
            title=ctx.guild.name,
            description=f"__{len(ctx.guild.members):,}__ member(s) are in this server!",
            color=libs.pastel_color(),
        )

        em.add_field(name="Owner", value=ctx.guild.owner, inline=True)
        em.add_field(
            name="Information",
            value=f"**Level:** {ctx.guild.premium_subscription_count} Boosts (lvl {ctx.guild.premium_tier})\n**Boosters:** {len(ctx.guild.premium_subscribers)}",
        )

        try:
            if ctx.guild.premium_tier == 3:
                em.add_field(
                    name="Graphics",
                    value=f"**Banner:** [Click Here]({ctx.guild.banner.url})\n**Splash:** [Click Here]({ctx.guild.splash.url})\n**Icon:** [Click Here]({ctx.guild.icon.url})",
                    inline=False,
                )

            elif ctx.guild.premium_tier == 2:
                em.add_field(
                    name="Graphics",
                    value=f"**Banner:** [Click Here]({ctx.guild.banner.url})\n**Splash:** [Click Here]({ctx.guild.splash.url})\n**Icon:** [Click Here]({ctx.guild.banner.url})",
                    inline=False,
                )

            elif ctx.guild.premium_tier == 1:
                em.add_field(
                    name="Graphics",
                    value=f"**Splash:** [Click Here]({ctx.guild.splash.url})\n**Icon:** [Click Here]({ctx.guild.banner.url})",
                    inline=False,
                )

            elif ctx.guild.premium_tier == 0:
                em.add_field(name="Graphics", value=f"**Icon:** [Click Here]({ctx.guild.icon.url})", inline=False)

            em.set_thumbnail(url=ctx.guild.icon.url)
        except AttributeError:
            em.add_field(name="Graphics", value="This server has no graphics!", inline=False)

        if hours == 0:
            footer_text = f"The server is {days} days old • Guild ID: {ctx.guild.id}"
        elif days == 0:
            footer_text = f"The server is {hours} hours old • Guild ID: {ctx.guild.id}"
        else:
            footer_text = f"The server is {days} days and {hours} hours old • Guild ID: {ctx.guild.id}"

        em.set_footer(text=footer_text)
        await ctx.send(embed=em)

    # shows some info about a role
    @commands.hybrid_command(
        name="roleinfo", aliases=['ri'], with_app_command=True, description="Role information like color, id, etc"
    )
    async def role_info(self, ctx, *, rolename=None):
        if rolename is None:
            return await ctx.send(f"`Usage: {await libs.get_prefix(self.bot, ctx.message)}roleinfo <roleinfo>`")

        for i in ctx.guild.roles:
            if rolename in i.name:
                rolename = i.name
            elif rolename in i.name.lower():
                rolename = i.name
        role = discord.utils.get(ctx.guild.roles, name=rolename)
        em = discord.Embed(title=role.name, description=f"{len(role.members)} member(s) have this role!", color=role.color)

        em.add_field(name="Role ID", value=f"{role.id}", inline=True)
        em.add_field(name="Color", value=f"{role.color}", inline=True)
        em.add_field(name="Guild", value=f"{ctx.guild.name} ({ctx.guild.id})", inline=False)

        try:
            em.set_thumbnail(url=role.icon.url)
        except AttributeError:
            if ctx.guild.icon:
                em.set_thumbnail(url=ctx.guild.icon.url)
        result = self.bot.time_now - role.created_at
        days, hours = libs.convert_timedelta(result)
        if hours == 0:
            footer_text = text = f"This role is {days} days old"
        elif days == 0:
            footer_text = f"This role is {hours} hours old"
        else:
            footer_text = f"This role is {days} days and {hours} hours old"
        em.set_footer(text=footer_text)
        await ctx.send(embed=em)

    @commands.hybrid_command(
        name='about', aliases=['ping', 'stats'], with_app_command=True, description='Gets various bot stats'
    )
    async def about(self, ctx):
        host = self.process
        embed_desc = f"There are `{libs.linecount():,}` lines of code.\nBot was started on {discord.utils.format_dt(self.bot.time_now, style='f')}."
        developers = f"{self.bot.get_user(739219467455823921)}\n{self.bot.get_user(524016475661664256)}"
        information = f'''
Guilds: `{len(self.bot.guilds):,}`
Users: `{len(self.bot.users):,}`
'''
        before_check = time.monotonic()
        await ctx.channel.typing()
        after_check = time.monotonic()
        api_latency = (after_check - before_check) * 1000
        embed = discord.Embed(title='Spork Stats', description=embed_desc, color=libs.pastel_color())
        embed.add_field(name='Developers', value=developers, inline=False)
        embed.add_field(name='Bot Info', value=information, inline=False)
        embed.add_field(
            name='Host Info',
            value=f'CPU Usage: `{host.cpu_percent()}%`\nRAM Usage: `{str(host.memory_percent())[:4]}%`\nRunning on `{host.num_threads()}` threads',
            inline=False,
        )
        embed.add_field(
            name='Bot Latency',
            value=f'Latency: `{round(self.bot.latency * 1000)}ms`\nAPI Latency: `{int(api_latency)}ms`',
            inline=False,
        )
        embed.set_footer(text=f"Made with discord.py {discord.__version__}")
        fetching = await ctx.send("Fetching data...")
        await fetching.edit(
            content=None, embed=embed, view=AboutDependencies(user=ctx.author, message=fetching, initial_embed=embed)
        )


async def setup(bot):
    await bot.add_cog(Main(bot))
