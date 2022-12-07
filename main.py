import asyncio
import datetime
import json
import logging
import logging.handlers
import os
import pathlib
import sys

import aiohttp
import asyncpg
import discord
from discord.ext import commands

from utils import db, libs

CONFIG_FILENAME = "config.json"
current_working_dir = pathlib.Path(__file__).parent
config_path = current_working_dir / CONFIG_FILENAME

with open(config_path) as fp:
    config = json.load(fp)

log_fmt = logging.Formatter(
    fmt="%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Logging stolen from Inferior-Spork (Made by fretgfr)

sh = logging.StreamHandler(sys.stdout)
sh.setLevel(logging.DEBUG)
sh.setFormatter(log_fmt)

max_bytes = 4 * 1024 * 1024  # 4 MB
rfh = logging.handlers.RotatingFileHandler("logs/superior-spork.log", maxBytes=max_bytes, backupCount=10)
rfh.setLevel(logging.DEBUG)
rfh.setFormatter(log_fmt)

if config.get("testing"):
    HANDLER = sh
else:
    HANDLER = rfh

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(HANDLER)

_logger = logging.getLogger(__name__)

# Defining intents and altering it for useless/un-used intents
intents = discord.Intents.all()
intents.typing = False


class SuperiorSpork(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix=libs.callable_prefix,
            intents=intents,
            case_insensitive=True,
            max_messages=5000,
            owner_ids=[739219467455823921, 524016475661664256, 101118549958877184, 683530527239962627],
        )
        self.config = config
        self.prefixes = {}
        self.snipes = {}
        self.edit_snipes = {}
        self.session = aiohttp.ClientSession()
        self.start_time = datetime.datetime.now(datetime.timezone.utc)
        self.time_now = discord.utils.utcnow()

    async def on_message_edit(self, before, after):
        await self.process_commands(after)

    async def on_guild_join(self, guild):
        if guild.member_count < 2:
            return await guild.leave()
        try:
            added_by = await libs.get_added_by(self, guild)
        except discord.errors.Forbidden:
            added_by = None
        async with self.db_pool.acquire() as connection:
            async with connection.transaction():
                await connection.execute(
                    "INSERT INTO guilds(id,added_by,prefix) VALUES($1,$2,$3) ON CONFLICT (id) DO UPDATE SET (added_by,prefix) = ($2,$3)",
                    guild.id,
                    added_by,
                    self.config.get("default_prefix"),
                )
                self.prefixes[guild.id] = self.config.get("default_prefix")

    async def on_guild_remove(self, guild):
        async with self.db_pool.acquire() as connection:
            async with connection.transaction():
                await connection.execute("DELETE FROM guilds WHERE id = $1", guild.id)
                self.prefixes.pop(guild.id, None)

    async def setup_hook(self) -> None:
        ### Credit: https://github.com/AbstractUmbra
        for file in sorted(pathlib.Path("cogs").glob("**/[!_]*.py")):
            cog = ".".join(file.parts).removesuffix(".py")
            try:
                await self.load_extension(cog)
                print(f"Loaded {cog}")
            except Exception as error:
                _logger.exception(f"Failed to load cog: {cog}\n{error}")
        ###

        os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
        os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"

        await self.load_extension("jishaku")

    async def close(self) -> None:
        await self.session.close()
        await super().close()

    async def run(self) -> None:
        """
        Note: it is not a good idea to overwrite run() for most cases but since this is personal it will stay as so
        """
        db_creds = config.get("db_credentials")
        await db.build(
            user=db_creds["user"],
            password=db_creds["password"],
            database=db_creds["database"],
            host=db_creds["host"],
        )
        async with self, asyncpg.create_pool(**db_creds) as db_pool:
            self.db_pool = db_pool
            async with self.db_pool.acquire() as conn:
                async with conn.transaction():
                    guild_prefixes = await self.db_pool.fetch("SELECT * FROM guilds")
                    if guild_prefixes:
                        guild_prefixes = [dict(row) for row in guild_prefixes]
                        for prefix in guild_prefixes:
                            if prefix["prefix"] is None:
                                prefix["prefix"] = self.config.get("default_prefix")
                                await conn.execute(
                                    "UPDATE guilds SET prefix = $1 WHERE id = $2",
                                    prefix["prefix"],
                                    prefix["id"],
                                )
                            self.prefixes[prefix["id"]] = prefix["prefix"]
            await self.start(config.get("token"), reconnect=True)


async def main():
    bot = SuperiorSpork()
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())
