from __future__ import annotations

import asyncio
import logging
import re
from urllib.parse import quote

import aiohttp

from config import HTTP_USER_AGENT

logger = logging.getLogger("pixeldrain")

PIXELDRAIN_RE = re.compile(r"^https?://pixeldrain\.com/d/([A-Za-z0-9]{8})(?:/.*)?$")


class PixeldrainAPIError(RuntimeError):
    pass


def extract_share_id(url_or_id: str) -> str:
    value = url_or_id.strip()
    match = PIXELDRAIN_RE.match(value)
    if match:
        return match.group(1)

    if re.fullmatch(r"[A-Za-z0-9]{8}", value):
        return value

    raise ValueError("不是有效的 pixeldrain 資料夾網址或 8 碼 share ID")


def encode_path(path: str) -> str:
    path = path.strip("/")
    if not path:
        raise ValueError("path is empty")
    return "/".join(quote(part, safe="") for part in path.split("/"))


def stat_url(path: str) -> str:
    return f"https://pixeldrain.com/api/filesystem/{encode_path(path)}?stat"


async def fetch_stat(session: aiohttp.ClientSession, path: str, retries: int = 3) -> dict:
    last_error: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            async with session.get(
                stat_url(path),
                timeout=aiohttp.ClientTimeout(total=30),
                headers={"User-Agent": HTTP_USER_AGENT},
            ) as resp:
                if resp.status >= 400:
                    body = await resp.text()
                    raise PixeldrainAPIError(f"HTTP {resp.status}: {body[:300]}")
                payload = await resp.json()
                if not isinstance(payload, dict):
                    raise PixeldrainAPIError("Unexpected JSON payload")
                return payload
        except (aiohttp.ClientError, asyncio.TimeoutError, PixeldrainAPIError) as exc:
            last_error = exc
            logger.warning("fetch_stat failed for %s attempt %s/%s: %s", path, attempt, retries, exc)
            if attempt < retries:
                await asyncio.sleep(1.5 * attempt)

    raise PixeldrainAPIError(f"Failed to fetch stat for {path}: {last_error}")


async def walk_folder(session: aiohttp.ClientSession, share_id: str) -> dict[str, dict]:
    results: dict[str, dict] = {}
    pending_dirs = [share_id]
    visited_dirs: set[str] = set()

    while pending_dirs:
        current = pending_dirs.pop()
        if current in visited_dirs:
            continue
        visited_dirs.add(current)

        data = await fetch_stat(session, current)
        children = data.get("children", [])
        if not isinstance(children, list):
            raise PixeldrainAPIError(f"Unexpected children payload for {current}")

        for node in children:
            if not isinstance(node, dict):
                continue

            node_path = node.get("path")
            if not node_path:
                continue

            results[node_path] = {
                "name": node.get("name"),
                "node_type": node.get("type"),
                "modified": node.get("modified"),
                "file_size": node.get("file_size"),
                "sha256_sum": node.get("sha256_sum"),
            }

            if node.get("type") == "dir":
                pending_dirs.append(node_path)

    return results
