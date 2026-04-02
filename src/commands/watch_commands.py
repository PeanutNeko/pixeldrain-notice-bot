from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from src import db
from src.pixeldrain_client import extract_share_id


class WatchCommands(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(name="watch_add", description="新增或覆蓋一個 pixeldrain 監視目標")
    @app_commands.describe(
        url="pixeldrain 資料夾網址或 8 碼 share ID",
        channel="要發送通知的頻道",
        interval_min="掃描間隔（分鐘）",
        label="顯示名稱，可省略",
    )
    async def watch_add(
        self,
        interaction: discord.Interaction,
        url: str,
        channel: discord.TextChannel,
        interval_min: app_commands.Range[int, 1, 1440] = 5,
        label: str | None = None,
    ) -> None:
        try:
            share_id = extract_share_id(url)
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return

        watch_id = await db.upsert_watch(
            share_id=share_id,
            label=label or share_id,
            channel_id=channel.id,
            interval_sec=interval_min * 60,
        )
        await interaction.response.send_message(
            f"已儲存 watch [{watch_id}] `{share_id}` → {channel.mention}，每 {interval_min} 分鐘掃描一次。",
            ephemeral=True,
        )

    @app_commands.command(name="watch_list", description="列出目前所有監視項目")
    async def watch_list(self, interaction: discord.Interaction) -> None:
        watches = await db.list_watches(enabled_only=False)
        if not watches:
            await interaction.response.send_message("目前沒有監視項目。", ephemeral=True)
            return

        lines = []
        for watch in watches:
            lines.append(
                f"[{watch.id}] `{watch.share_id}` | {watch.label or '-'} | "
                f"<#{watch.channel_id}> | {watch.interval_sec // 60} 分 | "
                f"{'啟用' if watch.enabled else '停用'}"
            )

        message = "\n".join(lines)
        await interaction.response.send_message(message[:1900], ephemeral=True)

    @app_commands.command(name="watch_remove", description="刪除監視項目")
    async def watch_remove(
        self,
        interaction: discord.Interaction,
        watch_id: int,
    ) -> None:
        ok = await db.delete_watch(watch_id)
        if not ok:
            await interaction.response.send_message("找不到這個 watch_id。", ephemeral=True)
            return
        await interaction.response.send_message(f"已刪除 watch [{watch_id}]。", ephemeral=True)

    @app_commands.command(name="watch_enable", description="啟用監視項目")
    async def watch_enable(self, interaction: discord.Interaction, watch_id: int) -> None:
        ok = await db.set_watch_enabled(watch_id, True)
        if not ok:
            await interaction.response.send_message("找不到這個 watch_id。", ephemeral=True)
            return
        await interaction.response.send_message(f"已啟用 watch [{watch_id}]。", ephemeral=True)

    @app_commands.command(name="watch_disable", description="停用監視項目")
    async def watch_disable(self, interaction: discord.Interaction, watch_id: int) -> None:
        ok = await db.set_watch_enabled(watch_id, False)
        if not ok:
            await interaction.response.send_message("找不到這個 watch_id。", ephemeral=True)
            return
        await interaction.response.send_message(f"已停用 watch [{watch_id}]。", ephemeral=True)

    @app_commands.command(name="watch_scan", description="立刻手動掃描一次")
    async def watch_scan(self, interaction: discord.Interaction, watch_id: int) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)
        manager = getattr(self.bot, "watch_manager", None)
        if manager is None:
            await interaction.followup.send("watch manager 尚未初始化。", ephemeral=True)
            return

        ok, message = await manager.manual_scan(watch_id)
        await interaction.followup.send(message, ephemeral=True)

    @app_commands.command(name="watch_help", description="顯示使用說明")
    async def watch_help(self, interaction: discord.Interaction) -> None:
        text = (
            "/watch_add url channel interval_min label\n"
            "/watch_list\n"
            "/watch_remove watch_id\n"
            "/watch_enable watch_id\n"
            "/watch_disable watch_id\n"
            "/watch_scan watch_id"
        )
        await interaction.response.send_message(text, ephemeral=True)


async def setup(bot) -> None:
    await bot.add_cog(WatchCommands(bot))
