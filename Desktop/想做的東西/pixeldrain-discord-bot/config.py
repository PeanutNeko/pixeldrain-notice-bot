from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "").strip()
DEV_GUILD_ID = int(os.getenv("DEV_GUILD_ID", "0") or 0)
DEFAULT_CHANNEL_ID = int(os.getenv("DEFAULT_CHANNEL_ID", "0") or 0)
DATABASE_PATH = os.getenv("DATABASE_PATH", str(DATA_DIR / "bot.db"))
DEFAULT_INTERVAL_SEC = max(60, int(os.getenv("DEFAULT_INTERVAL_SEC", "300") or 300))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
HTTP_USER_AGENT = os.getenv("HTTP_USER_AGENT", "PixeldrainDiscordWatchBot/1.0")

SEED_WATCH_IDS = [
    item.strip()
    for item in os.getenv("SEED_WATCH_IDS", "").split(",")
    if item.strip()
]

EMBED_ITEM_LIMIT = 10
COMMAND_SYNC_GLOBAL = DEV_GUILD_ID == 0
