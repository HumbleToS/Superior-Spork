import random

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from utils import libs
from utils.checks import *


class Nightmare(commands.Cog, name="nightmare"):
    def __init__(self, bot):
        self.bot = bot
        self._last_result = None

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild != self.bot.get_guild(812691071867944971):
            return
        x = discord.utils.get(message.guild.roles, id=875412407822979154)
        for i in message.guild.members:
            if x in i.roles and (
                i.display_name.lower() == message.content.lower() or i.name.lower() == message.content.lower()
            ):
                await message.reply(
                    i.mention,
                    allowed_mentions=discord.AllowedMentions(everyone=False, replied_user=False),
                )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild == self.bot.get_guild(812691071867944971):
            async with aiohttp.ClientSession() as session:
                webhook = discord.Webhook.from_url(
                    "https://discord.com/api/webhooks/1006716255924928624/hmt-3XNWPPAMEdFwWcXpDKRfNIklhLwn6SEndqbNebSM0tvgpUXQGaZJBSDGthhm9862",
                    session=session,
                )
                welcome_embed = discord.Embed(
                    description="・Check out 𝘕𝘪𝘨𝘩𝘵𝘮𝘢𝘳𝘦 to get information about our server!\n"
                    "・Get your <#850618427776434216> & <#850618429178511380>.",
                    color=0x7821B3,
                    timestamp=member.joined_at,
                )
                welcome_embed.set_author(name=member.guild.name, icon_url=member.guild.icon.url)
                welcome_embed.set_thumbnail(url=member.guild.icon.url)
                welcome_embed.set_footer(text="We hope you enjoy your stay in our server!")

                await webhook.send(
                    f"{member.mention}: <a:loveglow_DV:901915060966940722>",
                    embed=welcome_embed,
                    username=member.guild.name,
                    avatar_url="https://cdn.discordapp.com/attachments/782290693543428117/1006726913173246113/bcc0da927e66.jpg",
                )

    @commands.hybrid_command(name="nightmare", description="Help command for Nightmare server.")
    @app_commands.guilds(812691071867944971)
    @is_nightmare()
    async def nightmare_help(self, ctx):
        nm_cog = self.bot.get_cog("nightmare")
        nightmare_commands = [
            f"`{command.name}` {f' - {command.description}' if command.description else ''} {'' if len(command.aliases) == 0 else f'`{command.aliases}`'} {'' if command.usage is None else f'`[{command.usage}]`'}"
            for command in nm_cog.walk_commands()
        ]

        em = discord.Embed(
            title=f"{ctx.guild.name}'s Commands",
            description="\n".join(nightmare_commands),
            color=9962415,
        )

        return await ctx.send(embed=em)

    @commands.hybrid_command(name="rando", description="Ping a random person")
    @commands.cooldown(1, 30, type=commands.BucketType.user)
    @app_commands.guilds(812691071867944971)
    @is_nightmare()
    async def random_ping(self, ctx):
        await ctx.send(f"{random.choice(ctx.guild.members).mention}, You got randomly pinged! || I hate you all. ||")

    @commands.hybrid_group(name="hmblcult", aliases=["hc"], description="Humble's Cult")
    @app_commands.guilds(812691071867944971)
    @is_nightmare()
    @is_real_owner()
    async def humble_cult(self, ctx):
        humbles_cult = discord.utils.get(ctx.guild.roles, id=986825517900648459)
        added = []
        removed = []
        accepted_names = ["Humble", "jaden"]
        for i in ctx.guild.members:
            if i.display_name in accepted_names:
                if humbles_cult not in i.roles:
                    await i.add_roles(humbles_cult)
                    added.append(f"`{i.name}`")
            elif humbles_cult in i.roles:
                if i.id == 613202332880207872:
                    continue
                await i.remove_roles(humbles_cult)
                removed.append(f"`{i.name}`")
        em = discord.Embed(
            title="Humble's Cult",
            description="Users who were added/removed",
            color=16777215,
        )

        if libs.check_list(added):
            em.add_field(name="Added", value="No one was added", inline=True)
        else:
            em.add_field(name="Added", value="\n".join(added), inline=True)
        if libs.check_list(removed):
            em.add_field(name="Removed", value="No one was removed", inline=True)
        else:
            em.add_field(name="Removed", value="\n".join(removed), inline=True)

        em.set_footer(text=f"There are {len(humbles_cult.members)} Humble's in Humble's Cult")
        await ctx.send(embed=em)

    @humble_cult.command(name="list")
    @app_commands.guilds(812691071867944971)
    @is_nightmare()
    @is_real_owner()
    async def list_cult_members(self, ctx):
        humbles_cult = discord.utils.get(ctx.guild.roles, id=986825517900648459)
        cult_members = [f"`{i}`" for i in humbles_cult.members]
        em = discord.Embed(
            title="Humble's Cult Members",
            description="List of members in the cult",
            color=16777215,
        )

        em.add_field(
            name=f"Humble's | {len(cult_members)}",
            value="\n".join(cult_members),
            inline=False,
        )

        await ctx.send(embed=em)

    @humble_cult.command(name="ping")
    @is_nightmare()
    @is_real_owner()
    async def ping_cult_members(self, ctx):
        humbles_cult = discord.utils.get(ctx.guild.roles, id=986825517900648459)
        ping_members = [f"{i.mention}" for i in humbles_cult.members]
        embed = discord.Embed(description="Humble's Cult members have been pinged", color=16777215)

        await ctx.send(", ".join(ping_members), embed=embed)


async def setup(bot):
    await bot.add_cog(Nightmare(bot))
