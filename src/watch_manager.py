from __future__ import annotations

import asyncio
import datetime as dt
import logging

import aiohttp
import discord
from discord.ext import tasks

from src import db
from src.diff_engine import diff_snapshot
from src.models import WatchRecord
from src.notifier import build_diff_embed, build_error_embed
from src.pixeldrain_client import PixeldrainAPIError, walk_folder

logger = logging.getLogger("watch_manager")


class WatchManager:
    def __init__(self, bot) -> None:
        self.bot = bot
        self._run_lock = asyncio.Lock()
        self._loop = tasks.loop(seconds=60)(self._tick)
        self._loop.before_loop(self._before_tick)

    def start(self) -> None:
        if not self._loop.is_running():
            self._loop.start()

    def stop(self) -> None:
        self._loop.cancel()

    async def _before_tick(self) -> None:
        await self.bot.wait_until_ready()

    async def _tick(self) -> None:
        await self.scan_due_watches()

    async def scan_due_watches(self) -> None:
        if self._run_lock.locked():
            return

        async with self._run_lock:
            watches = await db.list_watches(enabled_only=True)
            if not watches:
                return

            async with aiohttp.ClientSession() as session:
                now = dt.datetime.now(dt.timezone.utc)
                for watch in watches:
                    if not self._is_due(watch, now):
                        continue
                    await self._scan_one(session, watch, send_update=True)

    def _is_due(self, watch: WatchRecord, now: dt.datetime) -> bool:
        if not watch.last_scan_ts:
            return True

        try:
            last = dt.datetime.fromisoformat(watch.last_scan_ts)
        except ValueError:
            return True

        return (now - last).total_seconds() >= watch.interval_sec

    async def manual_scan(self, watch_id: int) -> tuple[bool, str]:
        async with self._run_lock:
            watch = await db.get_watch_by_id(watch_id)
            if not watch:
                return False, "找不到這個 watch_id"

            async with aiohttp.ClientSession() as session:
                try:
                    changed = await self._scan_one(session, watch, send_update=True)
                except Exception as exc:
                    logger.exception("manual_scan failed: %s", exc)
                    return False, f"掃描失敗：{exc}"

        return True, "有變更，已發送通知" if changed else "掃描完成，沒有發現變更"

    async def _scan_one(self, session: aiohttp.ClientSession, watch: WatchRecord, send_update: bool) -> bool:
        old_snapshot = await db.get_snapshot(watch.id)
        label = watch.label or watch.share_id

        try:
            new_snapshot = await walk_folder(session, watch.share_id)
        except (aiohttp.ClientError, asyncio.TimeoutError, PixeldrainAPIError, RuntimeError) as exc:
            error_text = str(exc)
            logger.warning("scan failed for watch_id=%s share_id=%s: %s", watch.id, watch.share_id, error_text)
            await db.update_last_scan(watch.id, self._utc_now_iso(), error_text)
            channel = await self._get_channel(watch.channel_id)
            if channel:
                await channel.send(embed=build_error_embed(label, watch.share_id, error_text))
            return False

        diff = diff_snapshot(old_snapshot, new_snapshot)

        if old_snapshot and send_update and (diff.added or diff.removed or diff.changed):
            channel = await self._get_channel(watch.channel_id)
            if channel:
                await channel.send(
                    embed=build_diff_embed(
                        label=label,
                        share_id=watch.share_id,
                        diff=diff,
                        new_snapshot=new_snapshot,
                        old_snapshot=old_snapshot,
                    )
                )

        await db.replace_snapshot(watch.id, new_snapshot)
        await db.update_last_scan(watch.id, self._utc_now_iso(), None)

        return bool(old_snapshot and (diff.added or diff.removed or diff.changed))

    async def _get_channel(self, channel_id: int) -> discord.abc.Messageable | None:
        channel = self.bot.get_channel(channel_id)
        if channel is not None:
            return channel
        try:
            fetched = await self.bot.fetch_channel(channel_id)
            return fetched
        except discord.DiscordException:
            logger.warning("Unable to fetch channel %s", channel_id)
            return None

    @staticmethod
    def _utc_now_iso() -> str:
        return dt.datetime.now(dt.timezone.utc).isoformat()