from __future__ import annotations

import logging
import discord
from discord.ext import commands

from config import COMMAND_SYNC_GLOBAL, DEV_GUILD_ID, DISCORD_TOKEN
from src.db import init_db
from src.logging_config import setup_logging
from src.watch_manager import WatchManager


class PixeldrainWatchBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self.logger = logging.getLogger("bot")
        self.watch_manager: WatchManager | None = None

    async def setup_hook(self) -> None:
        await init_db()
        await self.load_extension("src.commands.watch_commands")

        synced = await self.tree.sync()
        self.logger.info("Synced %s global command(s)", len(synced))

        self.watch_manager = WatchManager(self)
        self.watch_manager.start()

    async def close(self) -> None:
        if self.watch_manager:
            self.watch_manager.stop()
        await super().close()


def main() -> None:
    setup_logging()
    if not DISCORD_TOKEN:
        raise RuntimeError("DISCORD_TOKEN is empty. Please fill .env first.")

    bot = PixeldrainWatchBot()
    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
