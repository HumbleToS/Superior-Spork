from typing import Union

import discord
from discord.ext import commands

from utils import checks, libs


class InviteInfoView(discord.ui.View):
    def __init__(
        self,
        user: Union[discord.Member, discord.User],
        message: discord.Message,
        initial_embed: discord.Embed,
        guild_invite: discord.Invite,
    ):
        super().__init__(timeout=120)
        self.user = user
        self.message = message
        self.initial_embed = initial_embed
        self.invite = guild_invite

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.user:
            await interaction.response.send_message("This view is not yours!", ephemeral=True)
            return False
        return await super().interaction_check(interaction)

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        await self.message.edit(view=None)
        return await super().on_timeout()

    @discord.ui.button(
        label='Features',
        custom_id='invite_features_btn',
        style=discord.ButtonStyle.blurple,
    )
    async def invite_features(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.disabled = True
        for child in self.children:
            if child.custom_id == "go_back":
                child.disabled = False

        full_features_list = [
            "ANIMATED_BANNER",
            "ANIMATED_ICON",
            "BANNER",
            "COMMERCE",
            "COMMUNITY",
            "DISCOVERABLE",
            "FEATURABLE",
            "INVITE_SPLASH",
            "MARKETPLACES_CONNECTION_ROLES",
            "MEMBER_VERIFICATION_GATE_ENABLED",
            "MONETIZATION_ENABLED",
            "MORE_EMOJI",
            "MORE_STICKER",
            "NEWS",
            "PARTNERED",
            "PRIVATE_THREADS",
            "PREVIEW_ENABLED",
            "ROLE_ICONS",
            "TICKETED_EVENTS_ENABLED",
            "VANITY_URL",
            "VERIFIED",
            "VIP_REGIONS",
            "WELCOME_SCREEN_ENABLED",
            'ENABLED_DISCOVERABLE_BEFORE',
            'AUTO_MODERATION',
            'MEMBER_PROFILES',
            'TEXT_IN_VOICE_ENABLED',
            'NEW_THREAD_PERMISSIONS',
            'THREE_DAY_THREAD_ARCHIVE',
            'SEVEN_DAY_THREAD_ARCHIVE',
            'THREADS_ENABLED',
            'APPLICATION_COMMAND_PERMISSIONS_V2',
        ]

        features = []
        for feat in self.invite.guild.features:
            if feat not in full_features_list:
                features.append(f'<:xmark:1030623974129946655> `{feat}`'.replace('_', ' '))
            else:
                features.append(f'<:checkmark:1030624012503625728> `{feat}`'.replace('_', ' '))

        embed = discord.Embed(
            title=f'Features for {self.invite.guild.name}', description='\n'.join(features), color=libs.pastel_color()
        )
        await interaction.response.edit_message(content=None, embed=embed, view=self)

    @discord.ui.button(
        label='Back',
        custom_id='go_back',
        style=discord.ButtonStyle.red,
        disabled=True,
    )
    async def go_back(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.disabled = True
        for child in self.children:
            if child.custom_id == 'invite_features_btn':
                child.disabled = False

        await interaction.response.edit_message(content=None, embed=self.initial_embed, view=self)


class Testing(commands.Cog, name="Testing"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def ii(self, ctx, invite: str):
        fetching = await ctx.send("Fetching Invite Info...")
        inv = await self.bot.fetch_invite(invite, with_counts=True, with_expiration=True)
        embed = discord.Embed(
            title=f"Invite Info",
            description=f"Invite info below provided via [{inv.code}](https://discord.gg/{inv.code})",
            color=libs.pastel_color(),
        )
        guild_info = f"""
**Name/ID:** [{inv.guild.name}](https://discord.gg/{inv.code}) `({inv.guild.id})`
**Created:** {discord.utils.format_dt(inv.guild.created_at)}
**Description:** `{inv.guild.description if inv.guild.description else 'No guild description found!'}`
**Users Online:** `{inv.approximate_presence_count:,}`
**Member Count:** `{inv.approximate_member_count:,}`
"""
        try:
            inviter_info = f"""
**Name/ID:** {inv.inviter} `({inv.inviter.id})`
**Registered:** {discord.utils.format_dt(inv.inviter.created_at)}
"""
        except AttributeError:
            inviter_info = 'I could not fetch any inviter info!\nThis could be due to a vanity invite.'

        embed.add_field(name="Inviter Info", value=inviter_info, inline=True)
        embed.add_field(name="Guild Info", value=guild_info, inline=True)
        embed.set_footer(text=f"Invite of {inv.guild.name}")
        await fetching.edit(
            content=None,
            embed=embed,
            view=InviteInfoView(user=ctx.author, message=fetching, initial_embed=embed, guild_invite=inv),
        )


async def setup(bot):
    await bot.add_cog(Testing(bot))
