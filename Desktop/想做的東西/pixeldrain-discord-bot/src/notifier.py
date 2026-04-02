from __future__ import annotations

import discord

from config import EMBED_ITEM_LIMIT
from src.models import DiffResult


def _short_name(path: str, snapshot: dict[str, dict]) -> str:
    name = snapshot.get(path, {}).get("name")
    return name or path.rsplit("/", 1)[-1] or path


def build_diff_embed(
    label: str,
    share_id: str,
    diff: DiffResult,
    new_snapshot: dict[str, dict],
    old_snapshot: dict[str, dict],
) -> discord.Embed:
    embed = discord.Embed(
        title=f"{label} 有更新",
        description=f"share_id: `{share_id}`",
    )
    embed.add_field(name="新增", value=str(len(diff.added)), inline=True)
    embed.add_field(name="刪除", value=str(len(diff.removed)), inline=True)
    embed.add_field(name="更新", value=str(len(diff.changed)), inline=True)

    if diff.added:
        value = "\n".join(
            f"🟢 `{_short_name(path, new_snapshot)}`\n`{path}`"
            for path in diff.added[:EMBED_ITEM_LIMIT]
        )
        if len(diff.added) > EMBED_ITEM_LIMIT:
            value += f"\n…其餘 {len(diff.added) - EMBED_ITEM_LIMIT} 項略過"
        embed.add_field(name="新增明細", value=value[:1024], inline=False)

    if diff.removed:
        value = "\n".join(
            f"🔴 `{_short_name(path, old_snapshot)}`\n`{path}`"
            for path in diff.removed[:EMBED_ITEM_LIMIT]
        )
        if len(diff.removed) > EMBED_ITEM_LIMIT:
            value += f"\n…其餘 {len(diff.removed) - EMBED_ITEM_LIMIT} 項略過"
        embed.add_field(name="刪除明細", value=value[:1024], inline=False)

    if diff.changed:
        chunks = []
        for path in diff.changed[:EMBED_ITEM_LIMIT]:
            old_item = old_snapshot.get(path, {})
            new_item = new_snapshot.get(path, {})
            chunks.append(
                f"🟡 `{_short_name(path, new_snapshot)}`\n`{path}`\n"
                f"size: {old_item.get('file_size')} → {new_item.get('file_size')} | "
                f"modified: {old_item.get('modified')} → {new_item.get('modified')}"
            )
        value = "\n".join(chunks)
        if len(diff.changed) > EMBED_ITEM_LIMIT:
            value += f"\n…其餘 {len(diff.changed) - EMBED_ITEM_LIMIT} 項略過"
        embed.add_field(name="更新明細", value=value[:1024], inline=False)

    return embed


def build_error_embed(label: str, share_id: str, error_text: str) -> discord.Embed:
    return discord.Embed(
        title=f"{label} 掃描失敗",
        description=f"share_id: `{share_id}`\n```\n{error_text[:900]}\n```",
    )
