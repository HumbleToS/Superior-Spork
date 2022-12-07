import discord
from discord.ext import commands


class MyServer(commands.Cog, name="ass"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id != 953535172941324298:
            return
        if member.bot:
            bot_adds = self.bot.get_channel(958068139986411581)
            bot_adds_em = discord.Embed(
                title="Discord Bot Added",
                description=f"{member.name}#{member.discriminator} `({member.id})`",
                color=0xF87676,
            )
            return await bot_adds.send(f"{member.guild.owner.mention}", embed=bot_adds_em)
        channel = self.bot.get_channel(953535172941324301)
        luversRole = discord.utils.get(member.guild.roles, name="Luvers")
        await member.add_roles(luversRole)
        joinEmbed = discord.Embed(
            description=f"Read {self.bot.get_channel(953743551852851271).mention} for information & rules!\nCheck out [Roles] & [Colors] for more <3",
            color=0xF87676,
        )
        joinEmbed.set_author(name="𝙰 𝚂 𝚂", icon_url=member.guild.icon.url)
        await channel.send(member.mention, embed=joinEmbed, delete_after=15)


async def setup(bot):
    await bot.add_cog(MyServer(bot))
